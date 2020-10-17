"""Provides a light for Home Connect."""
import logging
from math import ceil

from homeconnect.api import HomeConnectError

import homeassistant.util.color as color_util
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    LightEntity,
)

from .const import (
    BSH_AMBIENTLIGHTBRIGHTNESS,
    BSH_AMBIENTLIGHTCOLOR,
    BSH_AMBIENTLIGHTCOLOR_CUSTOMCOLOR,
    BSH_AMBIENTLIGHTCUSTOMCOLOR,
    BSH_AMBIENTLIGHTENABLED,
    COOKING_LIGHTING,
    COOKING_LIGHTINGBRIGHTNESS,
    DOMAIN,
)
from .entity import HomeConnectEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Home Connect light."""

    def get_entities():
        """Get a list of entities."""
        entities = []
        hc_api = hass.data[DOMAIN][config_entry.entry_id]
        for device_dict in hc_api.devices:
            entity_dicts = device_dict.get("entities", {}).get("light", [])
            entity_list = [HomeConnectLight(**d) for d in entity_dicts]
            entities += entity_list
        return entities

    async_add_entities(await hass.async_add_executor_job(get_entities), True)


class HomeConnectLight(HomeConnectEntity, LightEntity):
    """Light for Home Connect."""

    def __init__(self, device, desc, ambient):
        """Initialize the entity."""
        super().__init__(device, desc)
        self._state = None
        self._brightness = None
        self._hs_color = None
        self._ambient = ambient
        if self._ambient:
            self._brightnesskey = BSH_AMBIENTLIGHTBRIGHTNESS
            self._key = BSH_AMBIENTLIGHTENABLED
            self._customcolorkey = BSH_AMBIENTLIGHTCUSTOMCOLOR
            self._colorkey = BSH_AMBIENTLIGHTCOLOR
        else:
            self._brightnesskey = COOKING_LIGHTINGBRIGHTNESS
            self._key = COOKING_LIGHTING
            self._customcolorkey = None
            self._colorkey = None

    @property
    def is_on(self):
        """Return true if the light is on."""
        return bool(self._state)

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self):
        """Return the color property."""
        return self._hs_color

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._ambient:
            return SUPPORT_BRIGHTNESS | SUPPORT_COLOR
        return SUPPORT_BRIGHTNESS

    async def async_turn_on(self, **kwargs):
        """Switch the light on, change brightness, change color."""
        if self._ambient:
            if ATTR_BRIGHTNESS in kwargs or ATTR_HS_COLOR in kwargs:
                try:
                    await self.hass.async_add_executor_job(
                        self.device.appliance.set_setting,
                        self._colorkey,
                        BSH_AMBIENTLIGHTCOLOR_CUSTOMCOLOR,
                    )
                except HomeConnectError as err:
                    _LOGGER.error("Error while trying selecting customcolor: %s", err)
                if self._brightness != None:
                    brightness = 10 + ceil(self._brightness / 255 * 90)
                    if ATTR_BRIGHTNESS in kwargs:
                        brightness = 10 + ceil(kwargs[ATTR_BRIGHTNESS] / 255 * 90)

                    hs_color = self._hs_color
                    if ATTR_HS_COLOR in kwargs:
                        hs_color = kwargs[ATTR_HS_COLOR]

                    if hs_color != None:
                        rgb = color_util.color_hsv_to_RGB(*hs_color, brightness)
                        hex = color_util.color_rgb_to_hex(rgb[0], rgb[1], rgb[2])
                        try:
                            await self.hass.async_add_executor_job(
                                self.device.appliance.set_setting,
                                self._customcolorkey,
                                "#" + hex,
                            )
                        except HomeConnectError as err:
                            _LOGGER.error("Error while trying setting the color: %s", err)
                            self._state = False
            else:
                _LOGGER.debug("Tried to switch light on for: %s", self.name)
                try:
                    await self.hass.async_add_executor_job(
                        self.device.appliance.set_setting, self._key, True,
                    )
                except HomeConnectError as err:
                    _LOGGER.error("Error while trying to turn on ambient light: %s", err)
                    self._state = False

        elif ATTR_BRIGHTNESS in kwargs:
            _LOGGER.debug("Tried to change brightness for: %s", self.name)
            """Convert Home Assistant brightness (0-255) to Home Connect brightness (10-100)."""
            brightness = 10 + ceil(kwargs[ATTR_BRIGHTNESS] / 255 * 90)
            try:
                await self.hass.async_add_executor_job(
                    self.device.appliance.set_setting, self._brightnesskey, brightness,
                )
            except HomeConnectError as err:
                _LOGGER.error("Error while trying set the brightness: %s", err)
                self._state = False
                self._brightness = None
        else:
            _LOGGER.debug("Tried to switch light on for: %s", self.name)
            try:
                await self.hass.async_add_executor_job(
                    self.device.appliance.set_setting, self._key, True,
                )
            except HomeConnectError as err:
                _LOGGER.error("Error while trying to turn on light: %s", err)
                self._state = False

        self.async_entity_update()

    async def async_turn_off(self, **kwargs):
        """Switch the light off."""
        _LOGGER.debug("tried to switch light off for: %s", self.name)
        try:
            await self.hass.async_add_executor_job(
                self.device.appliance.set_setting, self._key, False,
            )
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to turn off light: %s", err)
            self._state = True
        self.async_entity_update()

    async def async_update(self):
        """Update the light's status."""
        if self.device.appliance.status.get(self._key, {}).get("value") is True:
            self._state = True
        elif self.device.appliance.status.get(self._key, {}).get("value") is False:
            self._state = False
        else:
            self._state = None

        _LOGGER.debug("Updated, new light state: %s", self._state)

        if self._ambient:
            color = self.device.appliance.status.get(self._customcolorkey, {})

            if not color:
                self._hs_color = None
                self._brightness = None
            else:
                colorvalue = color.get("value")[1:]
                rgb = color_util.rgb_hex_to_rgb_list(colorvalue)
                hsv = color_util.color_RGB_to_hsv(rgb[0], rgb[1], rgb[2])
                self._hs_color = [hsv[0], hsv[1]]
                self._brightness = ceil((hsv[2] - 10) * 255 / 90)
                _LOGGER.debug("Updated, new brightness: %s", self._brightness)

        else:
            brightness = self.device.appliance.status.get(self._brightnesskey, {})
            if brightness is None:
                self._brightness = None
            else:
                self._brightness = ceil((brightness.get("value") - 10) * 255 / 90)
            _LOGGER.debug("Updated, new brightness: %s", self._brightness)

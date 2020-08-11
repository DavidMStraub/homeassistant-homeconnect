"""Provides a light for Home Connect."""
import logging
from math import ceil

from homeconnect.api import HomeConnectError

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    LightEntity,
    SUPPORT_BRIGHTNESS,
)

from .const import COOKING_LIGHTING, COOKING_LIGHTINGBRIGHTNESS, DOMAIN
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

    def __init__(self, device, desc):
        """Initialize the entity."""
        super().__init__(device, desc)
        self._state = None
        self._brightness = None

    @property
    def is_on(self):
        """Return true if the light is on."""
        return bool(self._state)

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    async def async_turn_on(self, **kwargs):
        """Switch the light on / change brightness."""
        if ATTR_BRIGHTNESS in kwargs:
            _LOGGER.debug("Tried to change brightness for: %s", self.name)
            """Convert Home Assistant brightness (0-255) to Home Connect brightness (10-100)"""
            brightness = 10 + ceil(kwargs[ATTR_BRIGHTNESS] / 255 * 90)
            try:
                await self.hass.async_add_executor_job(
                    self.device.appliance.set_setting,
                    COOKING_LIGHTINGBRIGHTNESS,
                    brightness,
                )
            except HomeConnectError as err:
                _LOGGER.error("Error while trying set the brightness: %s", err)
                self._state = False
                self._brightness = None
        else:
            _LOGGER.debug("Tried to switch light on for: %s", self.name)
            try:
                await self.hass.async_add_executor_job(
                    self.device.appliance.set_setting, COOKING_LIGHTING, True,
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
                self.device.appliance.set_setting, COOKING_LIGHTING, False,
            )
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to turn off light: %s", err)
            self._state = True
        self.async_entity_update()

    async def async_update(self):
        """Update the light's status."""
        if self.device.appliance.status.get(COOKING_LIGHTING, {}).get("value") is True:
            self._state = True
        elif (
            self.device.appliance.status.get(COOKING_LIGHTING, {}).get("value") is False
        ):
            self._state = False
        else:
            self._state = None
        brightness = self.device.appliance.status.get(COOKING_LIGHTINGBRIGHTNESS, {})
        if brightness is None:
            self._brightness = None
        else:
            self._brightness = ceil((brightness.get("value") - 10) * 255 / 90)
        _LOGGER.debug("Updated, new light state: %s", self._state)
        _LOGGER.debug("Updated, new brightness: %s", self._brightness)

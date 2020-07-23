"""Provides a light for Home Connect."""
import logging

from homeconnect.api import HomeConnectError

from homeassistant.components.light import LightEntity

from .const import (
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
            """if "Hood" in str(type(device_dict["device"])):
              entity_list += [HomeConnectLight(device_dict["device"])]"""
            entities += entity_list
        return entities

    async_add_entities(await hass.async_add_executor_job(get_entities), True)


class HomeConnectLight(HomeConnectEntity, LightEntity):
    """Light for Home Connect."""

    def __init__(self, device, desc):
        """Initialize the entity."""
        super().__init__(device, desc)
        self._state = None

    @property
    def is_on(self):
        """Return true if the light is on."""
        return bool(self._state)

    async def async_turn_on(self, **kwargs):
        """Switch the light on."""
        _LOGGER.debug("Tried to switch light on for: %s", self.name)
        try:
            await self.hass.async_add_executor_job(
                self.device.appliance.set_setting, COOKING_LIGHTING, True,
            )
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to turn on light of device: %s", err)
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
            _LOGGER.error("Error while trying to turn off light of device: %s", err)
            self._state = True
        self.async_entity_update()

    async def async_update(self):
        """Update the light's status."""
        if (
            self.device.appliance.status.get(COOKING_LIGHTING, {}).get("value")
            == True
        ):
            self._state = True
        elif (
            self.device.appliance.status.get(COOKING_LIGHTING, {}).get("value")
            == False
        ):
            self._state = False
        _LOGGER.debug("Updated, new light state: %s", self._state)

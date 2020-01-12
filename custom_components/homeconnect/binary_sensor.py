"""Provides a binary sensor for Home Connect.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/integrations/binary_sensor.homeconnect/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice, DEVICE_CLASS_DOOR

from .api import HomeConnectEntity
from .const import (
    DOMAIN,
    BINARY_SENSORS_ON_STATES,
    BINARY_SENSORS_OFF_STATES,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Home Connect binary sensor."""

    def get_entities():
        entities = []
        hc_api = hass.data[DOMAIN][config_entry.entry_id]
        for device_dict in hc_api.devices:
            entity_dicts = device_dict.get("entities", {}).get("binary_sensor", [])
            entity_list = [HomeConnectBinarySensor(**d) for d in entity_dicts]
            device = device_dict["device"]
            device.entities += entity_list
            entities += entity_list
        return entities

    async_add_entities(await hass.async_add_executor_job(get_entities), True)


class HomeConnectBinarySensor(HomeConnectEntity, BinarySensorDevice):
    """Binary sensor for Home Connect."""

    def __init__(self, device, name, key, device_class = None):
        """Initialize the entitiy."""
        super().__init__(device, name)
        self._device_class = device_class
        self._state = None
        self._key = key

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self._state)

    @property
    def available(self):
        """Return true if the binary sensor is available."""
        return self._state is not None

    def update(self):
        """Update the binary sensor's status."""
        state = self.device.appliance.status.get(self._key, {})
        if not state:
            self._state = None
        elif isinstance(state.get("value", None), bool):
            self._state = state.get("value", None)
        elif state.get("value", None) in BINARY_SENSORS_OFF_STATES:
            self._state = False
        elif state.get("value", None) in BINARY_SENSORS_ON_STATES:
            self._state = True
        else:
            _LOGGER.warning("Unexpected value for HomeConnect door state: %s", state)
            self._state = None
        _LOGGER.debug("Binary Sensor {} updated, new state: {}".format(self._name, self._state))

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

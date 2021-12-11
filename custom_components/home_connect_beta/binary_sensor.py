"""Provides a binary sensor for Home Connect."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import BSH_OPERATION_STATE, BSH_DOOR_STATE, DOMAIN
from .entity import HomeConnectEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Home Connect binary sensor."""

    def get_entities():
        entities = []
        hc_api = hass.data[DOMAIN][config_entry.entry_id]
        for device_dict in hc_api.devices:
            entity_dicts = device_dict.get("entities", {}).get("binary_sensor", [])
            # print(entity_dicts)
            #[_LOGGER.debug("hello %s", **d) for d in entity_dicts]
            entities += [HomeConnectBinarySensor(**d) for d in entity_dicts]
        return entities

    async_add_entities(await hass.async_add_executor_job(get_entities), True)


class HomeConnectBinarySensor(HomeConnectEntity, BinarySensorEntity):
    """Binary sensor for Home Connect."""

    def __init__(self, device, desc, device_class, states):
        """Initialize the entity."""
        super().__init__(device, desc)
        self._device_class = device_class
        self._state = None
        self._states = states
        _LOGGER.debug('states %s', states)


    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self._state)

    @property
    def available(self):
        """Return true if the binary sensor is available."""
        return self._state is not None

    async def async_update(self):
        """Update the binary sensor's status."""
        state = self.device.appliance.status.get(self._states['key'], {}).get(
            "value", None)

        if state in self._states['on']:
            self._state = True
        elif state in self._states['off']:
            self._state = False
        else:
            self._state = None
        _LOGGER.debug("Updated, new state: %s", self._state)

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

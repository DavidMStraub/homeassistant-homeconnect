"""
Provides a binary sensor for Home Connect

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.homeconnect/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from custom_components.homeconnect import DOMAIN as HOMECONNECT_DOMAIN
from custom_components.homeconnect import HomeConnectEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homeconnect']


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Home Connect binary sensor."""
    entities = []
    for device_dict in hass.data[HOMECONNECT_DOMAIN]['devices']:
        entity_dicts = device_dict.get('entities', {}).get('binary_sensor', [])
        entity_list = [HomeConnectBinarySensor(**d) for d in entity_dicts]
        device = device_dict['device']
        device.entities += entity_list
        entities += entity_list
    add_entities(entities, True)



class HomeConnectBinarySensor(HomeConnectEntity, BinarySensorDevice):
    def __init__(self, device, name, device_class):
        super().__init__(device, name)
        self._device_class = device_class
        self._state = None

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self._state )

    @property
    def available(self):
        return self._state is not None

    def update(self):
        state = self.device.appliance.status.get('BSH.Common.Status.DoorState', {})
        if state.get('value', None) in ['BSH.Common.EnumType.DoorState.Closed', 'BSH.Common.EnumType.DoorState.Locked']:
            self._state = False
        elif state.get('value', None) == 'BSH.Common.EnumType.DoorState.Open':
            self._state = True
        else:
            _LOGGER.warning("Unexpected value for HomeConnect door state: {}"
                            .format(state))
            self._state = None
        _LOGGER.debug("Updated, new state: {}".format(self._state))

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

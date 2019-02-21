"""
Provides a binary sensor for Home Connect

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.homeconnect/
"""
import logging

from custom_components.homeconnect import DOMAIN as HOMECONNECT_DOMAIN
from custom_components.homeconnect import HomeConnectEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homeconnect']


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Home Connect sensor."""
    entities = []
    for device_dict in hass.data[HOMECONNECT_DOMAIN]['devices']:
        entity_dicts = device_dict.get('entities', {}).get('sensor', [])
        entity_list = [HomeConnectSensor(**d) for d in entity_dicts]
        device = device_dict['device']
        device.entities += entity_list
        entities += entity_list
    add_entities(entities, True)



class HomeConnectSensor(HomeConnectEntity):
    def __init__(self, device, name, key, unit):
        super().__init__(device, name)
        self._state = None
        self._key = key
        self._unit = unit

    @property
    def state(self):
        """Return true if the binary sensor is on."""
        return self._state

    @property
    def available(self):
        return self._state is not None

    def update(self):
        status = self.device.appliance.status
        if self._key not in status:
            self._state = None
        else:
            self._state = status[self._key].get('value', None)
        _LOGGER.debug("Updated, new state: {}".format(self._state))
    #
    # @property
    # def device_class(self):
    #     """Return the device class."""
    #     return self._device_class

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        if self._unit == 's':
            return 'mdi:progress-clock'
        if self._unit == '%':
            return 'mdi:timelapse'

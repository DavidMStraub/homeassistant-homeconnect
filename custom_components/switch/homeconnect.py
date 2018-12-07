"""
Provides a binary sensor for Home Connect

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.homeconnect/
"""
import logging

from homeassistant.components.switch import SwitchDevice
from custom_components.homeconnect import DOMAIN as HOMECONNECT_DOMAIN
from custom_components.homeconnect import HomeConnectEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homeconnect']


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Home Connect binary sensor."""
    entities = []
    for device_dict in hass.data[HOMECONNECT_DOMAIN]['devices']:
        entities += [HomeConnectPowerSwitch(device_dict['device'])]
        entity_dicts = device_dict.get('entities', {}).get('switch', [])
        entity_list = [HomeConnectProgramSwitch(**d) for d in entity_dicts]
        device = device_dict['device']
        device.entities += entity_list
        entities += entity_list
    add_entities(entities, True)



class HomeConnectProgramSwitch(HomeConnectEntity, SwitchDevice):
    def __init__(self, device, program_name):
        name = ' '.join([device.appliance.name,
                         'Program',
                         program_name.split('.')[-1]])
        super().__init__(device, name)
        self.program_name = program_name
        self._state = None
        self._remote_allowed = None

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return bool(self._state )

    @property
    def available(self):
        # return self._remote_allowed
        return True

    def turn_on(self, **kwargs):
        """Start the program."""
        _LOGGER.debug("tried to turn on program {}".format(self.program_name))
        self.device.appliance.start_program(self.program_name)

    def turn_off(self, **kwargs):
        """Stop the program."""
        _LOGGER.debug("tried to stop program {}".format(self.program_name))
        self.device.appliance.stop_program()

    def update(self):
        # remote = self.device.appliance.status.get('BSH.Common.Status.RemoteControlStartAllowed', {})
        # if remote.get('value', None):
        #     self._remote_allowed = True
        # else:
        #     self._remote_allowed = False
        state = self.device.appliance.status.get('BSH.Common.Root.ActiveProgram', {})
        if state.get('value', None) == self.program_name:
            self._state = True
        else:
            self._state = False
        _LOGGER.debug("Updated, new state: {}".format(self._state))


class HomeConnectPowerSwitch(HomeConnectEntity, SwitchDevice):
    def __init__(self, device):
        super().__init__(device, device.appliance.name)
        self._state = None

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return bool(self._state )

    def turn_on(self, **kwargs):
        """Switch the device on."""
        _LOGGER.debug("tried to switch on {}".format(self.name))
        self.device.appliance.set_setting('BSH.Common.Setting.PowerState',  'BSH.Common.Setting.PowerState.On')

    def turn_off(self, **kwargs):
        """Switch the device off."""
        _LOGGER.debug("tried to switch off {}".format(self.name))
        self.device.appliance.set_setting('BSH.Common.Setting.PowerState',  self.device._power_off_state)

    def update(self):
        if (self.device.appliance.status.get('BSH.Common.Setting.PowerState', {}).get('value', None) == 'BSH.Common.Setting.PowerState.On'
            or
            self.device.appliance.status.get('BSH.Common.EnumType.PowerState', {}).get('value', None)) == 'BSH.Common.Setting.PowerState.On':
            self._state = True
        else:
            self._state = False
        _LOGGER.debug("Updated, new state: {}".format(self._state))

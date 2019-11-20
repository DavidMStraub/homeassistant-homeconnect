"""
Provides a binary sensor for Home Connect

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.homeconnect/
"""
import logging
import re

from homeassistant.components.switch import SwitchDevice
from homeconnect.api import HomeConnectError

from .api import HomeConnectEntity
from .const import DOMAIN, DEVICES

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["homeconnect"]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Home Connect switch."""

    def get_entities():
        entities = []
        data = hass.data[DOMAIN]
        for device_dict in data.get(DEVICES, []):
            entities += [HomeConnectPowerSwitch(device_dict["device"])]
            entity_dicts = device_dict.get("entities", {}).get("switch", [])
            entity_list = [HomeConnectProgramSwitch(**d) for d in entity_dicts]
            device = device_dict["device"]
            device.entities += entity_list
            entities += entity_list
        return entities

    async_add_entities(await hass.async_add_executor_job(get_entities), True)


class HomeConnectProgramSwitch(HomeConnectEntity, SwitchDevice):
    def __init__(self, device, program_name):
        name = " ".join([device.appliance.name, "Program", program_name.split(".")[-1]])
        super().__init__(device, name)
        self.program_name = program_name
        self._state = None
        self._remote_allowed = None

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return bool(self._state)

    @property
    def available(self):
        # return self._remote_allowed
        return True

    def turn_on(self, **kwargs):
        """Start the program."""
        _LOGGER.debug("tried to turn on program {}".format(self.program_name))
        try:
            self.device.appliance.start_program(self.program_name)
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to start program: {}".format(err))
        self.async_entity_update()

    def turn_off(self, **kwargs):
        """Stop the program."""
        _LOGGER.debug("tried to stop program {}".format(self.program_name))
        try:
            self.device.appliance.stop_program()
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to stop program: {}".format(err))
        self.async_entity_update()

    def update(self):
        # remote = self.device.appliance.status.get('BSH.Common.Status.RemoteControlStartAllowed', {})
        # if remote.get('value', None):
        #     self._remote_allowed = True
        # else:
        #     self._remote_allowed = False
        state = self.device.appliance.status.get("BSH.Common.Root.ActiveProgram", {})
        if state.get("value", None) == self.program_name:
            self._state = True
        else:
            self._state = False
        _LOGGER.debug("Updated, new state: {}".format(self._state))


def convert_to_snake(s):
    """Convert from CamelCase to snake_case.
    
    Taken from https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def format_key(s):
    """Format Home Connect keys like `BSH.Something.SomeValue` to a simple `some_value`"""
    if not isinstance(s, str):
        return s
    return convert_to_snake(s.split(".")[-1])


class HomeConnectPowerSwitch(HomeConnectEntity, SwitchDevice):
    def __init__(self, device):
        super().__init__(device, device.appliance.name)
        self._state = None

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return bool(self._state)

    def turn_on(self, **kwargs):
        """Switch the device on."""
        _LOGGER.debug("tried to switch on {}".format(self.name))
        try:
            self.device.appliance.set_setting(
                "BSH.Common.Setting.PowerState", "BSH.Common.EnumType.PowerState.On"
            )
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to turn on device: {}".format(err))
            self._state = False
        try:
            self.device.appliance.get_status()
        except (HomeConnectError, ValueError):
            _LOGGER.debug("Unable to fetch appliance status. Probably offline.")
            self._state = False
        self.async_entity_update()

    def turn_off(self, **kwargs):
        """Switch the device off."""
        _LOGGER.debug("tried to switch off {}".format(self.name))
        try:
            self.device.appliance.set_setting(
                "BSH.Common.Setting.PowerState", self.device._power_off_state
            )
        except HomeConnectError as err:
            _LOGGER.error("Error while trying to turn on device: {}".format(err))
            self._state = False
        try:
            self.device.appliance.get_status()
        except (HomeConnectError, ValueError):
            _LOGGER.debug("Unable to fetch appliance status. Probably offline.")
            self._state = False
        self.async_entity_update()

    def update(self):
        if (
            self.device.appliance.status.get("BSH.Common.Setting.PowerState", {}).get(
                "value", None
            )
            == "BSH.Common.EnumType.PowerState.On"
        ):
            self._state = True
        elif (
            self.device.appliance.status.get("BSH.Common.Setting.PowerState", {}).get(
                "value", None
            )
            == "BSH.Common.EnumType.PowerState.Off"
        ):
            self._state = False
        elif self.device.appliance.status.get(
            "BSH.Common.Status.OperationState", {}
        ).get("value", None) in [
            "BSH.Common.EnumType.OperationState.Ready",
            "BSH.Common.EnumType.OperationState.DelayedStart",
            "BSH.Common.EnumType.OperationState.Run",
            "BSH.Common.EnumType.OperationState.Pause",
            "BSH.Common.EnumType.OperationState.ActionRequired",
            "BSH.Common.EnumType.OperationState.Aborting",
            "BSH.Common.EnumType.OperationState.Finished",
        ]:
            self._state = True
        elif (
            self.device.appliance.status.get(
                "BSH.Common.Status.OperationState", {}
            ).get("value", None)
            == "BSH.Common.EnumType.OperationState.Inactive"
        ):
            self._state = False
        else:
            self._state = None
        _LOGGER.debug("Updated, new state: {}".format(self._state))

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        status = self.device.appliance.status
        return {format_key(k): format_key(v.get("value")) for k, v in status.items()}

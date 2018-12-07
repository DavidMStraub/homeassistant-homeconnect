"""
Support for BSH Home Connect appliances.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/homeconnect/
"""
import logging

import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.entity import Entity
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import callback
import time


DOMAIN = 'homeconnect'

AUTH_CALLBACK_NAME = 'api:homeconnect'
AUTH_CALLBACK_PATH = '/api/homeconnect'
CACHE_PATH = '.homeconnect-token-cache'

CONFIGURATOR_DESCRIPTION = 'To link your Home Connect account, ' \
                           'click the link, login, and authorize:'
CONFIGURATOR_LINK_NAME = 'Link Home Connect account'
CONFIGURATOR_SUBMIT_CAPTION = 'I authorized successfully'

REQUIREMENTS = ['homeconnect==0.1']


_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required('client_id'): cv.string,
        vol.Required('client_secret'): cv.string,
        vol.Optional('simulate', default=False): cv.boolean,
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config, add_entities=None):
    """Set up Home Connect component."""
    from homeconnect import HomeConnect
    redirect_uri = '{}{}'.format(hass.config.api.base_url, AUTH_CALLBACK_PATH)

    token_cache = hass.config.path(CACHE_PATH)
    hc = HomeConnect(client_id=config.get(DOMAIN, {}).get('client_id', ''),
                     client_secret=config.get(DOMAIN, {}).get('client_secret', ''),
                     redirect_uri=redirect_uri,
                     token_cache=token_cache,
                     simulate=config.get(DOMAIN, {}).get('simulate', False))

    if not hc.oauth.token:
        _LOGGER.debug("no token; requesting authorization")
        hass.http.register_view(HomeConnectAuthCallbackView(
            config, add_entities, hc))
        request_configuration(hass, hc)
        return True

    if hass.data.get(DOMAIN):
        configurator = hass.components.configurator
        configurator.request_done(hass.data.get(DOMAIN))
        del hass.data[DOMAIN]

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]['devices'] = get_devices(hc)
    load_platform(hass, 'binary_sensor', DOMAIN, {}, config)
    load_platform(hass, 'sensor', DOMAIN, {}, config)
    load_platform(hass, 'switch', DOMAIN, {}, config)

    return True


def request_configuration(hass, hc):
    """Request Home Connect authorization."""
    configurator = hass.components.configurator
    hass.data[DOMAIN] = configurator.request_config(
        'Home Connect', lambda _: None,
        link_name=CONFIGURATOR_LINK_NAME,
        link_url=hc.get_authurl(),
        description=CONFIGURATOR_DESCRIPTION,
        submit_caption=CONFIGURATOR_SUBMIT_CAPTION)

# @config_entries.HANDLERS.register(DOMAIN)
# class HomeConnectFlowHandler(config_entries.ConfigFlow):
#
#     VERSION = 1
#
#     async def async_step_user(self, user_input=None):
#         data_schema = OrderedDict()
#         data_schema[vol.Required('client_id')] = str
#         data_schema[vol.Required('client_secret')] = str
#
#         if user_input is not None:
#             self.hass.http.register_view(HomeConnectAuthCallbackView())
#
#
#         return self.async_show_form(
#             step_id='user',
#             data_schema=vol.Schema(data_schema)
#         )


class HomeConnectAuthCallbackView(HomeAssistantView):
    """HomeConnect Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    def __init__(self, config, add_entities, hc):
        """Initialize."""
        self.config = config
        self.add_entities = add_entities
        self.hc = hc

    async def get(self, request):
        """Receive authorization token."""
        hass = request.app['hass']
        self.hc.get_token(str(request.url))
        hass.async_add_job(
            setup, hass, self.config, self.add_entities)


def retry(f, args=None, times=10, exceptions=(ValueError,), sleep=0.1):
    for i in range(times):
        if i > 0:
            _LOGGER.error("Error while executing {}. Retry #{}".format(f, i))
        try:
            if args:
                return f(*args)
            else:
                return f()
        except exceptions as e:
            _LOGGER.error('{} {}'.format(f, e))
            time.sleep(sleep)
            continue
        break


def get_devices(hc):
    appl = retry(hc.get_appliances, times=20, sleep=0.1)
    devices = []
    for app in appl:
        if app.type == 'Dryer':
            device = Dryer(app)
        elif app.type == 'Washer':
            device = Washer(app)
        elif app.type == 'Dishwasher':
            device = Dishwasher(app)
        elif app.type == 'FridgeFreezer':
            device = FridgeFreezer(app)
        elif app.type == 'Oven':
            device = Oven(app)
        elif app.type == 'CoffeeMaker':
            device = CoffeeMaker(app)
        elif app.type == 'Hood':
            device = Hood(app)
        else:
            _LOGGER.warning("Appliance type {} not implemented.".format(app.type))
            continue
        devices.append({'device': device,
                        'entities': device.get_entities()})
    return devices


class HomeConnectDevice:

    # for some devices, this is instead 'BSH.Common.EnumType.PowerState.Standby'
    # see https://developer.home-connect.com/docs/settings/power_state
    _power_off_state = 'BSH.Common.EnumType.PowerState.Off'

    def __init__(self, appliance):
        from homeconnect.api import HomeConnectError
        self.appliance = appliance
        retry(self.appliance.get_status,
              times=2,
              exceptions=(HomeConnectError, ValueError),
              sleep=0)
        program_active = retry(self.appliance.get_programs_active,
              times=2,
              exceptions=(HomeConnectError, ValueError),
              sleep=0)
        if program_active and 'key' in program_active:
            self.appliance.status['BSH.Common.Root.ActiveProgram'] = {'value': program_active['key']}
        self.appliance.listen_events(callback=self.event_callback)
        self.entities = []

    def event_callback(self, appliance):
        _LOGGER.debug("Update triggered on {}".format(appliance.name))
        _LOGGER.debug(self.entities)
        _LOGGER.debug(self.appliance.status)
        for entity in self.entities:
            entity.async_entity_update()


class HomeConnectEntity(Entity):
    def __init__(self, device, name):
        self.device = device
        self._name = name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    # @property
    # def unique_id(self) -> str:
    #     """Return a unique ID."""
    #     return self.appliance.haId

    @property
    def name(self):
        """Return the name of the node (used for Entity_ID)."""
        return self._name

    @callback
    def async_entity_update(self):
        _LOGGER.debug("Entity update triggered on {}".format(self))
        self.schedule_update_ha_state(True)


class DeviceWithPrograms:

    _programs = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_programs_available(self):
        return self._programs

    # def get_programs_available(self):
    #     from homeconnect.api import HomeConnectError
    #     return retry(self.appliance.get_programs_available,
    #                  exceptions=(HomeConnectError, ValueError))

    def get_program_switches(self):
        programs = self.get_programs_available()
        return [{'device': self,
                 'program_name': p['name']} for p in programs]

    def get_program_sensors(self):
        sensors = {'Remaining Program Time': 's',
                   'Program Progress': '%'}
        return [{'device': self,
                 'name': ' '.join((self.appliance.name, name)),
                 'unit': unit,
                 'key': 'BSH.Common.Option.{}'.format(name.replace(' ', '')),
                 } for name, unit in sensors.items()]


class DeviceWithDoor:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_door_entity(self):
        return {'device': self,
                'name': self.appliance.name + ' Door',
                'device_class': 'door'}


class Dryer(DeviceWithDoor, DeviceWithPrograms, HomeConnectDevice):

    _programs = [
        {'name': 'LaundryCare.Dryer.Program.Cotton',},
        {'name': 'LaundryCare.Dryer.Program.Synthetic',},
        {'name': 'LaundryCare.Dryer.Program.Mix',},
    ]

    def __init__(self, appliance):
        super().__init__(appliance)

    def get_entities(self):
        door_entity = self.get_door_entity()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {'binary_sensor': [door_entity],
                'switch': program_switches,
                'sensor': program_sensors,}


class Dishwasher(DeviceWithDoor, DeviceWithPrograms, HomeConnectDevice):

    _programs = [
        {'name': 'Dishcare.Dishwasher.Program.Auto1',},
        {'name': 'Dishcare.Dishwasher.Program.Auto2',},
        {'name': 'Dishcare.Dishwasher.Program.Auto3',},
        {'name': 'Dishcare.Dishwasher.Program.Eco50',},
        {'name': 'Dishcare.Dishwasher.Program.Quick45',},
    ]

    def __init__(self, appliance):
        super().__init__(appliance)

    def get_entities(self):
        door_entity = self.get_door_entity()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {'binary_sensor': [door_entity],
                'switch': program_switches,
                'sensor': program_sensors,}


class Oven(DeviceWithDoor, DeviceWithPrograms, HomeConnectDevice):

    _programs = [
        {'name': 'Cooking.Oven.Program.HeatingMode.PreHeating',},
        {'name': 'Cooking.Oven.Program.HeatingMode.HotAir',},
        {'name': 'Cooking.Oven.Program.HeatingMode.TopBottomHeating',},
        {'name': 'Cooking.Oven.Program.HeatingMode.PizzaSetting',},
    ]

    _power_off_state = 'BSH.Common.EnumType.PowerState.Standby'

    def __init__(self, appliance):
        super().__init__(appliance)

    def get_entities(self):
        door_entity = self.get_door_entity()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {'binary_sensor': [door_entity],
                'switch': program_switches,
                'sensor': program_sensors,}


class Washer(DeviceWithDoor, DeviceWithPrograms, HomeConnectDevice):

    _programs = [
        {'name': 'LaundryCare.Washer.Program.Cotton',},
        {'name': 'LaundryCare.Washer.Program.EasyCare',},
        {'name': 'LaundryCare.Washer.Program.Mix',},
        {'name': 'LaundryCare.Washer.Program.DelicatesSilk',},
        {'name': 'LaundryCare.Washer.Program.Wool',},
    ]

    def __init__(self, appliance):
        super().__init__(appliance)

    def get_entities(self):
        door_entity = self.get_door_entity()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {'binary_sensor': [door_entity],
                'switch': program_switches,
                'sensor': program_sensors,}


class CoffeeMaker(DeviceWithPrograms, HomeConnectDevice):

    _programs = [
        {'name': 'ConsumerProducts.CoffeeMaker.Program.Beverage.Espresso',},
        {'name': 'ConsumerProducts.CoffeeMaker.Program.Beverage.EspressoMacchiato',},
        {'name': 'ConsumerProducts.CoffeeMaker.Program.Beverage.Coffee',},
        {'name': 'ConsumerProducts.CoffeeMaker.Program.Beverage.Cappuccino',},
        {'name': 'ConsumerProducts.CoffeeMaker.Program.Beverage.LatteMacchiato',},
        {'name': 'ConsumerProducts.CoffeeMaker.Program.Beverage.CaffeLatte',},
    ]

    _power_off_state = 'BSH.Common.EnumType.PowerState.Standby'

    def __init__(self, appliance):
        super().__init__(appliance)

    def get_entities(self):
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {'switch': program_switches,
                'sensor': program_sensors,}


class Hood(DeviceWithPrograms, HomeConnectDevice):

    _programs = [
        {'name': 'Cooking.Common.Program.Hood.Automatic',},
        {'name': 'Cooking.Common.Program.Hood.Venting',},
        {'name': 'Cooking.Common.Program.Hood.DelayedShutOff',},
    ]

    def __init__(self, appliance):
        super().__init__(appliance)

    def get_entities(self):
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {'switch': program_switches,
                'sensor': program_sensors,}


class FridgeFreezer(DeviceWithDoor,HomeConnectDevice):

    _programs = [
        {'name': 'LaundryCare.Dryer.Program.Cotton',},
        {'name': 'LaundryCare.Dryer.Program.Synthetic',},
        {'name': 'LaundryCare.Dryer.Program.Mix',},
    ]

    def __init__(self, appliance):
        super().__init__(appliance)

    def get_entities(self):
        door_entity = self.get_door_entity()
        return {'binary_sensor': [door_entity],
                }


# async def async_setup_entry(hass, entry):
#     """Set up Home Connect from a config entry."""
#     from homeconnect import HomeConnect
#
#     _LOGGER.info("setting up HC entry: {}".format(entry))
#
#     _LOGGER.debug("async_setup_homeconnect is done")
#
#     return True

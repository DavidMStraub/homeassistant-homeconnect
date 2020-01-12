"""Provides a sensor for Home Connect.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/integrations/sensor.homeconnect/
"""
import logging

from .api import HomeConnectEntity
from .const import DOMAIN
from homeassistant.components.sensor import DEVICE_CLASS_TEMPERATURE
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Home Connect sensor."""

    def get_entities():
        """Get a list of entities."""
        entities = []
        hc_api = hass.data[DOMAIN][config_entry.entry_id]
        for device_dict in hc_api.devices:
            entity_dicts = device_dict.get("entities", {}).get("sensor", [])
            entity_list = [HomeConnectSensor(**d) for d in entity_dicts]
            device = device_dict["device"]
            device.entities += entity_list
            entities += entity_list
            if device.has_programs:
                services = device.get_programs_services()
                _LOGGER.debug(f"services to register: {services}")
                for s in services:
                    _LOGGER.debug(f"registering service {s['service_name']}")
                    hass.services.async_register(
                        s['service_domain'],
                        s['service_name'],
                        s['service_callback'],
                        schema=s['service_schema'],
                    )
        return entities

    async_add_entities(await hass.async_add_executor_job(get_entities), True)


class HomeConnectSensor(HomeConnectEntity):
    """Sensor class for Home Connect."""

    def __init__(self, device, name, key, unit, device_class = None):
        """Initialize the entity."""
        super().__init__(device, name)
        self._state = None
        self._device_class = device_class
        self._key = key
        self._unit = unit

    @property
    def state(self):
        """Return true if the binary sensor is on."""
        return self._state

    @property
    def available(self):
        """Return true if the sensor is available."""
        return self._state is not None

    def update(self):
        """Update the sensos status."""
        status = self.device.appliance.status
        if self._key not in status:
            self._state = None
        else:
            self._state = status[self._key].get("value", None)
            if isinstance(self._state, str):
                if "BSH.Common.EnumType.OperationState" in self._state:
                    self._state = self._state.replace("BSH.Common.EnumType.OperationState.", "")
                if "BSH.Common.EnumType.PowerState" in self._state:
                    self._state = self._state.replace("BSH.Common.EnumType.PowerState.", "")
        _LOGGER.debug("Sensor {} updated, new state: {}".format(self._name, self._state))

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._unit == "C":
            return TEMP_CELSIUS
        if self._unit == "F":
            return TEMP_FAHRENHEIT
        return self._unit

    @property
    def device_class(self):
        """Return the class of this device."""
        return self._device_class

    @property
    def icon(self):
        """Return the icon."""
        if self._unit == "s":
            return "mdi:progress-clock"
        if self._unit == "%s":
            return "mdi:timelapse"

"""
Support for BSH Home Connect appliances.

For more details about this component, please refer to the documentation at
https://home-assistant.io/integrations/homeconnect/
"""
import asyncio
from datetime import timedelta
import logging
import os

from requests import HTTPError
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
from homeassistant.util import Throttle

from . import api, config_flow
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN, CONF_SHOW_NOTIFICATIONS

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
                vol.Optional(CONF_SHOW_NOTIFICATIONS, default=True): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["binary_sensor", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: dict, add_entities=None):
    """Set up Home Connect component."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    hass.data[DOMAIN][CONF_SHOW_NOTIFICATIONS] = config[DOMAIN][CONF_SHOW_NOTIFICATIONS]

    config_flow.OAuth2FlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Home Connect from a config entry."""
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    hass.data[DOMAIN][entry.entry_id] = api.ConfigEntryAuth(hass, entry, implementation)

    await update_all_devices(hass, entry)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


@Throttle(SCAN_INTERVAL)
async def update_all_devices(hass, entry):
    """Update all the devices."""
    data = hass.data[DOMAIN]
    hc_api = data[entry.entry_id]
    try:
        await hass.async_add_executor_job(hc_api.get_devices)
        for device_dict in hc_api.devices:
            await hass.async_add_executor_job(device_dict["device"].initialize)
    except HTTPError as err:
        _LOGGER.warning("Cannot update devices: %s", err.response.status_code)

"""Dreame Air Purifier integration."""
import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .api import DreameCloudAPI, DreameAirPurifier
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, CONF_SCAN_INTERVAL, CONF_COUNTRY, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = DreameCloudAPI(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], entry.data.get(CONF_COUNTRY, "us"))
    if not await hass.async_add_executor_job(api.login):
        return False
    devices = await hass.async_add_executor_job(api.get_purifiers)
    if not devices:
        return False
    purifiers = [DreameAirPurifier(api, d) for d in devices]

    async def async_update():
        for p in purifiers:
            await hass.async_add_executor_job(p.update)

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = DataUpdateCoordinator(hass, _LOGGER, name=DOMAIN, update_method=async_update, update_interval=timedelta(seconds=scan_interval))
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator, "purifiers": purifiers, "api": api}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Handle options changes (update polling interval)
    async def async_update_options(hass, config_entry):
        new_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        coordinator.update_interval = timedelta(seconds=new_interval)
        _LOGGER.info("Updated scan interval to %d seconds", new_interval)
    
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False

"""Switch platform for Dreame Air Purifier."""
import logging
from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .api import DreameAirPurifier

_LOGGER = logging.getLogger(__name__)

# Switch entities are set up in setup_entities.py to control ordering with other entities

class DreameBaseSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, purifier: DreameAirPurifier, key: str, name: str):
        super().__init__(coordinator)
        self._purifier = purifier
        self._attr_unique_id = f"{purifier.unique_id}_{key}"
        self._attr_name = name
    @property
    def device_info(self):
        return {
            "identifiers": {("dreame_airpurifier", self._purifier.unique_id)},
            "name": self._purifier.name,
            "manufacturer": "Dreame",
            "model": self._purifier.model,
        }
    @property
    def available(self): return self._purifier.available

class DreameBuzzerSwitch(DreameBaseSwitch):
    _attr_icon = "mdi:volume-high"
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, c, p): super().__init__(c, p, "buzzer", "Buzzer")
    @property
    def is_on(self): return bool(self._purifier.buzzer)
    async def async_turn_on(self, **kwargs): 
        await self.hass.async_add_executor_job(self._purifier.set_buzzer, True)
        await self.coordinator.async_request_refresh()
    async def async_turn_off(self, **kwargs): 
        await self.hass.async_add_executor_job(self._purifier.set_buzzer, False)
        await self.coordinator.async_request_refresh()

class DreameChildLockSwitch(DreameBaseSwitch):
    _attr_icon = "mdi:lock"
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, c, p): super().__init__(c, p, "child_lock", "Child Lock")
    @property
    def is_on(self): return bool(self._purifier.child_lock)
    async def async_turn_on(self, **kwargs): 
        await self.hass.async_add_executor_job(self._purifier.set_child_lock, True)
        await self.coordinator.async_request_refresh()
    async def async_turn_off(self, **kwargs): 
        await self.hass.async_add_executor_job(self._purifier.set_child_lock, False)
        await self.coordinator.async_request_refresh()

class DreameBreathingLightSwitch(DreameBaseSwitch):
    _attr_icon = "mdi:light-recessed"
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, c, p): super().__init__(c, p, "breathing_light", "Breathing Light")
    @property
    def is_on(self): return bool(self._purifier.breathing_light)
    async def async_turn_on(self, **kwargs): 
        await self.hass.async_add_executor_job(self._purifier.set_breathing_light, True)
        await self.coordinator.async_request_refresh()
    async def async_turn_off(self, **kwargs): 
        await self.hass.async_add_executor_job(self._purifier.set_breathing_light, False)
        await self.coordinator.async_request_refresh()

"""Fan platform for Dreame Air Purifier."""
import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DreameAirPurifier, MODE_NAME_TO_VALUE, MODE_CUSTOM

_LOGGER = logging.getLogger(__name__)

# Fan entity is set up in setup_entities.py to control ordering with other entities

class DreameAirPurifierFan(CoordinatorEntity, FanEntity):
    """Dreame Air Purifier FP10 fan entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_speed_count = 10  # FP10 has 10 speed levels (1-10)

    def __init__(self, coordinator, purifier: DreameAirPurifier):
        super().__init__(coordinator)
        self._purifier = purifier
        self._attr_unique_id = f"{purifier.unique_id}_fan"
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        )
        self._attr_preset_modes = ["Auto", "Sleep", "Custom", "Pet"]

    @property
    def device_info(self):
        return {
            "identifiers": {("dreame_airpurifier", self._purifier.unique_id)},
            "name": self._purifier.name,
            "manufacturer": "Dreame",
            "model": self._purifier.model,
            "sw_version": "0.3.0",
        }

    @property
    def is_on(self) -> bool:
        return self._purifier.is_on

    @property
    def percentage(self) -> int | None:
        if not self._purifier.is_on:
            return 0
        return self._purifier.fan_speed_percent

    @property
    def preset_mode(self) -> str | None:
        return self._purifier.mode

    @property
    def available(self) -> bool:
        return self._purifier.available

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "fan_speed_level": self._purifier.fan_speed,
            "power_state": self._purifier.power_state,
            "temperature": self._purifier.temperature,
            "humidity": self._purifier.humidity,
            "tvoc": self._purifier.tvoc,
        }

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs) -> None:
        await self.hass.async_add_executor_job(self._purifier.turn_on)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        if percentage is not None:
            await self.async_set_percentage(percentage)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self._purifier.turn_off)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        # Map percentage to 1-10 (10%=1, 20%=2, ..., 100%=10)
        level = max(1, min(10, round(percentage / 10)))
        # Switch to Custom mode if not already
        if self._purifier.mode_value != MODE_CUSTOM:
            await self.hass.async_add_executor_job(self._purifier.set_mode, MODE_CUSTOM)
        await self.hass.async_add_executor_job(self._purifier.set_fan_speed, level)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        mode_value = MODE_NAME_TO_VALUE.get(preset_mode)
        if mode_value is not None:
            await self.hass.async_add_executor_job(self._purifier.set_mode, mode_value)
            await self.coordinator.async_request_refresh()

"""Select platform for Dreame Air Purifier."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .api import (
    DreameAirPurifier,
    LIGHT_OFF, LIGHT_ON_LAST, LIGHT_DIM, LIGHT_NATURAL, LIGHT_BRIGHT, LIGHT_MODES,
    TEMP_UNIT_CELSIUS, TEMP_UNIT_FAHRENHEIT, TEMP_UNIT_NAMES,
    WEIGHT_UNIT_KG, WEIGHT_UNIT_LB, WEIGHT_UNIT_NAMES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up select entities."""
    data = hass.data["dreame_airpurifier"][entry.entry_id]
    entities = []
    for p in data["purifiers"]:
        entities.extend([
            DreameTimerSelect(data["coordinator"], p),
            DreameAmbientLightSelect(data["coordinator"], p),
            DreameTemperatureUnitSelect(data["coordinator"], p),
            DreameWeightUnitSelect(data["coordinator"], p),
        ])
    async_add_entities(entities)

class DreameBaseSelect(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, purifier: DreameAirPurifier, key: str, name: str, options: list):
        super().__init__(coordinator)
        self._purifier = purifier
        self._attr_unique_id = f"{purifier.unique_id}_{key}"
        self._attr_name = name
        self._attr_options = options
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

class DreameAmbientLightSelect(DreameBaseSelect):
    _attr_icon = "mdi:lightbulb"
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, coordinator, purifier):
        super().__init__(coordinator, purifier, "ambient_light", "Ambient Light", ["Off", "Dim", "Natural", "Bright"])
    @property
    def current_option(self) -> str:
        return LIGHT_MODES.get(self._purifier.light_brightness, "Off")
    async def async_select_option(self, option: str) -> None:
        brightness_map = {"Off": LIGHT_OFF, "Dim": LIGHT_DIM, "Natural": LIGHT_NATURAL, "Bright": LIGHT_BRIGHT}
        brightness = brightness_map.get(option, LIGHT_OFF)
        # Optimistic update: show brightness change immediately
        self._purifier._light_brightness = brightness
        # When changing ambient light, disable breathing light
        self._purifier._breathing_light = 0
        result = await self.hass.async_add_executor_job(self._purifier.set_light_brightness, brightness)
        if not result:
            _LOGGER.error("Failed to set ambient light to %s", option)
        result = await self.hass.async_add_executor_job(self._purifier.set_breathing_light, False)
        if not result:
            _LOGGER.error("Failed to disable breathing light")
        await self.coordinator.async_request_refresh()

class DreameTemperatureUnitSelect(DreameBaseSelect):
    _attr_icon = "mdi:thermometer"
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, coordinator, purifier):
        super().__init__(coordinator, purifier, "temp_unit", "Temperature Unit", ["C", "F"])
    @property
    def current_option(self) -> str:
        return TEMP_UNIT_NAMES.get(self._purifier.temp_unit, "C")
    async def async_select_option(self, option: str) -> None:
        unit_map = {"C": TEMP_UNIT_CELSIUS, "F": TEMP_UNIT_FAHRENHEIT}
        unit = unit_map.get(option, TEMP_UNIT_CELSIUS)
        # Optimistic update: show unit change immediately
        self._purifier._temp_unit = unit
        result = await self.hass.async_add_executor_job(self._purifier.set_temp_unit, unit)
        if not result:
            _LOGGER.error("Failed to set temperature unit to %s", option)
        await self.coordinator.async_request_refresh()

class DreameWeightUnitSelect(DreameBaseSelect):
    _attr_icon = "mdi:weight"
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, coordinator, purifier):
        super().__init__(coordinator, purifier, "weight_unit", "Weight Unit", ["kg", "lb"])
    @property
    def current_option(self) -> str:
        return WEIGHT_UNIT_NAMES.get(self._purifier.weight_unit, "kg")
    async def async_select_option(self, option: str) -> None:
        unit_map = {"kg": WEIGHT_UNIT_KG, "lb": WEIGHT_UNIT_LB}
        unit = unit_map.get(option, WEIGHT_UNIT_KG)
        # Optimistic update: show unit change immediately
        self._purifier._weight_unit = unit
        result = await self.hass.async_add_executor_job(self._purifier.set_weight_unit, unit)
        if not result:
            _LOGGER.error("Failed to set weight unit to %s", option)
        await self.coordinator.async_request_refresh()

class DreameTimerSelect(DreameBaseSelect):
    _attr_icon = "mdi:timer"
    def __init__(self, coordinator, purifier):
        # Timer labels: Cancel (0), 1 hour, 2 hours, ..., 12 hours
        timer_options = self._get_timer_labels()
        super().__init__(coordinator, purifier, "timer", "Timer", timer_options)
    
    @staticmethod
    def _get_timer_labels() -> list:
        """Generate timer labels with correct English grammar."""
        labels = ["Cancel"]  # 0 - Cancel
        for i in range(1, 13):
            if i == 1:
                labels.append(f"{i} hour")
            else:
                labels.append(f"{i} hours")
        return labels
    
    @property
    def current_option(self) -> str:
        timer_value = self._purifier.timer
        labels = self._get_timer_labels()
        return labels[timer_value] if timer_value < len(labels) else "Cancel"
    
    async def async_select_option(self, option: str) -> None:
        # Extract hour value from label (e.g., "5 hours" -> 5, "Cancel" -> 0)
        if option == "Cancel":
            hours = 0
        else:
            # Extract first number from string (e.g., "5 hours" -> "5")
            hours = int(option.split()[0])
        # Optimistic update: show timer change immediately
        self._purifier._timer = hours
        result = await self.hass.async_add_executor_job(self._purifier.set_timer, hours)
        if not result:
            _LOGGER.error("Failed to set timer to %s", option)
        await self.coordinator.async_request_refresh()

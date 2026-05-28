"""Button platform for Dreame Air Purifier."""
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .api import DreameAirPurifier

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up button entities."""
    data = hass.data["dreame_airpurifier"][entry.entry_id]
    entities = [DreameStartSelfCleaningButton(data["coordinator"], p) for p in data["purifiers"]]
    entities.extend([DreameConfirmSelfCleaningButton(data["coordinator"], p) for p in data["purifiers"]])
    async_add_entities(entities)

class DreameBaseButton(CoordinatorEntity, ButtonEntity):
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

class DreameStartSelfCleaningButton(DreameBaseButton):
    _attr_icon = "mdi:auto-fix"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier):
        super().__init__(coordinator, purifier, "start_self_cleaning", "Start Self-Cleaning")
    async def async_press(self) -> None:
        # Optimistic update: show in-progress status immediately
        self._purifier._self_cleaning_status = 1  # 1 = in progress
        result = await self.hass.async_add_executor_job(self._purifier.start_self_cleaning)
        if not result:
            _LOGGER.error("Failed to start self-cleaning")
        await self.coordinator.async_request_refresh()

class DreameConfirmSelfCleaningButton(DreameBaseButton):
    _attr_icon = "mdi:check-circle"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier):
        super().__init__(coordinator, purifier, "confirm_self_cleaning", "Confirm Self-Cleaning Finished")
    async def async_press(self) -> None:
        # Optimistic update: show finished status immediately
        self._purifier._self_cleaning_status = 2  # 2 = finished
        result = await self.hass.async_add_executor_job(self._purifier.confirm_self_cleaning_finished)
        if not result:
            _LOGGER.error("Failed to confirm self-cleaning finished")
        await self.coordinator.async_request_refresh()

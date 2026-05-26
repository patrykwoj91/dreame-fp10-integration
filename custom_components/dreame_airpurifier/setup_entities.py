"""Central entity setup and orchestration for Dreame Air Purifier integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Import all entity classes
from .fan import DreameAirPurifierFan
from .sensor import (
    DreameAirQualitySensor,
    DreamePM25Sensor,
    DreameTVOCSensor,
    DreameTemperatureSensor,
    DreameHumiditySensor,
    DreameFilterUsedSensor,
    DreameFilterLifeSensor,
    DreameFilterDaysSensor,
    DreameHairBoxLifeSensor,
    DreameHairBoxDaysSensor,
    DreameSelfCleaningStatusSensor,
)
from .select import (
    DreameTimerSelect,
    DreameAmbientLightSelect,
    DreameTemperatureUnitSelect,
    DreameWeightUnitSelect,
)
from .switch import (
    DreameBuzzerSwitch,
    DreameChildLockSwitch,
    DreameBreathingLightSwitch,
)
from .button import (
    DreameStartSelfCleaningButton,
    DreameConfirmSelfCleaningButton,
)

_LOGGER = logging.getLogger(__name__)

# Entity platform for Home Assistant setup
PLATFORM_DOMAIN = "sensor"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up all entities in correct order."""
    data = hass.data["dreame_airpurifier"][entry.entry_id]
    entities = []
    
    for p in data["purifiers"]:
        entities.extend([
            # Bez kategorii (CONTROL) - Sterowanie
            DreameAirPurifierFan(data["coordinator"], p),
            DreameTimerSelect(data["coordinator"], p),
            DreameAirQualitySensor(data["coordinator"], p),
            DreamePM25Sensor(data["coordinator"], p),
            DreameTVOCSensor(data["coordinator"], p),
            DreameTemperatureSensor(data["coordinator"], p),
            DreameHumiditySensor(data["coordinator"], p),
            # CONFIG - Konfiguracja
            DreameAmbientLightSelect(data["coordinator"], p),
            DreameBreathingLightSwitch(data["coordinator"], p),
            DreameBuzzerSwitch(data["coordinator"], p),
            DreameChildLockSwitch(data["coordinator"], p),
            DreameTemperatureUnitSelect(data["coordinator"], p),
            DreameWeightUnitSelect(data["coordinator"], p),
            # DIAGNOSTIC - Diagnostyka
            DreameStartSelfCleaningButton(data["coordinator"], p),
            DreameSelfCleaningStatusSensor(data["coordinator"], p),
            DreameConfirmSelfCleaningButton(data["coordinator"], p),
            DreameHairBoxLifeSensor(data["coordinator"], p),
            DreameHairBoxDaysSensor(data["coordinator"], p),
            DreameFilterUsedSensor(data["coordinator"], p),
            DreameFilterLifeSensor(data["coordinator"], p),
            DreameFilterDaysSensor(data["coordinator"], p),
        ])
    
    async_add_entities(entities)

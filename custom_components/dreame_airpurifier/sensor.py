"""Sensor platform for Dreame Air Purifier."""
import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, PERCENTAGE, UnitOfTime, UnitOfTemperature, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .api import DreameAirPurifier

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data["dreame_airpurifier"][entry.entry_id]
    entities = []
    for p in data["purifiers"]:
        entities.extend([
            DreamePowerSensor(data["coordinator"], p),
            DreamePM25Sensor(data["coordinator"], p),
            DreameAirQualitySensor(data["coordinator"], p),
            DreameTemperatureSensor(data["coordinator"], p),
            DreameHumiditySensor(data["coordinator"], p),
            DreameTVOCSensor(data["coordinator"], p),
            DreameFilterLifeSensor(data["coordinator"], p),
            DreameFilterDaysSensor(data["coordinator"], p),
            DreameFilterUsedSensor(data["coordinator"], p),
            DreameHairBoxLifeSensor(data["coordinator"], p),
            DreameHairBoxDaysSensor(data["coordinator"], p),
            DreameSelfCleaningStatusSensor(data["coordinator"], p),
        ])
    async_add_entities(entities)

class DreameBaseSensor(CoordinatorEntity, SensorEntity):
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

class DreamePowerSensor(DreameBaseSensor):
    _attr_icon = "mdi:power"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "power", "Power")
    @property
    def native_value(self): return self._purifier.power_state

class DreamePM25Sensor(DreameBaseSensor):
    _attr_device_class = SensorDeviceClass.PM25
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_icon = "mdi:molecule"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "pm25", "PM2.5")
    @property
    def native_value(self): return self._purifier.pm25

class DreameAirQualitySensor(DreameBaseSensor):
    _attr_icon = "mdi:air-filter"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "air_quality", "Air Quality")
    @property
    def native_value(self): return self._purifier.air_quality_name

class DreameTemperatureSensor(DreameBaseSensor):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "temperature", "Temperature")
    @property
    def native_value(self): return self._purifier.temperature

class DreameHumiditySensor(DreameBaseSensor):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "humidity", "Humidity")
    @property
    def native_value(self): return self._purifier.humidity

class DreameTVOCSensor(DreameBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    _attr_icon = "mdi:molecule"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "tvoc", "TVOC")
    @property
    def native_value(self): return self._purifier.tvoc

class DreameFilterLifeSensor(DreameBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:air-filter"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "filter_life", "Filter Life")
    @property
    def native_value(self): return self._purifier.filter_life

class DreameFilterDaysSensor(DreameBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_icon = "mdi:calendar"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "filter_days", "Filter Days Remaining")
    @property
    def native_value(self): return self._purifier.filter_days_total

class DreameFilterUsedSensor(DreameBaseSensor):
    _attr_icon = "mdi:alert-circle"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "filter_used", "Filter Used")
    @property
    def native_value(self): return self._purifier.filter_used  # 0=not used, 1=used

class DreameHairBoxLifeSensor(DreameBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:trash-can"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "hair_box_life", "Hair Collection Box Life")
    @property
    def native_value(self): return self._purifier.hair_box_life

class DreameHairBoxDaysSensor(DreameBaseSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_icon = "mdi:calendar"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "hair_box_days", "Hair Collection Box Days Remaining")
    @property
    def native_value(self): return self._purifier.hair_box_days_total

class DreameSelfCleaningStatusSensor(DreameBaseSensor):
    _attr_icon = "mdi:auto-fix"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, purifier): super().__init__(coordinator, purifier, "self_cleaning_status", "Self-Cleaning Status")
    @property
    def native_value(self): return self._purifier.self_cleaning_status_name

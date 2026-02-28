from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, PERCENTAGE
from homeassistant.helpers.restore_state import RestoreEntity

DOMAIN = "ha_battery_storage_roi"


# v2.0 Statistik Upgrade
class BatteryStorageBaseSensor(SensorEntity, RestoreEntity):
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = float(last_state.state)
            except ValueError:
                pass


# v2.0 Statistik Upgrade
class BatteryTotalChargedSensor(BatteryStorageBaseSensor):
    _attr_name = "Battery Total Charged"
    _attr_device_# v2.0 Statistik Upgrade
class = SensorDeviceClass.ENERGY
    _attr_state_# v2.0 Statistik Upgrade
class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR


# v2.0 Statistik Upgrade
class BatteryTotalDischargedSensor(BatteryStorageBaseSensor):
    _attr_name = "Battery Total Discharged"
    _attr_device_# v2.0 Statistik Upgrade
class = SensorDeviceClass.ENERGY
    _attr_state_# v2.0 Statistik Upgrade
class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR


# v2.0 Statistik Upgrade
class BatteryTotalProfitSensor(BatteryStorageBaseSensor):
    _attr_name = "Battery Total Profit"
    _attr_device_# v2.0 Statistik Upgrade
class = SensorDeviceClass.MONETARY
    _attr_state_# v2.0 Statistik Upgrade
class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "€"


# v2.0 Statistik Upgrade
class BatteryRoiSensor(BatteryStorageBaseSensor):
    _attr_name = "Battery ROI"
    _attr_state_# v2.0 Statistik Upgrade
class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE


# v2.0 Statistik Upgrade
class BatteryCycleSensor(BatteryStorageBaseSensor):
    _attr_name = "Battery Cycles"
    _attr_state_# v2.0 Statistik Upgrade
class = SensorStateClass.TOTAL_INCREASING


# v2.0 Statistik Upgrade
class BatteryEfficiencySensor(BatteryStorageBaseSensor):
    _attr_name = "Battery Efficiency"
    _attr_state_# v2.0 Statistik Upgrade
class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE


# ==============================
# v2.0 Upgrade Notice
# All numeric sensors are now
# Home Assistant long-term
# statistics compatible.
# ==============================

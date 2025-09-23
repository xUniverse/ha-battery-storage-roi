from __future__ import annotations
from datetime import datetime, timedelta, date as dt_date
import math
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime, UnitOfEnergy, CURRENCY_EURO

from .const import (
    DOMAIN,
    CONF_START_DATE,
    CONF_INSTALL_COST,
    CONF_GRID_PRICE,
    CONF_FEEDIN_PRICE,
    CONF_CHARGED_ENTITY,
    CONF_DISCHARGED_ENTITY,
    CONF_INCLUSIVE_DAYS,
    CONF_BASELINE_CHARGED,
    CONF_BASELINE_DISCHARGED,
    CONF_USABLE_CAPACITY,
    ATTR_DAYS,
    ATTR_EFFICIENCY,
    ATTR_SAVINGS_GROSS,
    ATTR_OPPORTUNITY,
    ATTR_NET_BENEFIT,
    ATTR_NET_DAILY,
    ATTR_ROI_REMAINING,
    ATTR_ROI_DATE,
    ATTR_INPUTS_OK,
    ATTR_CHARGED_DELTA,
    ATTR_DISCHARGED_DELTA,
    ATTR_MONEY_EFF_OUT,
    ATTR_MONEY_EFF_IN,
    ATTR_SNY,
    ATTR_CYCLES_PER_DAY,
)

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(minutes=5)

def _num_state(state_obj):
    try:
        if state_obj and state_obj.state not in ("unknown", "unavailable", None):
            return float(str(state_obj.state).replace(",", "."))
    except Exception:
        pass
    return 0.0

def _num_cfg(v, default=0.0):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return default

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = RoiCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entities = [
        RoiSummarySensor(coordinator, entry),
        EfficiencySensor(coordinator, entry),
        DaysSensor(coordinator, entry),
        SavingsSensor(coordinator, entry),
        OpportunitySensor(coordinator, entry),
        NetBenefitSensor(coordinator, entry),
        NetDailySensor(coordinator, entry),
        RoidaysSensor(coordinator, entry),
        RoiDateSensor(coordinator, entry),
        ChargedSinceStartSensor(coordinator, entry),
        DischargedSinceStartSensor(coordinator, entry),
        MoneyEffOutSensor(coordinator, entry),
        MoneyEffInSensor(coordinator, entry),
        SpecificNetYieldSensor(coordinator, entry),
        CyclesPerDaySensor(coordinator, entry),
        CapacitySensor(coordinator, entry),
        StartDateSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class RoiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, _LOGGER, name="Battery Storage ROI", update_interval=UPDATE_INTERVAL)
        self.entry = entry

    async def _async_update_data(self):
        s = self.entry.data

        charged_state = self.hass.states.get(s[CONF_CHARGED_ENTITY])
        discharged_state = self.hass.states.get(s[CONF_DISCHARGED_ENTITY])

        inputs_ok = charged_state is not None and discharged_state is not None

        charged_total = _num_state(charged_state)
        discharged_total = _num_state(discharged_state)

        baseline_charged = _num_cfg(s.get(CONF_BASELINE_CHARGED, 0.0))
        baseline_discharged = _num_cfg(s.get(CONF_BASELINE_DISCHARGED, 0.0))

        charged = max(0.0, charged_total - baseline_charged)
        discharged = max(0.0, discharged_total - baseline_discharged)

        now = dt_util.now()
        start = datetime.fromisoformat(s[CONF_START_DATE]).replace(tzinfo=now.tzinfo)
        inclusive = s.get(CONF_INCLUSIVE_DAYS, True)

        delta_days = (now.date() - start.date()).days
        days = max(1, delta_days + (1 if inclusive else 0))

        grid_price = _num_cfg(s[CONF_GRID_PRICE])
        feedin_price = _num_cfg(s[CONF_FEEDIN_PRICE])
        install_cost = _num_cfg(s[CONF_INSTALL_COST])
        capacity = max(0.0, _num_cfg(s.get(CONF_USABLE_CAPACITY, 5.12)))

        efficiency = (discharged / charged * 100.0) if charged > 0 else 0.0
        eta = (discharged / charged) if charged > 0 else 0.0

        avoided = discharged * grid_price
        opportunity = charged * feedin_price
        net_benefit = avoided - opportunity
        net_daily = net_benefit / days if days > 0 else 0.0

        remaining = (install_cost - net_benefit)
        if net_daily > 0 and remaining > 0:
            roi_days_remaining = math.ceil(remaining / net_daily)
            roi_date = (now + timedelta(days=roi_days_remaining)).date().isoformat()
        else:
            roi_days_remaining = 0 if remaining <= 0 else None
            roi_date = now.date().isoformat() if remaining <= 0 else None

        # Comparison metrics
        money_eff_out = (grid_price - (feedin_price / eta)) if eta > 0 else None
        money_eff_in = (eta * grid_price - feedin_price) if eta > 0 else None
        sny = (net_daily / capacity) if capacity > 0 else None
        cycles_per_day = (discharged / (capacity * days)) if (capacity > 0 and days > 0) else None

        return {
            "inputs_ok": inputs_ok,
            "charged_kwh": charged_total,
            "discharged_kwh": discharged_total,
            "charged_since_start_kwh": round(charged, 3),
            "discharged_since_start_kwh": round(discharged, 3),
            "days": days,
            "efficiency": efficiency,
            "avoided_eur": avoided,
            "opportunity_eur": opportunity,
            "net_benefit_eur": net_benefit,
            "net_daily_eur": net_daily,
            "roi_days_remaining": roi_days_remaining,
            "roi_date": roi_date,
            "install_cost_eur": install_cost,
            "grid_price": grid_price,
            "feedin_price": feedin_price,
            "start_date": start.date().isoformat(),
            "capacity_kwh": capacity,
            "money_eff_out_eur_per_kwh_out": money_eff_out,
            "money_eff_in_eur_per_kwh_in": money_eff_in,
            "specific_net_yield_eur_per_kwhcap_day": sny,
            "cycles_per_day": cycles_per_day,
        }


class BaseRoiSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: RoiCoordinator, entry: ConfigEntry):
        self.coordinator = coordinator
        self.entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.title or "Battery Storage ROI",
            "manufacturer": "Custom",
            "model": "Battery Storage ROI Virtual Device",
        }

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    @callback
    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def _prefix(self) -> str:
        return self.entry.title or "Battery Storage"


class RoiSummarySensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} ROI Summary"

    @property
    def icon(self) -> str:
        return "mdi:cash-clock"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_roi_summary"

    @property
    def native_unit_of_measurement(self):
        return CURRENCY_EURO

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return round(d.get("net_benefit_eur", 0.0), 2)


class EfficiencySensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Efficiency"

    @property
    def icon(self) -> str:
        return "mdi:percent"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_efficiency"

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return round(d.get("efficiency", 0.0), 2)


class DaysSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Days in Operation"

    @property
    def icon(self) -> str:
        return "mdi:calendar-range"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_days"

    @property
    def native_unit_of_measurement(self):
        return UnitOfTime.DAYS

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return d.get("days")


class SavingsSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Avoided Grid Costs"

    @property
    def icon(self) -> str:
        return "mdi:transmission-tower-export"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_savings_gross"

    @property
    def native_unit_of_measurement(self):
        return CURRENCY_EURO

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return round(d.get("avoided_eur", 0.0), 2)


class OpportunitySensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Opportunity Costs"

    @property
    def icon(self) -> str:
        return "mdi:cash-minus"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_opportunity"

    @property
    def native_unit_of_measurement(self):
        return CURRENCY_EURO

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return round(d.get("opportunity_eur", 0.0), 2)


class NetBenefitSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Net Benefit"

    @property
    def icon(self) -> str:
        return "mdi:cash-plus"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_net_benefit"

    @property
    def native_unit_of_measurement(self):
        return CURRENCY_EURO

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return round(d.get("net_benefit_eur", 0.0), 2)


class NetDailySensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Net Benefit per Day"

    @property
    def icon(self) -> str:
        return "mdi:calendar-multiselect"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_net_daily"

    @property
    def native_unit_of_measurement(self):
        return "€/day"

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return round(d.get("net_daily_eur", 0.0), 2)


class RoidaysSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} ROI Days Remaining"

    @property
    def icon(self) -> str:
        return "mdi:calendar-clock"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_roi_days"

    @property
    def native_unit_of_measurement(self):
        return UnitOfTime.DAYS

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return d.get("roi_days_remaining")


class RoiDateSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} ROI Date"

    @property
    def icon(self) -> str:
        return "mdi:calendar"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_roi_date"

    @property
    def device_class(self):
        return SensorDeviceClass.DATE

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        v = d.get("roi_date")
        if not v:
            return None
        try:
            return dt_date.fromisoformat(v)
        except Exception:
            return None


class ChargedSinceStartSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Charged since Start"

    @property
    def icon(self) -> str:
        return "mdi:battery-arrow-up"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_charged_since_start"

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def native_unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def state_class(self):
        return SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return d.get("charged_since_start_kwh")


class DischargedSinceStartSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Discharged since Start"

    @property
    def icon(self) -> str:
        return "mdi:battery-arrow-down"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_discharged_since_start"

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def native_unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def state_class(self):
        return SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return d.get("discharged_since_start_kwh")


class MoneyEffOutSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Money Efficiency (per kWh_out)"

    @property
    def icon(self) -> str:
        return "mdi:cash-refund"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_money_eff_out"

    @property
    def native_unit_of_measurement(self):
        return "€/kWh"

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        v = d.get("money_eff_out_eur_per_kwh_out")
        return None if v is None else round(v, 3)


class MoneyEffInSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Money Efficiency (per kWh_in)"

    @property
    def icon(self) -> str:
        return "mdi:cash-plus"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_money_eff_in"

    @property
    def native_unit_of_measurement(self):
        return "€/kWh"

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        v = d.get("money_eff_in_eur_per_kwh_in")
        return None if v is None else round(v, 3)


class SpecificNetYieldSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Specific Net Yield"

    @property
    def icon(self) -> str:
        return "mdi:lightning-bolt"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_sny"

    @property
    def native_unit_of_measurement(self):
        return "€/kWhcap/day"

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        v = d.get("specific_net_yield_eur_per_kwhcap_day")
        return None if v is None else round(v, 4)


class CyclesPerDaySensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Cycles per Day"

    @property
    def icon(self) -> str:
        return "mdi:repeat"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_cycles_per_day"

    @property
    def native_unit_of_measurement(self):
        return "cycles/day"

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        v = d.get("cycles_per_day")
        return None if v is None else round(v, 4)


class CapacitySensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Battery Usable Capacity"

    @property
    def icon(self) -> str:
        return "mdi:battery-heart-variant"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_capacity"

    @property
    def native_unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        return d.get("capacity_kwh")


class StartDateSensor(BaseRoiSensor):
    @property
    def name(self) -> str:
        return f"{self._prefix} Start Date"

    @property
    def icon(self) -> str:
        return "mdi:calendar-start"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_start_date"

    @property
    def device_class(self):
        return SensorDeviceClass.DATE

    @property
    def native_value(self):
        d = self.coordinator.data or {}
        v = d.get("start_date")
        try:
            return dt_date.fromisoformat(v) if v else None
        except Exception:
            return None

from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from .sensor import RoiCoordinator, _LOGGER, UPDATE_INTERVAL
from .const import DOMAIN, ATTR_INPUTS_OK
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    coordinator = RoiCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([InputsOkBinarySensor(coordinator, entry)])

class BaseRoiBinary(BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry):
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

class InputsOkBinarySensor(BaseRoiBinary):
    @property
    def name(self) -> str:
        return f"{self._prefix} Inputs OK"

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_inputs_ok"

    @property
    def is_on(self) -> bool:
        d = self.coordinator.data or {}
        return bool(d.get("inputs_ok", False))

    @property
    def icon(self) -> str:
        return "mdi:check-circle" if self.is_on else "mdi:alert-circle"

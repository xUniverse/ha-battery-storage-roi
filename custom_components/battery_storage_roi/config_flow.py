from __future__ import annotations
from datetime import datetime, date
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
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
)

DATE_PATTERNS = [
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d.%m.%y",
    "%d/%m/%Y",
    "%d/%m/%y",
    "%d-%m-%Y",
    "%d-%m-%y",
]

def _normalize_date(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.date().isoformat() if isinstance(val, datetime) else val.isoformat()
    if isinstance(val, dict):
        obj = val
        if "date" in obj:
            inner = obj["date"]
            if isinstance(inner, (datetime, date)):
                return inner.date().isoformat() if isinstance(inner, datetime) else inner.isoformat()
            if isinstance(inner, dict) and all(k in inner for k in ("year", "month", "day")):
                try:
                    return date(int(inner["year"]), int(inner["month"]), int(inner["day"])).isoformat()
                except Exception:
                    return None
            if isinstance(inner, str):
                val = inner
            else:
                return None
        elif all(k in obj for k in ("year", "month", "day")):
            try:
                return date(int(obj["year"]), int(obj["month"]), int(obj["day"])).isoformat()
            except Exception:
                return None
        else:
            return None
    if isinstance(val, str):
        s = val.strip()
        try:
            return datetime.fromisoformat(s).date().isoformat()
        except Exception:
            pass
        for pat in DATE_PATTERNS:
            try:
                return datetime.strptime(s, pat).date().isoformat()
            except Exception:
                continue
        return None
    return None

def _num_cfg(v, default=0.0):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return default

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            raw = user_input.get(CONF_START_DATE)
            iso = _normalize_date(raw)
            if not iso:
                errors[CONF_START_DATE] = "invalid_date"
            else:
                user_input[CONF_START_DATE] = iso
                # normalize numbers
                user_input[CONF_BASELINE_CHARGED] = _num_cfg(user_input.get(CONF_BASELINE_CHARGED, 0.0))
                user_input[CONF_BASELINE_DISCHARGED] = _num_cfg(user_input.get(CONF_BASELINE_DISCHARGED, 0.0))
                user_input[CONF_USABLE_CAPACITY] = _num_cfg(user_input.get(CONF_USABLE_CAPACITY, 5.12))
                title = user_input.get(CONF_NAME, "Battery Storage ROI")
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema({
            vol.Required("name", default="Battery Storage"): str,
            vol.Required(CONF_START_DATE): selector.DateSelector(),
            vol.Required(CONF_INSTALL_COST, default=1100.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_GRID_PRICE, default=0.28): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, step=0.001, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_FEEDIN_PRICE, default=0.075): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, step=0.001, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_CHARGED_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Required(CONF_DISCHARGED_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional(CONF_BASELINE_CHARGED, default=0.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, step=0.001, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_BASELINE_DISCHARGED, default=0.0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, step=0.001, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_USABLE_CAPACITY, default=5.12): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.1, step=0.01, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_INCLUSIVE_DAYS, default=True): selector.BooleanSelector(),
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, import_config):
        return await self.async_step_user(import_config)

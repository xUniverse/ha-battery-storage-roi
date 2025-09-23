# Battery Storage ROI — Home Assistant Integration

[![GitHub release](https://img.shields.io/github/v/release/lemuba/ha-battery-storage-roi)](https://github.com/lemuba/ha-battery-storage-roi/releases) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A Home Assistant custom integration that calculates **efficiency, savings, and ROI** for a battery storage system from your **cumulative charge/discharge energy sensors**.  
Includes rich KPIs, comparison metrics for friendly benchmarking, and a tidy device with grouped entities.

> Version: 1.4.1 · Python 3 · Home Assistant custom component (created with ChatGPT 5)

---

## ✨ Features
- UI configuration (no YAML required)
- Robust date & number parsing (supports `23.9.2025`, `2025-09-23`, commas/decimal points)
- Works with **cumulative kWh sensors** (total or total\_increasing)
- Baselines for initial meter readings at commissioning date
- Detailed KPIs as individual sensors (efficiency, costs, ROI, daily net, etc.)
- **Comparison metrics** for cross-user benchmarking:
  - Money Efficiency (€/kWh_out & €/kWh_in)
  - Specific Net Yield (€/kWhcap/day)
  - Cycles per Day
- All entities grouped under a single device
- EN/DE translations

---

## 🧩 Requirements
- Two cumulative energy sensors (kWh): **Total charged** and **Total discharged**.
- Their `device_class` must be `energy`. Recommended `state_class`: `total_increasing`.

If your source sensors use `device_class: energy` with `state_class: measurement`, create template proxies (see Troubleshooting).

---

## 📦 Installation

### Manual (only)
1. Download the latest release ZIP from the repository.
2. Extract to your Home Assistant config so the path is:
   ```
   <config>/custom_components/battery_storage_roi/
   ```
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and search for **Battery Storage ROI**.

---

## 🚀 Setup (Step by step)
Open **Settings → Devices & Services → Add Integration → Battery Storage ROI**.

You’ll be asked for:
- **System name** — Any label, e.g. *Basement Battery* (used as prefix for entities).
- **Commissioning date** — The day your system started counting. Flexible input: `2025-09-03`, `03.09.2025`, etc.
- **Installation cost (€)** — Total cost of the storage system + install.
- **Grid price (€/kWh)** — Your electricity import price.
- **Feed-in tariff (€/kWh)** — What you earn when exporting to the grid.
- **Sensor: Total charged (kWh)** — Cumulative charge energy sensor.
- **Sensor: Total discharged (kWh)** — Cumulative discharge energy sensor.
- **Initial meter @ start (charged, kWh)** — Baseline of the *charged* sensor at the commissioning date.
- **Initial meter @ start (discharged, kWh)** — Baseline of the *discharged* sensor at the commissioning date.
- **Usable capacity (kWh)** — Your usable battery capacity. **Default 5.12**.
- **Count start day inclusively** — If enabled, days in operation includes the start date (+1).

> **Baselines explained:** If your cumulative sensors already had values **before** the commissioning date, enter those readings here. The integration uses deltas:  
> `charged_since_start = charged_total − baseline_charged`, `discharged_since_start = discharged_total − baseline_discharged`.

---

## 📊 Entities (Sensors)

All entities are created under a single **Battery Storage ROI Virtual Device**. Actual entity IDs include your instance name as prefix.

### Core KPIs
- **… ROI Summary** *(€)* — Net Benefit (total) = Avoided Grid Costs − Opportunity Costs.
- **… Efficiency** *(%)* — Round-trip efficiency = discharged / charged × 100.
- **… Days in Operation** *(d)* — Days since start (inclusive optional).
- **… Avoided Grid Costs** *(€)* — Discharged\_Δ × Grid price.
- **… Opportunity Costs** *(€)* — Charged\_Δ × Feed-in tariff.
- **… Net Benefit** *(€)* — Avoided − Opportunity.
- **… Net Benefit per Day** *(€/day)* — Net Benefit / Days.
- **… ROI Days Remaining** *(d)* — Days until break-even at current average.
- **… ROI Date** *(date)* — Today + ROI Days Remaining (true date type).
- **… Charged since Start** *(kWh, energy/total_increasing)* — Δ charged.
- **… Discharged since Start** *(kWh, energy/total_increasing)* — Δ discharged.
- **… Inputs OK** *(binary)* — True if source sensors are available.

### Comparison Metrics (Benchmarking)
- **… Money Efficiency (per kWh_out)** *(€/kWh)*  
  `grid_price − feedin_price / η` with `η = dischargedΔ / chargedΔ`  
  *How much value per discharged kWh you realize considering prices & efficiency.*
- **… Money Efficiency (per kWh_in)** *(€/kWh)*  
  `η × grid_price − feedin_price`
- **… Specific Net Yield** *(€/kWhcap/day)*  
  `net_benefit_per_day / usable_capacity_kWh`  
  *Normalizes to installed size for fair comparison.*
- **… Cycles per Day** *(cycles/day)*  
  `dischargedΔ / (usable_capacity_kWh × days)`

### Static / Meta
- **… Battery Usable Capacity** *(kWh)* — Configured usable capacity.
- **… Start Date** *(date)* — The commissioning date (stored & emitted as true date).

---

## 🧮 How calculations work (formulas)

Let:
- `CΔ` = charged since start (kWh) = `charged_total − baseline_charged`
- `DΔ` = discharged since start (kWh) = `discharged_total − baseline_discharged`
- `η`  = efficiency = `DΔ / CΔ` (0 if `CΔ = 0`)
- `Pg` = grid price (€/kWh), `Pe` = feed-in tariff (€/kWh)
- `Cap` = usable capacity (kWh), `Days` = days in operation

Then:
- **Avoided Grid Costs (€)** = `DΔ × Pg`
- **Opportunity Costs (€)** = `CΔ × Pe`
- **Net Benefit (€)** = `Avoided − Opportunity`
- **Net Benefit per Day (€)** = `Net Benefit / Days`
- **MoneyEff_out (€/kWh_out)** = `Pg − Pe/η` (if `η>0`)
- **MoneyEff_in (€/kWh_in)** = `η×Pg − Pe` (if `η>0`)
- **Specific Net Yield (€/kWhcap/day)** = `Net Benefit per Day / Cap`
- **Cycles per Day** = `DΔ / (Cap × Days)`
- **ROI Days Remaining** = `ceil( (InstallCost − NetBenefit) / (NetBenefit/Days) )` (if positive), else `0`
- **ROI Date** = `today + ROI Days Remaining`

---

## 🧰 Example Lovelace Cards

### Entities Card (quick)
```yaml
type: entities
title: Battery ROI
entities:
  - sensor.battery_storage_roi_roi_summary
  - sensor.battery_storage_roi_net_benefit_per_day
  - sensor.battery_storage_roi_efficiency
  - sensor.battery_storage_roi_money_efficiency_per_kwh_out
  - sensor.battery_storage_roi_specific_net_yield
  - sensor.battery_storage_roi_cycles_per_day
  - sensor.battery_storage_roi_roi_days_remaining
  - sensor.battery_storage_roi_roi_date
  - sensor.battery_storage_roi_battery_usable_capacity
  - sensor.battery_storage_roi_start_date
  - binary_sensor.battery_storage_roi_inputs_ok
```

### Tile Card (compact KPIs)
```yaml
type: tile
entity: sensor.battery_storage_roi_roi_summary
color: green
show_entity_picture: false
vertical: true
tap_action:
  action: more-info
```

---

## 🩺 Troubleshooting

### 1) “Could not parse date” during setup
The flow accepts many formats. If it still fails, use the date picker or ISO form `YYYY-MM-DD`.

### 2) Log: *state class 'measurement' impossible with device class 'energy'*
Your source sensors must be cumulative (`state_class: total_increasing` or `total`). Create proxies:
```yaml
template:
  - sensor:
      - name: "Total Charging Energy (fixed)"
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        state: "{ states('sensor.total_charging_energy') }"
      - name: "Total Discharging Energy (fixed)"
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        state: "{ states('sensor.total_discharging_energy') }"
```

### 3) ROI Date unavailable
Shows a date when ROI can be computed (i.e., positive net daily). Otherwise it’s intentionally `unavailable`.

### 4) Days seem off by 1
Enable/disable **“Count start day inclusively”** in the options to match your convention.

---

## 🗂 Project Structure
```
custom_components/battery_storage_roi/
  ├── __init__.py
  ├── binary_sensor.py
  ├── config_flow.py
  ├── const.py
  ├── manifest.json
  ├── sensor.py
  ├── strings.json
  └── translations/
      ├── de.json
      └── en.json
docs/
  └── images/
```

---

## 🇩🇪 Kurzanleitung (Deutsch)

**Beschreibung:** Dieses HA-Custom-Integration berechnet **Wirkungsgrad, Ersparnis und ROI** deines Speichers aus zwei **kumulativen kWh-Sensoren** (geladen/entladen). Baselines, viele KPIs und Vergleichskennzahlen sind enthalten. EN/DE Übersetzung vorhanden.

**Installation:** ZIP in `custom_components/battery_storage_roi/` kopieren → HA neu starten → Integration hinzufügen.

**Setup-Felder:**
- **Systemname**: Anzeigename / Präfix
- **Inbetriebnahmedatum**: flexibles Datum (z. B. `03.09.2025` oder `2025-09-03`)
- **Installationskosten (€)**, **Bezugspreis (€/kWh)**, **Einspeisetarif (€/kWh)**
- **Sensor: Gesamt geladen/entladen (kWh, kumulativ)**
- **Zählerstände zum Start (geladen/entladen, kWh)**
- **Nutzbare Kapazität (kWh)** (Default 5,12)
- **Starttag inklusiv zählen** (optional +1 Tag)

**Wichtige Sensoren:**
- **ROI Summary** (Nettoertrag, €)
- **Efficiency** (%), **Days in Operation** (d)
- **Avoided Grid Costs** (€), **Opportunity Costs** (€)
- **Net Benefit** (€), **Net Benefit per Day** (€/day)
- **ROI Days Remaining** (d), **ROI Date** (Datum)
- **Charged/Discharged since Start** (kWh, energy/total_increasing)
- **Money Efficiency (per kWh_out / per kWh_in)** (€/kWh)
- **Specific Net Yield** (€/kWhcap/day)
- **Cycles per Day** (cycles/day)
- **Battery Usable Capacity** (kWh), **Start Date** (Datum)
- **Inputs OK** (Binary: True/False)

**Formeln & Fehlerbehebung:** siehe englischen Abschnitt oben.

---

## 📜 License
MIT License — see `LICENSE`.

## 🤝 Contributing
PRs and issues welcome. Please include logs and your HA version.

---

**Changelog highlights**
- 1.4.1 — Capacity & Start Date sensors
- 1.4.0 — Usable capacity & benchmarking sensors (MoneyEff, SNY, Cycles/Day)
- 1.3.x — Grouped device, ROI Date fix, per-attribute sensors
- 1.2.x — Robust date/number parsing, UI config flow

---

**Maintainer:** [@lemuba](https://github.com/lemuba)

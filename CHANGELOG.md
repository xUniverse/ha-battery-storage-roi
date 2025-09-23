# Changelog

All notable changes to this project will be documented here.

## [1.4.1] - 2025-09-23
### Added
- Sensors: Battery Usable Capacity, Start Date.

## [1.4.0] - 2025-09-23
### Added
- Usable capacity (kWh) in setup.
- Benchmark sensors: Money Efficiency (in/out), Specific Net Yield, Cycles per Day.

## [1.3.3] - 2025-09-23
### Fixed
- Group all entities under a single device.
- ROI Date emits a true `date` value.

## [1.3.2] - 2025-09-23
### Fixed
- Compatibility with modern HA constants (`SensorDeviceClass`, `SensorStateClass`).

## [1.3.1] - 2025-09-23
### Added
- Per-attribute sensors and Inputs OK as binary sensor.

## [1.3.0] - 2025-09-23
### Added
- Baselines (initial meter readings).
- Corrected day/ROI math based on deltas.

## [1.4.1-manual] - Manual-only packaging
- Prepared repository for manual installation (no HACS metadata).

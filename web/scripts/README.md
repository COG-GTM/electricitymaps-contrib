# Web Data Generation Scripts

Scripts for generating the static data files consumed by the Electricity Maps frontend.

## Scripts

### 1. `generate_web_data.py`
Extracts zone and exchange metadata from the repo's YAML configs into JSON files.

**Outputs** (to `web/public/`):
- `zones.json` — 379 zones with name, country, region, timezone
- `exchanges.json` — 381 exchange pairs with coordinates
- `world.geojson` — copied from `geo/world.geojson` (362 zone polygons)

**Usage:**
```bash
python generate_web_data.py
```

### 2. `capture_grid_data.py`
Captures real-time grid state data from the Electricity Maps website using Playwright CDP to intercept API responses.

**Prerequisites:**
- Chrome running with remote debugging on port 29229
- `pip install playwright`

**Output:** JSON file with grid state data keyed by datetime (default: `/tmp/real_timeseries.json`)

**Usage:**
```bash
python capture_grid_data.py [output_path]
```

### 3. `generate_real_data.py`
Transforms captured API data + zone capacity configs into the frontend's `mock-data.json` with real electricity grid values.

**Input:** Captured grid state JSON (default: `web/data/grid_state_2026-05-03.json`)

**Output** (to `web/public/`):
- `mock-data.json` — real carbon intensity, production breakdown, and time series for 351 zones

**Usage:**
```bash
python generate_real_data.py [input_path]
```

## Quick Start

```bash
# Generate all static data from repo configs + pre-captured real data
cd web/scripts
python generate_web_data.py      # zones.json, exchanges.json, world.geojson
python generate_real_data.py     # mock-data.json with real grid data

# OR capture fresh data first
python capture_grid_data.py      # requires Chrome + Playwright
python generate_real_data.py
```

## Pre-captured Data

Real grid state data captured on May 3, 2026 is stored at:
- `web/data/grid_state_2026-05-03.json` (7.7 MB, 97 timepoints, 351 zones)

This data spans a 24-hour window (May 2–3, 2026) at 15-minute resolution and includes carbon intensity, fossil ratio, renewable ratio, and total load for each zone.

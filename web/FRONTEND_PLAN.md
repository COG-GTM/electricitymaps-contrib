# Electricity Maps Frontend — Reproducible Build Plan

> **Goal:** One-shot rebuild of the [Electricity Maps](https://app.electricitymaps.com/map/live/fifteen_minutes) frontend on top of the `COG-GTM/electricitymaps-contrib` repo. This plan contains every file, every line of code, every CSS rule, and every gotcha — so an agent can execute it start-to-finish with zero trial and error.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & Data Sources](#2-prerequisites--data-sources)
3. [Step 1 — Scaffold the Vite + React + TypeScript Project](#3-step-1--scaffold-the-vite--react--typescript-project)
4. [Step 2 — Generate Static Data Files](#4-step-2--generate-static-data-files)
5. [Step 3 — Create Type Definitions](#5-step-3--create-type-definitions)
6. [Step 4 — Create the Color System](#6-step-4--create-the-color-system)
7. [Step 5 — Create the Mock Time Series Generator](#7-step-5--create-the-mock-time-series-generator)
8. [Step 6 — Build Components (in order)](#8-step-6--build-components-in-order)
9. [Step 7 — Wire Up App.tsx and Styles](#9-step-7--wire-up-apptsx-and-styles)
10. [Step 8 — Verify, Build, and Create PR](#10-step-8--verify-build-and-create-pr)
11. [Known Gotchas & Pitfalls](#11-known-gotchas--pitfalls)
12. [Visual Reference](#12-visual-reference)

---

## 1. Architecture Overview

```
web/
├── index.html                     # Vite entrypoint
├── package.json                   # Dependencies
├── tsconfig.json                  # TypeScript config
├── vite.config.ts                 # Vite config
├── vite-env.d.ts                  # Vite type reference
├── public/
│   ├── favicon.svg                # Lightning bolt emoji SVG
│   ├── zones.json                 # 379 zones extracted from config/zones/*.yaml
│   ├── mock-data.json             # Mock carbon intensity + production per zone
│   ├── exchanges.json             # 381 exchanges from config/exchanges/*.yaml
│   └── world.geojson              # 362 zone polygons copied from geo/world.geojson
└── src/
    ├── main.tsx                   # React root mount
    ├── App.tsx                    # Root component + state management
    ├── App.css                    # Layout (flex, sidebar/main split)
    ├── index.css                  # Global styles + CSS variables
    ├── types.ts                   # Shared TypeScript interfaces
    ├── colors.ts                  # CO2 color scale + mode colors
    ├── mockTimeSeries.ts          # 48-hour time series generator
    └── components/
        ├── MapView.tsx + .css     # MapLibre GL map with zone polygons
        ├── Sidebar.tsx + .css     # Left nav (Home, Map, Dev Hub, Coverage)
        ├── ZonePanel.tsx + .css   # Right panel with zone details + charts
        ├── BottomBar.tsx + .css   # Bottom bar with time controls
        ├── CarbonLegend.tsx + .css # Color scale legend
        ├── DateHeader.tsx + .css  # Floating date/time header
        ├── SearchOverlay.tsx + .css # Zone search modal
        ├── CarbonIntensityChart.tsx # Recharts area chart (48h CI)
        └── ElectricityMixChart.tsx  # Recharts stacked area chart (48h mix)
```

### Tech Stack
| Library | Version | Purpose |
|---------|---------|---------|
| React | ^19.2.5 | UI framework |
| react-dom | ^19.2.5 | DOM rendering |
| maplibre-gl | ^5.24.0 | Interactive map |
| recharts | ^3.8.1 | Charts (CI + electricity mix) |
| Vite | ^8.0.10 | Build tool + dev server |
| TypeScript | ^6.0.3 | Type safety |
| @vitejs/plugin-react | ^6.0.1 | React HMR + JSX transform |

### Layout Hierarchy
```
┌──────────────────────────────────────────────┐
│ Sidebar (240px / 52px collapsed, fixed left) │
│  ┌────────────────────────────────────────┐  │
│  │           DateHeader (top center)      │  │
│  │                                        │  │
│  │  ┌──────────┐    ┌──────────────────┐  │  │
│  │  │ ZonePanel│    │     MapView      │  │  │
│  │  │ (440px)  │    │  (fills rest)    │  │  │
│  │  │ (on zone │    │                  │  │  │
│  │  │  click)  │    │                  │  │  │
│  │  └──────────┘    └──────────────────┘  │  │
│  │                         CarbonLegend   │  │
│  │         BottomBar (80px, bottom)       │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

### Z-Index Layers
| Layer | z-index |
|-------|---------|
| Sidebar | 100 |
| SearchOverlay | 60 |
| ZonePanel | 50 |
| BottomBar | 40 |
| DateHeader | 30 |
| CarbonLegend | 30 |

---

## 2. Prerequisites & Data Sources

### Repository Data Available
The `electricitymaps-contrib` repo contains:
- **`config/zones/*.yaml`** (379 files): Zone metadata — `zoneName`, `countryKey`, `countryName`, `timezone`, `capacity`, `bounding_box`
- **`config/exchanges/*.yaml`** (381 files): Exchange metadata — `lonlat`, `rotation`, `parsers`
- **`geo/world.geojson`**: 362 zone polygons with properties `{zoneName, countryKey, countryName}`

### Important: `countryKey` can be `null`
The `XX` zone (Northern Cyprus) has `countryKey: null` in the YAML config. Your TypeScript types MUST account for this: `countryKey: string | null`. Every place that uses `countryKey` must guard against null.

---

## 3. Step 1 — Scaffold the Vite + React + TypeScript Project

All files go in `web/` at the repo root.

### `web/package.json`
```json
{
  "name": "electricitymaps-web",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "maplibre-gl": "^5.24.0",
    "react": "^19.2.5",
    "react-dom": "^19.2.5",
    "recharts": "^3.8.1"
  },
  "devDependencies": {
    "@types/react": "^19.2.14",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^6.0.1",
    "typescript": "^6.0.3",
    "vite": "^8.0.10"
  }
}
```

### `web/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "resolveJsonModule": true,
    "allowJs": true
  },
  "include": ["src", "vite-env.d.ts"]
}
```

### `web/vite.config.ts`
```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
});
```

### `web/vite-env.d.ts`
```ts
/// <reference types="vite/client" />
```

### `web/index.html`
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Electricity Maps</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### `web/public/favicon.svg`
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <text y="28" font-size="28">&#9889;</text>
</svg>
```

### Install dependencies
```bash
cd web && npm install
```

---

## 4. Step 2 — Generate Static Data Files

Run a Python script from the repo root to extract zone/exchange config into JSON. This script reads the YAML configs and produces the 3 JSON files + copies the GeoJSON.

### Data generation scripts are in `web/scripts/` (already committed to the repo)

The following scripts handle all data generation. Run them in order:

1. **`web/scripts/generate_web_data.py`** — generates zones.json, exchanges.json, copies world.geojson
2. **`web/scripts/capture_grid_data.py`** — captures real API data from Electricity Maps (requires Chrome + Playwright)
3. **`web/scripts/generate_real_data.py`** — transforms captured API data into mock-data.json with real values

Pre-captured real data (May 3, 2026) is available at `web/data/grid_state_2026-05-03.json`.

```bash
cd web/scripts
python generate_web_data.py                    # generates zones.json, exchanges.json, world.geojson
python generate_real_data.py                    # generates mock-data.json from pre-captured data
# OR to capture fresh data: python capture_grid_data.py && python generate_real_data.py
```

### Reference: `generate_web_data.py` (already in web/scripts/)

```python
#!/usr/bin/env python3
"""Generate static data files for the web frontend from repo config."""
import json
import os
import random
import shutil

import yaml

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
ZONES_DIR = os.path.join(REPO_ROOT, 'config', 'zones')
EXCHANGES_DIR = os.path.join(REPO_ROOT, 'config', 'exchanges')
GEO_FILE = os.path.join(REPO_ROOT, 'geo', 'world.geojson')
OUT_DIR = os.path.join(REPO_ROOT, 'web', 'public')

os.makedirs(OUT_DIR, exist_ok=True)

# --- zones.json ---
zones = {}
for fname in sorted(os.listdir(ZONES_DIR)):
    if not fname.endswith('.yaml'):
        continue
    zone_key = fname.replace('.yaml', '')
    with open(os.path.join(ZONES_DIR, fname)) as f:
        cfg = yaml.safe_load(f)
    zones[zone_key] = {
        'zoneName': cfg.get('zone_name', cfg.get('zoneName', zone_key)),
        'countryKey': cfg.get('country_code', cfg.get('countryKey')),
        'countryName': cfg.get('country_name', cfg.get('countryName', zone_key)),
        'region': cfg.get('region', 'Unknown'),
        'timezone': cfg.get('timezone', 'UTC'),
    }
with open(os.path.join(OUT_DIR, 'zones.json'), 'w') as f:
    json.dump(zones, f, indent=2, ensure_ascii=False)
print(f"Generated zones.json: {len(zones)} zones")

# --- exchanges.json ---
exchanges = {}
for fname in sorted(os.listdir(EXCHANGES_DIR)):
    if not fname.endswith('.yaml'):
        continue
    key = fname.replace('.yaml', '').replace('_', '->')
    with open(os.path.join(EXCHANGES_DIR, fname)) as f:
        cfg = yaml.safe_load(f)
    lonlat = cfg.get('lonlat', [0, 0])
    rotation = cfg.get('rotation', 0)
    zones_pair = key.split('->')
    exchanges[key] = {
        'zones': zones_pair,
        'lonlat': lonlat,
        'rotation': rotation,
    }
with open(os.path.join(OUT_DIR, 'exchanges.json'), 'w') as f:
    json.dump(exchanges, f, indent=2, ensure_ascii=False)
print(f"Generated exchanges.json: {len(exchanges)} exchanges")

# --- mock-data.json ---
# Generate realistic-looking mock carbon intensity and production data per zone
random.seed(42)
MODE_EMISSION_FACTORS = {
    'nuclear': 12, 'wind': 11, 'solar': 45, 'hydro': 24,
    'gas': 380, 'coal': 820, 'oil': 650, 'biomass': 230, 'geothermal': 38,
}
mock_data = {}
for zone_key, info in zones.items():
    region = info.get('region', 'Unknown')
    # Regional profiles for realistic variety
    if region == 'Europe':
        profile = {'nuclear': 3.0, 'wind': 2.5, 'solar': 1.5, 'hydro': 2.0,
                   'gas': 2.0, 'coal': 1.0, 'oil': 0.1, 'biomass': 0.3, 'geothermal': 0.1}
    elif region == 'Americas':
        profile = {'nuclear': 2.0, 'wind': 1.5, 'solar': 2.0, 'hydro': 3.0,
                   'gas': 3.0, 'coal': 1.5, 'oil': 0.3, 'biomass': 0.5, 'geothermal': 0.2}
    elif region == 'Asia':
        profile = {'nuclear': 1.0, 'wind': 1.0, 'solar': 1.5, 'hydro': 2.0,
                   'gas': 2.5, 'coal': 4.0, 'oil': 0.5, 'biomass': 0.2, 'geothermal': 0.1}
    elif region == 'Africa':
        profile = {'nuclear': 0.1, 'wind': 0.5, 'solar': 1.0, 'hydro': 2.0,
                   'gas': 1.5, 'coal': 2.0, 'oil': 1.0, 'biomass': 0.3, 'geothermal': 0.2}
    elif region == 'Oceania':
        profile = {'nuclear': 0.0, 'wind': 2.0, 'solar': 2.5, 'hydro': 1.5,
                   'gas': 2.5, 'coal': 2.0, 'oil': 0.2, 'biomass': 0.3, 'geothermal': 0.1}
    else:
        profile = {'nuclear': 1.0, 'wind': 1.0, 'solar': 1.0, 'hydro': 1.0,
                   'gas': 2.0, 'coal': 2.0, 'oil': 0.5, 'biomass': 0.2, 'geothermal': 0.1}

    production = {}
    total = 0
    for mode, base in profile.items():
        val = round(base * (0.3 + random.random() * 1.4), 2)
        production[mode] = val
        total += val

    # Compute carbon intensity from weighted emission factors
    ci = sum(production[m] * MODE_EMISSION_FACTORS[m] for m in production) / total if total > 0 else 200
    ci = round(ci)

    carbon_free_modes = {'nuclear', 'wind', 'solar', 'hydro', 'geothermal'}
    renewable_modes = {'wind', 'solar', 'hydro', 'biomass', 'geothermal'}
    cf = sum(production[m] for m in carbon_free_modes) / total * 100 if total > 0 else 0
    rn = sum(production[m] for m in renewable_modes) / total * 100 if total > 0 else 0

    mock_data[zone_key] = {
        'carbonIntensity': ci,
        'carbonFree': round(cf, 1),
        'renewable': round(rn, 1),
        'totalProduction': round(total, 2),
        'production': production,
        'isEstimated': random.random() > 0.5,
    }
with open(os.path.join(OUT_DIR, 'mock-data.json'), 'w') as f:
    json.dump(mock_data, f, indent=2, ensure_ascii=False)
print(f"Generated mock-data.json: {len(mock_data)} zones")

# --- world.geojson ---
shutil.copy(GEO_FILE, os.path.join(OUT_DIR, 'world.geojson'))
print("Copied world.geojson")
```

**IMPORTANT:** The zone YAML fields vary. Look for `zone_name` or `zoneName`, `country_code` or `countryKey`, etc. The scripts handle both. After running, verify:
- `zones.json` has ~379 entries
- `mock-data.json` has ~351 zone entries (zones with API data) with real carbon intensity values
- `exchanges.json` has ~381 entries
- `world.geojson` has 362 features

**CRITICAL: Bosnia timezone bug.** The repo's `BA.yaml` has `timezone: Asia/Bahrain` (wrong). Fix it to `Europe/Sarajevo` in the generated `zones.json`.

### Real Data Format

The `mock-data.json` produced by `generate_real_data.py` has this structure:
```json
{
  "timestamp": "2026-05-03T23:15:00Z",
  "zones": {
    "FR": {
      "carbonIntensity": 11,
      "carbonFree": 99.9,
      "renewable": 23.4,
      "totalProduction": 38237.9,
      "production": { "nuclear": 26836.0, "wind": 3188.7, "solar": 0, "hydro": 3037.7, ... },
      "isEstimated": true
    }
  },
  "timeseries": {
    "FR": [
      { "datetime": "2026-05-02T23:15:00Z", "carbonIntensity": 12 },
      { "datetime": "2026-05-02T23:30:00Z", "carbonIntensity": 13 }
    ]
  }
}
```

Your `App.tsx` must extract `realData.zones` and `realData.timeseries` separately. The `ProductionMix` type must be `Record<string, number>` (not a fixed interface) since real data includes dynamic modes like "hydro storage", "battery discharge", etc.

---

## 5. Step 3 — Create Type Definitions

### `web/src/types.ts`
```ts
export interface ZoneInfo {
  zoneName: string;
  countryKey: string | null;  // null for XX (Northern Cyprus)
  countryName: string;
  region: string;
  timezone: string;
}

// Dynamic keys — real data includes modes like "hydro storage", "battery discharge", etc.
// Common modes: nuclear, wind, solar, hydro, hydro storage, hydro discharge,
// battery storage, battery discharge, gas, coal, oil, biomass, geothermal
export type ProductionMix = Record<string, number>;

export interface ZoneMockData {
  carbonIntensity: number;
  carbonFree: number;
  renewable: number;
  totalProduction: number;
  production: ProductionMix;
  isEstimated: boolean;
}

export interface ExchangeInfo {
  zones: string[];
  lonlat: [number, number];
  rotation: number;
}

export type Resolution = 'five_minutes' | 'fifteen_minutes' | 'hourly' | 'daily' | 'monthly' | 'yearly';

export interface TimeSeriesPoint {
  datetime: string;
  carbonIntensity: number;
  production?: ProductionMix;
}

// Matches the output format of generate_real_data.py
export interface RealDataFile {
  timestamp: string;
  zones: Record<string, ZoneMockData>;
  timeseries: Record<string, { datetime: string; carbonIntensity: number }[]>;
}
```

---

## 6. Step 4 — Create the Color System

### `web/src/colors.ts`

The Electricity Maps color scale goes:
- **0 gCO₂** → `#2AA364` (green)
- **150** → `#F5EB4D` (yellow)
- **600** → `#9E4229` (brown)
- **800** → `#381D02` (dark brown)
- **1500** → `#000000` (black)

```ts
export const CO2_COLOR_STOPS: [number, string][] = [
  [0, '#2AA364'],
  [150, '#F5EB4D'],
  [600, '#9E4229'],
  [800, '#381D02'],
  [1500, '#000000'],
];

export function getCO2Color(intensity: number): string {
  if (intensity <= 0) return CO2_COLOR_STOPS[0][1];
  if (intensity >= 1500) return CO2_COLOR_STOPS[CO2_COLOR_STOPS.length - 1][1];

  for (let i = 1; i < CO2_COLOR_STOPS.length; i++) {
    const [prevVal, prevColor] = CO2_COLOR_STOPS[i - 1];
    const [nextVal, nextColor] = CO2_COLOR_STOPS[i];
    if (intensity <= nextVal) {
      const t = (intensity - prevVal) / (nextVal - prevVal);
      return interpolateColor(prevColor, nextColor, t);
    }
  }
  return CO2_COLOR_STOPS[CO2_COLOR_STOPS.length - 1][1];
}

function interpolateColor(c1: string, c2: string, t: number): string {
  const r1 = parseInt(c1.slice(1, 3), 16);
  const g1 = parseInt(c1.slice(3, 5), 16);
  const b1 = parseInt(c1.slice(5, 7), 16);
  const r2 = parseInt(c2.slice(1, 3), 16);
  const g2 = parseInt(c2.slice(3, 5), 16);
  const b2 = parseInt(c2.slice(5, 7), 16);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

export const MODE_COLORS: Record<string, string> = {
  nuclear: '#AE4BBD',
  wind: '#74cdb9',
  solar: '#f27406',
  hydro: '#2772b2',
  'hydro storage': '#1B5E8C',
  'hydro discharge': '#3D8EB9',
  'battery storage': '#B76ECD',
  'battery discharge': '#9B4DCA',
  gas: '#bb2f51',
  coal: '#ac8c35',
  oil: '#867d66',
  biomass: '#A1A422',
  geothermal: '#CD6340',
  'unknown fossil': '#666666',
  'unknown renewable': '#8BC34A',
  unknown: '#ACACAC',
};

export const NO_DATA_COLOR = '#d4d4d4';
```

---

## 7. Step 5 — Create the Mock Time Series Generator

### `web/src/mockTimeSeries.ts`

Generates 48 hourly data points per zone with deterministic pseudo-random variation based on zone key. Simulates:
- Solar follows daylight curve (peak at noon, zero at night)
- Wind has semi-random sinusoidal pattern
- Demand peaks mid-day, troughs at night
- Nuclear/geothermal stay stable (baseload)

```ts
import type { ProductionMix, TimeSeriesPoint, ZoneMockData } from './types';

export function generateTimeSeries(
  zoneKey: string,
  baseData: ZoneMockData,
  hours: number = 48,
): TimeSeriesPoint[] {
  const points: TimeSeriesPoint[] = [];
  const now = new Date();
  const seed = hashCode(zoneKey);

  for (let i = hours; i >= 0; i--) {
    const dt = new Date(now.getTime() - i * 60 * 60 * 1000);
    const hour = dt.getHours();

    const solarFactor = Math.max(0, Math.sin(((hour - 6) / 12) * Math.PI));
    const windFactor = 0.5 + 0.5 * Math.sin((hour / 24) * Math.PI * 2 + pseudoRandom(seed + i) * 2);
    const demandFactor = 0.7 + 0.3 * Math.sin(((hour - 4) / 24) * Math.PI * 2);

    const production: ProductionMix = {
      nuclear: baseData.production.nuclear * (0.9 + pseudoRandom(seed + i * 7) * 0.2),
      wind: baseData.production.wind * windFactor * (0.5 + pseudoRandom(seed + i * 3) * 1),
      solar: baseData.production.solar * solarFactor,
      hydro: baseData.production.hydro * (0.8 + pseudoRandom(seed + i * 11) * 0.4),
      gas: baseData.production.gas * demandFactor * (0.7 + pseudoRandom(seed + i * 13) * 0.6),
      coal: baseData.production.coal * demandFactor * (0.8 + pseudoRandom(seed + i * 17) * 0.4),
      oil: baseData.production.oil * (0.6 + pseudoRandom(seed + i * 19) * 0.8),
      biomass: baseData.production.biomass * (0.9 + pseudoRandom(seed + i * 23) * 0.2),
      geothermal: baseData.production.geothermal * (0.95 + pseudoRandom(seed + i * 29) * 0.1),
    };

    for (const key of Object.keys(production)) {
      production[key as keyof ProductionMix] = Math.round(production[key as keyof ProductionMix] * 100) / 100;
    }

    const co2Factors: Record<string, number> = {
      nuclear: 12, wind: 11, solar: 45, hydro: 24, gas: 380,
      coal: 820, oil: 650, biomass: 230, geothermal: 38,
    };
    const total = Object.values(production).reduce((s, v) => s + v, 0);
    let ci = 0;
    if (total > 0) {
      ci = Object.entries(production).reduce((s, [k, v]) => s + v * (co2Factors[k] || 200), 0) / total;
    }

    points.push({
      datetime: dt.toISOString(),
      carbonIntensity: Math.round(ci),
      production,
    });
  }

  return points;
}

function hashCode(s: string): number {
  let hash = 0;
  for (let i = 0; i < s.length; i++) {
    const char = s.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash);
}

function pseudoRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}
```

---

## 8. Step 6 — Build Components (in order)

Build these components in this exact order. Each section includes the full TSX and CSS.

---

### 6.1 — MapView (the core map)

**CRITICAL GOTCHA — Stale Closures:** The map initialization runs once in a `useEffect([], [])`. Any callbacks registered on the map (click, mousemove) capture props from that first render. Use **refs** (`mockDataRef`, `onZoneSelectRef`) to always access current values.

**CRITICAL GOTCHA — Zone Coloring:** Do NOT try to use a MapLibre `match` expression with 379 entries for `fill-color`. It causes stale data issues. Instead, **embed the color directly into the GeoJSON properties** via `buildGeoJsonWithColors()` and use `['get', 'fillColor']` as the paint expression. Update via `source.setData()` when data changes.

#### `web/src/components/MapView.tsx`
```tsx
import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import type { ZoneMockData } from '../types';
import { getCO2Color, NO_DATA_COLOR } from '../colors';
import './MapView.css';

interface MapViewProps {
  mockData: Record<string, ZoneMockData>;
  selectedZone: string | null;
  onZoneSelect: (zoneKey: string | null) => void;
}

function buildGeoJsonWithColors(
  geojson: GeoJSON.FeatureCollection,
  data: Record<string, ZoneMockData>,
): GeoJSON.FeatureCollection {
  const hasData = Object.keys(data).length > 0;
  return {
    ...geojson,
    features: geojson.features.map((f) => {
      const zoneName = f.properties?.zoneName;
      const zd = hasData && zoneName ? data[zoneName] : undefined;
      return {
        ...f,
        properties: {
          ...f.properties,
          fillColor: zd ? getCO2Color(zd.carbonIntensity) : NO_DATA_COLOR,
          carbonIntensity: zd?.carbonIntensity ?? null,
        },
      };
    }),
  };
}

export default function MapView({ mockData, selectedZone, onZoneSelect }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const geoJsonRef = useRef<GeoJSON.FeatureCollection | null>(null);
  const mapLoadedRef = useRef(false);
  const mockDataRef = useRef(mockData);
  mockDataRef.current = mockData;
  const onZoneSelectRef = useRef(onZoneSelect);
  onZoneSelectRef.current = onZoneSelect;

  // Initialize map ONCE
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap contributors',
          },
        },
        layers: [
          {
            id: 'osm-tiles',
            type: 'raster',
            source: 'osm-tiles',
            paint: {
              'raster-opacity': 0.3,
              'raster-saturation': -0.5,
            },
          },
        ],
      },
      center: [10, 40],   // Europe-centered
      zoom: 2.5,
      minZoom: 1,
      maxZoom: 10,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

    map.on('load', async () => {
      const resp = await fetch('/world.geojson');
      const geojson = (await resp.json()) as GeoJSON.FeatureCollection;
      geoJsonRef.current = geojson;

      const colored = buildGeoJsonWithColors(geojson, mockDataRef.current);

      map.addSource('zones', { type: 'geojson', data: colored });

      // Zone fill layer
      map.addLayer({
        id: 'zones-fill',
        type: 'fill',
        source: 'zones',
        paint: {
          'fill-color': ['get', 'fillColor'],
          'fill-opacity': 0.85,
        },
      });

      // White borders between zones
      map.addLayer({
        id: 'zones-border',
        type: 'line',
        source: 'zones',
        paint: {
          'line-color': '#ffffff',
          'line-width': 0.8,
          'line-opacity': 0.6,
        },
      });

      // Selected zone highlight (black border, opacity toggled)
      map.addLayer({
        id: 'zones-highlight',
        type: 'line',
        source: 'zones',
        paint: {
          'line-color': '#000000',
          'line-width': 2.5,
          'line-opacity': 0,
        },
      });

      mapLoadedRef.current = true;
    });

    // Zone click → use ref to avoid stale closure
    map.on('click', 'zones-fill', (e) => {
      if (e.features && e.features.length > 0) {
        const zone = e.features[0].properties?.zoneName;
        if (zone) onZoneSelectRef.current(zone);
      }
    });

    map.on('mouseenter', 'zones-fill', () => {
      map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'zones-fill', () => {
      map.getCanvas().style.cursor = '';
    });

    // Hover tooltip
    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 10,
      className: 'zone-popup',
    });

    map.on('mousemove', 'zones-fill', (e) => {
      if (e.features && e.features.length > 0) {
        const zone = e.features[0].properties?.zoneName;
        const countryName = e.features[0].properties?.countryName;
        const ci = e.features[0].properties?.carbonIntensity;
        if (zone) {
          const ciText = ci != null ? `${ci} gCO\u2082eq/kWh` : 'No data';
          popup
            .setLngLat(e.lngLat)
            .setHTML(`<strong>${countryName || zone}</strong><br/>${ciText}`)
            .addTo(map);
        }
      }
    });

    map.on('mouseleave', 'zones-fill', () => {
      popup.remove();
    });

    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  // Re-color zones when mockData changes
  useEffect(() => {
    const map = mapRef.current;
    const geojson = geoJsonRef.current;
    if (!map || !geojson || !mapLoadedRef.current || Object.keys(mockData).length === 0) return;

    const colored = buildGeoJsonWithColors(geojson, mockData);
    const source = map.getSource('zones') as maplibregl.GeoJSONSource | undefined;
    if (source) source.setData(colored);
  }, [mockData]);

  // Highlight selected zone
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoadedRef.current) return;

    try {
      if (selectedZone) {
        map.setPaintProperty('zones-highlight', 'line-opacity', [
          'case',
          ['==', ['get', 'zoneName'], selectedZone],
          1,
          0,
        ] as unknown as maplibregl.ExpressionSpecification);
      } else {
        map.setPaintProperty('zones-highlight', 'line-opacity', 0);
      }
    } catch {
      // Layer might not be ready yet
    }
  }, [selectedZone]);

  return <div ref={containerRef} className="map-view" />;
}
```

#### `web/src/components/MapView.css`
```css
.map-view {
  width: 100%;
  height: 100%;
}

.maplibregl-ctrl-top-right {
  top: 60px;
  right: 8px;
}

.maplibregl-ctrl-group {
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12) !important;
}

.zone-popup .maplibregl-popup-content {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-family: var(--font-family);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
```

---

### 6.2 — Sidebar

Left navigation panel. 240px wide, collapses to 52px (icon-only). SVG icons for each nav item.

#### `web/src/components/Sidebar.tsx`
```tsx
import './Sidebar.css';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onSearchClick: () => void;
}

export default function Sidebar({ collapsed, onToggle, onSearchClick }: SidebarProps) {
  return (
    <nav className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="#2AA364" stroke="#2AA364" strokeWidth="1"/>
          </svg>
          {!collapsed && <span className="sidebar__title">Electricity Maps</span>}
        </div>
        <button className="sidebar__toggle" onClick={onToggle} aria-label="Toggle Sidebar">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            {collapsed ? (
              <path d="M6 3l5 5-5 5V3z"/>
            ) : (
              <path d="M10 3L5 8l5 5V3z"/>
            )}
          </svg>
        </button>
      </div>

      <ul className="sidebar__nav">
        <li>
          <a href="#" className="sidebar__link">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M3 10.5L10 4l7 6.5V17a1 1 0 01-1 1H4a1 1 0 01-1-1V10.5z"/>
            </svg>
            {!collapsed && <span>Home</span>}
          </a>
        </li>
        <li>
          <a href="#" className="sidebar__link sidebar__link--active">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="2" y="3" width="16" height="14" rx="2"/>
              <path d="M2 8h16M8 8v9"/>
            </svg>
            {!collapsed && <span>Map</span>}
          </a>
        </li>
        <li>
          <a href="#" className="sidebar__link">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M5 3l2 6H3l2 6M11 3l2 6h-4l2 6"/>
            </svg>
            {!collapsed && <span>Developer Hub</span>}
          </a>
        </li>
        <li>
          <a href="#" className="sidebar__link">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="2" y="2" width="6" height="6" rx="1"/>
              <rect x="12" y="2" width="6" height="6" rx="1"/>
              <rect x="2" y="12" width="6" height="6" rx="1"/>
              <rect x="12" y="12" width="6" height="6" rx="1"/>
            </svg>
            {!collapsed && <span>Coverage</span>}
          </a>
        </li>
      </ul>

      <div className="sidebar__footer">
        <button className="sidebar__link" onClick={onSearchClick}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="9" cy="9" r="6"/>
            <path d="M14 14l4 4"/>
          </svg>
          {!collapsed && <span>Search areas</span>}
        </button>
      </div>
    </nav>
  );
}
```

#### `web/src/components/Sidebar.css`
```css
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-bg);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.2s ease;
}

.sidebar--collapsed {
  width: 52px;
}

.sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 12px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar__logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar__title {
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
}

.sidebar__toggle {
  padding: 4px;
  border-radius: 4px;
  color: var(--color-text-secondary);
}

.sidebar__toggle:hover {
  background: var(--color-bg-secondary);
}

.sidebar__nav {
  list-style: none;
  padding: 8px 0;
  flex: 1;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  font-size: 14px;
  color: var(--color-text-secondary);
  border-radius: 8px;
  margin: 2px 8px;
  transition: background 0.15s;
  white-space: nowrap;
}

.sidebar--collapsed .sidebar__link {
  justify-content: center;
  padding: 10px;
  margin: 2px 4px;
}

.sidebar__link:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text);
}

.sidebar__link--active {
  background: var(--color-bg-secondary);
  color: var(--color-text);
  font-weight: 600;
}

.sidebar__footer {
  padding: 8px 0;
  border-top: 1px solid var(--color-border);
}
```

---

### 6.3 — ZonePanel

Right-side detail panel shown when a zone is selected. 440px wide. Shows:
1. Header with back button, flag emoji, zone name
2. Carbon intensity (large colored number), carbon-free %, renewable %
3. Installed capacity bar (stacked segments by fuel type)
4. Carbon intensity color bar with marker
5. Carbon intensity chart (48h)
6. Electricity mix chart (48h)
7. Electricity load
8. Data sources text

**Flag emoji generation:** Convert 2-letter country code to regional indicator symbols.
```ts
function getCountryFlag(countryKey: string): string {
  const code = countryKey.split('-')[0].toUpperCase();
  if (code.length !== 2) return '';
  const offset = 0x1f1e6;
  return String.fromCodePoint(
    code.charCodeAt(0) - 65 + offset,
    code.charCodeAt(1) - 65 + offset,
  );
}
```

**IMPORTANT:** Guard against null countryKey: `getCountryFlag(zoneInfo?.countryKey || zoneKey.split('-')[0])`

#### `web/src/components/ZonePanel.tsx`
Full file — see the working implementation. Key structural elements:
- `zone-panel__metrics` uses a 3-column CSS grid
- Carbon-free and renewable show a small gauge bar + percentage
- Capacity bar segments use `MODE_COLORS` and width proportional to production share
- CI color bar gradient: `linear-gradient(to right, #2AA364 0%, #F5EB4D 10%, #9E4229 40%, #381D02 53%, #000000 100%)`
- Marker position: `left: ${Math.min(100, (ci / 1500) * 100)}%`

#### `web/src/components/ZonePanel.css`
Full file — see working implementation. Key measurements:
- Panel width: `var(--panel-width)` (440px)
- Section padding: `16px 20px`
- CI number: `font-size: 28px; font-weight: 700`
- Gauge bar: `width: 60px; height: 8px`

---

### 6.4 — BottomBar

Fixed to bottom. Contains date/time (UTC), resolution dropdown, and time slider.

**CRITICAL:** All date/time formatting MUST use `timeZone: 'UTC'` — both `toLocaleDateString` and `toLocaleTimeString`. Otherwise the date and time will be in the user's local timezone but labeled "UTC".

**Time tick generation:** Compare each tick's date against the *previous* tick's date (not against start) to determine whether to show a date label or time label. Otherwise you get duplicate "May 3" labels.

#### `web/src/components/BottomBar.tsx`
See full file above. Key: `generateTimeTicks` uses `prevDate` tracking.

#### `web/src/components/BottomBar.css`
See full file above. Key: 80px height, live-dot has `pulse` animation.

---

### 6.5 — CarbonLegend

Small floating box at bottom-right showing the color gradient scale 0–1500.

#### `web/src/components/CarbonLegend.tsx`
```tsx
import './CarbonLegend.css';

export default function CarbonLegend() {
  return (
    <div className="carbon-legend">
      <div className="carbon-legend__header">
        <span className="carbon-legend__title">Carbon intensity</span>
        <span className="carbon-legend__unit">gCO&#x2082;eq/kWh</span>
      </div>
      <div className="carbon-legend__bar" />
      <div className="carbon-legend__ticks">
        <span>0</span><span>300</span><span>600</span><span>900</span><span>1200</span><span>1500</span>
      </div>
    </div>
  );
}
```

Gradient: `linear-gradient(to right, #2AA364 0%, #F5EB4D 10%, #9E4229 40%, #381D02 53%, #000000 100%)`

---

### 6.6 — DateHeader

Floating pill at top center showing date + time with red pulsing "live" dot.

#### `web/src/components/DateHeader.tsx`
```tsx
import './DateHeader.css';

interface DateHeaderProps {
  currentTime: Date;
}

export default function DateHeader({ currentTime }: DateHeaderProps) {
  const dateStr = currentTime.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
  const timeStr = currentTime.toLocaleTimeString('en-US', {
    hour: 'numeric', minute: '2-digit',
  });

  return (
    <div className="date-header">
      <span className="date-header__date">{dateStr}</span>
      <span className="date-header__time">
        {timeStr}
        <span className="date-header__live" />
      </span>
    </div>
  );
}
```

---

### 6.7 — SearchOverlay

Modal overlay with search input and zone results list. Each result shows flag, zone name, country name, and carbon intensity.

**IMPORTANT:** Guard null countryKey: `info.countryKey ? getCountryFlag(info.countryKey) : ''`

---

### 6.8 — CarbonIntensityChart

Recharts `AreaChart` with gradient fill. X-axis is time (48h), Y-axis is gCO₂eq/kWh.

**GOTCHA:** Do NOT add explicit type annotations to Recharts `formatter` callbacks like `(v: number) => ...`. Let TypeScript infer the types — Recharts has complex generic types that cause errors with explicit annotations.

---

### 6.9 — ElectricityMixChart

Recharts stacked `AreaChart`. Each fuel type is an `Area` with `stackId="1"`.

Fuel type rendering order (bottom to top): nuclear, hydro, wind, solar, geothermal, biomass, gas, oil, coal.

---

## 9. Step 7 — Wire Up App.tsx and Styles

### `web/src/main.tsx`
```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

### `web/src/index.css`

Key CSS variables:
```css
@import 'maplibre-gl/dist/maplibre-gl.css';

:root {
  --sidebar-width: 240px;
  --panel-width: 440px;
  --bottom-bar-height: 80px;
  --color-bg: #ffffff;
  --color-bg-secondary: #f8f9fa;
  --color-border: #e5e7eb;
  --color-text: #1a1a2e;
  --color-text-secondary: #6b7280;
  --color-accent: #0ea5e9;
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
```

**CRITICAL:** Must import `maplibre-gl/dist/maplibre-gl.css` here. Without it, the map controls won't render properly.

Also: hide MapLibre attribution controls:
```css
.maplibregl-ctrl-bottom-left,
.maplibregl-ctrl-bottom-right {
  display: none;
}
```

### `web/src/App.tsx`

State managed at root level:
- `zones: Record<string, ZoneInfo>` — loaded from `/zones.json`
- `mockData: Record<string, ZoneMockData>` — loaded from `/mock-data.json`
- `selectedZone: string | null`
- `resolution: Resolution` — default `'fifteen_minutes'`
- `sidebarCollapsed: boolean`
- `searchOpen: boolean`
- `currentTime: Date`

**IMPORTANT:** Wrap `handleZoneSelect` and `handleBack` in `useCallback([], [])` for stable references passed to MapView.

### `web/src/App.css`

```css
.app {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
}

.main-area {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: var(--sidebar-width);
  transition: left 0.2s ease;
  overflow: hidden;
}
```

**GOTCHA:** The `main-area` MUST have `overflow: hidden`. Without it, the map container won't render at the correct size.

---

## 10. Step 8 — Verify, Build, and Create PR

```bash
# 1. Type-check
cd web && npx tsc --noEmit

# 2. Build for production
npx vite build

# 3. Start dev server and verify in browser
npm run dev
# Open http://localhost:5173
# Verify: zones colored, clicking opens panel, charts render

# 4. Commit and push
cd ..
git add web/
git commit -m "feat(web): rebuild Electricity Maps frontend with React + TypeScript"
git push origin <branch-name>

# 5. Create PR to COG-GTM/electricitymaps-contrib
```

---

## 11. Known Gotchas & Pitfalls

| # | Gotcha | Solution |
|---|--------|----------|
| 1 | **Stale closures in MapLibre event handlers** | Use refs (`mockDataRef`, `onZoneSelectRef`) updated on every render. Event handlers read `.current` |
| 2 | **Map container renders at 0px height** | Ensure `.main-area` has `overflow: hidden` and `.map-view` has `width: 100%; height: 100%` |
| 3 | **Zones show NO_DATA_COLOR despite data loaded** | Don't use `match` expression with 379 entries for fill-color. Embed `fillColor` directly in GeoJSON properties, use `['get', 'fillColor']` |
| 4 | **Zones not visible until zoom** | At zoom 2.5 centered on [10, 40], European zones are visible. Color becomes obvious on zoom in |
| 5 | **Recharts formatter type errors** | Don't annotate formatter params explicitly. Let TypeScript infer types |
| 6 | **Bosnia (BA) timezone wrong** | Repo has `Asia/Bahrain`. Correct to `Europe/Sarajevo` |
| 7 | **Northern Cyprus (XX) has null countryKey** | Type `countryKey: string \| null`. Guard all usages with null checks |
| 8 | **Time displayed as local but labeled UTC** | Always pass `timeZone: 'UTC'` to both `toLocaleDateString` and `toLocaleTimeString` when labeling as UTC |
| 9 | **Duplicate date labels in time ticks** | Track `prevDate` and compare each tick against it, not against the start date |
| 10 | **MapLibre CSS missing** | Import `maplibre-gl/dist/maplibre-gl.css` in `index.css` |

---

## 12. Visual Reference

The final app should look like the live Electricity Maps app:
- **Map view:** Full-screen map with colored zone polygons (green=low CO₂, brown/black=high CO₂)
- **Sidebar:** Left sidebar with lightning bolt logo, 4 nav links, search button at bottom
- **Date header:** Floating pill at top center with date, time, red live dot
- **Carbon legend:** Small box at bottom-right with color gradient bar and 0–1500 scale
- **Bottom bar:** Fixed bottom bar with date/time (UTC), resolution dropdown, time slider
- **Zone panel:** 440px panel sliding in from left when zone clicked, showing metrics + charts
- **Hover tooltip:** Shows zone name and carbon intensity on mouse hover
- **Search:** Modal overlay filtering zones by name/country with carbon intensity preview

Reference: https://app.electricitymaps.com/map/live/fifteen_minutes

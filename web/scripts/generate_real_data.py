#!/usr/bin/env python3
"""
Generate real data JSON files for the frontend from:
1. Live grid-state data captured from the Electricity Maps API
2. Zone capacity configs from the repo's YAML files

The grid-state API provides per-zone:
  - ci: carbon intensity (gCO2eq/kWh)
  - fr: fossil ratio (0-1)
  - rr: renewable ratio (0-1)
  - tl: total load (MW)
  - pr: price
  - prc: price currency
  - em: estimation method

We combine this with zone capacity configs to compute a realistic
production breakdown per mode.
"""

import json
import os
import sys

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZONES_DIR = os.path.join(REPO_ROOT, "config", "zones")
WEB_PUBLIC = os.path.join(REPO_ROOT, "web", "public")

# Mode classification
RENEWABLE_MODES = {"solar", "wind", "hydro", "biomass", "geothermal"}
FOSSIL_MODES = {"coal", "gas", "oil"}
LOW_CARBON_MODES = {"nuclear", "hydro storage", "hydro discharge", "battery discharge"}

# Map capacity mode names to our frontend mode names
MODE_MAP = {
    "battery storage": "battery storage",
    "biomass": "biomass",
    "coal": "coal",
    "gas": "gas",
    "geothermal": "geothermal",
    "hydro": "hydro",
    "hydro storage": "hydro storage",
    "hydro discharge": "hydro discharge",
    "nuclear": "nuclear",
    "oil": "oil",
    "solar": "solar",
    "wind": "wind",
    "unknown": "unknown",
}


def get_latest_capacity(zone_config):
    """Extract the latest capacity value for each mode from zone config."""
    cap = zone_config.get("capacity", {})
    latest_cap = {}
    for mode, entries in cap.items():
        if isinstance(entries, list) and entries:
            latest_cap[mode] = entries[-1].get("value", 0)
        elif isinstance(entries, int | float):
            latest_cap[mode] = entries
    return latest_cap


def distribute_production(total_mw, fossil_ratio, renewable_ratio, capacity):
    """
    Distribute total production (MW) across modes based on capacity weights
    and the known fossil/renewable ratios from the API.
    """
    if total_mw <= 0 or not capacity:
        return {}

    renewable_cap = {}
    fossil_cap = {}
    lowcarbon_cap = {}

    for mode, cap_mw in capacity.items():
        if cap_mw <= 0:
            continue
        mapped_mode = MODE_MAP.get(mode, mode)
        if mode in RENEWABLE_MODES:
            renewable_cap[mapped_mode] = cap_mw
        elif mode in FOSSIL_MODES:
            fossil_cap[mapped_mode] = cap_mw
        elif mode in LOW_CARBON_MODES or mode == "nuclear":
            lowcarbon_cap[mapped_mode] = cap_mw

    fossil_mw = total_mw * fossil_ratio
    renewable_mw = total_mw * renewable_ratio
    lowcarbon_mw = total_mw - fossil_mw - renewable_mw
    if lowcarbon_mw < 0:
        lowcarbon_mw = 0

    production = {}

    total_fossil_cap = sum(fossil_cap.values())
    if total_fossil_cap > 0 and fossil_mw > 0:
        for mode, cap_mw in fossil_cap.items():
            production[mode] = round(fossil_mw * cap_mw / total_fossil_cap, 1)

    total_renewable_cap = sum(renewable_cap.values())
    if total_renewable_cap > 0 and renewable_mw > 0:
        for mode, cap_mw in renewable_cap.items():
            production[mode] = round(renewable_mw * cap_mw / total_renewable_cap, 1)

    total_lowcarbon_cap = sum(lowcarbon_cap.values())
    if total_lowcarbon_cap > 0 and lowcarbon_mw > 0:
        for mode, cap_mw in lowcarbon_cap.items():
            production[mode] = round(lowcarbon_mw * cap_mw / total_lowcarbon_cap, 1)

    return {k: v for k, v in production.items() if v > 0}


def main():
    default_data = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "grid_state_2026-05-03.json",
    )
    timeseries_path = sys.argv[1] if len(sys.argv) > 1 else default_data

    print(f"Loading real API data from {timeseries_path}...")
    with open(timeseries_path) as f:
        all_datetimes = json.load(f)

    sorted_dts = sorted(all_datetimes.keys())
    latest_dt = sorted_dts[-1]
    latest_data = all_datetimes[latest_dt]
    zones_data = latest_data.get("z", {})
    print(f"  {len(sorted_dts)} timepoints, latest: {latest_dt}")
    print(f"  {len(zones_data)} zones in latest timepoint")

    zones_json_path = os.path.join(WEB_PUBLIC, "zones.json")
    with open(zones_json_path) as f:
        zones_info = json.load(f)
    print(f"  {len(zones_info)} zones in zones.json")

    print("Loading zone capacity configs...")
    zone_capacities = {}
    for fname in os.listdir(ZONES_DIR):
        if not fname.endswith(".yaml"):
            continue
        zone_key = fname.replace(".yaml", "")
        with open(os.path.join(ZONES_DIR, fname)) as f:
            config = yaml.safe_load(f)
        cap = get_latest_capacity(config)
        if cap:
            zone_capacities[zone_key] = cap

    print(f"  {len(zone_capacities)} zones with capacity data")

    print("Generating real data...")
    mock_data = {}

    for zone_key, _zone_info in zones_info.items():
        api_data = zones_data.get(zone_key, {})
        capacity = zone_capacities.get(zone_key, {})

        prod = api_data.get("p", {})
        cons = api_data.get("c", {})

        carbon_intensity = (
            prod.get("ci")
            if prod.get("ci") is not None
            else (cons.get("ci") if cons.get("ci") is not None else 0)
        )
        fossil_ratio = (
            prod.get("fr")
            if prod.get("fr") is not None
            else (cons.get("fr") if cons.get("fr") is not None else 0.5)
        )
        renewable_ratio = (
            prod.get("rr")
            if prod.get("rr") is not None
            else (cons.get("rr") if cons.get("rr") is not None else 0.3)
        )
        total_load = api_data.get("tl") or 0
        estimation_method = api_data.get("em", "")

        carbon_free = (1 - fossil_ratio) * 100
        renewable_pct = renewable_ratio * 100

        production = distribute_production(
            total_load, fossil_ratio, renewable_ratio, capacity
        )

        if not production and total_load > 0:
            if fossil_ratio > 0:
                production["unknown fossil"] = round(total_load * fossil_ratio, 1)
            if renewable_ratio > 0:
                production["unknown renewable"] = round(total_load * renewable_ratio, 1)
            remaining = (
                total_load - total_load * fossil_ratio - total_load * renewable_ratio
            )
            if remaining > 0:
                production["nuclear"] = round(remaining, 1)

        total_prod = sum(production.values())
        if total_prod == 0:
            total_prod = max(total_load, 1)

        mock_data[zone_key] = {
            "carbonIntensity": carbon_intensity,
            "carbonFree": round(carbon_free, 1),
            "renewable": round(renewable_pct, 1),
            "totalProduction": round(total_prod, 1),
            "production": production,
            "isEstimated": "ESTIMATED" in estimation_method
            if estimation_method
            else True,
        }

    print("Generating time series from real data...")
    timeseries_output = {}
    for zone_key in zones_info:
        series = []
        for dt in sorted_dts:
            dt_data = all_datetimes[dt]
            z = dt_data.get("z", {}).get(zone_key, {})
            p = z.get("p", {})
            c = z.get("c", {})
            ci = p.get("ci", c.get("ci", None))
            if ci is not None:
                series.append({"datetime": dt, "carbonIntensity": ci})
        if series:
            timeseries_output[zone_key] = series

    output = {
        "timestamp": latest_dt,
        "zones": mock_data,
        "timeseries": timeseries_output,
    }

    output_path = os.path.join(WEB_PUBLIC, "mock-data.json")
    with open(output_path, "w") as f:
        json.dump(output, f, separators=(",", ":"))
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"\nSaved to {output_path} ({size_mb:.1f} MB)")

    zones_with_real_data = sum(1 for zk in mock_data if zones_data.get(zk))
    zones_with_capacity = sum(1 for zk in mock_data if zone_capacities.get(zk))
    zones_with_timeseries = sum(
        1 for zk in timeseries_output if len(timeseries_output[zk]) > 1
    )
    print(f"  Zones with real API data: {zones_with_real_data}/{len(mock_data)}")
    print(f"  Zones with capacity breakdown: {zones_with_capacity}/{len(mock_data)}")
    print(f"  Zones with time series: {zones_with_timeseries}/{len(mock_data)}")

    for zk in ["FR", "DE", "US-CAL-CISO", "GB"]:
        if zk in mock_data:
            print(f"\n  {zk}:")
            d = mock_data[zk]
            print(
                f"    CI={d['carbonIntensity']} gCO2/kWh, "
                f"CF={d['carbonFree']}%, RW={d['renewable']}%"
            )
            print(f"    Total={d['totalProduction']} MW, Modes: {len(d['production'])}")
            top = sorted(d["production"].items(), key=lambda x: -x[1])[:5]
            for mode, val in top:
                print(f"      {mode}: {val} MW")


if __name__ == "__main__":
    main()

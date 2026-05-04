#!/usr/bin/env python3
"""
Generate static data files for the web frontend from repo config.

Reads the YAML zone and exchange configs from the repo and produces:
  - web/public/zones.json      — 379 zones with metadata
  - web/public/exchanges.json  — 381 exchanges with coordinates
  - web/public/world.geojson   — copied from geo/world.geojson (362 polygons)

Usage:
    python generate_web_data.py

Run from anywhere; paths are resolved relative to the repo root.
"""

import json
import os
import shutil

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZONES_DIR = os.path.join(REPO_ROOT, "config", "zones")
EXCHANGES_DIR = os.path.join(REPO_ROOT, "config", "exchanges")
GEO_FILE = os.path.join(REPO_ROOT, "geo", "world.geojson")
OUT_DIR = os.path.join(REPO_ROOT, "web", "public")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # --- zones.json ---
    zones = {}
    for fname in sorted(os.listdir(ZONES_DIR)):
        if not fname.endswith(".yaml"):
            continue
        zone_key = fname.replace(".yaml", "")
        with open(os.path.join(ZONES_DIR, fname)) as f:
            cfg = yaml.safe_load(f)
        timezone = cfg.get("timezone", "UTC")
        # Bug in source data: BA.yaml lists Asia/Bahrain instead of Europe/Sarajevo.
        if zone_key == "BA" and timezone == "Asia/Bahrain":
            timezone = "Europe/Sarajevo"
        zones[zone_key] = {
            "zoneName": cfg.get("zone_name", cfg.get("zoneName", zone_key)),
            "countryKey": cfg.get(
                "country", cfg.get("country_code", cfg.get("countryKey"))
            ),
            "countryName": cfg.get("country_name", cfg.get("countryName", zone_key)),
            "region": cfg.get("region", "Unknown"),
            "timezone": timezone,
        }
    with open(os.path.join(OUT_DIR, "zones.json"), "w") as f:
        json.dump(zones, f, indent=2, ensure_ascii=False)
    print(f"Generated zones.json: {len(zones)} zones")

    # --- exchanges.json ---
    exchanges = {}
    for fname in sorted(os.listdir(EXCHANGES_DIR)):
        if not fname.endswith(".yaml"):
            continue
        key = fname.replace(".yaml", "").replace("_", "->")
        with open(os.path.join(EXCHANGES_DIR, fname)) as f:
            cfg = yaml.safe_load(f)
        lonlat = cfg.get("lonlat", [0, 0])
        rotation = cfg.get("rotation", 0)
        zones_pair = key.split("->")
        exchanges[key] = {
            "zones": zones_pair,
            "lonlat": lonlat,
            "rotation": rotation,
        }
    with open(os.path.join(OUT_DIR, "exchanges.json"), "w") as f:
        json.dump(exchanges, f, indent=2, ensure_ascii=False)
    print(f"Generated exchanges.json: {len(exchanges)} exchanges")

    # --- world.geojson ---
    if os.path.exists(GEO_FILE):
        shutil.copy2(GEO_FILE, os.path.join(OUT_DIR, "world.geojson"))
        print("Copied world.geojson")
    else:
        print(f"WARNING: {GEO_FILE} not found!")


if __name__ == "__main__":
    main()

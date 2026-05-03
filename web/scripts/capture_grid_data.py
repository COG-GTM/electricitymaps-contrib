#!/usr/bin/env python3
"""
Capture real-time grid state data from the Electricity Maps website
using Playwright CDP (Chrome DevTools Protocol) to intercept API responses.

This script:
1. Connects to an existing Chrome browser via CDP
2. Navigates to the Electricity Maps live map page
3. Intercepts /api/grid-state-page responses as they load
4. Collects data across multiple pages (the API is paginated)
5. Saves all captured data to a JSON file

The output JSON is keyed by datetime strings (ISO 8601), each containing
the full grid state for that timestamp. This file is then consumed by
generate_real_data.py to produce the frontend's mock-data.json.

Prerequisites:
- Chrome running with remote debugging on port 29229
- Playwright installed: pip install playwright
- Network access to app.electricitymaps.com

Usage:
    python capture_grid_data.py [output_path]

    output_path: Where to save the captured data (default: /tmp/real_timeseries.json)
"""

import asyncio
import json
import sys

from playwright.async_api import async_playwright


async def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/real_timeseries.json"
    all_data: dict = {}
    pages_captured = 0

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:29229")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        async def handle_response(response):
            nonlocal pages_captured
            url = response.url
            if "/api/grid-state-page" not in url:
                return
            try:
                body = await response.json()
                data = body.get("data", {})
                datetimes = data.get("datetimes", {})
                for dt_str, dt_data in datetimes.items():
                    if dt_str not in all_data:
                        all_data[dt_str] = dt_data
                pages_captured += 1
                zone_count = len(dt_data.get("z", {})) if datetimes else 0
                print(
                    f"  Page {pages_captured}: "
                    f"{len(datetimes)} timepoints, "
                    f"~{zone_count} zones/timepoint, "
                    f"total unique timepoints: {len(all_data)}"
                )
            except Exception as e:
                print(f"  Error parsing response: {e}")

        page.on("response", handle_response)

        print("Navigating to Electricity Maps live page...")
        await page.goto(
            "https://app.electricitymaps.com/map/live/fifteen_minutes",
            wait_until="networkidle",
            timeout=60000,
        )

        # Wait for paginated API responses to arrive
        print("Waiting for grid-state pages to load...")
        await asyncio.sleep(15)

        # Scroll/interact to trigger any lazy-loaded pages
        for _i in range(3):
            await page.evaluate("window.scrollBy(0, 100)")
            await asyncio.sleep(3)

        print("\nCapture complete!")
        print(f"  Total pages captured: {pages_captured}")
        print(f"  Total unique timepoints: {len(all_data)}")

        if all_data:
            sorted_dts = sorted(all_data.keys())
            print(f"  Time range: {sorted_dts[0]} to {sorted_dts[-1]}")
            sample_dt = sorted_dts[-1]
            sample_zones = all_data[sample_dt].get("z", {})
            print(f"  Zones in latest timepoint: {len(sample_zones)}")

    print(f"\nSaving to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(all_data, f)
    print(f"Done! File size: {len(json.dumps(all_data)) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    asyncio.run(main())

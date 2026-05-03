"""Unit tests for `electricitymap/contrib/parsers/SG.py`.

The Singapore parser combines:
  1. A JSON ticker (`emcsg.com`) that drives the production / price breakdown.
  2. An OCR pass over a solar PNG (`ema.gov.sg`) that adds a `solar` mode.

These tests mock the JSON ticker via `requests-mock` and patch out the
solar fetcher (`get_solar`) with a deterministic value so the tests stay
fast and never touch tesseract. A separate test exercises the OCR helper
in isolation against a synthetic PIL image plus a patched
`pytesseract.image_to_string` to confirm the regex extraction still works.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from electricitymap.contrib.parsers import SG

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "parsers"

TICKER_URL = "https://www.emcsg.com/ChartServer/blue/ticker"


def _png_bytes(size: tuple[int, int] = (200, 200), color: str = "black") -> bytes:
    """Generate an in-memory PNG so the parser's `Image.open(...)` doesn't
    need a fixture file on disk."""
    buf = io.BytesIO()
    Image.new("RGB", size, color=color).save(buf, format="PNG")
    return buf.getvalue()


def test_fetch_production_success(adapter, session):
    """Happy path: well-formed ticker JSON + patched solar → ProductionBreakdownList."""
    payload = (FIXTURES / "sg_ticker.json").read_text(encoding="utf-8")
    adapter.register_uri("GET", TICKER_URL, text=payload)

    # Patch get_solar to a deterministic value so the test does not depend on
    # OCR / tesseract / wall-clock-vs-image-timestamp drift.
    with patch.object(SG, "get_solar", return_value=42.0):
        result = SG.fetch_production(session=session)

    assert isinstance(result, list)
    assert len(result) == 1

    event = result[0]
    assert event["zoneKey"] == "SG"
    assert event["source"] == "emcsg.com, ema.gov.sg"

    # 03 May 2026, period 27 → sg_period_to_hour returns 13.0 (1-indexed,
    # half-hour periods, with the marketing convention SG.py implements) →
    # 13:00 SGT == 05:00 UTC.
    expected_dt = datetime(2026, 5, 3, 13, 0, 0, tzinfo=SG.TIMEZONE).astimezone(
        timezone.utc
    )
    assert event["datetime"].astimezone(timezone.utc) == expected_dt

    # generation = demand 5000 + system_loss 100 = 5100
    # CCGT/COGEN/TRIGEN 90% → gas, GT 5% → gas, ST 4% → unknown,
    # ANOTHER 1% → unknown (logged warning).
    production = event["production"]
    assert production["gas"] == pytest.approx(5100.0 * (0.90 + 0.05))
    assert production["unknown"] == pytest.approx(5100.0 * (0.04 + 0.01))
    assert production["solar"] == pytest.approx(42.0)


def test_fetch_production_raises_when_ticker_missing_sections(adapter, session):
    """If the JSON ticker is missing the `Sections` key, the parser must fail.

    SG.fetch_production does not wrap upstream errors in `ParserException`,
    so we just assert that *some* exception is raised — `KeyError` / `IndexError`
    are both acceptable signals that the upstream contract is broken.
    """
    broken = json.dumps({"NotSections": []})
    adapter.register_uri("GET", TICKER_URL, text=broken)

    with (
        patch.object(SG, "get_solar", return_value=None),
        pytest.raises((KeyError, IndexError)),
    ):
        SG.fetch_production(session=session)


def test_fetch_production_raises_when_target_datetime_set(adapter, session):
    """SG explicitly does not support historical lookups — that should NOT
    silently succeed."""
    with pytest.raises(NotImplementedError):
        SG.fetch_production(
            session=session, target_datetime=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )


def test_detect_output_from_solar_image_extracts_mw():
    """OCR helper smoke test: with a patched `image_to_string` returning the
    expected layout, the regex extracts the MW value as a float."""
    detect_output = getattr(SG, "__detect_output_from_solar_image")
    img = Image.new("RGB", (200, 200), "black")

    with patch.object(
        SG, "image_to_string", return_value="Est. PV Output: 12.50MWac\n"
    ):
        mw = detect_output(img, SG.getLogger("test"))

    assert mw == pytest.approx(12.5)


def test_detect_output_from_solar_image_returns_none_on_unparseable_text():
    detect_output = getattr(SG, "__detect_output_from_solar_image")
    img = Image.new("RGB", (200, 200), "black")

    with patch.object(SG, "image_to_string", return_value="garbage no MW here"):
        mw = detect_output(img, SG.getLogger("test"))

    assert mw is None

"""Unit tests for `electricitymap/contrib/parsers/ERP_PGCB.py`.

ERP_PGCB scrapes an HTML table from the Bangladesh Power Grid Company portal.
These tests mount canned HTML responses via `requests-mock` and exercise both
the happy path (well-formed table) and an obvious failure mode (no `<table>`
in the response) which should raise `ParserException`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from electricitymap.contrib.parsers import ERP_PGCB
from electricitymap.contrib.parsers.lib.exceptions import ParserException

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "parsers"
DHAKA = ZoneInfo("Asia/Dhaka")

LATEST_URL = "https://erp.pgcb.gov.bd/web/generations/view_generations"


def test_fetch_production_success(adapter, session):
    """Happy path: 2-row HTML table → 2 ProductionBreakdown events with
    correct production breakdown and `unknown` inferred from the residual."""
    html = (FIXTURES / "erp_pgcb.html").read_text(encoding="utf-8")
    adapter.register_uri("GET", LATEST_URL, text=html)

    result = ERP_PGCB.fetch_production(session=session)

    assert isinstance(result, list)
    assert len(result) == 2

    first = result[0]
    assert first["zoneKey"] == "BD"
    assert first["source"] == "erp.pgcb.gov.bd"
    # ERP_PGCB stores the table time as backwards-looking — `13:00:00` in the
    # table represents the bucket starting at 12:00 local Dhaka time.
    expected_dt = datetime(2026, 5, 3, 12, 0, 0, tzinfo=DHAKA)
    assert first["datetime"] == expected_dt

    production = first["production"]
    assert production["coal"] == pytest.approx(1500.0)
    assert production["gas"] == pytest.approx(5000.0)
    assert production["hydro"] == pytest.approx(200.0)
    assert production["oil"] == pytest.approx(1000.0)
    assert production["solar"] == pytest.approx(800.0)
    assert production["wind"] == pytest.approx(50.0)
    # unknown = 11000 - sum(known) - bheramara - tripura - adani
    #        = 11000 - 8550 - 900 - 100 - 450 = 1000
    assert production["unknown"] == pytest.approx(1000.0)


def test_fetch_production_raises_when_table_missing(adapter, session):
    """When the response HTML has no `<table>`, the parser must raise."""
    html = (FIXTURES / "erp_pgcb_no_table.html").read_text(encoding="utf-8")
    adapter.register_uri("GET", LATEST_URL, text=html)

    with pytest.raises(ParserException) as excinfo:
        ERP_PGCB.fetch_production(session=session)
    assert "Could not find table" in str(excinfo.value)


def test_fetch_production_raises_on_http_error(adapter, session):
    """A non-200 response from ERP must surface as a ParserException."""
    adapter.register_uri("GET", LATEST_URL, status_code=503, text="<html/>")

    with pytest.raises(ParserException) as excinfo:
        ERP_PGCB.fetch_production(session=session)
    assert "503" in str(excinfo.value)


def test_datetime_is_timezone_aware(adapter, session):
    """Sanity check: datetimes returned must be timezone-aware (UTC offset)."""
    html = (FIXTURES / "erp_pgcb.html").read_text(encoding="utf-8")
    adapter.register_uri("GET", LATEST_URL, text=html)

    result = ERP_PGCB.fetch_production(session=session)
    for event in result:
        ts: datetime = event["datetime"]
        assert ts.tzinfo is not None
        assert ts.tzinfo.utcoffset(ts) is not None
        # Sanity: same instant in UTC matches Dhaka offset (+06:00).
        assert ts.astimezone(timezone.utc).utcoffset() == timezone.utc.utcoffset(ts)

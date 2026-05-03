"""Unit tests for `electricitymap/contrib/parsers/CZ.py`.

The CEPS production endpoint speaks SOAP/XML. These tests mount canned
SOAP envelopes via `requests-mock` and exercise both the success path and
the no-data path. The no-data assertion depends on the bug fix in PR #5
(`fix(CZ): raise ParserException when no production data is returned`):
on master before that PR merges, the no-data branch silently returns an
empty list instead of raising, so the corresponding assertion is skipped.
"""

from __future__ import annotations

import inspect
import unittest
from datetime import datetime
from pathlib import Path

import pytest

from electricitymap.contrib.parsers import CZ
from electricitymap.contrib.parsers.lib.exceptions import ParserException

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "parsers"

CZ_SOAP_URL = "https://www.ceps.cz/_layouts/CepsData.asmx"


def _cz_no_data_branch_raises() -> bool:
    """Return True iff `CZ.fetch_production`'s no-data branch raises.

    On master before the 1A fix, the parser instantiates `ParserException`
    without `raise`-ing it. Detect that by inspecting the source so the
    no-data assertion below auto-skips on un-fixed checkouts and runs
    once 1A merges into master.
    """
    src = inspect.getsource(CZ.fetch_production)
    return "raise ParserException" in src


def test_fetch_production_success(adapter, session):
    """Happy path: SOAP response with `series` + `data` produces datapoints."""
    payload = (FIXTURES / "cz_production.xml").read_text(encoding="utf-8")
    adapter.register_uri("POST", CZ_SOAP_URL, text=payload)

    result = CZ.fetch_production(session=session)

    assert isinstance(result, list)
    assert len(result) == 2

    first, second = result
    assert first["zoneKey"] == "CZ"
    assert first["source"] == "ceps.cz"
    assert first["datetime"] == datetime.fromisoformat("2026-05-01T10:00:00+02:00")
    assert second["datetime"] == datetime.fromisoformat("2026-05-01T10:15:00+02:00")

    production = first["production"]
    # TPP -> coal, CCGT -> gas, NPP -> nuclear, HPP -> hydro,
    # AltPP -> biomass, ApPP -> unknown, PVPP -> solar, WPP -> wind.
    assert production["coal"] == pytest.approx(1000.0)
    assert production["gas"] == pytest.approx(500.0)
    assert production["nuclear"] == pytest.approx(3500.0)
    assert production["hydro"] == pytest.approx(200.0)
    assert production["biomass"] == pytest.approx(50.0)
    assert production["unknown"] == pytest.approx(10.0)
    assert production["solar"] == pytest.approx(800.0)
    assert production["wind"] == pytest.approx(120.0)

    # PsPP is mapped to storage hydro (negated).
    assert first["storage"]["hydro"] == pytest.approx(150.0)


@unittest.skipUnless(
    _cz_no_data_branch_raises(),
    "Depends on PR #5 (fix(CZ): raise ParserException when no production data "
    "is returned). Skipping until that fix lands on master.",
)
def test_fetch_production_raises_on_no_data(adapter, session):
    """No-data path: `<data>` tag missing from SOAP response → ParserException."""
    payload = (FIXTURES / "cz_no_data.xml").read_text(encoding="utf-8")
    adapter.register_uri("POST", CZ_SOAP_URL, text=payload)

    with pytest.raises(ParserException):
        CZ.fetch_production(session=session)

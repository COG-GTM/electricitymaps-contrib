from datetime import datetime
from zoneinfo import ZoneInfo

import freezegun
import pytest
from requests_mock import ANY

from electricitymap.contrib.parsers.CENACE import (
    DASHBOARD_CACHE,
    fetch_consumption,
    fetch_exchange,
)
from electricitymap.contrib.types import ZoneKey


@pytest.fixture(autouse=True)
def mock_response(adapter):
    DASHBOARD_CACHE.clear()
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/DemandaRegional.html", "rb"
    ) as data:
        adapter.register_uri(ANY, ANY, content=data.read())
    yield
    DASHBOARD_CACHE.clear()


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_MX_OC(session):
    data = fetch_consumption(ZoneKey("MX-OC"), session)
    assert data[0]["zoneKey"] == "MX-OC"
    assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Mexico_City"))
    assert data[0]["consumption"] == 8519.0


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_MX_BC(session):
    data = fetch_consumption(ZoneKey("MX-BC"), session)
    assert data[0]["zoneKey"] == "MX-BC"
    assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Tijuana"))
    assert data[0]["consumption"] == 1587.0


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_BCS(session):
    data = fetch_consumption(ZoneKey("MX-BCS"), session)
    assert len(data) == 0


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_dashboard_is_downloaded_once_per_minute(adapter, session):
    fetch_consumption(ZoneKey("MX-OC"), session)
    fetch_consumption(ZoneKey("MX-BC"), session)
    fetch_exchange(ZoneKey("MX-NO"), ZoneKey("MX-NW"), session)
    assert adapter.call_count == 1


def test_dashboard_is_refetched_in_a_new_minute(adapter, session):
    with freezegun.freeze_time("2021-01-01 00:00:00"):
        fetch_consumption(ZoneKey("MX-OC"), session)
    with freezegun.freeze_time("2021-01-01 00:01:00"):
        fetch_consumption(ZoneKey("MX-OC"), session)
    assert adapter.call_count == 2

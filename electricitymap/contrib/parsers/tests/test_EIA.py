import json
import os
from datetime import datetime, timezone
from importlib import resources
from typing import Any

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers import EIA
from electricitymap.contrib.types import ZoneKey


@pytest.fixture(autouse=True)
def eia_key_env():
    os.environ["EIA_KEY"] = "token"


def _load_mock(filename: str) -> dict[str, Any]:
    return json.loads(
        resources.files("electricitymap.contrib.parsers.tests.mocks.EIA")
        .joinpath(filename)
        .read_text()
    )


def production_mix_response(
    default_mock: str, mocks_by_fuel_code: dict[str, str] | None = None
) -> dict[str, Any]:
    """
    Build the response of a single fuel-type-data request, which covers every
    fuel type the parser asks for. The datapoints of `default_mock` are used
    for the fuel types absent from `mocks_by_fuel_code`.
    """
    mocks_by_fuel_code = mocks_by_fuel_code or {}
    response = _load_mock(default_mock)
    data = []
    for fuel_code in EIA.TYPES.values():
        mock = mocks_by_fuel_code.get(fuel_code, default_mock)
        for datapoint in _load_mock(mock)["response"]["data"]:
            data.append({**datapoint, "fueltype": fuel_code})
    response["response"]["data"] = data
    return response


def test_parse_hourly_interval():
    """
    We add a 'frequency=hourly' parameter to our EIA API requests; this
    requests results grouped by hourly intervals in UTC time.

    Each time window in the response indicates the _end_ of that hourly
    interval; ElectricityMaps stores intervals using start hour instead.
    """
    fixtures = [
        ("2022-02-28T23", datetime(2022, 2, 28, 22, 0, 0, tzinfo=timezone.utc)),
        ("2022-03-01T00", datetime(2022, 2, 28, 23, 0, 0, tzinfo=timezone.utc)),
        ("2022-03-01T01", datetime(2022, 3, 1, 0, 0, 0, tzinfo=timezone.utc)),
    ]

    for period, expected in fixtures:
        result = EIA._parse_hourly_interval(period)
        assert result == expected


def test_fetch_production_mix(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=production_mix_response("US_NW_AVRN-wind.json"),
    )
    data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PGE"), session)

    assert data_list == snapshot


def test_production_mix_is_fetched_in_a_single_request(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=production_mix_response("US_NW_AVRN-wind.json"),
    )
    EIA.fetch_production_mix(ZoneKey("US-NW-PGE"), session)

    assert len(adapter.request_history) == 1
    requested_fuel_types = adapter.request_history[0].qs["facets[fueltype][]"]
    assert sorted(requested_fuel_types) == sorted(
        code.lower() for code in EIA.TYPES.values()
    )


def test_US_NW_AVRN_rerouting(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=production_mix_response("US_NW_AVRN-other.json"),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("AVRN"),
        json=production_mix_response(
            "US_NW_AVRN-other.json",
            {"WND": "US_NW_AVRN-wind.json", "NG": "US_NW_AVRN-gas.json"},
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("PACW"),
        json=production_mix_response(
            "US_NW_AVRN-other.json",
            {
                "NG": "US_NW_PACW-gas.json",
                "WAT": "US_SMTH-coal.json",
                "SUN": "US_SMTH-coal.json",
                "WND": "US_SMTH-coal.json",
            },
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("BPAT"),
        json=production_mix_response(
            "US_NW_AVRN-other.json",
            {
                "WND": "US_NW_BPAT-wind.json",
                "NG": "US_SMTH-coal.json",
                "WAT": "US_SMTH-coal.json",
                "NUC": "US_SMTH-coal.json",
                "SUN": "US_SMTH-coal.json",
            },
        ),
    )

    data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PACW"), session)
    assert data_list == snapshot
    data_list = EIA.fetch_production_mix(ZoneKey("US-NW-BPAT"), session)
    assert data_list == snapshot


def test_US_CAR_SC_nuclear_split(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=production_mix_response("US_NW_AVRN-other.json"),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SC"),
        json=production_mix_response(
            "US_NW_AVRN-other.json",
            {
                "COL": "US_SMTH-coal.json",
                "NG": "US_SMTH-coal.json",
                "WAT": "US_SMTH-coal.json",
                "OIL": "US_SMTH-coal.json",
                "SUN": "US_SMTH-coal.json",
                "NUC": "US_CAR_SC-nuclear.json",
            },
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SCEG"),
        json=production_mix_response(
            "US_NW_AVRN-other.json",
            {
                "NUC": "US_CAR_SCEG-nuclear.json",
                "COL": "US_SMTH-coal.json",
                "NG": "US_SMTH-coal.json",
                "WAT": "US_SMTH-coal.json",
                "OIL": "US_SMTH-coal.json",
                "SUN": "US_SMTH-coal.json",
            },
        ),
    )

    data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SC"), session)
    assert data_list == snapshot
    data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SCEG"), session)
    assert data_list == snapshot


def test_check_transfer_mixes():
    for production in EIA.PRODUCTION_ZONES_TRANSFERS.values():
        all_production = production.get("all", {})
        for production_type, supplying_zones in production.items():
            if production_type == "all":
                continue
            for zone in supplying_zones:
                if zone in all_production:
                    raise Exception(
                        f"{zone} is both in the all production export\
                        and exporting its {production_type} production. \
                        This is not possible please fix this ambiguity."
                    )


def test_hydro_transfer_mix(adapter, session, snapshot):
    """
    Make sure that with zones that integrate production only zones
    the hydro production events are properly handled and the storage
    is accounted for on a zone by zone basis.
    """
    adapter.register_uri(
        GET,
        ANY,
        json=production_mix_response("US_NW_AVRN-other.json"),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SRP"),
        json=production_mix_response(
            "US_NW_AVRN-other.json",
            {
                "COL": "US_SMTH-coal.json",
                "NG": "US_SMTH-coal.json",
                "NUC": "US_SMTH-coal.json",
                "SUN": "US_SMTH-coal.json",
                "WND": "US_SMTH-coal.json",
                "WAT": "US_SW_SRP-hydro.json",
            },
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("DEAA"),
        json=production_mix_response(
            "US_NW_AVRN-other.json", {"WAT": "US_SW_DEAA-hydro.json"}
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("HGMA"),
        json=production_mix_response(
            "US_NW_AVRN-other.json", {"WAT": "US_SW_HGMA-hydro.json"}
        ),
    )

    data = EIA.fetch_production_mix(ZoneKey("US-SW-SRP"), session)
    assert data == snapshot


def test_exchange_transfer(adapter, session):
    exchange_key = "US-FLA-FPC->US-FLA-FPL"
    remapped_exchange_key = "US-FLA-FPC->US-FLA-NSB"
    # target_datetime = (
    #     "2020-01-07T05:00:00+00:00"  # Last datapoint before decommissioning of NSB
    # )
    # 1. Get data directly from EIA for both
    fpl_exchange_data = _load_mock("US-FLA-FPC_US-FLA-FPL_exchange.json")
    adapter.register_uri(
        GET,
        # For example:
        # https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=FPL&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24
        EIA.EXCHANGE.format(EIA.EXCHANGES[exchange_key]),
        json=fpl_exchange_data,
    )
    nsb_exchange_data = _load_mock("US-FLA-FPC_US-FLA-NSB_exchange.json")
    adapter.register_uri(
        GET,
        # For example:
        # https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=NSB&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24
        EIA.EXCHANGE.format(EIA.EXCHANGES[remapped_exchange_key]),
        json=nsb_exchange_data,
    )

    # 2. Get data from the EIA parser fetch_exchange for
    # US-FLA-FPC->US-FLA-FPL
    z_k_1, z_k_2 = exchange_key.split("->")
    data_list = EIA.fetch_exchange(ZoneKey(z_k_1), ZoneKey(z_k_2), session)

    # Verify that the sum of the data directly fetched matches the data
    # from the parser.
    for fpl, nsb, parser in zip(
        fpl_exchange_data["response"]["data"],
        nsb_exchange_data["response"]["data"],
        data_list,
        strict=True,
    ):
        assert fpl["value"] + nsb["value"] == parser["netFlow"]


def test_fetch_production_mix_discards_null(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=production_mix_response("US-NW-PGE-with-nulls.json"),
    )

    data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PGE"), session)

    assert data_list == snapshot

    assert (
        datetime(2022, 10, 31, 11, 0, tzinfo=timezone.utc) == data_list[0]["datetime"]
    )


def test_fetch_exchange(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=_load_mock("US-NW-BPAT-US-NW-NWMT-exchange.json"),
    )
    data_list = EIA.fetch_exchange(
        ZoneKey("US-NW-BPAT"), ZoneKey("US-NW-NWMT"), session
    )
    expected = [
        {
            "source": "eia.gov",
            "datetime": datetime(2022, 2, 28, 22, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
            "netFlow": -12,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2022, 2, 28, 23, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
            "netFlow": -11,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2022, 3, 1, 0, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
            "netFlow": -2,
        },
    ]
    assert len(data_list) == len(expected)
    for i, data in enumerate(data_list):
        assert data["source"] == expected[i]["source"]
        assert data["datetime"] == expected[i]["datetime"]
        assert data["sortedZoneKeys"] == expected[i]["sortedZoneKeys"]
        assert data["netFlow"] == expected[i]["netFlow"]


def test_fetch_consumption(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=_load_mock("US_NW_BPAT-consumption.json"),
    )
    data_list = EIA.fetch_consumption(ZoneKey("US-NW-BPAT"), session)
    expected = [
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=timezone.utc),
            "consumption": 4792,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=timezone.utc),
            "consumption": 6215,
        },
    ]
    assert len(data_list) == len(expected)
    for i, data in enumerate(data_list):
        assert data["source"] == expected[i]["source"]
        assert data["datetime"] == expected[i]["datetime"]
        assert data["consumption"] == expected[i]["consumption"]


def test_fetch_forecasted_consumption(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=_load_mock("US_NW_BPAT-consumption.json"),
    )
    data_list = EIA.fetch_consumption_forecast(ZoneKey("US-NW-BPAT"), session)
    expected = [
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=timezone.utc),
            "consumption": 4792,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=timezone.utc),
            "consumption": 6215,
        },
    ]
    assert len(data_list) == len(expected)
    for i, data in enumerate(data_list):
        assert data["source"] == expected[i]["source"]
        assert data["datetime"] == expected[i]["datetime"]
        assert data["consumption"] == expected[i]["consumption"]
        assert data["sourceType"] == EventSourceType.forecasted


def test_fetch_returns_storage(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=production_mix_response("US_CAL_IID-battery_storage.json"),
    )

    data_list = EIA.fetch_production_mix(ZoneKey("US-CAL-IID"), session)

    assert data_list == snapshot

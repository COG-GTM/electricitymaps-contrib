#!/usr/bin/env python3


import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    TotalConsumptionList,
)
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
EXCHANGE_URL = f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise?host=https://www.wrldc.in"
CONSUMPTION_URL = f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData_state_Wise?host=https://www.wrldc.in"
ZONE_INFO = ZoneInfo("Asia/Kolkata")

EXCHANGES_MAPPING = {
    "WR-SR": "IN-SO->IN-WE",
    "WR-ER": "IN-EA->IN-WE",
    "WR-NR": "IN-NO->IN-WE",
}

KIND_MAPPING = {
    "exchange": {
        "url": EXCHANGE_URL,
        "datetime_col": "lastUpdate",
        "region_col": "Region_Name",
    },
    "consumption": {
        "url": CONSUMPTION_URL,
        "datetime_col": "current_datetime",
        "region_col": "StateName",
    },
}


def _get_hour_dts(dt: datetime):
    """
    Returns up to 24 datetime objects for a given datetime's date, one for each
    hour, excluding future hours.
    """
    date_dt = datetime.combine(dt.date(), datetime.min.time()).replace(tzinfo=ZONE_INFO)
    dts = pd.date_range(
        date_dt,
        date_dt + timedelta(hours=23),
        freq="H",
    ).to_pydatetime()

    now_dt = datetime.now(ZONE_INFO)
    return [dt for dt in dts if dt < now_dt]


def _fetch_data(
    kind: str,
    session: Session,
    target_datetime: datetime,
) -> dict:
    """
    Fetches 24 hours of either exchange or production data from wrldc.in.
    """
    url = KIND_MAPPING[kind]["url"]
    datetime_col = KIND_MAPPING[kind]["datetime_col"]

    payload = {"date": target_datetime.strftime("%Y-%m-%d")}
    resp: Response = session.post(url, json=payload)

    try:
        data = json.loads(resp.json().get("d", {}))
    except Exception as e:
        raise ParserException(
            parser="IN_WE.py",
            message=f"{target_datetime}: {kind} data is not available",
        ) from e

    # The source data is a 12 hour format without mentioning if its AM/PM, so
    # 12:15 (AM or PM) could mean 00:15 or 12:15. This is addressed by relying
    # on the full date worth of ordered data, where we assume the second time
    # 12:xx shows up it must have transitioned to PM time.
    am_time = True
    checkpoint = False
    dt_format = "%Y-%d-%m %I:%M:%S %p"
    for item in data:
        dt_string = item[datetime_col] + (" AM" if am_time else " PM")
        dt = datetime.strptime(dt_string, dt_format).replace(tzinfo=ZONE_INFO)
        if am_time:
            if not checkpoint and dt.hour != 0:
                checkpoint = True
            elif checkpoint and dt.hour == 0:
                am_time = False
                dt_string = item[datetime_col] + (" AM" if am_time else " PM")
                dt = datetime.strptime(dt_string, dt_format).replace(tzinfo=ZONE_INFO)
        item[datetime_col] = dt
    return data


def _get_hourly_df(kind: str, data: dict) -> pd.DataFrame:
    """
    Returns a dataframe of the full day of data, with an hour column.
    """
    datetime_col = KIND_MAPPING[kind]["datetime_col"]
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["hour"] = df[datetime_col].map(lambda dt: dt.hour)
    return df


def _get_mean_hourly_net_flows(
    data: dict,
    zone_key1: str,
    zone_key2: str,
) -> dict[int, float]:
    """
    Average all data points of the exchange, per hour of the day.
    """
    region_col = KIND_MAPPING["exchange"]["region_col"]
    exchange_string = "->".join(sorted([zone_key1, zone_key2]))

    df = _get_hourly_df(kind="exchange", data=data)
    if df.empty:
        return {}

    df = df.loc[df[region_col].map(EXCHANGES_MAPPING) == exchange_string]
    means = (
        df.groupby(["hour", region_col])
        .mean(numeric_only=True)
        .reset_index()
        .groupby("hour")
        .first()
    )
    if "Current_Loading" not in means.columns:
        return dict.fromkeys(means.index, 0.0)

    return {hour: -round(value, 3) for hour, value in means["Current_Loading"].items()}


def _get_mean_hourly_consumptions(data: dict) -> dict[int, float]:
    """
    Average all data points per region and sum them up, per hour of the day.
    """
    region_col = KIND_MAPPING["consumption"]["region_col"]

    df = _get_hourly_df(kind="consumption", data=data)
    if df.empty:
        return {}

    totals = df.groupby(["hour", region_col])["Demand"].mean().groupby("hour").sum()
    return {hour: round(value, 3) for hour, value in totals.items()}


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if session is None:
        session = Session()
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    exchange_string = "->".join(sorted([zone_key1, zone_key2]))
    data = _fetch_data(
        kind="exchange",
        session=session,
        target_datetime=target_datetime,
    )
    net_flows = _get_mean_hourly_net_flows(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        data=data,
    )

    exchange_list = ExchangeList(logger)
    for dt in _get_hour_dts(target_datetime):
        if dt.hour not in net_flows:
            logger.warning(f"{dt}: no exchange data for {exchange_string}")
            continue
        net_flow = net_flows[dt.hour]
        exchange_list.append(
            zoneKey=ZoneKey(exchange_string),
            datetime=dt,
            netFlow=net_flow,
            source="wrldc.in",
        )

    return exchange_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("IN-WE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if session is None:
        session = Session()
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    data = _fetch_data(
        kind="consumption",
        session=session,
        target_datetime=target_datetime,
    )

    consumptions = _get_mean_hourly_consumptions(data=data)

    consumption_list = TotalConsumptionList(logger)
    for dt in _get_hour_dts(target_datetime):
        if dt.hour not in consumptions:
            logger.warning(f"{dt}: no consumption data")
            continue
        consumption = consumptions[dt.hour]
        consumption_list.append(
            zoneKey=zone_key,
            datetime=dt,
            consumption=consumption,
            source="wrldc.in",
        )
    return consumption_list.to_list()


if __name__ == "__main__":
    print(fetch_exchange(zone_key1="IN-WE", zone_key2="IN-NO"))
    print(fetch_consumption())

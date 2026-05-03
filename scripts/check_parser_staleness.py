#!/usr/bin/env python3
"""Staleness detection for production / consumption / price parsers.

For each opted-in zone, the script calls the configured parser with
`target_datetime=None` and inspects the most recent datapoint's UTC timestamp.
A zone is `STALE` if the latest datapoint is older than the configured
threshold; `MISSING` if the parser returns nothing or raises; otherwise `OK`.

The script prints a markdown summary table and exits 0 if every zone is OK,
or 1 if any zone is stale or missing — making it suitable as the aggregate
step of the parser smoke-test workflow.

Usage:
    uv run python scripts/check_parser_staleness.py --zones FR,DE,GB
    uv run python scripts/check_parser_staleness.py --all --max-age-hours 12
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# Parser data types that this script knows how to staleness-check. We only
# include data types whose parser signature is the standard
# (zone_key, session, target_datetime, logger) form and whose output is a
# list of per-event dicts (or a single dict) carrying a `datetime` key.
SUPPORTED_DATA_TYPES = ("production", "consumption", "price")
DEFAULT_DATA_TYPE = "production"
DEFAULT_MAX_AGE_HOURS = 6.0


class StalenessStatus(str, Enum):
    OK = "OK"
    STALE = "STALE"
    MISSING = "MISSING"


@dataclass(frozen=True)
class ZoneStaleness:
    zone: str
    latest_datetime_utc: datetime | None
    age_hours: float | None
    status: StalenessStatus
    detail: str = ""


def _to_event_list(parser_output: Any) -> list[dict[str, Any]]:
    """Normalize a parser's return value into a list of per-event dicts."""
    if parser_output is None:
        return []
    if isinstance(parser_output, dict):
        return [parser_output]
    if isinstance(parser_output, list | tuple):
        return [e for e in parser_output if isinstance(e, dict)]
    return []


def _latest_datetime_utc(parser_output: Any) -> datetime | None:
    """Return the most recent UTC datetime in `parser_output`, or `None`."""
    events = _to_event_list(parser_output)
    timestamps: list[datetime] = []
    for event in events:
        ts = event.get("datetime")
        if not isinstance(ts, datetime):
            continue
        if ts.tzinfo is None:
            # Treat naive datetimes as UTC rather than crash; a parser that
            # returns naive timestamps is itself a bug, but the staleness
            # script should still produce a row for it.
            ts = ts.replace(tzinfo=timezone.utc)
        timestamps.append(ts.astimezone(timezone.utc))
    return max(timestamps) if timestamps else None


def evaluate_staleness(
    zone: str,
    parser_output: Any,
    *,
    now_utc: datetime,
    max_age: timedelta,
) -> ZoneStaleness:
    """Decide whether `parser_output` is OK / STALE / MISSING for `zone`."""
    latest = _latest_datetime_utc(parser_output)
    if latest is None:
        return ZoneStaleness(
            zone=zone,
            latest_datetime_utc=None,
            age_hours=None,
            status=StalenessStatus.MISSING,
            detail="parser returned no datapoints",
        )
    age = now_utc - latest
    age_hours = age.total_seconds() / 3600.0
    status = StalenessStatus.OK if age <= max_age else StalenessStatus.STALE
    return ZoneStaleness(
        zone=zone,
        latest_datetime_utc=latest,
        age_hours=age_hours,
        status=status,
    )


def render_markdown_table(rows: Iterable[ZoneStaleness]) -> str:
    """Render staleness rows as a deterministic markdown table."""
    header = "| Zone | Latest datapoint (UTC) | Age (hours) | Status |"
    separator = "| --- | --- | --- | --- |"
    body_lines: list[str] = []
    for row in rows:
        latest_str = (
            row.latest_datetime_utc.isoformat(timespec="seconds")
            if row.latest_datetime_utc is not None
            else "—"
        )
        age_str = f"{row.age_hours:.2f}" if row.age_hours is not None else "—"
        body_lines.append(
            f"| {row.zone} | {latest_str} | {age_str} | {row.status.value} |"
        )
    return "\n".join([header, separator, *body_lines])


def _resolve_parser(zone: str, data_type: str):
    """Look up the configured parser for `zone` / `data_type`.

    Imported lazily so that `--help` and the unit tests don't pay the cost of
    loading every parser module on import.
    """
    from electricitymap.contrib.config import ZONES_CONFIG
    from electricitymap.contrib.parsers.lib.parsers import PARSER_DATA_TYPE_TO_DICT
    from electricitymap.contrib.types import ParserDataType

    if zone not in ZONES_CONFIG:
        raise KeyError(f"unknown zone {zone!r}")
    zone_config = ZONES_CONFIG[zone]
    parsers_for_zone = zone_config.get("parsers", {}) or {}
    if data_type not in parsers_for_zone:
        raise KeyError(f"zone {zone!r} has no {data_type!r} parser configured")
    parser_data_type = ParserDataType(data_type)
    parser_dict = PARSER_DATA_TYPE_TO_DICT[parser_data_type]
    if zone not in parser_dict:
        raise KeyError(f"no {data_type!r} parser registered for {zone!r}")
    return parser_dict[zone]


def _run_parser(zone: str, data_type: str) -> Any:
    parser = _resolve_parser(zone, data_type)
    return parser(zone, target_datetime=None, logger=logger)


def collect_zones_with_parser(data_type: str) -> list[str]:
    """Return every zone that has `data_type` configured, sorted."""
    from electricitymap.contrib.config import ZONES_CONFIG

    return sorted(
        zone
        for zone, cfg in ZONES_CONFIG.items()
        if data_type in (cfg.get("parsers", {}) or {})
    )


def parse_zones_arg(zones_arg: str | None) -> list[str]:
    if not zones_arg:
        return []
    return [z.strip() for z in zones_arg.split(",") if z.strip()]


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--zones",
        type=str,
        help="Comma-separated list of zone keys (e.g. FR,DE,GB).",
    )
    target.add_argument(
        "--all",
        action="store_true",
        help=(
            "Check every zone that has the requested data-type configured. "
            "Use with care — runs many live API calls in sequence."
        ),
    )
    parser.add_argument(
        "--data-type",
        choices=SUPPORTED_DATA_TYPES,
        default=DEFAULT_DATA_TYPE,
        help=f"Parser data type to check (default: {DEFAULT_DATA_TYPE}).",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=DEFAULT_MAX_AGE_HOURS,
        help=(
            "Threshold above which a zone is reported STALE "
            f"(default: {DEFAULT_MAX_AGE_HOURS} hours)."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase log verbosity. Repeat for DEBUG.",
    )
    return parser


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    )


def run_for_zones(
    zones: list[str],
    *,
    data_type: str,
    max_age: timedelta,
    now_utc: datetime,
) -> list[ZoneStaleness]:
    rows: list[ZoneStaleness] = []
    for zone in zones:
        try:
            output = _run_parser(zone, data_type)
        except Exception as exc:  # noqa: BLE001 — surface every parser failure
            logger.warning("parser for %s failed: %s", zone, exc)
            rows.append(
                ZoneStaleness(
                    zone=zone,
                    latest_datetime_utc=None,
                    age_hours=None,
                    status=StalenessStatus.MISSING,
                    detail=str(exc),
                )
            )
            continue
        rows.append(evaluate_staleness(zone, output, now_utc=now_utc, max_age=max_age))
    return rows


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    configure_logging(args.verbose)
    data_type: str = args.data_type
    max_age = timedelta(hours=args.max_age_hours)

    if args.all:
        zones = collect_zones_with_parser(data_type)
    else:
        zones = parse_zones_arg(args.zones)

    if not zones:
        print(
            "No zones to check (got empty --zones / --all returned nothing).",
            file=sys.stderr,
        )
        return 1

    now_utc = datetime.now(timezone.utc)
    rows = run_for_zones(zones, data_type=data_type, max_age=max_age, now_utc=now_utc)
    print(render_markdown_table(rows))
    return 0 if all(r.status is StalenessStatus.OK for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())

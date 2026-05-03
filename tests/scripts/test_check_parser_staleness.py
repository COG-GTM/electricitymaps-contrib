"""Unit tests for `scripts/check_parser_staleness.py`.

The tests exercise the pure staleness logic against synthetic datapoints —
they never call a live parser. The only dependency on the rest of the repo
is on stdlib + the script under test.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


def _load_module():
    """Import `scripts.check_parser_staleness` without depending on a top-level
    `scripts` package being importable. The repo's `scripts/` directory has an
    `__init__.py` but `tests/scripts/` is the namespace this test module lives
    in, so we load by file path instead to avoid name collisions.
    """
    module_name = "scripts_check_parser_staleness"
    if module_name in sys.modules:
        return sys.modules[module_name]
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "scripts" / "check_parser_staleness.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so that dataclass / typing machinery can resolve the
    # module via sys.modules during class body evaluation.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


staleness = _load_module()


NOW = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


class EvaluateStalenessTestcase(unittest.TestCase):
    def test_ok_when_latest_within_threshold(self):
        latest = NOW - timedelta(hours=1)
        result = staleness.evaluate_staleness(
            "FR",
            [{"datetime": latest, "production": {}}],
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.status, staleness.StalenessStatus.OK)
        self.assertEqual(result.latest_datetime_utc, latest)
        self.assertAlmostEqual(result.age_hours or 0.0, 1.0, places=4)

    def test_stale_when_latest_older_than_threshold(self):
        latest = NOW - timedelta(hours=12)
        result = staleness.evaluate_staleness(
            "DE",
            [{"datetime": latest}],
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.status, staleness.StalenessStatus.STALE)
        self.assertAlmostEqual(result.age_hours or 0.0, 12.0, places=4)

    def test_missing_when_parser_returns_empty_list(self):
        result = staleness.evaluate_staleness(
            "GB",
            [],
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.status, staleness.StalenessStatus.MISSING)
        self.assertIsNone(result.latest_datetime_utc)

    def test_missing_when_parser_returns_none(self):
        result = staleness.evaluate_staleness(
            "GB",
            None,
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.status, staleness.StalenessStatus.MISSING)

    def test_dict_output_treated_as_single_event(self):
        latest = NOW - timedelta(minutes=30)
        result = staleness.evaluate_staleness(
            "ZA",
            {"datetime": latest, "production": {}},
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.status, staleness.StalenessStatus.OK)
        self.assertEqual(result.latest_datetime_utc, latest)

    def test_picks_max_datetime(self):
        latest = NOW - timedelta(hours=2)
        events = [
            {"datetime": NOW - timedelta(hours=10)},
            {"datetime": latest},
            {"datetime": NOW - timedelta(hours=4)},
        ]
        result = staleness.evaluate_staleness(
            "NZ",
            events,
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.latest_datetime_utc, latest)
        self.assertEqual(result.status, staleness.StalenessStatus.OK)

    def test_naive_datetime_treated_as_utc(self):
        latest_naive = (NOW - timedelta(hours=1)).replace(tzinfo=None)
        result = staleness.evaluate_staleness(
            "TW",
            [{"datetime": latest_naive}],
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.status, staleness.StalenessStatus.OK)
        self.assertIsNotNone(result.latest_datetime_utc)
        assert result.latest_datetime_utc is not None
        self.assertEqual(result.latest_datetime_utc.tzinfo, timezone.utc)

    def test_non_dict_events_are_ignored(self):
        result = staleness.evaluate_staleness(
            "BR",
            ["not-a-dict", {"no_datetime_here": True}],
            now_utc=NOW,
            max_age=timedelta(hours=6),
        )
        self.assertEqual(result.status, staleness.StalenessStatus.MISSING)


class RenderMarkdownTableTestcase(unittest.TestCase):
    def test_renders_header_and_rows(self):
        rows = [
            staleness.ZoneStaleness(
                zone="FR",
                latest_datetime_utc=NOW - timedelta(hours=1),
                age_hours=1.0,
                status=staleness.StalenessStatus.OK,
            ),
            staleness.ZoneStaleness(
                zone="GB",
                latest_datetime_utc=None,
                age_hours=None,
                status=staleness.StalenessStatus.MISSING,
            ),
        ]
        out = staleness.render_markdown_table(rows)
        lines = out.splitlines()
        self.assertEqual(
            lines[0], "| Zone | Latest datapoint (UTC) | Age (hours) | Status |"
        )
        self.assertEqual(lines[1], "| --- | --- | --- | --- |")
        self.assertIn("| FR |", lines[2])
        self.assertIn("OK", lines[2])
        self.assertIn("| GB |", lines[3])
        self.assertIn("MISSING", lines[3])
        self.assertIn("—", lines[3])


class RunForZonesTestcase(unittest.TestCase):
    """End-to-end (mocked parser) sweep through `run_for_zones`."""

    def test_mixed_outcomes(self):
        outputs = {
            "OK_ZONE": [{"datetime": NOW - timedelta(minutes=30)}],
            "STALE_ZONE": [{"datetime": NOW - timedelta(hours=24)}],
            "EMPTY_ZONE": [],
        }

        def fake_run(zone, data_type):  # noqa: ARG001
            return outputs[zone]

        with patch.object(staleness, "_run_parser", side_effect=fake_run):
            rows = staleness.run_for_zones(
                ["OK_ZONE", "STALE_ZONE", "EMPTY_ZONE"],
                data_type="production",
                max_age=timedelta(hours=6),
                now_utc=NOW,
            )
        self.assertEqual(
            [r.status for r in rows],
            [
                staleness.StalenessStatus.OK,
                staleness.StalenessStatus.STALE,
                staleness.StalenessStatus.MISSING,
            ],
        )

    def test_parser_exception_becomes_missing(self):
        def fake_run(zone, data_type):  # noqa: ARG001
            raise RuntimeError("boom")

        with patch.object(staleness, "_run_parser", side_effect=fake_run):
            rows = staleness.run_for_zones(
                ["FR"],
                data_type="production",
                max_age=timedelta(hours=6),
                now_utc=NOW,
            )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].status, staleness.StalenessStatus.MISSING)
        self.assertIn("boom", rows[0].detail)


class ParseZonesArgTestcase(unittest.TestCase):
    def test_strips_and_filters_empty(self):
        self.assertEqual(
            staleness.parse_zones_arg(" FR , DE,GB,, "), ["FR", "DE", "GB"]
        )

    def test_empty_inputs(self):
        self.assertEqual(staleness.parse_zones_arg(""), [])
        self.assertEqual(staleness.parse_zones_arg(None), [])


if __name__ == "__main__":
    unittest.main()

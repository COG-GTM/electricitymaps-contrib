import glob
import inspect
import unittest
from collections.abc import Callable
from inspect import isfunction
from pathlib import Path
from typing import Any, NamedTuple

from electricitymap.contrib.config.model import CONFIG_MODEL

PARSER_FOLDERS = (
    Path(__file__).parent.resolve() / "../electricitymap/contrib/parsers"
).resolve()
PARSER_FILES_GLOB = f"{PARSER_FOLDERS}/*.py"

# Files that exist on disk in the parser folder but are NOT registered as a
# `parsers.production` / `consumption` / `price` / etc. function for any zone or
# exchange. `__init__.py` is package boilerplate and should always be excluded.
# The remaining entries are parsers that are not currently wired to any zone —
# they are tracked here as known-orphans so that any new orphan added in the
# future causes the test below to fail in CI.
EXPECTED_UNUSED_FILES = {
    "__init__.py",
    # TODO: archive — none of the entries below are referenced by any zone or
    # exchange config. They should either be re-wired to the appropriate
    # zone/exchange config or moved under
    # `electricitymap/contrib/parsers/archived/`.
    "CH.py",
    "ENERCAL.py",
    "IN_DL.py",
    "IN_HP.py",
    "IN_KA.py",
    "IN_MH.py",
    "IN_PB.py",
    "IN_UT.py",
    "NL.py",
    "NO-NO4_SE.py",
    "US_PREPA.py",
    "eSett.py",
}
_PARSER_FUNCTION_ARGS = ["zone_key", "session", "target_datetime", "logger"]
_CAPACITY_PARSER_FUNCTION_ARGS = ["zone_key", "target_datetime", "session"]
_EXCHANGE_FUNCTION_ARGS = [
    "zone_key1",
    "zone_key2",
    "session",
    "target_datetime",
    "logger",
]
EXPECTED_MODE_FUNCTION_ARGS = {
    "consumption": _PARSER_FUNCTION_ARGS,
    "consumptionForecast": _PARSER_FUNCTION_ARGS,
    "exchange": _EXCHANGE_FUNCTION_ARGS,
    "exchangeCapacityForecastDayAhead": _EXCHANGE_FUNCTION_ARGS,
    "exchangeCapacityForecastWeekAhead": _EXCHANGE_FUNCTION_ARGS,
    "exchangeCapacityForecastMonthAhead": _EXCHANGE_FUNCTION_ARGS,
    "shadowAuctionAtcDayAhead": _EXCHANGE_FUNCTION_ARGS,
    "coreExternalAtcDayAhead": _EXCHANGE_FUNCTION_ARGS,
    "maxBexDayAhead": _EXCHANGE_FUNCTION_ARGS,
    "scheduledExchangesDayAhead": _EXCHANGE_FUNCTION_ARGS,
    "maxBflowDayAhead": _EXCHANGE_FUNCTION_ARGS,
    "exchangeForecast": _EXCHANGE_FUNCTION_ARGS,
    "generationForecast": _PARSER_FUNCTION_ARGS,
    "dayaheadLocationalMarginalPrice": _PARSER_FUNCTION_ARGS,
    "realtimeLocationalMarginalPrice": _PARSER_FUNCTION_ARGS,
    "price": _PARSER_FUNCTION_ARGS,
    "production": _PARSER_FUNCTION_ARGS,
    "productionPerModeForecast": _PARSER_FUNCTION_ARGS,
    "productionPerModeForecastDayAhead": _PARSER_FUNCTION_ARGS,
    "productionPerModeForecastIntraday": _PARSER_FUNCTION_ARGS,
    "productionPerModeForecastLatest": _PARSER_FUNCTION_ARGS,
    "productionCapacity": _CAPACITY_PARSER_FUNCTION_ARGS,
    "gridAlerts": _PARSER_FUNCTION_ARGS,
}
_RETURN_PARSER_TYPE = [
    dict,
    list,
    list[dict],
    list[dict[str, Any]],
    list | dict,
    list[dict] | dict,
    dict[str, Any],
    dict[str, Any] | list[dict[str, Any]],
    dict[str, Any] | None,
]
EXPECTED_MODE_RETURN_ANNOTATIONS = {
    "consumption": _RETURN_PARSER_TYPE,
    "consumptionForecast": _RETURN_PARSER_TYPE,
    "exchange": _RETURN_PARSER_TYPE,
    "exchangeCapacityForecastDayAhead": _RETURN_PARSER_TYPE,
    "exchangeCapacityForecastWeekAhead": _RETURN_PARSER_TYPE,
    "exchangeCapacityForecastMonthAhead": _RETURN_PARSER_TYPE,
    "shadowAuctionAtcDayAhead": _RETURN_PARSER_TYPE,
    "coreExternalAtcDayAhead": _RETURN_PARSER_TYPE,
    "maxBexDayAhead": _RETURN_PARSER_TYPE,
    "scheduledExchangesDayAhead": _RETURN_PARSER_TYPE,
    "maxBflowDayAhead": _RETURN_PARSER_TYPE,
    "exchangeForecast": _RETURN_PARSER_TYPE,
    "generationForecast": _RETURN_PARSER_TYPE,
    "dayaheadLocationalMarginalPrice": _RETURN_PARSER_TYPE,
    "realtimeLocationalMarginalPrice": _RETURN_PARSER_TYPE,
    "price": _RETURN_PARSER_TYPE,
    "production": _RETURN_PARSER_TYPE,
    "productionPerModeForecast": _RETURN_PARSER_TYPE,
    "productionPerModeForecastDayAhead": _RETURN_PARSER_TYPE,
    "productionPerModeForecastIntraday": _RETURN_PARSER_TYPE,
    "productionPerModeForecastLatest": _RETURN_PARSER_TYPE,
    "productionCapacity": _RETURN_PARSER_TYPE,
    "gridAlerts": _RETURN_PARSER_TYPE,
}


class ZoneParserFunction(NamedTuple):
    zone: str
    mode: str
    function_name: str
    function: Callable


def undecorated(o):
    """Remove all decorators from a function.
    Inspired by https://github.com/iartarisi/undecorated/blob/master/undecorated.py
    """

    closure = o.__closure__

    if closure:
        for cell in closure:
            if cell.cell_contents is o:
                continue

            if isfunction(cell.cell_contents):
                undecd = undecorated(cell.cell_contents)
                if undecd:
                    return undecd
        else:
            return o
    else:
        return o


class ParserInterfaceTestcase(unittest.TestCase):
    def setUp(self):
        self.zone_parser_functions: list[ZoneParserFunction] = []

        for model_map in [CONFIG_MODEL.exchanges, CONFIG_MODEL.zones]:
            for zone in model_map:
                model = model_map[zone]
                if not model.parsers:
                    continue

                for mode, function_name in model.parsers:
                    if function_name is not None:
                        # load all functions
                        function = model.parsers.get_function(mode)
                        self.assertTrue(callable(function))
                        assert function

                        self.zone_parser_functions.append(
                            ZoneParserFunction(
                                zone=zone,
                                mode=mode,
                                function_name=function_name,
                                function=function,
                            )
                        )

    def test_interface(self):
        for zone_parser_function in self.zone_parser_functions:
            _zone, _mode, function_name, function = zone_parser_function

            # do a poor mans type checking (until we use MyPy or a similar tool)
            arg_spec = inspect.getfullargspec(undecorated(function))

            (
                args,
                varargs,
                varkw,
                defaults,
                _kwonlyargs,
                _kwonlydefaults,
                annotations,
            ) = arg_spec

            self.assertIsNone(
                varargs,
                f"expected no varargs for {function_name}, arg_spec={arg_spec}",
            )

            self.assertIsNone(
                varkw,
                f"expected no varkw for {function_name}, arg_spec={arg_spec}",
            )

            self.assertEqual(
                sorted(args),
                sorted(EXPECTED_MODE_FUNCTION_ARGS[_mode]),
                f"invalid args for {function_name}, arg_spec={arg_spec}",
            )

            if annotations and "return" in annotations:
                expected = EXPECTED_MODE_RETURN_ANNOTATIONS[_mode]
                correct_annotations = any(annotations["return"] == a for a in expected)
                self.assertTrue(
                    correct_annotations,
                    f"expected annotation for {function_name} to be in {expected} not {annotations['return']}",
                )

    def test_unused_files(self):
        parser_files_used = {
            f"{f.function_name.rsplit('.', 1)[0]}.py"
            for f in self.zone_parser_functions
        }

        all_parser_files = {f.rsplit("/", 1)[-1] for f in glob.glob(PARSER_FILES_GLOB)}

        unused_parser_files = all_parser_files - parser_files_used

        self.assertEqual(
            unused_parser_files,
            EXPECTED_UNUSED_FILES,
            (
                "Unused parser files diverged from EXPECTED_UNUSED_FILES. "
                "Either wire the new file(s) to a zone / exchange config, "
                "move them under electricitymap/contrib/parsers/archived/, "
                "or update EXPECTED_UNUSED_FILES if the change is intentional."
            ),
        )


if __name__ == "__main__":
    unittest.main(buffer=True)

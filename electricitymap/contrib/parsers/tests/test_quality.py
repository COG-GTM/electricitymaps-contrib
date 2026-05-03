import pytest

from electricitymap.contrib.parsers.lib.quality import (
    validate_consumption,
    validate_exchange,
    validate_production,
)
from electricitymap.contrib.parsers.tests.mocks.quality_check import (
    c1,
    c2,
    c3,
    e1,
    e2,
    e3,
    e4,
    p1,
    p2,
    p3,
    p4,
    p5,
)
from electricitymap.contrib.types import ZoneKey


def test_validate_consumption_positive():
    assert not validate_consumption(c1, ZoneKey("FR")), "Positive consumption is fine!"


def test_validate_consumption_negative():
    with pytest.raises(ValueError):
        validate_consumption(c2, ZoneKey("FR"))


def test_validate_consumption_none():
    assert not validate_consumption(c3, ZoneKey("FR")), "Consumption can be undefined!"


def test_validate_exchange_key_mismatch():
    with pytest.raises(Exception):
        validate_exchange(e1, "DK->NA")


def test_validate_exchange_no_datetime():
    with pytest.raises(Exception):
        validate_exchange(e2, "DK->NO")


def test_validate_exchange_bad_datetime():
    with pytest.raises(Exception):
        validate_exchange(e3, "DK->NO")


def test_validate_exchange_future_not_allowed():
    with pytest.raises(Exception):
        validate_exchange(e4, "DK->NO")


def test_validate_production_positive():
    assert not validate_production(p1, ZoneKey("FR")), (
        "Positive production should pass!"
    )


def test_validate_production_negative_total():
    with pytest.raises(ValueError):
        validate_production(p2, ZoneKey("FR"))


def test_validate_production_implausibly_high_total():
    with pytest.raises(ValueError):
        validate_production(p3, ZoneKey("FR"))


def test_validate_production_missing_production_key():
    with pytest.raises(ValueError):
        validate_production(p4, ZoneKey("FR"))


def test_validate_production_implausibly_high_single_mode():
    with pytest.raises(ValueError):
        validate_production(p5, ZoneKey("FR"))

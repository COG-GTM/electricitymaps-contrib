"""Shared fixtures for parser unit tests under `tests/parsers/`.

Mirrors the `requests-mock`-backed `adapter` / `session` fixtures used by
the in-tree parser tests in `electricitymap/contrib/parsers/tests/conftest.py`
so each test can mount mocked responses for `https://`-scheme URLs.
"""

from __future__ import annotations

import pytest
from requests import Session
from requests_mock import Adapter


@pytest.fixture
def adapter() -> Adapter:
    return Adapter()


@pytest.fixture
def session(adapter: Adapter) -> Session:
    sess = Session()
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    return sess

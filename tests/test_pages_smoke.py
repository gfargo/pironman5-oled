"""Smoke test: every registered info page must render N times without
raising, using a MockOLED (no real display/hardware/network needed).

Catches import errors, missing deps, and typos in page code before deploying.
"""
import importlib
import urllib.error

import pytest

from mock_oled import MockOLED
from pages.alert_page import PageAlert
from pages.orchestrator import INFO_PAGE_MODULES

DRAW_ITERATIONS = 5

PAGE_CLASSES = [
    getattr(importlib.import_module(modname, package="pages"), clsname)
    for modname, clsname in INFO_PAGE_MODULES.values()
] + [PageAlert]


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Pages degrade gracefully on fetch failure (see AGENTS notes), but a
    real network call in CI would be slow/flaky. Fail fast instead."""
    def _raise(*args, **kwargs):
        raise urllib.error.URLError("network disabled in tests")

    monkeypatch.setattr("urllib.request.urlopen", _raise)


@pytest.mark.parametrize("cls", PAGE_CLASSES, ids=lambda c: c.__name__)
def test_page_renders(cls):
    oled = MockOLED()
    page = cls()

    for _ in range(DRAW_ITERATIONS):
        page.main(oled, {}, {})

    # A page that clears the screen must also display the result — a page
    # that legitimately has nothing to show (e.g. PageAlert with no active
    # alert, see AGENTS graceful-degradation notes) is fine as long as it
    # never clears either.
    assert oled.displayed or not oled.cleared


def test_all_pages_registered():
    assert len(PAGE_CLASSES) > 0
    assert len(set(PAGE_CLASSES)) == len(PAGE_CLASSES)

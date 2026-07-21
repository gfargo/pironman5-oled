"""Smoke test: every registered info page must render N times without
raising, using a MockOLED (no real display/hardware/network needed).

Catches import errors, missing deps, and typos in page code before deploying.
"""
import urllib.error

import pytest

from mock_oled import MockOLED
from pages.alert_page import PageAlert
from pages.orchestrator import INFO_PAGE_REGISTRY

DRAW_ITERATIONS = 5

PAGE_CLASSES = list(INFO_PAGE_REGISTRY.values()) + [PageAlert]


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


def test_all_pages_registered():
    assert len(PAGE_CLASSES) > 0
    assert len(set(PAGE_CLASSES)) == len(PAGE_CLASSES)

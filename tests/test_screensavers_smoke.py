"""Smoke test: every registered screensaver must reset() and draw() N times
without raising, using a MockOLED (no real display/hardware needed).
"""
import random

import pytest

from mock_oled import MockOLED
from pages.screensavers import ALL_SCREENSAVERS

DRAW_ITERATIONS = 5


@pytest.fixture(autouse=True)
def _seeded_rng():
    random.seed(0)


@pytest.mark.parametrize("cls", ALL_SCREENSAVERS, ids=lambda c: c.__name__)
def test_screensaver_renders(cls):
    oled = MockOLED()
    screensaver = cls()
    screensaver.reset()

    for _ in range(DRAW_ITERATIONS):
        screensaver.draw(oled)

    assert oled.cleared
    assert oled.displayed


def test_all_screensavers_registered():
    assert len(ALL_SCREENSAVERS) > 0
    assert len(set(ALL_SCREENSAVERS)) == len(ALL_SCREENSAVERS)

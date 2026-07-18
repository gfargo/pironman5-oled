"""Tests for raindrop_ripples.py — pure-logic step/render split."""
import sys
import random

sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
from raindrop_ripples import (
    RaindropRipples,
    _ring_point_count,
    MIN_RIPPLES,
    MAX_RIPPLES,
    MAX_RADIUS,
    RING_SPEED,
    SPAWN_MIN,
    SPAWN_MAX,
    SCREEN_W,
    SCREEN_H,
)


class MockDraw:
    def __init__(self):
        self.points_drawn = []

    def point(self, coords, fill=1):
        self.points_drawn.append((coords, fill))


class MockOLED:
    def __init__(self):
        self.draw = MockDraw()
        self.cleared = False
        self.displayed = False

    def clear(self):
        self.cleared = True
        self.draw.points_drawn = []

    def display(self):
        self.displayed = True

    def reset_tracking(self):
        self.cleared = False
        self.displayed = False
        self.draw.points_drawn = []


def test_parameterless_init():
    saver = RaindropRipples()
    assert hasattr(saver, 'ripples')
    assert MIN_RIPPLES <= len(saver.ripples) <= MAX_RIPPLES


def test_reset_exists():
    saver = RaindropRipples()
    saver.last_time = 999.0
    saver.reset()
    assert saver.last_time == 0
    assert MIN_RIPPLES <= len(saver.ripples) <= MAX_RIPPLES


def test_draw_exists_and_renders():
    saver = RaindropRipples()
    oled = MockOLED()
    saver.draw(oled)
    assert oled.cleared
    assert oled.displayed


def test_step_expands_radius():
    saver = RaindropRipples()
    before = [r['radius'] for r in saver.ripples]
    saver._step(0.5)
    after = [r['radius'] for r in saver.ripples]
    # Every ripple present both before and after should have grown by RING_SPEED * dt
    for b in before:
        expected = b + RING_SPEED * 0.5
        assert any(abs(a - expected) < 1e-9 for a in after), \
            f"Expected a ripple with radius {expected}, got {after}"


def test_ripples_never_exceed_max_radius():
    saver = RaindropRipples()
    for _ in range(500):
        saver._step(0.05)
        for r in saver.ripples:
            assert r['radius'] < MAX_RADIUS


def test_active_count_stays_within_bounds():
    saver = RaindropRipples()
    for _ in range(500):
        saver._step(0.05)
        assert MIN_RIPPLES <= len(saver.ripples) <= MAX_RIPPLES


def test_spawn_cadence_adds_new_ripple():
    random.seed(42)
    saver = RaindropRipples()
    initial_count = len(saver.ripples)
    assert initial_count == MIN_RIPPLES

    # Advance time well past the max spawn interval with a controlled dt.
    total_elapsed = 0.0
    dt = 0.05
    grew = False
    while total_elapsed < SPAWN_MAX + 1.0:
        saver._step(dt)
        total_elapsed += dt
        if len(saver.ripples) > initial_count:
            grew = True
            break

    assert grew, "Expected a new ripple to spawn within SPAWN_MAX + 1.0 seconds"
    assert len(saver.ripples) <= MAX_RIPPLES


def test_density_fade_point_count_decreases_with_radius():
    small = _ring_point_count(2.0)
    large = _ring_point_count(40.0)
    assert large < small


def test_ring_point_count_has_minimum():
    assert _ring_point_count(1000.0) >= 4


def test_draw_renders_within_bounds():
    saver = RaindropRipples()
    oled = MockOLED()

    for frame in range(100):
        oled.reset_tracking()
        saver.draw(oled)

        for (x, y), fill in oled.draw.points_drawn:
            assert 0 <= x <= SCREEN_W - 1, f"Frame {frame}: x={x} out of bounds"
            assert 0 <= y <= SCREEN_H - 1, f"Frame {frame}: y={y} out of bounds"
            assert fill == 1, f"Frame {frame}: fill should be 1, got {fill}"


def test_concentric_rings_per_drop():
    saver = RaindropRipples()
    saver.ripples = [{'x': 64, 'y': 32, 'radius': 30.0}]
    oled = MockOLED()
    saver._render(oled)

    # A radius of 30 with RING_GAP=7 should produce points at multiple
    # distinct distances from the drop center (i.e. more than one ring).
    distances = set()
    for (x, y), _ in oled.draw.points_drawn:
        dist = round(((x - 64) ** 2 + (y - 32) ** 2) ** 0.5)
        distances.add(dist)
    assert len(distances) > 1, "Expected multiple concentric ring radii to be rendered"

"""Smoke tests for the Lorenz attractor screensaver's integration math."""
import sys
sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
from lorenz_attractor import LorenzAttractor, SCREEN_W, SCREEN_H, MAX_TRAIL


class MockDraw:
    """Mock for oled.draw with a .point() method."""
    def __init__(self):
        self.points_drawn = []

    def point(self, coords, fill=1):
        self.points_drawn.append((coords, fill))


class MockOLED:
    """Mock OLED object matching the PIL-style interface used by the screensavers."""
    def __init__(self):
        self.draw = MockDraw()
        self.cleared = False
        self.displayed = False

    def clear(self):
        self.cleared = True
        self.draw.points_drawn = []

    def display(self):
        self.displayed = True


def test_parameterless_init():
    """API contract: __init__() takes no arguments."""
    attractor = LorenzAttractor()
    assert hasattr(attractor, 'x')
    assert hasattr(attractor, 'y')
    assert hasattr(attractor, 'z')
    assert hasattr(attractor, 'trail')


def test_reset_reinitializes_state():
    attractor = LorenzAttractor()
    attractor.x, attractor.y, attractor.z = 999.0, 999.0, 999.0
    attractor.trail = [(1, 1)] * 10
    attractor.reset()
    assert attractor.x == 0.1
    assert attractor.y == 0.0
    assert attractor.z == 0.0
    assert attractor.trail == []


def test_draw_renders_and_advances_state():
    attractor = LorenzAttractor()
    oled = MockOLED()

    x0, y0, z0 = attractor.x, attractor.y, attractor.z
    attractor.draw(oled)

    assert oled.cleared
    assert oled.displayed
    # The system state must have moved off the initial position.
    assert (attractor.x, attractor.y, attractor.z) != (x0, y0, z0)


def test_trail_accumulates_and_caps_at_max():
    attractor = LorenzAttractor()
    oled = MockOLED()

    attractor.draw(oled)
    assert len(attractor.trail) > 0
    first_len = len(attractor.trail)

    # Drawing many more frames should never exceed MAX_TRAIL.
    for _ in range(400):
        attractor.draw(oled)
    assert len(attractor.trail) <= MAX_TRAIL
    assert len(attractor.trail) >= first_len


def test_trail_points_within_bounds_over_long_run():
    """Chaotic system stays bounded on the attractor manifold; the projected
    trail should stay within (or safely clipped from) the display bounds
    across a long run — matching the 45s screensaver duration."""
    attractor = LorenzAttractor()
    oled = MockOLED()

    out_of_bounds = 0
    total = 0
    for _ in range(600):  # ~600 draw() calls, well beyond a single rotation
        attractor.draw(oled)
        for (px, py), fill in oled.draw.points_drawn:
            total += 1
            assert fill == 1
            if not (0 <= px < SCREEN_W and 0 <= py < SCREEN_H):
                out_of_bounds += 1

    assert total > 0
    # The projection is tuned so essentially all points land on-screen;
    # any off-screen points are simply skipped at render time, never crash.
    assert out_of_bounds == 0


def test_butterfly_shape_emerges_after_growth_period():
    """After enough steps the trail should have visited both lobes of the
    butterfly (i.e. both positive and negative x excursions)."""
    attractor = LorenzAttractor()
    oled = MockOLED()

    for _ in range(500):
        attractor.draw(oled)

    xs = [px for (px, py) in attractor.trail]
    assert min(xs) < SCREEN_W // 2
    assert max(xs) > SCREEN_W // 2

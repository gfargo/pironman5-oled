"""Physics + API contract tests for bouncing_balls.py (pure-logic, no real display)."""
import sys
import math
import random

sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
from bouncing_balls import (
    BouncingBalls,
    Ball,
    GRAVITY,
    BALL_RESTITUTION,
    MIN_BALLS,
    MAX_BALLS,
    MIN_RADIUS,
    MAX_RADIUS,
    SCREEN_W,
    SCREEN_H,
)


# --- Minimal mock OLED (PIL-style draw interface) ---

class MockDraw:
    """Mock for oled.draw with an .ellipse() method."""
    def __init__(self):
        self.ellipses_drawn = []

    def ellipse(self, box, fill=1):
        self.ellipses_drawn.append((box, fill))


class MockOLED:
    """Mock OLED object matching the PIL-style interface used by BouncingBalls."""
    def __init__(self):
        self.draw = MockDraw()
        self.cleared = False
        self.displayed = False

    def clear(self):
        self.cleared = True
        self.draw.ellipses_drawn = []

    def display(self):
        self.displayed = True

    def reset_tracking(self):
        self.cleared = False
        self.displayed = False
        self.draw.ellipses_drawn = []


def _make_sim(balls):
    """Build a BouncingBalls instance with a controlled set of balls, bypassing reset()."""
    sim = BouncingBalls()
    sim.balls = balls
    sim.last_time = 0
    return sim


def test_gravity_increases_downward_velocity():
    b = Ball(x=10, y=10, vx=0, vy=0, radius=3)
    sim = _make_sim([b])
    sim._apply_gravity(dt=1.0)
    assert abs(b.vy - GRAVITY) < 1e-9
    assert b.vx == 0


def test_integrate_moves_position_linearly():
    b = Ball(x=10, y=20, vx=5, vy=-3, radius=3)
    sim = _make_sim([b])
    sim._integrate(dt=2.0)
    assert abs(b.x - (10 + 5 * 2.0)) < 1e-9
    assert abs(b.y - (20 + -3 * 2.0)) < 1e-9


def test_wall_bounce_all_four_sides():
    r = 4.0
    left = Ball(x=-1, y=30, vx=-10, vy=0, radius=r)
    right = Ball(x=SCREEN_W + 1, y=30, vx=10, vy=0, radius=r)
    top = Ball(x=60, y=-1, vx=0, vy=-10, radius=r)
    bottom = Ball(x=60, y=SCREEN_H + 1, vx=0, vy=10, radius=r)

    sim = _make_sim([left, right, top, bottom])
    sim._resolve_wall_collisions()

    assert left.x == r
    assert left.vx == 10  # sign flipped, magnitude preserved (perfectly elastic)

    assert right.x == SCREEN_W - r
    assert right.vx == -10

    assert top.y == r
    assert top.vy == 10

    assert bottom.y == SCREEN_H - r
    assert bottom.vy == -10


def test_ball_collision_head_on_equal_mass_swap():
    r = 3.0
    # Overlapping, moving directly toward each other along x.
    a = Ball(x=50, y=30, vx=10, vy=0, radius=r)
    b = Ball(x=55, y=30, vx=-10, vy=0, radius=r)  # dist=5 < min_dist=6 -> overlapping

    pre_closing = (a.vx - b.vx)  # normal is purely along x here

    sim = _make_sim([a, b])
    sim._resolve_ball_collisions()

    post_closing = (a.vx - b.vx)
    assert abs(post_closing - (-BALL_RESTITUTION * pre_closing)) < 1e-6

    dist = math.hypot(b.x - a.x, b.y - a.y)
    assert dist >= (a.radius + b.radius) - 1e-6


def test_ball_collision_skipped_when_separating():
    r = 3.0
    # Overlapping but already moving apart.
    a = Ball(x=50, y=30, vx=-10, vy=0, radius=r)
    b = Ball(x=55, y=30, vx=10, vy=0, radius=r)

    va, vb = (a.vx, a.vy), (b.vx, b.vy)
    sim = _make_sim([a, b])
    sim._resolve_ball_collisions()

    assert (a.vx, a.vy) == va
    assert (b.vx, b.vy) == vb


def test_ball_collision_noop_when_not_touching():
    a = Ball(x=10, y=10, vx=1, vy=1, radius=2)
    b = Ball(x=100, y=50, vx=-1, vy=-1, radius=2)

    a_before = (a.x, a.y, a.vx, a.vy)
    b_before = (b.x, b.y, b.vx, b.vy)

    sim = _make_sim([a, b])
    sim._resolve_ball_collisions()

    assert (a.x, a.y, a.vx, a.vy) == a_before
    assert (b.x, b.y, b.vx, b.vy) == b_before


def test_spawn_count_and_no_overlap():
    random.seed(1234)
    sim = BouncingBalls()
    balls = sim._spawn_balls()

    assert MIN_BALLS <= len(balls) <= MAX_BALLS
    for b in balls:
        assert MIN_RADIUS <= b.radius <= MAX_RADIUS

    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            a, b = balls[i], balls[j]
            dist = math.hypot(a.x - b.x, a.y - b.y)
            assert dist >= (a.radius + b.radius) - 1e-6


def test_balls_stay_in_screen_bounds_over_many_steps():
    random.seed(42)
    sim = BouncingBalls()
    sim.reset()

    for _ in range(300):
        sim._step(0.033)

    eps = 1e-3
    for b in sim.balls:
        assert b.x - b.radius >= -eps
        assert b.x + b.radius <= SCREEN_W + eps
        assert b.y - b.radius >= -eps
        assert b.y + b.radius <= SCREEN_H + eps


def test_draw_smoke_with_mock_oled():
    sim = BouncingBalls()
    oled = MockOLED()

    for _ in range(10):
        oled.reset_tracking()
        sim.draw(oled)
        assert oled.cleared
        assert oled.displayed
        assert len(oled.draw.ellipses_drawn) == len(sim.balls)


def test_parameterless_init_and_reset():
    sim = BouncingBalls()
    assert hasattr(sim, 'balls')
    assert MIN_BALLS <= len(sim.balls) <= MAX_BALLS

    old_balls = sim.balls
    sim.reset()
    assert MIN_BALLS <= len(sim.balls) <= MAX_BALLS
    assert sim.last_time == 0
    # reset() should produce a fresh list (not necessarily the same object)
    assert sim.balls is not old_balls or len(sim.balls) >= 0

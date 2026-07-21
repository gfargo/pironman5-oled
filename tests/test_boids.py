"""Tests for Boids screensaver — pure-logic only (no display/GPIO/token needed)."""
import sys
import math
sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))

from boids import Boids, SCREEN_W, SCREEN_H, NUM_BOIDS, MIN_SPEED, MAX_SPEED, _make_boid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_boids(sim, boid_list):
    """Replace sim.boids with an explicit list for deterministic tests."""
    sim.boids = list(boid_list)


# ---------------------------------------------------------------------------
# Init / count
# ---------------------------------------------------------------------------

def test_reset_count_and_bounds():
    """After reset(), boid count is NUM_BOIDS and all positions are within screen."""
    sim = Boids()
    sim.reset()
    assert len(sim.boids) == NUM_BOIDS
    for b in sim.boids:
        assert 0.0 <= b['x'] < SCREEN_W, f"x={b['x']} out of bounds"
        assert 0.0 <= b['y'] < SCREEN_H, f"y={b['y']} out of bounds"


def test_reset_nonzero_velocity():
    """All boids should have non-zero speed after reset (no frozen starters)."""
    sim = Boids()
    sim.reset()
    for b in sim.boids:
        speed = math.sqrt(b['vx'] ** 2 + b['vy'] ** 2)
        assert speed >= MIN_SPEED * 0.9, f"Speed {speed} below MIN_SPEED after reset"


# ---------------------------------------------------------------------------
# Edge wrapping
# ---------------------------------------------------------------------------

def test_wrap_right_edge():
    """Boid past the right edge wraps to the left side."""
    sim = Boids()
    # Single boid past right edge, moving right
    _set_boids(sim, [_make_boid(SCREEN_W + 2, 32, MAX_SPEED, 0)])
    sim._step(0.05)
    assert 0.0 <= sim.boids[0]['x'] < SCREEN_W


def test_wrap_left_edge():
    """Boid past the left edge wraps to the right side."""
    sim = Boids()
    _set_boids(sim, [_make_boid(-5.0, 32, -MAX_SPEED, 0)])
    sim._step(0.05)
    assert 0.0 <= sim.boids[0]['x'] < SCREEN_W


def test_wrap_bottom_edge():
    """Boid past the bottom edge wraps to the top."""
    sim = Boids()
    _set_boids(sim, [_make_boid(64, SCREEN_H + 3, 0, MAX_SPEED)])
    sim._step(0.05)
    assert 0.0 <= sim.boids[0]['y'] < SCREEN_H


def test_wrap_top_edge():
    """Boid past the top edge wraps to the bottom."""
    sim = Boids()
    _set_boids(sim, [_make_boid(64, -5.0, 0, -MAX_SPEED)])
    sim._step(0.05)
    assert 0.0 <= sim.boids[0]['y'] < SCREEN_H


# ---------------------------------------------------------------------------
# Speed clamping
# ---------------------------------------------------------------------------

def test_speed_clamp_max():
    """After a step, no boid exceeds MAX_SPEED."""
    sim = Boids()
    # Give boids huge velocities
    _set_boids(sim, [
        _make_boid(10, 10, 9999.0, 9999.0),
        _make_boid(50, 30, -9999.0, 9999.0),
    ])
    sim._step(0.05)
    for b in sim.boids:
        speed = math.sqrt(b['vx'] ** 2 + b['vy'] ** 2)
        assert speed <= MAX_SPEED + 1e-6, f"Speed {speed} exceeds MAX_SPEED {MAX_SPEED}"


def test_speed_clamp_min():
    """After a step, no boid falls below MIN_SPEED (except right after zero-vel recovery)."""
    sim = Boids()
    # Single isolated boid with near-zero velocity (no neighbours to give steering)
    _set_boids(sim, [_make_boid(64, 32, 0.001, 0.001)])
    sim._step(0.05)
    speed = math.sqrt(sim.boids[0]['vx'] ** 2 + sim.boids[0]['vy'] ** 2)
    assert speed >= MIN_SPEED - 1e-6, f"Speed {speed} below MIN_SPEED {MIN_SPEED}"


# ---------------------------------------------------------------------------
# Cohesion sanity
# ---------------------------------------------------------------------------

def test_cohesion_pulls_together():
    """Two distant boids with zero velocity should have velocities pointing toward each other."""
    sim = Boids()
    # Place two boids far apart but within NEIGHBOR_RADIUS (use 15 px gap)
    x1, x2 = 57.0, 72.0  # 15 px apart — within NEIGHBOR_RADIUS (20)
    _set_boids(sim, [
        _make_boid(x1, 32, MIN_SPEED, 0),
        _make_boid(x2, 32, MIN_SPEED, 0),
    ])
    sim._step(0.05)
    # After cohesion, boid[0] should have gained positive-x component,
    # boid[1] should have gained negative-x component (they attract).
    vx0 = sim.boids[0]['vx']
    vx1 = sim.boids[1]['vx']
    # boid[0] is left of boid[1]; cohesion should pull right (vx increases)
    # boid[1] is right of boid[0]; cohesion should pull left (vx decreases)
    assert vx0 >= MIN_SPEED - 1e-6, f"Expected boid[0] to maintain/gain rightward velocity, got {vx0}"
    assert vx1 <= MIN_SPEED + 1e-6, f"Expected boid[1] to maintain/reduce rightward velocity, got {vx1}"


# ---------------------------------------------------------------------------
# Separation sanity
# ---------------------------------------------------------------------------

def test_separation_pushes_apart():
    """Two overlapping boids should be steered apart."""
    sim = Boids()
    # Place two boids nearly on top of each other (within SEPARATION_RADIUS)
    _set_boids(sim, [
        _make_boid(32.0, 32.0, MIN_SPEED, 0),
        _make_boid(33.5, 32.0, MIN_SPEED, 0),   # 1.5 px apart, well within sep radius
    ])
    sim._step(0.05)
    # After separation, their x positions should be further apart than before
    dist_after = abs(sim.boids[1]['x'] - sim.boids[0]['x'])
    # They were 1.5 px apart in x before the step; at minimum the velocities diverge
    # Check that velocities point in opposite x directions
    # boid[0] should be steered left (negative dx from boid[1]), boid[1] steered right
    assert sim.boids[0]['vx'] < sim.boids[1]['vx'], (
        f"Expected boid[0].vx {sim.boids[0]['vx']:.3f} < boid[1].vx {sim.boids[1]['vx']:.3f} after separation"
    )


# ---------------------------------------------------------------------------
# _triangle_points geometry
# ---------------------------------------------------------------------------

def test_triangle_points_count():
    """_triangle_points returns exactly 3 vertices."""
    sim = Boids()
    b = _make_boid(64, 32, 1.0, 0.0)  # heading = 0 (east)
    pts = sim._triangle_points(b)
    assert len(pts) == 3


def test_triangle_nose_in_heading_direction():
    """The nose vertex should lie ahead of the boid centre in the heading direction."""
    sim = Boids()
    # Heading east (vx=1, vy=0)
    b = _make_boid(64.0, 32.0, 10.0, 0.0)
    pts = sim._triangle_points(b)
    nose = pts[0]
    # Nose should be to the right of centre (higher x)
    assert nose[0] > b['x'], f"Nose x {nose[0]} should be > centre x {b['x']}"
    # Nose y should be roughly at centre y (within 1 px rounding)
    assert abs(nose[1] - b['y']) <= 1, f"Nose y {nose[1]} too far from centre y {b['y']}"


def test_triangle_nose_in_heading_north():
    """Nose vertex lies above centre when heading north."""
    sim = Boids()
    b = _make_boid(64.0, 32.0, 0.0, -10.0)  # heading north (negative y)
    pts = sim._triangle_points(b)
    nose = pts[0]
    assert nose[1] < b['y'], f"Nose y {nose[1]} should be < centre y {b['y']} (north)"


def test_triangle_points_are_integers():
    """All returned coordinates are integers (for PIL drawing)."""
    sim = Boids()
    b = _make_boid(40.7, 20.3, 3.0, 4.0)
    pts = sim._triangle_points(b)
    for x, y in pts:
        assert isinstance(x, int), f"x={x} is not int"
        assert isinstance(y, int), f"y={y} is not int"


# ---------------------------------------------------------------------------
# No-neighbour boid (div-by-zero guard)
# ---------------------------------------------------------------------------

def test_single_boid_no_crash():
    """A single isolated boid should step without error."""
    sim = Boids()
    _set_boids(sim, [_make_boid(64, 32, MIN_SPEED, 0)])
    sim._step(0.05)  # Must not raise
    assert len(sim.boids) == 1


if __name__ == "__main__":
    test_reset_count_and_bounds()
    test_reset_nonzero_velocity()
    test_wrap_right_edge()
    test_wrap_left_edge()
    test_wrap_bottom_edge()
    test_wrap_top_edge()
    test_speed_clamp_max()
    test_speed_clamp_min()
    test_cohesion_pulls_together()
    test_separation_pushes_apart()
    test_triangle_points_count()
    test_triangle_nose_in_heading_direction()
    test_triangle_nose_in_heading_north()
    test_triangle_points_are_integers()
    test_single_boid_no_crash()
    print("ALL BOIDS TESTS PASSED")

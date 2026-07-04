"""Final checkpoint verification for fractal_tree.py.

Verifies:
1. Module imports cleanly (no unused imports, no syntax errors)
2. Public API contract: parameterless __init__, reset(), draw(oled)
3. Smoke test with mock OLED object
4. Branch count validation
5. Growth state initialization
6. Growth advances over 25+ draw calls
7. Wind phase advances on every draw call
"""
import sys
import math

sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
from fractal_tree import FractalTree, INITIAL_DEPTH, MAX_DEPTH, GROWTH_SPEED


# --- Minimal mock OLED (PIL-style draw interface) ---

class MockDraw:
    """Mock for oled.draw with .line() method."""
    def __init__(self):
        self.lines_drawn = []

    def line(self, coords, fill=1):
        self.lines_drawn.append((coords, fill))


class MockOLED:
    """Mock OLED object matching the PIL-style interface used by FractalTree."""
    def __init__(self):
        self.draw = MockDraw()
        self.cleared = False
        self.displayed = False

    def clear(self):
        self.cleared = True
        self.draw.lines_drawn = []

    def display(self):
        self.displayed = True

    def reset_tracking(self):
        self.cleared = False
        self.displayed = False
        self.draw.lines_drawn = []


# --- Tests ---

def test_parameterless_init():
    """API contract: __init__() takes no arguments."""
    tree = FractalTree()
    assert hasattr(tree, 'branches')
    assert hasattr(tree, 'growth_state')
    assert hasattr(tree, 'wind_phase')
    print("✓ Parameterless __init__() works")


def test_reset_exists():
    """API contract: reset() method exists and reinitializes state."""
    tree = FractalTree()
    tree.wind_phase = 999.0  # Pollute state
    tree.reset()
    assert tree.wind_phase == 0.0
    assert tree.growth_state.complete is False
    print("✓ reset() exists and reinitializes state")


def test_draw_exists():
    """API contract: draw(oled) method exists and renders a frame."""
    tree = FractalTree()
    oled = MockOLED()
    tree.draw(oled)
    assert oled.cleared
    assert oled.displayed
    assert len(oled.draw.lines_drawn) > 0
    print("✓ draw(oled) exists and renders")


def test_branch_count():
    """Verify branch count is reasonable for depth-8 binary tree.

    A perfect binary tree of depth 8 has 2^8 - 1 = 255 nodes.
    Due to length < 2 cutoff, actual count may be less.
    """
    tree = FractalTree()
    count = len(tree.branches)
    # Should have branches from depth 1 to up to 8
    # With length cutoff, expect at least 100 branches, up to 255
    assert 50 < count <= 255, f"Expected 50-255 branches, got {count}"

    # Verify depth distribution
    depths = {}
    for b in tree.branches:
        depths[b.depth] = depths.get(b.depth, 0) + 1

    # Must have trunk (depth 1)
    assert depths.get(1, 0) == 1, "Must have exactly one trunk"
    # Must have branches at all depths up to at least INITIAL_DEPTH
    for d in range(1, INITIAL_DEPTH + 1):
        assert d in depths, f"Missing branches at depth {d}"

    print(f"✓ Branch count = {count} (depths: {depths})")


def test_growth_state_init():
    """Growth state starts at depth 7 with progress dict populated."""
    tree = FractalTree()
    gs = tree.growth_state

    assert gs.current_depth == INITIAL_DEPTH + 1  # depth 7
    assert gs.complete is False

    # Progress dict should have entries for depth-7 branches
    d7_indices = [i for i, b in enumerate(tree.branches) if b.depth == 7]
    if len(d7_indices) > 0:
        for idx in d7_indices:
            assert idx in gs.progress, f"Depth-7 branch {idx} not in progress dict"
            assert gs.progress[idx] == 0.0, f"Depth-7 branch {idx} should start at 0.0"

    # No depth-8 branches should be in progress yet
    d8_indices = [i for i, b in enumerate(tree.branches) if b.depth == 8]
    for idx in d8_indices:
        assert idx not in gs.progress, f"Depth-8 branch {idx} should NOT be in progress yet"

    print(f"✓ Growth state initialized: depth={gs.current_depth}, {len(gs.progress)} branches in front")


def test_growth_advances_over_draws():
    """Calling draw() 25+ times should advance growth."""
    tree = FractalTree()
    oled = MockOLED()

    # Record initial state
    initial_progress = dict(tree.growth_state.progress)
    initial_depth = tree.growth_state.current_depth

    # Draw 30 times
    for _ in range(30):
        tree.draw(oled)

    # Growth should have advanced
    d7_indices = [i for i, b in enumerate(tree.branches) if b.depth == 7]
    if len(d7_indices) > 0:
        # After 25 draws at GROWTH_SPEED=0.04, depth 7 should be complete (25 * 0.04 = 1.0)
        # After 30 draws, should have transitioned to depth 8
        assert tree.growth_state.current_depth >= INITIAL_DEPTH + 1
        # Either still growing depth 7 or transitioned to 8
        if tree.growth_state.current_depth == MAX_DEPTH:
            # Depth 7 completed, now on depth 8
            for idx in d7_indices:
                assert tree.growth_state.progress[idx] >= 1.0
            print("  → Transitioned to depth 8 after 30 draws")
        else:
            # Still on depth 7 but progress should have increased
            for idx in d7_indices:
                assert tree.growth_state.progress[idx] > initial_progress.get(idx, 0.0)

    print("✓ Growth advances over 30 draw() calls")


def test_wind_phase_advances_every_draw():
    """Wind phase must advance on every draw() call regardless of growth state."""
    tree = FractalTree()
    oled = MockOLED()

    phases = [tree.wind_phase]
    for _ in range(10):
        tree.draw(oled)
        phases.append(tree.wind_phase)

    # Every consecutive pair should show increase
    for i in range(1, len(phases)):
        assert phases[i] > phases[i - 1], f"Wind phase did not advance at draw {i}: {phases[i-1]} -> {phases[i]}"

    # Also test when growth is complete
    tree.growth_state.complete = True
    phase_before = tree.wind_phase
    tree.draw(oled)
    assert tree.wind_phase > phase_before, "Wind phase must advance even when growth is complete"

    print("✓ Wind phase advances on every draw() call")


def test_no_unused_imports():
    """Check that the module doesn't import unused modules like `time`."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fractal_tree",
        "/Users/gfargo/Documents/Claude/Projects/Life Automation/pironman5-oled/pages/screensavers/fractal_tree.py"
    )
    # Read the source and check imports
    with open(spec.origin, 'r') as f:
        source = f.read()

    # These modules should NOT be imported (legacy leftovers)
    banned_imports = ['import time', 'from time']
    for banned in banned_imports:
        assert banned not in source, f"Found unused import: '{banned}'"

    # These modules SHOULD be imported
    required_imports = ['import math', 'import random', 'from dataclasses']
    for req in required_imports:
        assert req in source, f"Missing required import: '{req}'"

    print("✓ No unused imports, all required imports present")


def test_draw_renders_within_bounds():
    """All rendered line coordinates must be within 128x64 display bounds."""
    tree = FractalTree()
    oled = MockOLED()

    # Draw multiple frames to test various growth states
    for frame in range(50):
        oled.reset_tracking()
        tree.draw(oled)

        for coords, fill in oled.draw.lines_drawn:
            (x1, y1), (x2, y2) = coords
            assert 0 <= x1 <= 127, f"Frame {frame}: x1={x1} out of bounds"
            assert 0 <= y1 <= 63, f"Frame {frame}: y1={y1} out of bounds"
            assert 0 <= x2 <= 127, f"Frame {frame}: x2={x2} out of bounds"
            assert 0 <= y2 <= 63, f"Frame {frame}: y2={y2} out of bounds"
            assert fill == 1, f"Frame {frame}: fill should be 1, got {fill}"

    print("✓ All rendered lines within 128x64 bounds across 50 frames")


def test_full_growth_cycle():
    """Run through the complete growth cycle and verify completion."""
    tree = FractalTree()
    oled = MockOLED()

    # Should complete in ~50 frames (25 for depth 7, 25 for depth 8)
    for _ in range(60):
        tree.draw(oled)

    d8_indices = [i for i, b in enumerate(tree.branches) if b.depth == 8]
    if len(d8_indices) > 0:
        assert tree.growth_state.complete is True, "Growth should be complete after 60 frames"
    else:
        # If no depth-8 branches (due to length cutoff), should still have completed depth-7
        d7_complete = all(
            tree.growth_state.progress[i] >= 1.0
            for i in tree.growth_state.progress
            if tree.branches[i].depth == 7
        )
        assert d7_complete, "All depth-7 branches should be complete"

    print("✓ Full growth cycle completes within expected frame count")


# --- Run all tests ---

if __name__ == "__main__":
    print("=" * 60)
    print("FINAL CHECKPOINT: fractal_tree.py verification")
    print("=" * 60)
    print()

    test_parameterless_init()
    test_reset_exists()
    test_draw_exists()
    test_branch_count()
    test_growth_state_init()
    test_growth_advances_over_draws()
    test_wind_phase_advances_every_draw()
    test_no_unused_imports()
    test_draw_renders_within_bounds()
    test_full_growth_cycle()

    print()
    print("=" * 60)
    print("ALL VERIFICATION TESTS PASSED ✓")
    print("=" * 60)

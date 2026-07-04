"""Smoke test for _advance_growth() method."""
import sys
sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
from fractal_tree import FractalTree, GROWTH_SPEED, INITIAL_DEPTH, MAX_DEPTH


def test_advance_growth():
    tree = FractalTree()
    tree.branches = tree._compute_tree()
    tree.growth_state = tree._init_growth_state()

    d7 = [i for i, b in enumerate(tree.branches) if b.depth == 7]
    d8 = [i for i, b in enumerate(tree.branches) if b.depth == 8]

    # Initial state
    assert tree.growth_state.current_depth == 7
    assert tree.growth_state.complete is False
    assert len(d7) > 0

    # After 1 advance: progress incremented by GROWTH_SPEED
    tree._advance_growth()
    assert abs(tree.growth_state.progress[d7[0]] - GROWTH_SPEED) < 1e-9

    # After 25 total: depth-7 complete, transitions to depth 8
    for _ in range(24):
        tree._advance_growth()
    assert tree.growth_state.current_depth == MAX_DEPTH

    if len(d8) > 0:
        # Depth-8 branches seeded
        assert tree.growth_state.complete is False
        d8_in_prog = [i for i in tree.growth_state.progress if tree.branches[i].depth == 8]
        assert len(d8_in_prog) == len(d8)
        assert tree.growth_state.progress[d8_in_prog[0]] == 0.0

        # After 25 more: depth-8 complete
        for _ in range(25):
            tree._advance_growth()
        assert tree.growth_state.complete is True
    else:
        # No depth-8 branches exist (all terminated by length < 2)
        # Next advance should complete since there are no depth-8 to grow
        tree._advance_growth()
        assert tree.growth_state.complete is True

    # No-op after complete
    old = dict(tree.growth_state.progress)
    tree._advance_growth()
    assert tree.growth_state.progress == old
    print("ALL TESTS PASSED")


def test_skip_when_complete():
    tree = FractalTree()
    tree.branches = tree._compute_tree()
    tree.growth_state = tree._init_growth_state()
    tree.growth_state.complete = True

    old = dict(tree.growth_state.progress)
    old_depth = tree.growth_state.current_depth
    tree._advance_growth()
    assert tree.growth_state.progress == old
    assert tree.growth_state.current_depth == old_depth
    print("SKIP TEST PASSED")


def test_clamp_to_one():
    tree = FractalTree()
    tree.branches = tree._compute_tree()
    tree.growth_state = tree._init_growth_state()

    # Set a branch to just below 1.0
    d7 = [i for i, b in enumerate(tree.branches) if b.depth == 7]
    tree.growth_state.progress[d7[0]] = 0.99
    tree._advance_growth()
    assert tree.growth_state.progress[d7[0]] == 1.0
    print("CLAMP TEST PASSED")


def test_monotonic_progress():
    """Progress values never decrease."""
    tree = FractalTree()
    tree.branches = tree._compute_tree()
    tree.growth_state = tree._init_growth_state()

    prev = dict(tree.growth_state.progress)
    for _ in range(60):
        tree._advance_growth()
        for k in prev:
            if k in tree.growth_state.progress:
                assert tree.growth_state.progress[k] >= prev[k]
        prev = dict(tree.growth_state.progress)
    print("MONOTONIC TEST PASSED")


if __name__ == "__main__":
    test_advance_growth()
    test_skip_when_complete()
    test_clamp_to_one()
    test_monotonic_progress()

"""Tests for maze.py — pure algorithm logic only (no OLED required)."""
import sys
sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
import random
from collections import deque
from maze import (
    Maze, COLS, ROWS, ENTRANCE, EXIT,
    CARVE_SECS, SOLVE_SECS, HOLD_SECS,
)


def _full_carve(maze):
    """Drive carve to completion; raises if it takes too long."""
    guard = 0
    while not maze._carve_done:
        maze._carve_step()
        guard += 1
        assert guard < COLS * ROWS * 4, "Carve did not terminate within expected steps"


# ---------------------------------------------------------------------------
# Carve tests
# ---------------------------------------------------------------------------

def test_carve_visits_all_cells():
    """Carving terminates and visits exactly COLS*ROWS distinct cells."""
    maze = Maze()
    _full_carve(maze)
    assert maze._carve_done is True
    assert len(maze.visited) == COLS * ROWS


def test_carve_visited_monotonically_grows():
    """visited set only gains cells, never loses them."""
    maze = Maze()
    prev_size = len(maze.visited)
    while not maze._carve_done:
        maze._carve_step()
        assert len(maze.visited) >= prev_size
        prev_size = len(maze.visited)


def test_maze_connectivity():
    """Perfect maze: BFS from ENTRANCE reaches every cell (no isolated regions)."""
    maze = Maze()
    _full_carve(maze)
    seen = {ENTRANCE}
    queue = deque([ENTRANCE])
    while queue:
        r, c = queue.popleft()
        for dr, dc in maze.passages[r][c]:
            nb = (r + dr, c + dc)
            if nb not in seen:
                seen.add(nb)
                queue.append(nb)
    assert len(seen) == COLS * ROWS


def test_passages_are_bidirectional():
    """Every carved passage is stored in both directions."""
    maze = Maze()
    _full_carve(maze)
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in maze.passages[r][c]:
                assert (-dr, -dc) in maze.passages[r + dr][c + dc], (
                    f"Passage ({r},{c})→({r+dr},{c+dc}) not reciprocated"
                )


def test_passages_stay_in_bounds():
    """All passage destinations are within the grid."""
    maze = Maze()
    _full_carve(maze)
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in maze.passages[r][c]:
                nr, nc = r + dr, c + dc
                assert 0 <= nr < ROWS and 0 <= nc < COLS


# ---------------------------------------------------------------------------
# Solve path tests
# ---------------------------------------------------------------------------

def test_solve_path_endpoints():
    """BFS path starts at ENTRANCE and ends at EXIT."""
    maze = Maze()
    _full_carve(maze)
    path = maze._compute_solve_path()
    assert path[0] == ENTRANCE
    assert path[-1] == EXIT


def test_solve_path_follows_passages():
    """Every consecutive pair in the path shares a carved passage."""
    maze = Maze()
    _full_carve(maze)
    path = maze._compute_solve_path()
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i + 1]
        dr, dc = r2 - r1, c2 - c1
        assert (dr, dc) in maze.passages[r1][c1], (
            f"No passage between {path[i]} and {path[i+1]}"
        )


def test_solve_path_nonempty():
    """Path has at least 2 cells (ENTRANCE != EXIT on a 32×16 grid)."""
    maze = Maze()
    _full_carve(maze)
    path = maze._compute_solve_path()
    assert len(path) >= 2


# ---------------------------------------------------------------------------
# Randomness / determinism tests
# ---------------------------------------------------------------------------

def test_deterministic_with_same_seed():
    """Same random seed produces an identical maze."""
    def passages_snapshot(seed):
        random.seed(seed)
        m = Maze()
        _full_carve(m)
        random.seed()
        return tuple(
            tuple(sorted(m.passages[r][c]))
            for r in range(ROWS)
            for c in range(COLS)
        )

    assert passages_snapshot(42) == passages_snapshot(42)


def test_different_seeds_give_different_mazes():
    """Different seeds (overwhelmingly) produce different mazes."""
    def passages_snapshot(seed):
        random.seed(seed)
        m = Maze()
        _full_carve(m)
        random.seed()
        return tuple(
            tuple(sorted(m.passages[r][c]))
            for r in range(ROWS)
            for c in range(COLS)
        )

    assert passages_snapshot(1) != passages_snapshot(2)


# ---------------------------------------------------------------------------
# Phase helper and constants
# ---------------------------------------------------------------------------

def test_phase_constants_sum_to_screensaver_duration():
    """Phase durations add up to 45 s (SCREENSAVER_DURATION in orchestrator)."""
    assert CARVE_SECS + SOLVE_SECS + HOLD_SECS == 45


def test_phase_for():
    """_phase_for maps elapsed time to the correct phase."""
    assert Maze._phase_for(0) == 'carve'
    assert Maze._phase_for(CARVE_SECS - 0.001) == 'carve'
    assert Maze._phase_for(CARVE_SECS) == 'solve'
    assert Maze._phase_for(CARVE_SECS + SOLVE_SECS - 0.001) == 'solve'
    assert Maze._phase_for(CARVE_SECS + SOLVE_SECS) == 'hold'
    assert Maze._phase_for(CARVE_SECS + SOLVE_SECS + HOLD_SECS) == 'hold'


def test_carve_step_noop_when_done():
    """_carve_step is a no-op after carve completes."""
    maze = Maze()
    _full_carve(maze)
    visited_before = set(maze.visited)
    passages_before = [set(maze.passages[r][c]) for r in range(ROWS) for c in range(COLS)]
    maze._carve_step()
    assert maze.visited == visited_before
    passages_after = [set(maze.passages[r][c]) for r in range(ROWS) for c in range(COLS)]
    assert passages_after == passages_before

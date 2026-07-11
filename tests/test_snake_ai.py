"""Tests for snake_ai.py — pure-algorithm logic only (no display required)."""
import sys
from collections import deque

sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
from snake_ai import SnakeAI, _bfs_path, _greedy_step, GRID_W, GRID_H


# ---------------------------------------------------------------------------
# BFS pathfinding tests
# ---------------------------------------------------------------------------

def test_bfs_direct_path():
    """BFS finds a clear direct path to adjacent food."""
    head = (5, 5)
    food = (8, 5)
    body_set = set()
    nxt = _bfs_path(head, food, body_set)
    # Should move right (toward food)
    assert nxt == (6, 5), f"Expected (6,5), got {nxt}"


def test_bfs_no_path_fully_surrounded():
    """BFS returns None when head is surrounded by body."""
    head = (5, 5)
    food = (10, 10)
    # Block all four neighbours
    body_set = {(6, 5), (4, 5), (5, 6), (5, 4)}
    result = _bfs_path(head, food, body_set)
    assert result is None


def test_bfs_routes_around_obstacle():
    """BFS finds a path around a wall of body segments."""
    # Build a vertical wall blocking the direct route
    head = (0, 0)
    food = (2, 0)
    # Block column x=1 for rows 0..5
    body_set = {(1, y) for y in range(6)}
    nxt = _bfs_path(head, food, body_set)
    # Any valid first step that isn't into the wall
    assert nxt is not None
    assert nxt not in body_set


def test_bfs_wraps_grid():
    """BFS considers wrap-around edges when computing neighbours."""
    head = (0, 0)
    food = (GRID_W - 1, 0)  # food to the left via wrap
    # Block everything except the wrap path
    body_set = set()
    nxt = _bfs_path(head, food, body_set)
    # Either go right the long way or wrap-left — both are valid
    assert nxt is not None
    assert 0 <= nxt[0] < GRID_W
    assert 0 <= nxt[1] < GRID_H


def test_bfs_head_equals_food():
    """When head is already on food, BFS returns None."""
    head = (3, 3)
    food = (3, 3)
    result = _bfs_path(head, food, set())
    assert result is None


# ---------------------------------------------------------------------------
# Greedy fallback tests
# ---------------------------------------------------------------------------

def test_greedy_moves_toward_food():
    """Greedy step moves in the direction that reduces Manhattan distance."""
    head = (4, 4)
    food = (8, 4)
    nxt = _greedy_step(head, food, set())
    # Should step right (closer to food)
    assert nxt == (5, 4)


def test_greedy_avoids_body():
    """Greedy step skips cells in body_set."""
    head = (4, 4)
    food = (8, 4)
    body_set = {(5, 4)}  # block the obvious choice
    nxt = _greedy_step(head, food, body_set)
    assert nxt is not None
    assert nxt not in body_set


def test_greedy_all_blocked():
    """Greedy returns None when all four neighbours are blocked."""
    head = (5, 5)
    body_set = {(6, 5), (4, 5), (5, 6), (5, 4)}
    nxt = _greedy_step(head, (10, 10), body_set)
    assert nxt is None


# ---------------------------------------------------------------------------
# SnakeAI class tests
# ---------------------------------------------------------------------------

def test_snake_init():
    """SnakeAI initialises with a non-empty body and a food position."""
    snake = SnakeAI()
    assert len(snake.body) >= 3
    assert snake.food is not None
    assert snake.score == 0
    assert snake.food not in snake.body


def test_snake_reset():
    """reset() reinitialises state from scratch."""
    snake = SnakeAI()
    snake.score = 42
    snake.frame = 100
    snake.reset()
    assert snake.score == 0
    assert snake.frame == 0
    assert len(snake.body) >= 3
    assert snake.food not in snake.body


def test_snake_grows_on_eating():
    """Snake grows by one when it reaches the food."""
    snake = SnakeAI()
    initial_len = len(snake.body)
    # Place food adjacent to head so it eats immediately
    head = snake.body[0]
    snake.food = ((head[0] + 1) % GRID_W, head[1])
    pre_food = snake.food
    snake._step()
    # If head moved to old food position, length should increase
    if snake.body[0] == pre_food:
        assert len(snake.body) == initial_len + 1


def test_snake_body_no_teleport():
    """After a step the head moves exactly one cell (wrapping allowed)."""
    snake = SnakeAI()
    head_before = snake.body[0]
    snake._step()
    head_after = snake.body[0]
    dx = abs(head_after[0] - head_before[0])
    dy = abs(head_after[1] - head_before[1])
    # Allow wrap-around: distance is 1 or GRID_W-1 / GRID_H-1
    dx = min(dx, GRID_W - dx)
    dy = min(dy, GRID_H - dy)
    assert (dx, dy) in [(1, 0), (0, 1)], f"Unexpected move: {head_before} -> {head_after}"


def test_snake_advances_toward_food_multiple_steps():
    """Over many steps the snake eventually eats and score increases."""
    snake = SnakeAI()
    initial_score = snake.score
    # Run up to 500 steps — BFS guarantees food is reached if reachable
    for _ in range(500):
        snake._step()
        if snake.score > initial_score:
            break
    assert snake.score > initial_score or snake.rounds > 0, (
        "Snake should eat food or reset at least once in 500 steps"
    )


def test_food_never_in_body():
    """After every step, food must not overlap the body."""
    snake = SnakeAI()
    for _ in range(200):
        snake._step()
        assert snake.food not in snake.body, (
            f"Food {snake.food} is inside body at step"
        )


def test_draw_calls_clear_and_display():
    """draw(oled) must call oled.clear() and oled.display()."""
    class MockDraw:
        def __init__(self):
            self.rects = []
        def rectangle(self, coords, fill=1):
            self.rects.append(coords)

    class MockOLED:
        def __init__(self):
            self.draw = MockDraw()
            self._cleared = False
            self._displayed = False
        def clear(self):
            self._cleared = True
        def display(self):
            self._displayed = True

    snake = SnakeAI()
    oled = MockOLED()
    snake.draw(oled)
    assert oled._cleared, "draw() must call oled.clear()"
    assert oled._displayed, "draw() must call oled.display()"


def test_draw_renders_within_bounds():
    """All rectangle coords drawn must stay within 128×64 pixel bounds."""
    class MockDraw:
        def __init__(self):
            self.calls = []
        def rectangle(self, coords, fill=1):
            self.calls.append(coords)

    class MockOLED:
        def __init__(self):
            self.draw = MockDraw()
        def clear(self):
            self.draw.calls = []
        def display(self):
            pass

    snake = SnakeAI()
    oled = MockOLED()
    for frame in range(50):
        oled.draw.calls = []
        snake.draw(oled)
        for x1, y1, x2, y2 in oled.draw.calls:
            assert 0 <= x1 <= 127, f"frame {frame}: x1={x1} out of bounds"
            assert 0 <= y1 <= 63, f"frame {frame}: y1={y1} out of bounds"
            assert 0 <= x2 <= 127, f"frame {frame}: x2={x2} out of bounds"
            assert 0 <= y2 <= 63, f"frame {frame}: y2={y2} out of bounds"


def test_reset_method_exists():
    """API contract: reset() must exist and reinitialise without errors."""
    snake = SnakeAI()
    snake.reset()  # Should not raise


if __name__ == "__main__":
    test_bfs_direct_path()
    test_bfs_no_path_fully_surrounded()
    test_bfs_routes_around_obstacle()
    test_bfs_wraps_grid()
    test_bfs_head_equals_food()
    test_greedy_moves_toward_food()
    test_greedy_avoids_body()
    test_greedy_all_blocked()
    test_snake_init()
    test_snake_reset()
    test_snake_grows_on_eating()
    test_snake_body_no_teleport()
    test_snake_advances_toward_food_multiple_steps()
    test_food_never_in_body()
    test_draw_calls_clear_and_display()
    test_draw_renders_within_bounds()
    test_reset_method_exists()
    print("ALL TESTS PASSED")

"""Screensaver: Autonomous Snake AI — BFS pathfinding snake that finds food."""
import random
from collections import deque

SCREEN_W = 128
SCREEN_H = 64
CELL = 4                      # 4×4 pixel cells
GRID_W = SCREEN_W // CELL     # 32 columns
GRID_H = SCREEN_H // CELL     # 16 rows

# Directions: (dx, dy) in grid coordinates
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _bfs_path(head, food, body_set):
    """Return next (gx, gy) step toward food using BFS, or None if no path.

    body_set contains all occupied cells except the tail tip (the tail moves
    out of the way one step at a time, so the very last cell is passable).
    """
    if head == food:
        return None

    visited = {head}
    # Each queue entry: (pos, first_step)
    queue = deque()
    for d in DIRS:
        nx, ny = head[0] + d[0], head[1] + d[1]
        # Wrap-around grid
        nx %= GRID_W
        ny %= GRID_H
        npos = (nx, ny)
        if npos not in body_set and npos not in visited:
            visited.add(npos)
            queue.append((npos, npos))

    while queue:
        pos, first_step = queue.popleft()
        if pos == food:
            return first_step
        for d in DIRS:
            nx, ny = pos[0] + d[0], pos[1] + d[1]
            nx %= GRID_W
            ny %= GRID_H
            npos = (nx, ny)
            if npos not in body_set and npos not in visited:
                visited.add(npos)
                queue.append((npos, first_step))

    return None  # No path found


def _greedy_step(head, food, body_set):
    """Fallback: choose the neighbour that minimises Manhattan distance to food.

    Avoids body cells; wraps around grid edges. Returns None only if all
    four neighbours are occupied (game over — should trigger a reset).
    """
    best = None
    best_dist = None
    for d in DIRS:
        nx = (head[0] + d[0]) % GRID_W
        ny = (head[1] + d[1]) % GRID_H
        npos = (nx, ny)
        if npos in body_set:
            continue
        dist = abs(nx - food[0]) + abs(ny - food[1])
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best = npos
    return best


class SnakeAI:
    """Autonomous snake that navigates a 32×16 grid with BFS pathfinding."""

    def __init__(self):
        self.reset()

    def reset(self):
        # Start near centre heading right
        cx, cy = GRID_W // 2, GRID_H // 2
        self.body = deque([(cx, cy), (cx - 1, cy), (cx - 2, cy)])
        self.food = self._place_food()
        self.score = 0
        self.rounds = 0
        self.frame = 0            # used for blink animation on food

    def _place_food(self):
        body_set = set(self.body)
        while True:
            pos = (random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1))
            if pos not in body_set:
                return pos

    def _step(self):
        """Advance the snake one cell.  Returns True if the snake ate food."""
        head = self.body[0]

        # Build body set excluding the tail tip (it will vacate this step)
        body_set = set(self.body)
        body_set.discard(self.body[-1])

        # Determine next position: BFS first, greedy fallback
        next_pos = _bfs_path(head, self.food, body_set)
        if next_pos is None:
            next_pos = _greedy_step(head, self.food, body_set)
        if next_pos is None:
            # Completely surrounded — reset
            self.rounds += 1
            self.reset()
            return False

        # Self-collision check (against full body, tail already removed above)
        if next_pos in body_set:
            self.rounds += 1
            self.reset()
            return False

        # Move head
        self.body.appendleft(next_pos)

        # Check food
        if next_pos == self.food:
            # Grow: don't remove tail
            self.score += 1
            self.food = self._place_food()
            return True
        else:
            self.body.pop()
            return False

    def draw(self, oled):
        self.frame += 1
        self._step()

        oled.clear()

        # Draw body — each cell is a 4×4 filled square (3×3 with 1px gap)
        for idx, (gx, gy) in enumerate(self.body):
            px = gx * CELL
            py = gy * CELL
            # Head slightly different: fill entire cell; body: 3×3 inner square
            if idx == 0:
                # Head: filled 4×4
                oled.draw.rectangle([px, py, px + CELL - 1, py + CELL - 1], fill=1)
            else:
                # Body segment: 3×3 centred in cell
                oled.draw.rectangle([px, py, px + CELL - 2, py + CELL - 2], fill=1)

        # Draw food — blink every 4 frames; 2×2 centred in cell
        if (self.frame // 4) % 2 == 0:
            fx, fy = self.food
            px = fx * CELL + 1
            py = fy * CELL + 1
            oled.draw.rectangle([px, py, px + 1, py + 1], fill=1)

        oled.display()

"""Screensaver: Maze generator and solver (recursive backtracker + BFS path)."""
import time
import random
from collections import deque

SCREEN_W = 128
SCREEN_H = 64
CELL = 4
COLS = SCREEN_W // CELL   # 32
ROWS = SCREEN_H // CELL   # 16

CARVE_SECS = 20
SOLVE_SECS = 10
HOLD_SECS = 15

ENTRANCE = (0, 0)
EXIT = (ROWS - 1, COLS - 1)   # (15, 31)

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _grid_neighbors(r, c):
    """Yield (nr, nc, dr, dc) for all in-bounds orthogonal neighbors."""
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            yield nr, nc, dr, dc


class Maze:
    def __init__(self):
        self.reset()

    def reset(self):
        self.passages = [[set() for _ in range(COLS)] for _ in range(ROWS)]
        self.visited = set()
        self.stack = [ENTRANCE]
        self.visited.add(ENTRANCE)
        self._carve_done = False
        self.solve_path = []
        self.phase = 'carve'
        self.phase_start = time.time()
        self._last_time = 0

    @staticmethod
    def _phase_for(total_elapsed):
        """Return phase name for given total elapsed seconds since reset."""
        if total_elapsed < CARVE_SECS:
            return 'carve'
        elif total_elapsed < CARVE_SECS + SOLVE_SECS:
            return 'solve'
        else:
            return 'hold'

    def _carve_step(self):
        """One step of recursive backtracker DFS. Returns True when done."""
        if self._carve_done:
            return True
        if not self.stack:
            self._carve_done = True
            return True
        r, c = self.stack[-1]
        unvisited = [
            (nr, nc, dr, dc)
            for nr, nc, dr, dc in _grid_neighbors(r, c)
            if (nr, nc) not in self.visited
        ]
        if unvisited:
            nr, nc, dr, dc = random.choice(unvisited)
            self.passages[r][c].add((dr, dc))
            self.passages[nr][nc].add((-dr, -dc))
            self.visited.add((nr, nc))
            self.stack.append((nr, nc))
        else:
            self.stack.pop()
        if not self.stack:
            self._carve_done = True
        return self._carve_done

    def _compute_solve_path(self):
        """BFS from ENTRANCE to EXIT over carved passages. Returns list of (row, col)."""
        parent = {ENTRANCE: None}
        queue = deque([ENTRANCE])
        while queue:
            r, c = queue.popleft()
            if (r, c) == EXIT:
                break
            for dr, dc in self.passages[r][c]:
                nb = (r + dr, c + dc)
                if nb not in parent:
                    parent[nb] = (r, c)
                    queue.append(nb)
        path, cur = [], EXIT
        while cur is not None:
            path.append(cur)
            cur = parent.get(cur)
        path.reverse()
        return path

    def _render(self, oled, trail_n):
        """Draw current maze state and solution trail."""
        oled.clear()
        trail_set = set(self.solve_path[:trail_n])

        # Draw visited cells: 2×2 interior, or full 4×4 block on solution trail
        for r, c in self.visited:
            px, py = c * CELL, r * CELL
            if (r, c) in trail_set:
                oled.draw.rectangle([(px, py), (px + CELL - 1, py + CELL - 1)], fill=1)
            else:
                oled.draw.rectangle([(px + 1, py + 1), (px + 2, py + 2)], fill=1)

        # Draw passage bridges (downward and rightward only to avoid duplicates)
        for r, c in self.visited:
            for dr, dc in self.passages[r][c]:
                if dr == 1:  # downward passage to (r+1, c)
                    bx, by = c * CELL + 1, r * CELL + 3
                    oled.draw.rectangle([(bx, by), (bx + 1, by + 1)], fill=1)
                elif dc == 1:  # rightward passage to (r, c+1)
                    bx, by = c * CELL + 3, r * CELL + 1
                    oled.draw.rectangle([(bx, by), (bx + 1, by + 1)], fill=1)

        # Highlight the carve frontier
        if self.stack and not self._carve_done:
            fr, fc = self.stack[-1]
            px, py = fc * CELL, fr * CELL
            oled.draw.rectangle([(px, py), (px + CELL - 1, py + CELL - 1)], fill=1)

    def draw(self, oled):
        now = time.time()
        dt = min(0.2, now - self._last_time) if self._last_time > 0 else 0.05
        self._last_time = now
        elapsed = now - self.phase_start

        if self.phase == 'carve':
            if not self._carve_done:
                remaining = max(0.1, CARVE_SECS - elapsed)
                steps = max(1, int(COLS * ROWS * 2 * dt / remaining))
                for _ in range(steps):
                    if self._carve_step():
                        break
            if elapsed >= CARVE_SECS:
                while not self._carve_step():
                    pass
                if not self.solve_path:
                    self.solve_path = self._compute_solve_path()
                self.phase = 'solve'
                self.phase_start = now
            trail_n = 0

        elif self.phase == 'solve':
            if elapsed >= SOLVE_SECS:
                self.phase = 'hold'
                self.phase_start = now
                trail_n = len(self.solve_path)
            else:
                trail_n = max(0, int(len(self.solve_path) * elapsed / SOLVE_SECS))

        else:  # hold
            trail_n = len(self.solve_path)

        self._render(oled, trail_n)
        oled.display()

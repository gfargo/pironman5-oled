"""Conway's Game of Life — random seed, evolves until stable then reseeds."""
import random

SCREEN_W = 128
SCREEN_H = 64


class GameOfLife:
    def __init__(self):
        self.grid = [[0] * SCREEN_W for _ in range(SCREEN_H)]
        self.generation = 0
        self.stale_count = 0
        self.last_alive = 0
        self._seed()

    def _seed(self):
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                self.grid[y][x] = 1 if random.random() < 0.3 else 0
        self.generation = 0
        self.stale_count = 0

    def _count_neighbors(self, y, x):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                ny, nx = (y + dy) % SCREEN_H, (x + dx) % SCREEN_W
                count += self.grid[ny][nx]
        return count

    def step(self):
        new_grid = [[0] * SCREEN_W for _ in range(SCREEN_H)]
        alive = 0
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                n = self._count_neighbors(y, x)
                if self.grid[y][x]:
                    new_grid[y][x] = 1 if n in (2, 3) else 0
                else:
                    new_grid[y][x] = 1 if n == 3 else 0
                alive += new_grid[y][x]
        self.grid = new_grid
        self.generation += 1

        # Detect stagnation
        if abs(alive - self.last_alive) < 3:
            self.stale_count += 1
        else:
            self.stale_count = 0
        self.last_alive = alive

        # Reseed if stagnant or dead
        if self.stale_count > 30 or alive < 5:
            self._seed()

    def render(self, oled):
        oled.clear()
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                if self.grid[y][x]:
                    oled.draw.point((x, y), fill=1)
        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)

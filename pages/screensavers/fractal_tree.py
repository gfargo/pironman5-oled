"""Fractal tree — recursive branches that sway in the wind."""
import math
import random
from dataclasses import dataclass, field

SCREEN_W = 128
SCREEN_H = 64

INITIAL_DEPTH = 6
MAX_DEPTH = 8
GROWTH_SPEED = 0.04


@dataclass
class Branch:
    """A single branch segment in the fractal tree."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    depth: int
    angle: float
    length: float


@dataclass
class GrowthState:
    """Tracks animation progress for the growth-front branches."""
    progress: dict = field(default_factory=dict)  # branch_index -> progress [0.0, 1.0]
    current_depth: int = 7
    complete: bool = False


class FractalTree:
    def __init__(self):
        self.reset()

    def _compute_tree(self) -> list:
        """Pre-compute all branch segments using seed 42.

        Returns a flat list of Branch objects ordered by depth-first recursion.
        Depth 1 is the trunk, depth MAX_DEPTH (8) is the outermost leaves.
        """
        random.seed(42)
        branches: list = []
        self._recurse_tree(
            x=SCREEN_W // 2,
            y=SCREEN_H - 1,
            angle=math.pi / 2,
            length=18,
            depth=1,
            branches=branches,
        )
        random.seed()  # Restore entropy
        return branches

    def _recurse_tree(self, x: float, y: float, angle: float, length: float, depth: int, branches: list) -> None:
        """Recursive helper that builds Branch objects without drawing."""
        if depth > MAX_DEPTH or length < 2:
            return

        # Compute endpoint using angle (no wind displacement)
        end_x = x + math.cos(angle) * length
        end_y = y - math.sin(angle) * length

        # Store this branch
        branches.append(Branch(
            start_x=x,
            start_y=y,
            end_x=end_x,
            end_y=end_y,
            depth=depth,
            angle=angle,
            length=length,
        ))

        # Branch into two children (mirrors existing logic)
        new_length = length * random.uniform(0.65, 0.75)
        spread = random.uniform(0.3, 0.5)
        self._recurse_tree(end_x, end_y, angle + spread, new_length, depth + 1, branches)
        self._recurse_tree(end_x, end_y, angle - spread, new_length, depth + 1, branches)

    def _init_growth_state(self) -> GrowthState:
        """Initialize growth state from pre-computed branches.

        Branches at depths 1–INITIAL_DEPTH are implicitly complete (not tracked).
        Depth 7 branches form the initial growth front (progress 0.0).
        Depth 8 branches are not yet tracked (they start after depth 7 completes).
        """
        progress = {}
        for i, branch in enumerate(self.branches):
            if branch.depth == INITIAL_DEPTH + 1:  # depth 7
                progress[i] = 0.0
        return GrowthState(progress=progress, current_depth=INITIAL_DEPTH + 1, complete=False)

    def _advance_growth(self) -> None:
        """Advance the growth front by GROWTH_SPEED per frame.

        - Increments all progress values for current_depth, clamped to 1.0
        - When all depth-7 branches complete, transitions to depth 8
        - When all depth-8 branches complete, sets complete = True
        - No-ops if growth is already complete
        """
        if self.growth_state.complete:
            return

        # Increment progress for all branches at the current growth depth
        for i in list(self.growth_state.progress.keys()):
            if self.branches[i].depth == self.growth_state.current_depth:
                self.growth_state.progress[i] = min(1.0, self.growth_state.progress[i] + GROWTH_SPEED)

        # Check if all branches at current depth are complete
        all_complete = all(
            self.growth_state.progress[i] >= 1.0
            for i in self.growth_state.progress
            if self.branches[i].depth == self.growth_state.current_depth
        )

        if all_complete:
            if self.growth_state.current_depth == INITIAL_DEPTH + 1:  # depth 7 done
                # Transition to depth 8: seed depth-8 branches at 0.0
                self.growth_state.current_depth = MAX_DEPTH
                for i, branch in enumerate(self.branches):
                    if branch.depth == MAX_DEPTH:
                        self.growth_state.progress[i] = 0.0
            elif self.growth_state.current_depth == MAX_DEPTH:  # depth 8 done
                self.growth_state.complete = True

    def _render_frame(self, oled):
        """Render all visible branches with wind displacement and clipping.

        For each branch:
        - Depths 1-INITIAL_DEPTH render fully (t=1.0)
        - Growth-front branches render partially based on progress
        - Wind displaces the branch angle (same formula as legacy _draw_branch)
        - All coordinates are clipped to display bounds before drawing
        """
        oled.clear()

        for i, branch in enumerate(self.branches):
            # Determine visibility and progress
            if branch.depth <= INITIAL_DEPTH:
                t = 1.0  # Fully visible
            elif i in self.growth_state.progress:
                t = self.growth_state.progress[i]
                if t <= 0.0:
                    continue
            else:
                continue  # Not yet started

            # Apply wind displacement to the branch angle
            # Formula matches existing _draw_branch: sin(phase + y * 0.05) * 0.15 * (1 - y/H)
            wind = math.sin(self.wind_phase + branch.start_y * 0.05) * 0.15 * (1 - branch.start_y / SCREEN_H)

            # Compute wind-displaced endpoint (recompute from start using angle + wind)
            ex = branch.start_x + math.cos(branch.angle + wind) * branch.length * t
            ey = branch.start_y - math.sin(branch.angle + wind) * branch.length * t

            # Clip all coordinates to display bounds
            sx = max(0, min(127, int(branch.start_x)))
            sy = max(0, min(63, int(branch.start_y)))
            ex = max(0, min(127, int(ex)))
            ey = max(0, min(63, int(ey)))

            oled.draw.line([(sx, sy), (ex, ey)], fill=1)

        oled.display()

    def reset(self):
        self.branches = self._compute_tree()
        self.growth_state = self._init_growth_state()
        self.wind_phase = 0.0
        self.wind_speed = random.uniform(0.3, 0.8)

    def draw(self, oled):
        self.wind_phase += self.wind_speed * 0.05
        self._advance_growth()
        self._render_frame(oled)

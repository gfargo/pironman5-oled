# Design Document: Fractal Tree Growth Animation

## Overview

This design enhances the FractalTree screensaver to pre-compute full tree geometry on `reset()`, render depths 1–6 immediately on the first frame, and animate depths 7–8 growing pixel-by-pixel across subsequent frames. Wind sway runs continuously. The implementation stays within the existing `reset()` + `draw(oled)` interface contract.

## Architecture

The enhanced FractalTree screensaver separates tree geometry computation from frame-by-frame rendering. On `reset()`, the full tree structure (all branches at all depths 1–8) is pre-computed and stored as a static data structure. A growth state machine then controls how much of each branch is visible on any given frame.

```
┌─────────────────────────────────────────────────────┐
│                    FractalTree                        │
├─────────────────────────────────────────────────────┤
│  reset()                                             │
│    ├── Compute full tree geometry (seed 42)          │
│    ├── Mark depths 1–6 as fully grown                │
│    └── Initialize growth front at depth 7            │
│                                                      │
│  draw(oled)                                          │
│    ├── Advance wind phase                            │
│    ├── Advance growth state (if not complete)        │
│    ├── Clear OLED buffer                             │
│    ├── Render all visible branches with wind + clip  │
│    └── oled.display()                                │
└─────────────────────────────────────────────────────┘
```

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pre-compute full geometry | Store all branch endpoints at init | Avoids re-seeding `random` every frame; O(1) per-frame cost |
| Growth as progress floats | Each branch has a `progress: float [0.0, 1.0]` | Simple linear interpolation for partial rendering |
| Depth-level growth fronts | All branches at depth N complete before depth N+1 starts | Visually coherent; simpler state than per-branch scheduling |
| Wind applied at render time | Wind displaces endpoints during drawing, not stored | Keeps geometry pure; wind is a view-layer concern |
| Coordinate clipping | `min(max(x, 0), 127)` / `min(max(y, 0), 63)` | Lightweight; no trigonometric line-clip needed for aesthetic |

## Components and Interfaces

### 1. Branch Data Structure

Each branch is a precomputed record containing the geometry needed for rendering:

```python
@dataclass
class Branch:
    """A single branch segment in the fractal tree."""
    start_x: float        # Parent junction x
    start_y: float        # Parent junction y
    end_x: float          # Full-length endpoint x
    end_y: float          # Full-length endpoint y
    depth: int            # Recursion depth (1 = trunk, 8 = leaf)
    angle: float          # Branch angle in radians
    length: float         # Full segment length in pixels
```

Branches are stored in a flat list, ordered by depth. This allows efficient iteration during both growth advancement and rendering.

### 2. Growth State Machine

```python
@dataclass
class GrowthState:
    """Tracks animation progress for the growth-front branches."""
    progress: dict[int, float]   # branch_index → progress [0.0, 1.0]
    current_depth: int           # The depth level currently growing (7 or 8)
    complete: bool               # True when all depth-8 branches are at 1.0
```

State transitions:
- `current_depth = 7`: All depth-7 branches advance by `GROWTH_SPEED` per frame
- When all depth-7 progress values reach 1.0 → `current_depth = 8`
- When all depth-8 progress values reach 1.0 → `complete = True`

### 3. Geometry Computation (one-time on reset)

```python
def _compute_tree(self) -> list[Branch]:
    """Pre-compute all branch segments using seed 42."""
    random.seed(42)
    branches = []
    self._recurse(
        x=SCREEN_W // 2,
        y=SCREEN_H - 1,
        angle=math.pi / 2,
        length=18,
        depth=1,
        max_depth=8,
        branches=branches,
    )
    random.seed()  # Restore entropy
    return branches
```

The recursion mirrors the existing `_draw_branch` logic but stores geometry instead of drawing. Each recursive call appends a `Branch` to the list and recurses for child branches.

### 4. Rendering Pipeline (per frame)

```python
def _render_frame(self, oled):
    """Render all visible branches with wind displacement and clipping."""
    oled.clear()
    for i, branch in enumerate(self.branches):
        # Determine visibility
        if branch.depth <= INITIAL_DEPTH:
            t = 1.0  # Fully visible
        elif i in self.growth_state.progress:
            t = self.growth_state.progress[i]
            if t <= 0.0:
                continue
        else:
            continue  # Not yet started

        # Interpolate endpoint
        cur_x = branch.start_x + (branch.end_x - branch.start_x) * t
        cur_y = branch.start_y + (branch.end_y - branch.start_y) * t

        # Apply wind displacement
        wind = math.sin(self.wind_phase + branch.start_y * 0.05) * 0.15 * (1 - branch.start_y / SCREEN_H)
        dx = math.cos(branch.angle + wind) - math.cos(branch.angle)
        dy = -math.sin(branch.angle + wind) + math.sin(branch.angle)
        sx = branch.start_x + dx * branch.length
        sy = branch.start_y + dy * branch.length
        ex = cur_x + dx * branch.length * t
        ey = cur_y + dy * branch.length * t

        # Clip to display bounds
        sx = max(0, min(127, int(sx)))
        sy = max(0, min(63, int(sy)))
        ex = max(0, min(127, int(ex)))
        ey = max(0, min(63, int(ey)))

        oled.draw.line([(sx, sy), (ex, ey)], fill=1)

    oled.display()
```

> Note: The actual wind application will replicate the existing formula (`sin(wind_offset + y * 0.05) * 0.15 * (1 - y / SCREEN_H)`) applied to each branch's angle during rendering. The pseudocode above shows the concept; implementation will match the current behavior exactly for depths 1–6.

### 5. Wind Animation

Wind phase advances unconditionally on every `draw()` call:

```python
self.wind_phase += self.wind_speed * 0.05
```

Wind speed is set to a fixed value (within the existing `[0.3, 0.8]` range) on `reset()` — deterministic for the session but varying between sessions.

## Interfaces

### Public API (unchanged)

```python
class FractalTree:
    def __init__(self):
        """Parameterless constructor. Calls reset() internally."""

    def reset(self):
        """Reinitialize all state. Called by Orchestrator at screensaver start."""

    def draw(self, oled):
        """Advance state + render one frame. Called repeatedly by Orchestrator."""
```

### Internal State

| Attribute | Type | Purpose |
|-----------|------|---------|
| `branches` | `list[Branch]` | Pre-computed full tree geometry |
| `growth_state` | `GrowthState` | Per-branch animation progress |
| `wind_phase` | `float` | Current wind oscillation phase |
| `wind_speed` | `float` | Wind oscillation rate (fixed per session) |

## Data Models

### Tree Geometry Storage

The tree for depth 8 with binary branching produces `2^8 - 1 = 255` branch segments. At ~48 bytes per Branch (6 floats + 1 int + padding), total memory is ~12 KB — negligible on the Pi 5's 8 GB RAM.

### Growth Speed Tuning

```
INITIAL_DEPTH = 6
MAX_DEPTH = 8
GROWTH_SPEED = 0.04  # Progress per frame (0.0 → 1.0)

Frames to complete one depth level: 1.0 / 0.04 = 25 frames
At 15 FPS: 25 / 15 ≈ 1.7 seconds per depth level
Total growth time: ~3.4 seconds for depths 7 + 8
Hold time: 45 - 3.4 ≈ 41.6 seconds of fully-grown sway
```

This provides generous hold time while keeping growth perceptible. The `GROWTH_SPEED` constant can be tuned without changing any logic.

## Error Handling

| Scenario | Handling |
|----------|----------|
| `oled` object is None or invalid | Let exception propagate; Orchestrator's try/except catches it and skips to next page |
| `random.seed(42)` produces fewer branches than expected | Cannot happen — seed is deterministic with fixed recursion params |
| Branch coordinates overflow display bounds | Clamped via `max(0, min(bound, val))` before drawing |
| Growth state references invalid branch index | Cannot happen — indices computed at geometry time, immutable thereafter |
| Wind causes visual jitter at high offsets | Sine function is bounded; amplitude is `0.15 * height_factor` (max ~0.15 radians) |

## Performance Considerations

- **Per-frame cost**: One loop over 255 branches with float arithmetic + integer clipping. No recursion, no `random.seed()` calls during rendering.
- **Memory**: ~12 KB for branch geometry + growth state dict (max 128 entries for depths 7–8). Well within Pi 5 constraints.
- **Target frame rate**: The existing screensaver runs at whatever rate the Orchestrator calls `draw()` (typically 10–20 FPS). The simplified per-frame work (no recursion, no random reseeding) should be faster than the current implementation.

## Testing Strategy

- **Property-based tests** (using Hypothesis): Validate the 9 correctness properties below across randomized frame counts, verifying growth invariants, determinism, and bounds.
- **Unit tests** (pytest): Verify interface contract (reset/draw exist, parameterless constructor), rendering calls (mock oled receives clear/line/display), and specific timing examples (growth completes within N frames).
- **Manual visual testing**: Deploy to the Pi 5 OLED and observe growth animation aesthetics (organic feel, timing, wind continuity).

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Initial State Completeness

*For any* FractalTree instance after `reset()` is called, all branches at depths 1 through 6 SHALL have a growth progress of 1.0 (fully complete), and the growth front SHALL begin at depth 7.

**Validates: Requirements 1.1**

### Property 2: Deterministic Geometry

*For any* two independent calls to `reset()` on the same or different FractalTree instances, the computed branch geometry (start points, end points, angles, lengths) SHALL be identical.

**Validates: Requirements 1.3**

### Property 3: Growth Front Monotonic Advance

*For any* frame where growth is not complete, calling `draw()` SHALL increase the progress value of at least one growth-front branch (progress values are monotonically non-decreasing across frames).

**Validates: Requirements 2.1**

### Property 4: Branch Completion Triggers Child Extension

*For any* branch at depth 7 that reaches progress 1.0, subsequent `draw()` calls SHALL begin advancing progress on that branch's child branches at depth 8 (once all depth-7 branches are complete).

**Validates: Requirements 2.2, 2.4**

### Property 5: Partial Branch Interpolation

*For any* branch with progress `t` where `0 < t < 1`, the rendered endpoint SHALL equal `start + (end - start) * t` (linear interpolation), not the full endpoint.

**Validates: Requirements 2.3**

### Property 6: Depth Ordering Invariant

*For any* frame, if any depth-8 branch has progress > 0, then all depth-7 branches SHALL have progress equal to 1.0.

**Validates: Requirements 2.4**

### Property 7: Growth State Freezes at Completion

*For any* number of `draw()` calls after all depth-8 branches reach progress 1.0, the growth state (all progress values and current_depth) SHALL remain unchanged.

**Validates: Requirements 3.1**

### Property 8: Wind Phase Always Advances

*For any* `draw()` call regardless of growth state (growing or complete), the wind phase SHALL increase by a positive constant increment.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 9: Display Bounds Invariant

*For all* rendered line segments across all frames (at any growth progress and any wind phase), both start and end coordinates SHALL satisfy `0 ≤ x ≤ 127` and `0 ≤ y ≤ 63`.

**Validates: Requirements 6.1, 6.3**

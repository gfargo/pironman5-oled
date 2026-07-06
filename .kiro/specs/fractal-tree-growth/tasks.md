# Implementation Plan: Fractal Tree Growth Animation

## Overview

Refactor `pages/screensavers/fractal_tree.py` to pre-compute full tree geometry on `reset()`, render depths 1–6 immediately on the first frame, and animate depths 7–8 growing pixel-by-pixel via a growth state machine. Wind sway remains continuous. The public API (`__init__`, `reset`, `draw`) is unchanged.

## Tasks

- [x] 1. Define data structures and constants
  - [x] 1.1 Add `Branch` dataclass and `GrowthState` dataclass to `fractal_tree.py`
    - Define `Branch` with fields: `start_x`, `start_y`, `end_x`, `end_y`, `depth`, `angle`, `length`
    - Define `GrowthState` with fields: `progress` (dict mapping branch index to float), `current_depth` (int), `complete` (bool)
    - Add module-level constants: `INITIAL_DEPTH = 6`, `MAX_DEPTH = 8`, `GROWTH_SPEED = 0.04`
    - _Requirements: 1.1, 2.1, 3.3_

- [x] 2. Implement geometry pre-computation
  - [x] 2.1 Implement `_compute_tree()` method that recursively generates all `Branch` objects
    - Seed `random` with 42, recurse from trunk (depth 1) to `MAX_DEPTH` (8)
    - Mirror existing branching logic (spread, length scaling) but store `Branch` objects instead of drawing
    - Return a flat `list[Branch]` ordered by recursion (depth-first)
    - Restore `random.seed()` after computation
    - _Requirements: 1.3, 1.1_

  - [ ]* 2.2 Write property test for deterministic geometry (Property 2)
    - **Property 2: Deterministic Geometry**
    - **Validates: Requirements 1.3**

  - [x] 2.3 Implement `_init_growth_state()` that initializes `GrowthState` from computed branches
    - Set all branches at depths 1–6 as implicitly complete (not tracked in `progress` dict)
    - Add all depth-7 branch indices to `progress` dict with value `0.0`
    - Set `current_depth = 7`, `complete = False`
    - _Requirements: 1.1, 1.2, 2.4_

  - [ ]* 2.4 Write property test for initial state completeness (Property 1)
    - **Property 1: Initial State Completeness**
    - **Validates: Requirements 1.1**

- [x] 3. Implement growth state machine
  - [x] 3.1 Implement `_advance_growth()` method to progress the growth front
    - Increment all `progress` values in `growth_state.progress` for `current_depth` by `GROWTH_SPEED`
    - Clamp to `1.0` maximum
    - When all depth-7 branches reach `1.0`, transition `current_depth` to 8 and seed depth-8 branches at `0.0`
    - When all depth-8 branches reach `1.0`, set `complete = True`
    - Skip entirely if `growth_state.complete` is already `True`
    - _Requirements: 2.1, 2.2, 2.4, 3.1_

  - [ ]* 3.2 Write property test for monotonic growth advance (Property 3)
    - **Property 3: Growth Front Monotonic Advance**
    - **Validates: Requirements 2.1**

  - [ ]* 3.3 Write property test for depth ordering invariant (Property 6)
    - **Property 6: Depth Ordering Invariant**
    - **Validates: Requirements 2.4**

  - [ ]* 3.4 Write property test for growth state freeze at completion (Property 7)
    - **Property 7: Growth State Freezes at Completion**
    - **Validates: Requirements 3.1**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement rendering pipeline
  - [x] 5.1 Implement `_render_frame(oled)` method
    - Clear the OLED buffer
    - Iterate all branches: skip if not visible, use `t = 1.0` for depths ≤ `INITIAL_DEPTH`, use `progress[i]` for growth-front branches
    - Compute interpolated endpoint: `start + (end - start) * t`
    - Apply wind displacement using existing formula: `sin(wind_phase + y * 0.05) * 0.15 * (1 - y / SCREEN_H)`
    - Clip all coordinates to display bounds: `max(0, min(127, x))` and `max(0, min(63, y))`
    - Draw line segment via `oled.draw.line()`
    - Call `oled.display()`
    - _Requirements: 2.3, 4.1, 4.2, 6.1, 6.2, 6.3_

  - [ ]* 5.2 Write property test for partial branch interpolation (Property 5)
    - **Property 5: Partial Branch Interpolation**
    - **Validates: Requirements 2.3**

  - [ ]* 5.3 Write property test for display bounds invariant (Property 9)
    - **Property 9: Display Bounds Invariant**
    - **Validates: Requirements 6.1, 6.3**

- [x] 6. Wire public API methods
  - [x] 6.1 Rewrite `reset()` to call `_compute_tree()` and `_init_growth_state()`, set `wind_phase` and `wind_speed`
    - Initialize `self.branches = self._compute_tree()`
    - Initialize `self.growth_state = self._init_growth_state()`
    - Set `self.wind_phase = 0.0`
    - Set `self.wind_speed = random.uniform(0.3, 0.8)`
    - _Requirements: 5.1, 1.1, 1.3_

  - [x] 6.2 Rewrite `draw(oled)` to advance wind, advance growth, and call `_render_frame(oled)`
    - Advance `self.wind_phase += self.wind_speed * 0.05` unconditionally
    - Call `self._advance_growth()` (no-ops when complete)
    - Call `self._render_frame(oled)`
    - _Requirements: 4.3, 5.2, 5.4_

  - [x] 6.3 Update `__init__()` to call `self.reset()`
    - Maintain parameterless constructor contract
    - Remove old instance variables (`wind_offset`, etc.)
    - _Requirements: 5.3_

  - [ ]* 6.4 Write property test for wind phase always advances (Property 8)
    - **Property 8: Wind Phase Always Advances**
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All implementation targets the single file: `pironman5-oled/pages/screensavers/fractal_tree.py`
- Property tests should use `hypothesis` library and live in a `tests/` directory adjacent to the screensaver
- The existing public API (`__init__`, `reset`, `draw`) MUST remain unchanged — the Orchestrator depends on it
- Growth completes in ~50 frames (25 frames per depth level at `GROWTH_SPEED = 0.04`), leaving ~41s of hold time in the 45s window
- Total branch count: 255 segments (2⁸ − 1), ~12 KB memory — trivial on Pi 5

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.3"] },
    { "id": 2, "tasks": ["2.2", "2.4", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3"] },
    { "id": 6, "tasks": ["6.4"] }
  ]
}
```

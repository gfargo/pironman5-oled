# Requirements Document

## Introduction

Enhance the FractalTree screensaver so it renders a pre-formed tree on the first frame and continues growing additional branches smoothly over time. The tree starts at depth 6 (of a maximum 8), with depth-7 and depth-8 branches animating outward pixel-by-pixel across subsequent frames. Once full depth is reached, the tree holds its completed form with wind sway for the remainder of the 45-second screensaver window.

## Glossary

- **FractalTree**: The screensaver class responsible for rendering a recursive branching tree on the 128×64 monochrome OLED display.
- **Orchestrator**: The PageOrchestrator that calls `reset()` once per screensaver session and then calls `draw(oled)` repeatedly at the display refresh rate.
- **Depth**: The recursion level of branch generation. Depth 1 is the trunk, depth 8 is the outermost leaf-level branches.
- **Initial_Depth**: The recursion depth rendered fully on the first frame (depth 6).
- **Max_Depth**: The maximum recursion depth the tree grows to (depth 8).
- **Growth_Front**: The set of branches currently animating outward (partially drawn, extending over multiple frames).
- **Branch_Extension**: The pixel-by-pixel lengthening of a branch segment across consecutive draw calls.
- **Wind_Sway**: The sinusoidal lateral displacement applied to all branches, simulating wind.
- **Seed_42**: The fixed random seed used to produce a deterministic tree shape across frames.

## Requirements

### Requirement 1: Initial Tree State

**User Story:** As a viewer, I want to see a recognizable tree from the very first frame, so the screensaver is visually interesting immediately without a blank-screen growth delay.

#### Acceptance Criteria

1. WHEN `reset()` is called, THE FractalTree SHALL initialize internal state such that the first subsequent `draw(oled)` call renders branches at depth 1 through Initial_Depth (6) at full length.
2. WHEN the first `draw(oled)` call occurs after `reset()`, THE FractalTree SHALL display a tree with trunk and main branching structure visible (depths 1–6 fully drawn).
3. THE FractalTree SHALL use Seed_42 to generate a deterministic branch geometry so the tree shape is consistent across resets.

### Requirement 2: Smooth Branch Extension Animation

**User Story:** As a viewer, I want new branches to extend outward gradually like time-lapse footage, so the growth feels organic rather than branches popping into existence.

#### Acceptance Criteria

1. WHILE the tree has not reached Max_Depth, THE FractalTree SHALL extend Growth_Front branches by a fractional length increment on each `draw(oled)` call.
2. WHEN a Growth_Front branch reaches its full computed length, THE FractalTree SHALL mark that branch as complete and begin extending its child branches at the next depth level.
3. THE FractalTree SHALL render partially-extended branches as line segments from the parent junction to the current intermediate endpoint (not the final endpoint).
4. THE FractalTree SHALL animate depth-7 branches to completion before beginning depth-8 branch extension.

### Requirement 3: Growth Completion and Hold

**User Story:** As a viewer, I want the tree to reach its full form and hold steady with wind sway, so the completed tree is displayed for the remainder of the screensaver window.

#### Acceptance Criteria

1. WHEN all branches at Max_Depth (8) have reached full length, THE FractalTree SHALL stop advancing Growth_Front state on subsequent `draw(oled)` calls.
2. WHILE the tree has reached Max_Depth completion, THE FractalTree SHALL continue rendering the full tree with Wind_Sway animation on each `draw(oled)` call.
3. THE FractalTree SHALL complete growth from Initial_Depth to Max_Depth within a duration that allows visible hold time before the 45-second screensaver window ends.

### Requirement 4: Wind Animation Continuity

**User Story:** As a viewer, I want wind sway to be present throughout the entire screensaver, so the tree always feels alive regardless of growth state.

#### Acceptance Criteria

1. WHILE branches are still growing (Growth_Front is active), THE FractalTree SHALL apply Wind_Sway displacement to all rendered branches including partially-extended ones.
2. WHILE the tree is fully grown, THE FractalTree SHALL continue applying Wind_Sway displacement to all branches.
3. THE FractalTree SHALL advance the wind phase on every `draw(oled)` call regardless of growth state.

### Requirement 5: Interface Contract Preservation

**User Story:** As the Orchestrator, I want the FractalTree to maintain its existing `reset()` + `draw(oled)` interface, so no changes are needed to the orchestrator or screensaver registry.

#### Acceptance Criteria

1. THE FractalTree SHALL expose a `reset()` method that reinitializes all growth and animation state.
2. THE FractalTree SHALL expose a `draw(oled)` method that performs one frame update (advance state + render + display).
3. THE FractalTree SHALL not require any constructor arguments beyond the existing parameterless `__init__()`.
4. THE FractalTree SHALL clear the OLED buffer, render the current tree state, and call `oled.display()` within each `draw(oled)` invocation.

### Requirement 6: Display Constraints

**User Story:** As a developer, I want the tree to fit within the 128×64 pixel monochrome display, so no rendering occurs outside visible bounds.

#### Acceptance Criteria

1. THE FractalTree SHALL render all branch segments within the 128-pixel width and 64-pixel height of the OLED display.
2. THE FractalTree SHALL use monochrome pixel values (fill=1 for branches on a cleared display).
3. IF a computed branch endpoint falls outside the display bounds, THEN THE FractalTree SHALL clip the line segment at the display boundary.

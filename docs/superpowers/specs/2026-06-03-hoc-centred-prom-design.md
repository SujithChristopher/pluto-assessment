# HOC centred PROM — design

Date: 2026-06-03

## Goal

Make HOC PROM behave like FPS/WFE centred PROM:

- Center = midpoint of the best-of-3 averaged AROM range.
- Single-line cursor (no HOC mirror twin).
- AROM reference lines + a persistent resting (center) line.
- Trial must start at the center (start gate around center).
- Only active when AROM was actually completed (FPS gating); otherwise fall
  back to the existing symmetric HOC PROM display.

## Key insight

`_xpos(pos)` already returns `_dispsign * pos` for non-HOC and the
corner-anchored map for HOC. The centred draw path can therefore use `_xpos()`
for **both** mechanisms instead of HOC-vs-not branching. Logic reads the live
position through one accessor (`hocdisp` for HOC, `angle` otherwise).

## Changes (`plutoapromwindow.py` unless noted)

1. **Enable centred for HOC** — drop the `!= "HOC"` exclusion in
   `PlutoAPRomAssessmentStateMachine._is_prom_centered` and in the window's
   `_is_prom_centered` flag. New definition: `PASSIVE and arom is not None`.

2. **FPS gating** (`plutofullassessment.py`) — HOC PROM uses
   `get_arom_if_completed()` like the other mechanisms. AROM skipped/terminated
   → `arom=None` → plain symmetric PROM (unchanged path).

3. **State-machine position abstraction** — add `_pos()` → `hocdisp`/`angle`.
   Make the centred branches mechanism-agnostic and two-sided:
   - `subj_near_center`: `abs(_pos - center) <= th` (HOC/non-HOC threshold).
   - `subj_in_the_stop_zone` / `is_trialrom_valid`: when centred, require both
     sides beyond the center (the existing non-HOC two-sided test), HOC
     included.
   - `_handle_rest` centred instruction: unit `cm`/`deg` by mechanism.

4. **Display (centred path uses `_xpos` for both mechanisms):**
   - Axis: HOC centred → corner-anchored `[-0.5, MAXHOC+0.5]` (same as cycling
     HOC) instead of `[-10, 10]`.
   - Cursor: single line at `_xpos(pos)` (drop HOC mirror twin) when centred.
   - AROM reference lines (green dotted, persistent): draw at `_xpos(arom[0])`,
     `_xpos(arom[1])` instead of the mirrored `±arom[1]`.
   - Resting/center line: solid cyan line at `_xpos(center)`, drawn
     persistently through REST + trial states. Create `restPosLine` /
     `restZoneFill` for centred PROM too (today only created for ACTIVE).
   - Start gate band + stop-zone lines: `center ± threshold` via `_xpos`.

5. **Non-HOC PROM** — also gets the explicit center/resting line (same code
   path, no other behaviour change).

## Out of scope

- APROM slow/fast (separate window, `plutoassistpromwindow.py`).
- AROM cycling behaviour.
- Summary CSV format — PROM still logs start / min / max / range.

## Constants (existing, `plutofullassessdef.py`)

- `MAXHOC = 9.4` cm
- `STOP_POS_HOC_THRESHOLD = 0.5` cm
- `START_POS_HOC_THRESHOLD = 0.25` cm
- `REST_ZONE_HALF_WIDTH_HOC = 0.5` cm

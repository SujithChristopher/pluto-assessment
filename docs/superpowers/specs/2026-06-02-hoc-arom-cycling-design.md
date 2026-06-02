# HOC AROM — Cycling Assessment Design

Date: 2026-06-02
Status: Approved (pending implementation plan)

## Goal

Rebuild **AROM for the HOC mechanism** so it behaves like the non-HOC AROM
cycling assessment, instead of the current symmetric two-line single-value
capture. Subject opens and closes the hand repeatedly; each cycle's aperture is
marked using the existing rest-driven algorithm; the best of the last 3 cycles
becomes the recorded HOC AROM.

Only **AROM-HOC** changes. PROM-HOC and APROM-HOC keep the existing
single-value path (they are not `ROMType.ACTIVE`, so they never enter the
cycling code).

## Background — current state

- Non-HOC AROM uses a rest-driven cycling engine in `plutoapromwindow.py`:
  `States.CYCLING` / `States.WAIT_FOR_REST`, `APRomData.update_cycling_data`,
  best-of-3 (`best_cycle`), per-cycle dotted lines, top-right per-cycle readout,
  rest-position hold to finish.
- This engine is gated to non-HOC only:
  `_is_arom_cycling = (romtype == ACTIVE and mechanism != "HOC")`.
- HOC currently falls through to the old single-value path and is drawn as two
  mirrored vertical lines spreading from centre (`-hocdisp` / `+hocdisp`).

## Design

### 1. Cycle semantics (mapping HOC onto the existing algorithm)

The existing algorithm marks a "left" extreme (toward the start) and a "right"
extreme (the far excursion), closing a cycle on a distinct return toward start.
HOC maps onto this directly:

- **closed end** (`hocdisp` ≈ 0) = the "left" extreme (toward start)
- **open end** (max aperture) = the "right" extreme (far excursion)
- `startpos` ≈ 0 (lowest-velocity sample at trial start, i.e. closed)
- First move = **open** → first rest seeds the open (right) extreme
- Return toward closed → distinct rest near 0 closes the cycle, seeds the next
- 5 cycles; each cycle = `(closed_rest, open_rest)`; cycle ROM = open − closed
- best of last 3 cycles (widest) = final HOC AROM
- rest-position = mid-aperture of the best cycle; held briefly to finish

`update_cycling_data` is reused unchanged in logic — only the fed signal
(`hocdisp` instead of `angle`) and the unit-dependent thresholds differ.

### 2. Display geometry — single line, corner anchor

Replace the two mirrored HOC lines with one cursor line, like non-HOC AROM.
Add a HOC position transform that pins the closed end to a corner by hand side:

- X-axis range `[0, MAXHOC]` (`MAXHOC` ≈ device full-open, ~9.4 cm)
- **Right hand:** `x = hocdisp` → closed at the **left** corner, opens rightward
- **Left hand:** `x = MAXHOC - hocdisp` → closed at the **right** corner, opens
  leftward

Hand side comes from `self.data.limb`. Provide one helper `hoc_x(pos)` and route
every HOC-drawn element through it: cursor, per-cycle dotted lines, best-of-3
fill, rest line, stop zone. `_dispsign` stays 1.0 for non-HOC; HOC uses
`hoc_x()`.

Kept the same as non-HOC AROM:
- per-cycle dotted lines + top-right readout, units changed `deg` → `cm`
  (e.g. `Cycle N: X.X cm`)
- direction indicator text changed from `◄ Move LEFT first` to
  `Open hand first`

### 3. New HOC cycling constants

Add cm twins of the deg-based cycling constants to the `AROM` class in
`plutofullassessdef.py`:

```
REST_ZONE_HALF_WIDTH_HOC       = 2.0   # cm   (non-HOC: 5 deg)
CYCLING_REST_VEL_THRESHOLD_HOC = 0.5   # cm/s (non-HOC: 1.0 deg/s)
CYCLING_MIN_EXCURSION_HOC      = 0.5   # cm   (non-HOC: 5.0 deg)
MAXHOC                         = 9.4   # cm   device full-open (far corner)
```

Values are starting points to be tuned on the device. Code selects HOC vs
non-HOC twins the same way existing thresholds already do (`VEL_HOC_THRESHOLD`
etc.).

### 4. Code touch-points (`plutoapromwindow.py` unless noted)

1. `_is_arom_cycling` — drop `and mechanism != "HOC"`; gate becomes
   `romtype == ACTIVE`. Apply in both the state machine property and the
   `APRomData` summary-header selection (init) and `set_rom` /
   `write_failed_trial`.
2. `_handle_cycling` — feed `hocdisp` for HOC:
   `update_cycling_data(self._pluto.hocdisp if HOC else self._pluto.angle)`.
3. `update_cycling_data`, `subj_in_rest_zone`, `compute_rest_position` — use the
   HOC twins (rest-vel, min-excursion, rest-zone half-width) when
   `mechanism == "HOC"`.
4. Summary header / row writing — AROM-HOC uses the 10-col cycling header
   (`SUMMARY_HEADER_CYCLING`); values in cm.
5. Add `hoc_x(pos)` transform; route all HOC draws through it; remove the old
   symmetric `-hocdisp` / `+hocdisp` HOC branches in the draw methods.
6. Graph init — HOC X-range `[0, MAXHOC]`; enable the cycle dotted-lines /
   readout / rest-position visuals block for HOC (currently gated non-HOC only).
7. Instruction/readout units `deg` → `cm` for HOC; direction text
   `Open hand first`.
8. Old HOC single-value path (`_trialrom=[0,]`, `add_new_trialrom_data` HOC
   branch, `is_trialrom_valid` HOC branch) is no longer reached by AROM-HOC.
   Leave it intact for PROM-HOC / APROM-HOC — verify those remain unchanged.

### 5. Data output

AROM-HOC summary switches to the 10-col cycling header:
`session, type, limb, mechanism, trial, last_cycle_left, last_cycle_right,
last_cycle_range, rest_position, cycles_completed` — all aperture values in cm.
Raw log is unchanged (already records both `angle` and `hocdisp`).

## Out of scope

- PROM-HOC and APROM-HOC behaviour (unchanged).
- Tuning the placeholder constants (done on-device after implementation).
- Non-HOC AROM behaviour (unchanged).

## Verification

- AROM-HOC: open/close cycling marks both extremes; 5 cycles; best-of-3 sets
  final ROM; single corner-anchored line; left vs right hand mirrors correctly.
- PROM-HOC and APROM-HOC still use the old single-value path (no regression).
- Non-HOC AROM unchanged.
- Summary CSV for AROM-HOC has the 10 cycling columns in cm.

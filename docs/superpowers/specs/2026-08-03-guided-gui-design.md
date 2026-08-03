# Guided Single-Window Assessment GUI — Design

Date: 2026-08-03
Status: Approved, ready for implementation planning

## Problem

`plutofullassessment.py` presents the operator with a control panel: a protocol
table, a grid of mechanism buttons, a grid of task buttons, plus skip buttons for
each. The operator must know the protocol order and click the right button at the
right time. Every task then opens as a separate modal window on top.

The assessment protocol is in fact strictly linear. The GUI should reflect that:
show what is next, and let the PLUTO device button drive the session forward. The
mouse is needed only to accept or redo a finished task.

## Goals

- One window for the whole session. No modal task windows, no protocol table.
- The PLUTO hardware button advances the flow: ready → task → next ready → …
- The mouse is used only for setup, Accept, and Redo.
- Task set reduced to: Calibration, AROM, PROM, Assisted PROM, Discrete Reaching.
- All four mechanisms: FPS, WFE, WURD, HOC.
- One setup screen covering both Screening and Assessment modes.
- Data written on disk stays byte-identical to the current app, so S3 sync and
  existing analysis scripts keep working.

## Non-goals

- Rewriting the task displays or their trial state machines.
- Changing CSV formats, folder layout, or the S3 sync worker.
- Removing or breaking `plutofullassessment.py`. It stays runnable.
- Proprioception, Position Hold, and Force Control tasks. They are out of the
  new flow entirely (their modules stay in the repo, unused by the new GUI).

## Layout on disk

```
newgui/
  main.py         entry point: QApplication, QtPluto, shell window
  shell.py        PlutoGuidedAssessor(QMainWindow) — the single window
  sequencer.py    linear step list, cursor, resume, auto-skip rules
  pages.py        page factory: builds the task widget for a given step
  setup.py        embedded setup page (mode / subject / limb / timepoint)
```

Run with `uv run python newgui/main.py`. `main.py` inserts the repository root
on `sys.path` so the root modules (`qtpluto`, `plutofullassessdef`, the task
windows, …) import unchanged.

## Window structure

The shell is a `QMainWindow` holding a `QStackedWidget`, with:

- a header: `FPS · Active ROM` on the left, step counter `3 / 20` on the right;
- the stacked page area;
- a footer strip: either a hint line ("Press the PLUTO button to start") or the
  `Accept` / `Redo` buttons;
- the existing status bar content (uptime, connection, frame rate, subject) and
  the S3 sync indicator.

Pages:

| Page | Contents |
|---|---|
| `SetupPage` | Screening/Assessment radio, subject id, affected side, limb, dominant hand, time point |
| `ReadyPage` | Mechanism image + fit instruction + "Press the PLUTO button" |
| `TaskPage` | The live task widget for the current step |
| `ReviewPage` | The finished task display, frozen, with Accept / Redo |
| `DonePage` | Session complete. Screening additionally shows the eligibility verdict |

`ReadyPage` images come from `assets/`: `fps.png`, `wfe.png`, `hoc.png`. WURD has
no image of its own and reuses `wfe.png`, matching the current `_img_map` in
`plutofullassessment.py`.

## Sequencer

`sequencer.py` owns the step list and the cursor. A step is
`(mechanism, task)` where task is one of `CALIB`, `AROM`, `PROM`, `APROM`, `DISC`.

```
tasks(assessment) = [CALIB, AROM, PROM, APROM, DISC]
tasks(screening)  = [CALIB, AROM]

steps = [(mech, task) for mech in pfadef.MECHANISMS
                      for task in tasks(mode)]
```

`pfadef.MECHANISMS` is the ordering source (`FPS, WFE, WURD, HOC`). Screening
keeps its current AROM-only protocol; the mode differs only in the task list, the
folder tree, the subject-list file, and the eligibility verdict on `DonePage`.

The sequencer exposes: `current()`, `advance()`, `redo()`, `mark_skipped(reason)`,
`is_done()`, and `position()` for the `n / total` header counter.

`CALIB` steps are flow-only. They are not rows in the protocol CSV and are never
persisted; every other step maps to exactly one protocol row.

## Flow

```
SetupPage
   └─ Start ──▶ ReadyPage(step 0)

ReadyPage ── PLUTO button ──▶ TaskPage
TaskPage  ── task finishes  ──▶ ReviewPage
ReviewPage ── Accept ──▶ persist, cursor++, ReadyPage(next step)
           └─ Redo   ──▶ rebuild the same TaskPage from scratch

… last step accepted ──▶ DonePage
```

### PLUTO button ownership

The shell connects to `pluto.btnreleased` for navigation, but that handler is
active only while no `TaskPage` is live. Task windows attach their own
`btnreleased` handler on construction and detach it on close, so during a task
the shell's navigation handler is disconnected and the task owns the button. On
`ReviewPage` the shell handler stays disconnected — Accept/Redo are mouse-only,
so a stray button press cannot skip the review.

### Mechanism transitions

The first step of every mechanism is its `CALIB` step. Its `ReadyPage` shows the
mechanism image and the fit instruction ("Fit the FPS mechanism"), so a mechanism
change needs no separate screen.

### Resume

On setup completion the shell reads the protocol CSV for the
subject/limb/timepoint via `PlutoAssessmentData`. Steps whose row already has a
session value are marked complete; the cursor parks on the first incomplete step.
Because calibration is not persisted, the sequencer re-inserts the `CALIB` step
for the resumed mechanism ahead of the cursor, so the device is always calibrated
before a task runs. The `ReadyPage` for that step is labelled "(resumed)".

### Auto-skip rules (carried over unchanged)

- After AROM completes, if the recorded range is below the movement threshold
  (10 deg for joint mechanisms, 2 cm for HOC), or no valid AROM was recorded,
  DISC for that mechanism is logged as skipped with the existing reason text.
- If AROM terminates because the subject failed `AROM.MAX_FAILED_TRIALS` trials
  on the time limit, AROM is logged as skipped and DISC is skipped too.

Auto-skipped steps are written to the protocol CSV and the cursor slides past
them without stopping on a page.

There are no operator-facing skip controls — no skip-task, no skip-mechanism, no
step-back. The only way out of the flow is closing the window.

## Reusing the existing task windows

The task windows are `QMainWindow` subclasses, which are `QWidget`s, so they can
be added to the stack directly as page widgets. Two behaviours block embedding:

1. They deliver their result from inside `closeEvent` via `onclosecb`.
2. `closeEvent` pops a `CommentDialog` asking the operator to accept/reject and
   type a comment — exactly what the new `ReviewPage` replaces.

Fix: add an `embedded: bool = False` keyword argument to the four task window
classes used by the new flow:

- `plutoapromwindow.PlutoAPRomAssessWindow` (AROM and PROM)
- `plutoassistpromwindow.PlutoAssistPRomAssessWindow` (APROM)
- `plutodiscreachwindow.PlutoDiscReachAssessWindow` (DISC)
- `plutocalibwindow.PlutoCalibrationWindow` (calibration)

When `embedded=True`:

- `closeEvent` skips the `CommentDialog` and delivers its payload with
  `status=None` and `taskcomment=""`;
- everything else — trial state machines, CSV writers, pyqtgraph display, the
  per-trial timeout dialog and its AROM-termination path — is untouched.

The default `False` preserves today's behaviour, so `plutofullassessment.py`
keeps working with no changes.

`ReviewPage` is not a separate widget: `close()` on an embedded widget hides it,
so the shell re-shows the finished task widget in place and only swaps the footer
from the hint line to the Accept / Redo buttons. The operator therefore reviews
the same display the task ended on.

The shell fills in the status from the review: Accept →
`AssessStatus.COMPLETE`, Redo → `AssessStatus.REJECTED`. The AROM-termination
path still delivers `AssessStatus.SKIPPED` itself and bypasses the review page.

Each step gets a freshly constructed task widget. On Accept or Redo the widget is
removed from the stack and deleted, so its state machine and CSV writers do not
leak into the next step.

## Data layer

`PlutoAssessmentData` (session folders, subject list, protocol CSV, detailed
summary, AROM lookup for DISC/APROM) is reused as-is. The new sequencer replaces
`PlutoFullAssessmentStateMachine` (which the new GUI does not import), but the
rows it writes and the files it creates are the same.

Accept writes the row with an empty task comment. Redo discards the attempt: the
rejected attempt is recorded with `status = REJECTED`, exactly as today, and the
retry writes to a new raw/summary file. Nothing is deleted from disk.

`SessionSetupWorker` (async folder + protocol creation) is reused so the UI does
not block during setup.

The heartbeat timer, the device status display, and the `S3SyncWorker` are all
carried into the shell with their current behaviour.

## Error handling

- **Device disconnected / no data:** the status bar shows the connection state,
  as today. The PLUTO button simply produces no events, so the flow stalls on the
  current `ReadyPage` rather than advancing into a task with no device.
- **Calibration fails:** the calibration window reports `done=False`. The shell
  returns to the same `ReadyPage` so the operator can retry; the flow does not
  advance until calibration succeeds.
- **Session setup fails** (folder/protocol creation): the error is shown and the
  shell stays on `SetupPage`, matching the current `_on_setup_worker_error`
  behaviour.
- **Window closed mid-session:** the protocol CSV holds everything already
  accepted, and the resume path picks up from the first incomplete step.

## Testing

- Manual run against the device is the real acceptance test:
  `uv run python newgui/main.py`.
- `uv run python -m py_compile` over every new and modified file.
- The four modified task windows are checked in the old GUI too, confirming that
  `embedded=False` leaves their behaviour unchanged.
- Sequencer logic (step list per mode, cursor advance/redo, resume from a
  partially filled protocol CSV, auto-skip of DISC) is pure Python with no Qt or
  device dependency, so it is covered by unit tests under `tests/`.

## Risks

- Embedding a `QMainWindow` inside a `QStackedWidget` is legal but unusual;
  window-level features (its own status bar, window flags) are inert. The task
  windows use a plain central widget, so this is expected to be cosmetic only,
  and is the first thing to verify when the shell is stood up.
- `CommentDialog` currently supplies the only per-task free-text comment. The new
  flow records empty comments. This is a deliberate simplification, not an
  oversight.

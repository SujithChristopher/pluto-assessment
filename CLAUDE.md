# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A Python/PySide6 desktop GUI application for assessing hand function using **PLUTO** — a robotic rehabilitation device. The app connects to PLUTO over serial (COM port), runs structured assessment protocols, and logs sensor data to CSV files.

## Running the Application

```bash
# Use uv to run scripts
uv run python plutofullassessment.py

# Or run the legacy proprioception-only assessment
uv run python plutopropass.py
```

The COM port for PLUTO is hardcoded in `plutofullassessdef.py` as `PLUTOCOMM = "COM4"`. Change this to match the connected device.

## Environment Setup

The project uses `uv` for package management (not conda/pip). A `.venv` is present in the repo root. Always use `uv run <cmd>` — never `conda run` or bare `python`.

## Regenerating UI Python Files

Qt `.ui` files live in `ui/`. Their generated Python counterparts live in `uipy/`. After editing a `.ui` file in Qt Designer, regenerate all at once:

```bash
genpycode.bat
```

Or regenerate a single file:

```bash
uv run pyside6-uic ui/<filename>.ui -o uipy/ui_<name>.py
```

## Syntax Checking

```bash
uv run python -m py_compile <file1.py> [file2.py ...]
```

## Building a Standalone Executable

A PyInstaller spec file (`plutofullassessment.spec`) is present. Build with:

```bash
uv run pyinstaller plutofullassessment.spec
```

Output goes to `dist/plutofullassessment.exe`.

## Architecture

### Hardware Communication Layer
- **`qtjedi.py`** — `JediComm(QThread)`: Runs in a background thread, reads the JEDI binary serial protocol from the device (header `0xFF 0xFF`, length byte, payload, checksum), and emits `newdata_signal`.
- **`qtpluto.py`** — `QtPluto(QObject)`: Wraps `JediComm`, unpacks sensor packets into named properties (`angle`, `hocdisp`, `torque`, `button`, etc.), and re-emits `newdata`, `btnpressed`, `btnreleased` Qt signals.
- **`plutodefs.py`** — All device-level constants: mechanism names (`WFE`, `FPS`, `HOC`), control types (`POSITION`, `TORQUE`, `RESIST`), packet type codes, error codes, calibration status, and conversion functions.

### Application Entry Point
- **`plutofullassessment.py`** — `PlutoFullAssesor(QMainWindow)`: The top-level window. Manages subject selection, limb setup, and launches sub-windows for each assessment task. Coordinates the full assessment state machine.

### State Machine Layer
- **`plutofullassessstatemachine.py`** — `PlutoFullAssessmentStateMachine`: Controls the high-level sequencing of subjects → mechanisms → tasks → trials across the full assessment session.
- **`plutostatemachines.py`** — Individual task-level state machines:
  - `PlutoCalibrationStateMachine` — device calibration steps
  - `PlutoRomAssessmentStateMachine` — AROM/PROM recording
  - `PlutoPropAssessmentStateMachine` — proprioception haptic display + response
  - Note: APROM, PositionHold, DiscreteReach, and ForceControl task flow is controlled inline within `PlutoFullAssessmentStateMachine` — they do not have separate state machine classes.

### Assessment Protocol Definitions
- **`plutofullassessdef.py`** — Protocol constants for the full assessment: which mechanisms (`FPS`, `WFE`, `HOC`), which tasks per mechanism (`AROM`, `PROM`, `APROMSLOW`, `APROMFAST`, `DISC`, `POSHOLD`, `PROP`, `FCTRLLOW/MED/HIGH`), task ordering rules, task dependency rules (subject type: `stroke` vs `healthy`), and per-task data column headers. Also contains constants classes (`AROM`, `PROM`, `APROM`, `PositionHold`, `DiscreteReach`, `Proprioception`, `ForceControl`) with trial counts, target positions, timing, and display colors.
- **`plutoassessdef.py`** — Constants for the standalone proprioception assessment protocol.

### Task Windows (Sub-Windows)
Each file follows the pattern `pluto<taskname>window.py` and implements a `QMainWindow` or `QDialog` that handles one assessment task. They receive a `QtPluto` instance, run their task-level state machine on incoming `newdata` signals, write raw + summary CSV files via `CSVBufferWriter`, and signal completion back to the main window.

| File | Task |
|---|---|
| `plutocalibwindow.py` | Device calibration |
| `plutoromwindow.py` | Active/Passive ROM |
| `plutoapromwindow.py` | Assisted Passive ROM |
| `plutoassistpromwindow.py` | Assisted PROM (alternate) |
| `plutopropassesswindow.py` | Proprioception |
| `plutoposholdwindow.py` | Position hold |
| `plutodiscreachwindow.py` | Discrete reaching |
| `plutoforcecontrolwindow.py` | Force control |
| `plutotestwindow.py` | Manual control tester |
| `plutodataviewwindow.py` | Live data viewer |
| `plutocontroltesterwindow.py` | Control parameter tester |

### Data Management
- **`plutofullassesssdata.py`** — `PlutoAssessmentData`: Manages the session folder structure under `../fullassessment/`, loads/saves the subject list CSV (`fullassess_subjects.csv`) and per-session summary CSV. Also provides `DataFrameModel` (a `QAbstractTableModel` wrapping a pandas DataFrame for display in Qt table views).
- **`misc.py`** — `CSVBufferWriter`: Buffered CSV writer used by all task windows to log raw sensor data; flushes on a time interval or when buffer fills.
- **`async_workers.py`** — `LimbSetupWorker(QThread)`: Offloads blocking file I/O (folder creation, JSON writing, protocol CSV init) when setting up a timepoint session.

### Custom Widgets
- **`myqt.py`** — Shared PySide6 dialog/widget classes used across task windows: `CommentDialog` (operator notes), `MechStartDialog` (mechanism intro), `MechTaskSkipDialog` (skip confirmation), and `create_sector` (pyqtgraph arc helper).

### Subject Management
- **`subjectcreator.py`** / **`subjectselector.py`** — QDialog subclasses for creating new subject records and selecting existing ones from the subject list CSV.

### UI Layer
- `ui/*.ui` — Qt Designer source files (XML), one per window.
- `uipy/ui_*.py` — Auto-generated Python classes from `pyside6-uic`. Never edit these directly.

### Firmware
- `plutofire/plutofire/plutofire.ino` — Arduino firmware for the PLUTO device (communicates at 115200 baud using the JEDI protocol).

## Data Flow

```
PLUTO hardware (serial 115200 baud)
  → JediComm (QThread, qtjedi.py) — parses JEDI binary frames
  → QtPluto (QObject, qtpluto.py) — unpacks to named properties, emits Qt signals
  → Task window — runs state machine, controls device, logs data
  → CSVBufferWriter (misc.py) — raw CSV + summary CSV per trial
  → PlutoAssessmentData (plutofullassesssdata.py) — session-level tracking
```

## Key Conventions

- **`debugconfig.py`** — Set `DEBUG = True` to bypass sequential assessment ordering (all mechanisms and tasks become selectable in any order). Set `False` to restore normal behavior. Use for debugging only; do not ship with `DEBUG = True`. **Current repo state: `DEBUG = True`** — always verify before building a release.
- The `QtPluto` object is created once in the main window and passed to all sub-windows; sub-windows must not create their own serial connections.
- Task constants (trial counts, timing, thresholds) live as class attributes on the classes in `plutofullassessdef.py` (e.g., `AROM.NO_OF_TRIALS`, `Proprioception.TGT_POSITIONS`). Use `get_task_constants(task_name)` to retrieve them by string name.
- `pdef.get_name(dict, code)` and `pdef.get_code(dict, name)` are the lookups for converting between device codes and string names — use these instead of direct dict access.
- Assessment data is written under the user's Documents folder: `<Documents>/homerpluto/fullassessment/` for the full assessment and `<Documents>/homerpluto/propassessment/` for the legacy proprioception app. The base is resolved by `homer_data_root()` in `plutofullassessdef.py` via `QStandardPaths.DocumentsLocation` (OneDrive-redirection safe, falls back to `~/Documents`). `DATA_DIR`/`SUBJLIST_FILE` (in `plutofullassessdef.py`) and `DATA_DIR`/`PROTOCOL_FILE` (in `plutoassessdef.py`) derive from it. These are absolute, user-writable paths so the packaged Windows `.exe` always writes to a stable location regardless of its launch directory.
- The `plutofire` subdirectory is Arduino firmware — not Python. Do not treat `.ino` files as Python.

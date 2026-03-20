# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A Python/PySide6 desktop GUI application for assessing hand function using **PLUTO** — a robotic rehabilitation device. The app connects to PLUTO over serial (COM port), runs structured assessment protocols, and logs sensor data to CSV files.

## Running the Application

```bash
# Activate the conda environment
conda activate pa

# Run the full assessment application (main entry point)
python plutofullassessment.py

# Or run the legacy proprioception-only assessment
python plutopropass.py
```

The COM port for PLUTO is hardcoded in `plutofullassessdef.py` as `PLUTOCOMM = "COM19"`. Change this to match the connected device.

## Environment Setup

The project uses a conda environment defined in `environment.yml` (name: `pa`, Python 3.9). A `.venv` with PySide6 is also present in the repo root but targets a different Python version.

```bash
conda env create -f environment.yml
conda activate pa
```

## Regenerating UI Python Files

Qt `.ui` files live in `ui/`. Their generated Python counterparts live in `uipy/`. After editing a `.ui` file in Qt Designer, regenerate with:

```bash
pyside6-uic ui/<filename>.ui -o uipy/ui_<name>.py
```

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
- **`async_workers.py`** — `LimbSetupWorker(QThread)`: Offloads blocking file I/O (folder creation, JSON writing) when setting up a limb assessment session.

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

- The `QtPluto` object is created once in the main window and passed to all sub-windows; sub-windows must not create their own serial connections.
- Task constants (trial counts, timing, thresholds) live as class attributes on the classes in `plutofullassessdef.py` (e.g., `AROM.NO_OF_TRIALS`, `Proprioception.TGT_POSITIONS`). Use `get_task_constants(task_name)` to retrieve them by string name.
- `pdef.get_name(dict, code)` and `pdef.get_code(dict, name)` are the lookups for converting between device codes and string names — use these instead of direct dict access.
- Assessment data output goes to `../fullassessment/` (one level above the repo root) — this path is gitignored. Proprioception data goes to `propassessment/` (gitignored).
- The `plutofire` subdirectory is Arduino firmware — not Python. Do not treat `.ino` files as Python.

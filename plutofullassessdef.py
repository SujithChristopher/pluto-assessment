"""
Module containing definitions for the PLUTO full assessment protocol.

Author: Sivakumar Balasubramanian
Date: 16 May 2025
Email: siva82kb@gmail.com
"""

import json
import pathlib
import numpy as np
import pandas as pd
from enum import Enum
import misc

from PySide6.QtGui import QColor
from PySide6.QtCore import QStandardPaths


def homer_data_root() -> pathlib.Path:
    """Base folder for all HOMER-PLUTO data: <Documents>/homerpluto.

    Stored under the user's Documents so the packaged Windows app always writes
    to a stable, user-writable location regardless of where the .exe is launched
    from. QStandardPaths resolves the real Documents folder (incl. OneDrive
    redirection); fall back to ~/Documents if it is unavailable."""
    _docs = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    if not _docs:
        _docs = str(pathlib.Path.home() / "Documents")
    return pathlib.Path(_docs) / "homerpluto"


#
# PLUTO COM Port
#
PLUTOCOMM = "COM5" # Sujith system
# PLUTOCOMM = "COM8"


class ROMType(Enum):
    ACTIVE = "Active"
    PASSIVE = "Passive"
    ASSISTED_PASSIVE = "Assisted Passive"

    def __str__(self):
        return self.value


class AssessStatus(Enum):
    INCOMPLETE = "Incomplete"
    COMPLETE = "Complete"
    PARTIALCOMPLETE = "Partially Complete"
    SKIPPED = "Skipped"
    EXCLUDED = "Excluded"
    REJECTED = "Rejected"
    TERMINATED = "Terminated"

    def __str__(self):
        return self.value


#
# Full Assessment Constant
#
# Module level constants.
DATA_DIR = str(homer_data_root() / "fullassessment")
SUBJLIST_FILE = str(pathlib.Path(DATA_DIR) / "fullassess_subjects.csv")

# Screening: separate tree, single-shot (no timepoint), AROM only.
SCREENING_DIR = str(homer_data_root() / "screening")
SCREENING_SUBJLIST_FILE = str(pathlib.Path(SCREENING_DIR) / "screening_subjects.csv")

# Subjects-list CSV headers per mode.
ASSESS_SUBJECT_HEADER = ["subjid", "domlimb", "afflimb", "createdat"]
SCREENING_SUBJECT_HEADER = ["subjid", "afflimb", "createdat"]

# Proprioceptive assessment control timer delta (seconds).
PROPASS_CTRL_TIMER_DELTA = 0.01

# List of time points for longitudinal assessment.
TIMEPOINTS = ["A0", "A1", "A2"]

# List of mechanisms to be used in the order it is to be used.
MECHANISMS = ["FPS", "WFE", "WURD", "HOC"]

# Mechanisms labels
MECH_LABELS = {
    "WFE": "Wrist Flexion/Extension",
    "WURD": "Ulnar/Radial Deviation",
    "FPS": "Forearm Pronation/Supination",
    "HOC": "Hand Opening/Closing",
}

# List of tasks in the order they are to be done.
ALLTASKS = [
    "AROM",
    "PROM",
    "APROM",
    "DISC",
    "POSHOLD",
    "PROP",
    "FCTRLLOW",
    "FCTRLMED",
    "FCTRLHIGH",
]

# Tasks labels
TASK_LABELS = {
    "AROM": "Active ROM",
    "PROM": "Passive ROM",
    "APROM": "Assisted Passive ROM",
    "DISC": "Discrete Reaching",
    "POSHOLD": "Position Hold",
    "PROP": "Proprioceptiion",
    "FCTRLLOW": "Force Control (Low)",
    "FCTRLMED": "Force Control (Med)",
    "FCTRLHIGH": "Force Control (High)",
}

# Tasks for each mechanisms in the order they are to be done.
# The first list contains the tasks that are to be done first in that
# specific order. While the lists after that contain the tasks that are to be done
# after the first list tasks are completed, but in a random order. When one of
# the lists is empty, it means that there are no tasks to be done in that order.
MECH_TASKS = {
    "FPS": [["AROM", "PROM", "APROM"], ["DISC"]],
    "WFE": [["AROM", "PROM", "APROM", "DISC"], []],
    "WURD": [["AROM", "PROM", "APROM", "DISC"], []],
    "HOC": [
        ["AROM", "PROM", "APROM"],
        ['DISC']
        # ["PROP"],
        # ["FCTRLLOW", "FCTRLMED", "FCTRLHIGH"],
    ],
}

# Screening protocol: AROM only, every mechanism.
SCREENING_MECH_TASKS = {_m: [["AROM"]] for _m in MECHANISMS}

TASK_DEPENDENCIES = {
    "AROM": {"in_unaffected": False, "depends_on": []},
    "PROM": {"in_unaffected": False, "depends_on": []},
    "APROM": {"in_unaffected": False, "depends_on": []},
    "DISC": {"in_unaffected": True, "depends_on": ["AROM"]},
    "POSHOLD": {"in_unaffected": False, "depends_on": ["AROM"]},
    "FCTRLLOW": {"in_unaffected": True, "depends_on": ["AROM"]},
    "FCTRLMED": {"in_unaffected": True, "depends_on": ["AROM"]},
    "FCTRLHIGH": {"in_unaffected": True, "depends_on": ["AROM"]},
    "PROP": {"in_unaffected": True, "depends_on": ["PROM"]},
}

# Mech/task status stylesheet
STATUS_STYLESHEET = {
    AssessStatus.INCOMPLETE: "color: rgb(170, 0, 0);",  # Dark red
    AssessStatus.COMPLETE: "color: rgb(0, 100, 0);",  # Dark green
    AssessStatus.PARTIALCOMPLETE: "color: rgb(255, 165, 0);",  # Orange
    AssessStatus.SKIPPED: "color: rgb(100, 149, 237);",  # Light blue (Cornflower Blue)
    AssessStatus.EXCLUDED: "color: rgb(200, 200, 200);",  # Light blue (Cornflower Blue)
    None: "",  # Default color (black)
}
STATUS_TEXT = {
    AssessStatus.INCOMPLETE: "",
    AssessStatus.COMPLETE: "[C]",
    AssessStatus.PARTIALCOMPLETE: "[*C]",
    AssessStatus.SKIPPED: "[S]",
    AssessStatus.EXCLUDED: "[E]",
    None: "",
}

# Full assessment summary file header.
FA_SUMMARY_HEADER = [
    "session",
    "mechanism",
    "task",
    "ntrial",
    "rawfile",
    "summaryfile",
    "mechcomment",
    "taskcomment",
    "status",
]
# Pandas DataFrame column format for the full assessment summary.
# This is used to define the data types of each column in the summary DataFrame.
SUMMARY_COLUMN_FORMAT = {
    "session": "string",
    "mechanism": "string",
    "task": "string",
    "ntrial": "int64",
    "rawfile": "string",
    "summaryfile": "string",
    "mechcomment": "string",
    "taskcomment": "string",
    "status": "string",
}
#
# Main GUI relted constants
#
DISPLAY_INTERVAL = 200  # ms
VISUAL_FEEDBACK_UPDATE_INTERVAL = 33  # ms


class BaseConstants:
    POS_VEL_WINDOW_LENGHT = 50
    START_POS_HOC_THRESHOLD = 0.25  # cm
    START_POS_NOT_HOC_THRESHOLD = 2.5  # deg
    STOP_POS_HOC_THRESHOLD = 0.5  # cm
    STOP_POS_NOT_HOC_THRESHOLD = 5  # deg
    VEL_HOC_THRESHOLD = 1  # cm/sec
    VEL_NOT_HOC_THRESHOLD = 7.5  # deg/sec
    STOP_ZONE_DURATION_THRESHOLD = 1  # sec
    HOC_NEW_ROM_TH = 0.10  # cm
    NOT_HOC_NEW_ROM_TH = 1.0  # deg
    # HOC PROM/APROM: the closed end is bounded at fully closed (hocdisp ~ 0).
    # When the AROM closed boundary is already at fully closed, the passive range
    # cannot be pushed beyond it, so accept the closed boundary when the cursor
    # is within this distance of fully closed instead of requiring it to exceed
    # the AROM closed limit.
    FULLY_CLOSED_HOC_THRESHOLD = 0.5  # cm

    # Data logging constants
    RAW_HEADER = [
        "systime",
        "devtime",
        "packno",
        "status",
        "controltype",
        "error",
        "limb",
        "mechanism",
        "angle",
        "hocdisp",
        "button",
        "trialno",
        "assessmentstate",
    ]
    # AROM/PROM/APROM SUMMARY HEADER
    SUMMARY_HEADER = [
        "session",
        "type",
        "limb",
        "mechanism",
        "trial",
        "startpos",
        "rommin",
        "rommax",
        "romrange",
    ]

    #
    # Display constants
    #
    CURSOR_LOWER_LIMIT = -30
    CURSOR_UPPER_LIMIT = 10


#
# Active Range of Motion Constants
#
class AROM(BaseConstants):
    NO_OF_TRIALS = 3  # Number of trials.
    NO_OF_CYCLES = 5  # Full oscillation cycles required (non-HOC AROM only).
    TRIAL_TIME_LIMIT = 60.0  # sec — wall-clock window to complete one trial.
    MAX_FAILED_TRIALS = 2  # failed trials that terminate AROM (disables DISC).
    REST_ZONE_HOLD_DURATION = 1.0  # sec to hold inside rest zone to complete trial.
    REST_ZONE_HALF_WIDTH = 5  # deg — half-width of rest zone (total = 10 deg).
    CYCLING_HOLD_SAMPLES = 10  # samples averaged for cycling velocity estimate.
    CYCLING_REST_VEL_THRESHOLD = 1.0  # deg/s — at/below this = at rest; the rest position is marked as a boundary. Tunable.
    CYCLING_MIN_EXCURSION = 5.0  # deg — a rest must be this far from the last rest to count as a new extreme (rejects settle jitter / same-spot stops).
    # HOC (cm) twins of the deg-based cycling constants. Used when the cycling
    # engine drives the HOC mechanism (open/close cycling). Placeholders to be
    # tuned on the device.
    REST_ZONE_HALF_WIDTH_HOC = 0.5  # cm — half-width of the HOC rest zone.
    CYCLING_REST_VEL_THRESHOLD_HOC = 0.5  # cm/s — at/below this = at rest (HOC).
    CYCLING_MIN_EXCURSION_HOC = 0.5  # cm — distinct-rest threshold (HOC).
    MAXHOC = 9.4  # cm — device full-open aperture (HOC far corner).
    SUMMARY_HEADER_CYCLING = [
        "session", "type", "limb", "mechanism",
        "trial", "last_cycle_left", "last_cycle_right",
        "last_cycle_range", "rest_position", "cycles_completed",
    ]


#
# Passive Range of Motion Constants
#
class PROM(BaseConstants):
    NO_OF_TRIALS = 1  # Number of trials.


class APROM(BaseConstants):
    TORQUE_DIR1 = +1.0  # Toque to apply in direction 1
    TORQUE_DIR2 = -1.0  # Toque to apply in direction 2
    NO_OF_TRIALS = 3  # Number of trials
    APROMTYPE = "Assisted"  # Single assisted-PROM type (slow/fast merged).
    # Torque is ramped from 0 to the target over RAMP_DURATION, then held at the
    # target for HOLD_DURATION. DURATION = RAMP_DURATION + HOLD_DURATION is the
    # total torque-application time per direction.
    RAMP_DURATION = 2.5  # seconds — 0 -> target ramp ("ramp wave").
    HOLD_DURATION = 0.5  # seconds — hold at target after the ramp.
    DURATION = 3.0  # seconds — total torque application per direction.

    # Data logging constants
    RAW_HEADER = [
        "systime",
        "devtime",
        "packno",
        "status",
        "controltype",
        "error",
        "limb",
        "mechanism",
        "angle",
        "hocdisp",
        "torque",
        "gripforce",
        "control",
        "target",
        "desired",
        "controlbound",
        "controldir",
        "controlgain",
        "button",
        "trialno",
        "assessmentstate",
    ]
    # AROM/PROM/APROM SUMMARY HEADER
    SUMMARY_HEADER = [
        "session",
        "type",
        "limb",
        "mechanism",
        "apromtype",
        "trial",
        "startpos",
        "rommin",
        "rommax",
        "romrange",
        "torqdir1",
        "torqdir2",
        "duration",
    ]


#
# Position Hold Constants
#
class PositionHold(BaseConstants):
    NO_OF_TRIALS = 3  # Number of trials.
    TGT_POSITIONS = [0.1, 0.9]  # Fraction of AROM range
    TGT_WIDTH_DEG = 10  # Absolute target width in degrees
    TGT_HOLD_DURATION = 01.0  # seconds

    # Display color constant
    START_WAIT_COLOR = QColor(128, 128, 128, 64)
    START_HOLD_COLOR = QColor(255, 255, 255, 128)
    TARGET_DISPLAY_COLOR = QColor(255, 0, 0, 128)
    TARGET_REACHED_COLOR = QColor(255, 255, 0, 128)
    HIDE_COLOR = QColor(0, 0, 0, 0)

    # Data logging constants
    RAW_HEADER = [
        "systime",
        "devtime",
        "packno",
        "status",
        "controltype",
        "error",
        "limb",
        "mechanism",
        "angle",
        "hocdisp",
        "button",
        "trialno",
        "assessmentstate",
    ]
    # POSHOLD SUMMARY HEADER
    SUMMARY_HEADER = [
        "session",
        "type",
        "limb",
        "mechanism",
        "trial",
        "arommin",
        "arommax",
        "aromrange",
        "targetpos",
        "targetwidthmin",
        "targetwidthmax",
    ]


#
# Discrete Reaching Constants
#
class DiscreteReach(BaseConstants):
    NO_OF_TRIALS = 3  # Number of trials.
    TGT1_POSITION = 0.20  # Fraction of AROM range
    TGT2_POSITION = 0.80  # Fraction of AROM range
    TGT_WIDTH = 0.05  # Fraction of AROM range
    START_HOLD_DURATION = 0.5  # seconds
    TGT_HOLD_DURATION = 1.0  # seconds
    START_TGT_MAX_DURATION = 10.0  # seconds
    RETURN_WAIT_DURATION = 0.0  # seconds
    REACH_TGT_MAX_DURATION = 10.0  # seconds

    # Display color constant
    START_WAIT_COLOR = QColor(128, 128, 128, 64)
    START_HOLD_COLOR = QColor(255, 255, 255, 128)
    TARGET_DISPLAY_COLOR = QColor(255, 0, 0, 128)
    TARGET_REACHED_COLOR = QColor(255, 255, 0, 128)
    HIDE_COLOR = QColor(0, 0, 0, 0)

    # Data logging constants
    RAW_HEADER = [
        "systime",
        "devtime",
        "packno",
        "status",
        "controltype",
        "error",
        "limb",
        "mechanism",
        "angle",
        "hocdisp",
        "button",
        "trialno",
        "assessmentstate",
    ]
    # DISC SUMMARY HEADER
    SUMMARY_HEADER = [
        "session",
        "type",
        "limb",
        "mechanism",
        "trial",
        "arommin",
        "arommax",
        "aromrange",
        "target1pos",
        "target1widthmin",
        "target1widthmax",
        "target2pos",
        "target2widthmin",
        "target2widthmax",
    ]


#
# Prioprioceptive Assessment Constants
#
class Proprioception(BaseConstants):
    NO_OF_TRIALS = 3  # Number of trials.
    START_POSITION_TH = 0.25  # Start position of the hanbd (cm).
    TGT_POSITIONS = [0.25, 0.5, 0.75]  # Target positions (fraction of PROM).
    MIN_TGT_SEP = 1  # Minimum target separation (cm).
    MOVE_SPEED = 0.5  # Duration for haptic demonstration (cm/seconds).
    ON_OFF_TGT_DURATION = (
        1  # Duration for deciding the hand is on or off target (seconds).
    )
    TGT_ERR_TH = 0.50  # Target error threshold (cm).
    DEMO_DURATION = 3  # Duration for haptic demonstration (seconds).
    INTRA_TRIAL_REST_DURATION = 3  # Intra-Trial Rest Duration (seconds).
    INTER_TRIAL_REST_DURATION = 5  # Inter-Trial Rest Duration (seconds).
    DEMO_TGT_REACH_DURATION = (
        2.0  # Duration for the position controller to reach the target.
    )

    # Raw data file header.
    RAW_HEADER = [
        "systime",
        "devtime",
        "packno",
        "status",
        "controltype",
        "error",
        "limb",
        "mechanism",
        "angle",
        "hocdisp",
        "torque",
        "control",
        "target",
        "desired",
        "controlbound",
        "controldir",
        "controlgain",
        "controlhold",
        "button",
        "trialno",
        "assessmentstate",
    ]

    # Summary file header.
    SUMMARY_HEADER = [
        "session",
        "type",
        "limb",
        "mechanism",
        "trial",
        "startpos",
        "aromin",
        "aromax",
        "promin",
        "promax",
        "target",
        "shownpos",
        "sensedpos",
        "showntorq",
        "sensedtorq",
    ]


#
# Force Control Assessment Constants
#
class ForceControl(BaseConstants):
    NO_OF_TRIALS = 3  # Number of trials.
    FULL_RANGE_WIDTH = 2.0  # The full force range in position. (cm)
    TGT_POSITION = 0.4  # Target positions (fraction of AROM).
    TGT_FORCE = 8.00  # Target force (N).
    TGT_FORCE_WIDTH = 01.00  # Target force width (N).
    DURATION = 05.0  # Task duration (seconds).
    HOLD_START_DURATION = 1.0  # Duration for holding the target force (seconds).
    RELAX_DURATION = 1.0  # Duration for relaxing.

    # Raw data file header.
    RAW_HEADER = [
        "systime",
        "devtime",
        "packno",
        "status",
        "controltype",
        "error",
        "limb",
        "mechanism",
        "angle",
        "hocdisp",
        "torque",
        "gripforce",
        "control",
        "controlhold",
        "button",
        "objectPosition",
        "objectDelPosition",
        "trialno",
        "assessmentstate",
    ]

    # Summary file header.
    SUMMARY_HEADER = [
        "session",
        "type",
        "limb",
        "mechanism",
        "trial",
        "aromin",
        "aromax",
        "targetposition",
        "targetforce",
        "targetforcemin",
        "targetforcemax",
    ]

    # Display constants
    CURSOR_LOWER_LIMIT = -30
    CURSOR_UPPER_LIMIT = 10

    FREE_COLOR = QColor(128, 128, 255, 128)
    HELD_COLOR = QColor(0, 255, 0, 128)
    CRUSHED_COLOR = QColor(255, 0, 0, 128)


class ForceControlLow(ForceControl):
    TGT_FORCE = 2.00  # Target force (N).
    TGT_FORCE_WIDTH = 01.00  # Target force width (N).


class ForceControlMed(ForceControl):
    TGT_FORCE = 4.00  # Target force (N).
    TGT_FORCE_WIDTH = 01.50  # Target force width (N).


class ForceControlHigh(ForceControl):
    TGT_FORCE = 8.00  # Target force (N).
    TGT_FORCE_WIDTH = 02.00  # Target force width (N).


# Some useful functions
def get_task_constants(task):
    """
    Returns the constants for the given task.

    Args:
        task (str): The task name.

    Returns:
        dict: The constants for the task.
    """
    if task == "AROM":
        return AROM()
    elif task == "PROM":
        return PROM()
    elif task == "APROM":
        return APROM()
    elif task == "POSHOLD":
        return PositionHold()
    elif task == "DISC":
        return DiscreteReach()
    elif task == "PROP":
        return Proprioception()
    elif task == "FCTRLLOW":
        return ForceControlLow()
    elif task == "FCTRLMED":
        return ForceControlMed()
    elif task == "FCTRLHIGH":
        return ForceControlHigh()
    else:
        raise ValueError(f"Unknown task: {task}")


def is_task_included(taskname: str, limb: str, afflimb: str) -> bool:
    """Whether the task is included for the given limb and affected limb.
    Subject type is no longer used (all subjects are stroke)."""
    return TASK_DEPENDENCIES[taskname]["in_unaffected"] or limb == afflimb


def assessment_protocol_path(subjid: str, limb: str, timepoint: str) -> pathlib.Path:
    """Path to the assessment protocol CSV for a subject/limb/timepoint."""
    return pathlib.Path(
        DATA_DIR, subjid, limb, timepoint,
        f"{subjid}_{limb}_{timepoint}_protocol.csv",
    )


def is_assessment_timepoint_completed(subjid: str, limb: str, timepoint: str) -> bool:
    """True if the assessment protocol for this timepoint exists and has no
    unfinished (NaN session) rows."""
    _proto = assessment_protocol_path(subjid, limb, timepoint)
    if not _proto.exists():
        return False
    try:
        _df = pd.read_csv(
            _proto.as_posix(), header=0, index_col=None,
            dtype=SUMMARY_COLUMN_FORMAT,
        )
        return not _df["session"].isna().any()
    except Exception:
        return False

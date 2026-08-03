"""Builds the embedded task widget for a step.

The assessinfo dicts are copied from plutofullassessment.py so the task windows
receive exactly what they receive in the old GUI."""

from PySide6 import QtWidgets

import plutofullassessdef as pfadef
from plutoapromwindow import PlutoAPRomAssessWindow
from plutoassistpromwindow import PlutoAssistPRomAssessWindow
from plutocalibwindow import PlutoCalibrationWindow
from plutodiscreachwindow import PlutoDiscReachAssessWindow
from plutofullassesssdata import PlutoAssessmentData
from qtpluto import QtPluto

from newgui.sequencer import CALIB, Step


def build_page(step: Step, pluto: QtPluto, data: PlutoAssessmentData, onclosecb):
    if step.task == CALIB:
        return _calib_page(step, pluto, data, onclosecb)
    if step.task == "AROM":
        return _rom_page(step, pluto, data, onclosecb, pfadef.ROMType.ACTIVE)
    if step.task == "PROM":
        return _rom_page(step, pluto, data, onclosecb, pfadef.ROMType.PASSIVE)
    if step.task == "APROM":
        return _aprom_page(step, pluto, data, onclosecb)
    if step.task == "DISC":
        return _disc_page(step, pluto, data, onclosecb)
    raise ValueError(f"No page for task [{step.task}]")


def _calib_page(step, pluto, data, onclosecb):
    return PlutoCalibrationWindow(
        plutodev=pluto,
        mechanism=step.mech,
        limb=data.limb,
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )


def _rom_page(step, pluto, data, onclosecb, romtype):
    _protocol = data.protocol
    _info = {
        "type": "stroke",
        "limb": data.limb,
        "mechanism": step.mech,
        "romtype": romtype,
        "session": data.session,
        "ntrials": _protocol.get_no_of_trials(step.mech, step.task),
        "rawfile": _protocol.rawfilename,
        "summaryfile": _protocol.summaryfilename,
    }
    if romtype == pfadef.ROMType.PASSIVE:
        # PROM boundaries come from AROM's best cycle; None when AROM was not
        # completed, which makes the window fall back to a plain display.
        _info["arom"] = data.detailedsummary.get_arom_if_completed()
    return PlutoAPRomAssessWindow(
        plutodev=pluto,
        assessinfo=_info,
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )


def _aprom_page(step, pluto, data, onclosecb):
    _protocol = data.protocol
    return PlutoAssistPRomAssessWindow(
        plutodev=pluto,
        assessinfo={
            "type": "stroke",
            "limb": data.limb,
            "mechanism": step.mech,
            "session": data.session,
            "ntrials": _protocol.get_no_of_trials(step.mech, "APROM"),
            "rawfile": _protocol.rawfilename,
            "summaryfile": _protocol.summaryfilename,
            "arom": data.detailedsummary.get_arom(),
            "duration": pfadef.get_task_constants("APROM").DURATION,
            "apromtype": pfadef.APROM.APROMTYPE,
        },
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )


def _disc_page(step, pluto, data, onclosecb):
    _protocol = data.protocol
    return PlutoDiscReachAssessWindow(
        plutodev=pluto,
        assessinfo={
            "subjid": data.subjid,
            "type": "stroke",
            "limb": data.limb,
            "mechanism": step.mech,
            "session": data.session,
            "ntrials": _protocol.get_no_of_trials(step.mech, "DISC"),
            "rawfile": _protocol.rawfilename,
            "summaryfile": _protocol.summaryfilename,
            "arom": data.detailedsummary.get_arom(),
        },
        modal=False,
        embedded=True,
        onclosecb=onclosecb,
    )

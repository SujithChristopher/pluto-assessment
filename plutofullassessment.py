"""
QT script defining the functionality of the PLUTO full assessment main window.

Author: Sivakumar Balasubramanian
Date: 16 May 2025
Email: siva82kb@gmail.com
"""

import itertools
import random
import sys
import re
import time
import pathlib
import json
import numpy as np
import pandas as pd

from enum import Enum

from qtpluto import QtPluto
from datetime import datetime as dt

from PySide6 import (
    QtWidgets,
)
from PySide6.QtCore import (
    QTimer,
)
from PySide6.QtWidgets import QMessageBox, QInputDialog
from PySide6 import QtCore, QtGui, QtWidgets

from plutodataviewwindow import PlutoDataViewWindow
from plutocalibwindow import PlutoCalibrationWindow
from plutotestwindow import PlutoTestControlWindow
from plutoapromwindow import PlutoAPRomAssessWindow
from plutoromwindow import PlutoRomAssessWindow
from plutopropassesswindow import PlutoPropAssessWindow
from plutoforcecontrolwindow import PlutoForceControlWindow
from myqt import MechStartDialog, MechTaskSkipDialog, ScreeningStatsDialog
from uipy.ui_plutofullassessment import Ui_PlutoFullAssessor

import plutodefs as pdef
import plutofullassessdef as pfadef
from sessionsetupwindow import SessionSetupWindow
from plutofullassessstatemachine import PlutoFullAssessmentStateMachine
from plutofullassessstatemachine import Events, States
from plutofullassesssdata import PlutoAssessmentData
from plutoassistpromwindow import PlutoAssistPRomAssessWindow
from plutoposholdwindow import PlutoPositionHoldAssessWindow
from plutodiscreachwindow import PlutoDiscReachAssessWindow
from plutopropassesswindow import PlutoPropAssessWindow
from plutofullassesssdata import DataFrameModel
from async_workers import SessionSetupWorker
from s3sync import S3SyncWorker, load_s3_config


DEBUG = False


# Application-wide theme. Applied once on the QApplication so every task
# window/dialog inherits it. Per-widget stylesheets (e.g. status colours from
# pfadef.STATUS_STYLESHEET, the black device terminal) still override locally.
APP_STYLESHEET = """
QWidget {
    background-color: #f4f6f8;
    color: #202124;
    font-family: "Segoe UI", "Bahnschrift Light";
    font-size: 10pt;
}
QGroupBox {
    border: 1px solid #d0d4d9;
    border-radius: 8px;
    margin-top: 10px;
    padding: 8px 6px 6px 6px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #5f6368;
    font-weight: 600;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #c4c9cf;
    border-radius: 6px;
    padding: 5px 12px;
}
QPushButton:hover {
    background-color: #eef2f7;
    border-color: #9aa4b2;
}
QPushButton:pressed {
    background-color: #e2e8f0;
}
QPushButton:disabled {
    color: #9aa0a6;
    background-color: #f1f3f4;
    border-color: #e3e6ea;
}
/* Primary / accent action button. Set objectName("btnPrimary"). */
QPushButton#btnPrimary {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #1d4ed8;
    font-weight: 600;
    padding: 6px 16px;
}
QPushButton#btnPrimary:hover {
    background-color: #1d4ed8;
    border-color: #1e40af;
}
QPushButton#btnPrimary:pressed {
    background-color: #1e40af;
}
QPushButton#btnPrimary:disabled {
    background-color: #b9c5e6;
    color: #eef2ff;
    border-color: #b9c5e6;
}
/* Leave the QComboBox frame, drop-down arrow and popup to the Fusion style so
   they always render. Styling the combobox border/::drop-down in QSS suppresses
   the native arrow and the popup list (the "invisible picker" bug). We only tidy
   the editable inner line edit and give the popup nicer selection colours. */
QComboBox {
    min-height: 22px;
    padding: 2px 6px;
}
QComboBox QLineEdit {
    border: none;
    background: transparent;
    padding: 0 2px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c4c9cf;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: 0;
    padding: 2px;
}
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #c4c9cf;
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border-color: #2563eb;
}
QLineEdit:disabled {
    background-color: #f1f3f4;
    color: #9aa0a6;
}
QRadioButton {
    spacing: 8px;
    padding: 2px 12px 2px 2px;
    background: transparent;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QRadioButton::indicator:unchecked {
    border: 1px solid #c4c9cf;
    border-radius: 9px;
    background: #ffffff;
}
QRadioButton::indicator:checked {
    border: 5px solid #2563eb;
    border-radius: 9px;
    background: #ffffff;
}
QLabel {
    background: transparent;
}
/* Window header / subtitle helpers (set objectName). */
QLabel#lblTitle {
    font-size: 15pt;
    font-weight: 600;
    color: #1f2937;
}
QLabel#lblSubtitle {
    color: #6b7280;
}
QLabel#lblHint {
    color: #2563eb;
}
QFrame#hsep {
    background-color: #e5e7eb;
    max-height: 1px;
    min-height: 1px;
    border: none;
}
QTableView {
    border: 1px solid #d0d4d9;
    border-radius: 6px;
    background-color: #ffffff;
    gridline-color: #e8eaed;
    alternate-background-color: #f7f9fb;
    selection-background-color: #dbe6fe;
    selection-color: #1f2937;
}
QHeaderView::section {
    background-color: #eceff1;
    border: none;
    border-right: 1px solid #e0e3e7;
    border-bottom: 1px solid #d0d4d9;
    padding: 4px 6px;
    color: #3c4043;
    font-weight: 600;
}
QStatusBar {
    background-color: #eceff1;
    color: #3c4043;
    border-top: 1px solid #d8dce0;
}
QToolTip {
    background-color: #1f2937;
    color: #ffffff;
    border: none;
    padding: 4px 6px;
    border-radius: 4px;
}
"""


class PlutoFullAssesor(QtWidgets.QMainWindow, Ui_PlutoFullAssessor):
    """Main window of the PLUTO proprioception assessment program."""

    def __init__(self, port, *args, **kwargs) -> None:
        """View initializer."""
        super(PlutoFullAssesor, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # UI file locks window to 1200x607 — clear both constraints before maximizing
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.lblSubjDetails.setMaximumSize(16777215, 16777215)

        # Restructure the loose left-column controls into titled group boxes.
        self._group_left_column()

        self.showMaximized()

        self._flag = False
        self._subjdetails = ""
        self._title = "Pluto Full Assessment"

        # PLUTO COM
        self.pluto: QtPluto = QtPluto(port)
        self.pluto.newdata.connect(self._callback_newdata)
        self.pluto.btnpressed.connect(self._callback_btn_pressed)
        self.pluto.btnreleased.connect(self._callback_btn_released)

        # Get the version and device information
        self.pluto.get_version()
        self.pluto.start_sensorstream()

        # Assessment data
        self.data: PlutoAssessmentData = PlutoAssessmentData()

        # Initialize timers.
        self._init_timers()

        # Initialize the state machine.
        self._smachine = PlutoFullAssessmentStateMachine(
            plutodev=self.pluto, data=self.data, progconsole=self.textProtocolDetails
        )

        # Initialize worker thread for async operations
        self._setup_worker = None

        if DEBUG:
            self.data.setup_session({
                "mode": "assessment", "subjid": "1234", "limb": "left",
                "afflimb": "left", "domlimb": "right", "timepoint": "A0",
            })
            self.data.create_session_folder()
            self.data.start_protocol()
            self.pluto.send_heartbeat()
            self.pluto.set_limb(self.data.limb)
            self._smachine.run_statemachine(Events.SETUP_DONE, {})

        # Attach callback to the buttons
        self._attach_guicontrol_callbacks()

        # Other windows
        self._init_task_windowvariables()

        # Update UI
        # A flag to disable the main window when another window is open.
        self._maindisable = False
        self._updatetable = True
        self.update_ui()

        # One time set up
        self._one_time_setup()

        # Background S3 sync. Mirrors the whole data tree (fullassessment +
        # screening) to the bucket; local files stay the source of truth.
        self._last_sync_kick = 0.0
        self._s3sync = S3SyncWorker(
            root=pfadef.homer_data_root(),
            config=load_s3_config(),
        )
        self._s3sync.status.connect(self._on_s3_status)
        self._s3sync.start()

    @property
    def protocol(self):
        return self.data.protocol

    #
    # Controls callback
    #
    def _attach_guicontrol_callbacks(self):
        # Session setup (combined subject + limb + timepoint)
        self.pbSetupSession.clicked.connect(self._callback_setup_session)
        # Mechanisms and skip
        self.pbWFE.clicked.connect(self._callback_wfe_assess)
        self.pbWFESkip.clicked.connect(self._callback_wfe_skip)
        self.pbWURD.clicked.connect(self._callback_wurd_assess)
        self.pbWURDSkip.clicked.connect(self._callback_wurd_skip)
        self.pbFPS.clicked.connect(self._callback_fps_assess)
        self.pbFPSSkip.clicked.connect(self._callback_fps_skip)
        self.pbHOC.clicked.connect(self._callback_hoc_assess)
        self.pbHOCSkip.clicked.connect(self._callback_hoc_skip)
        # Calibration
        self.pbCalibrate.clicked.connect(self._callback_calibrate)
        # Tasks and skip
        self.pbAROM.clicked.connect(self._callback_assess_arom)
        self.pbAROMSkip.clicked.connect(self._callback_skip_arom)
        self.pbPROM.clicked.connect(self._callback_assess_prom)
        self.pbPROMSkip.clicked.connect(self._callback_skip_prom)
        self.pbAPROMSlow.clicked.connect(self._callback_assess_aprom)
        self.pbAPROMSlowSkip.clicked.connect(self._callback_skip_aprom)
        self.pbPosHold.clicked.connect(self._callback_poshold)
        self.pbPosHoldSkip.clicked.connect(self._callback_skip_poshold)
        self.pbDiscReach.clicked.connect(self._callback_disc_reach)
        self.pbDiscReachSkip.clicked.connect(self._callback_skip_disc_reach)
        self.pbProp.clicked.connect(self._callback_assess_prop)
        self.pbPropSkip.clicked.connect(self._callback_skip_prop)
        self.pbForceCtrlLow.clicked.connect(self._callback_assess_fctrllow)
        self.pbForceCtrlLowSkip.clicked.connect(self._callback_skip_fctrllow)
        self.pbForceCtrlMed.clicked.connect(self._callback_assess_fctrlmed)
        self.pbForceCtrlMedSkip.clicked.connect(self._callback_skip_fctrlmed)
        self.pbForceCtrlHigh.clicked.connect(self._callback_assess_fctrlhigh)
        self.pbForceCtrlHighSkip.clicked.connect(self._callback_skip_fctrlhigh)
        # self.pbStartMechAssessment.clicked.connect(self._callback_start_mech_assess)
        # self.pbSkipMechanismAssessment.clicked.connect(self._callback_skip_mech_assess)

    def _callback_setup_session(self):
        self._maindisable = True
        self._currwndclosed = False
        self._subjwnd = SessionSetupWindow(
            parent=self, modal=True, onclosecb=self._setupwnd_close_event
        )
        self._subjwnd.show()

    def _setupwnd_close_event(self, data):
        if self._currwndclosed is True:
            self._subjwnd = None
            return
        self._currwndclosed = True
        self._maindisable = False
        if data:
            # Store fields, then build folder + protocol off the UI thread.
            self.data.setup_session(data)
            self.statusBar().showMessage("Creating session folder and protocol... Please wait.")
            self._maindisable = True
            self._setup_worker = SessionSetupWorker(self.data)
            self._setup_worker.progress.connect(self._on_setup_worker_progress)
            self._setup_worker.finished.connect(self._on_setup_worker_finished)
            self._setup_worker.error.connect(self._on_setup_worker_error)
            self._setup_worker.start()
        else:
            self._updatetable = True
            self.update_ui()

    def _on_setup_worker_progress(self, message):
        self.statusBar().showMessage(message)

    def _on_setup_worker_finished(self):
        try:
            self._smachine.run_statemachine(Events.SETUP_DONE, {})
            self._subjdetails = self._get_subject_details()
            self._title = " | ".join([
                "Pluto Full Assessment", self.data.subjid, self.data.mode,
                f"Dom: {self.data.domlimb}", f"Aff: {self.data.afflimb}",
                f"Limb: {self.data.limb}",
                f"TP: {self.data.timepoint}" if not self.data.is_screening else "screening",
                f"{self.data.session}",
            ])
            self.setWindowTitle(self._title)
            self.statusBar().showMessage("Session setup completed successfully.")
        except Exception as e:
            self._on_setup_worker_error(f"Error updating UI after setup: {str(e)}")
        finally:
            self._maindisable = False
            self._updatetable = True
            self._setup_worker = None
            self.update_ui()

    def _on_setup_worker_error(self, error_message):
        self._maindisable = False
        self._setup_worker = None
        QMessageBox.critical(self, "Error", f"Error during session setup:\n{error_message}")
        self.statusBar().showMessage("Error during session setup.")
        self.update_ui()

    def _callback_calibrate(self):
        # Disable main controls
        self._maindisable = True
        # Calibration window and open it as a modal window.
        self._calibwnd = PlutoCalibrationWindow(
            plutodev=self.pluto,
            mechanism=self.protocol.mech,
            limb=self.data.limb,
            modal=True,
            onclosecb=self._calibwnd_close_event,
        )
        self._calibwnd.show()
        self._currwndclosed = False

    def _callback_test_device(self):
        # Disable main controls
        self._maindisable = True
        self._testdevwnd = PlutoTestControlWindow(plutodev=self.pluto, modal=True)
        self._testdevwnd.closeEvent = self._testwnd_close_event
        self._testdevwnd.show()

    def _callback_assess_arom(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.AROM_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._romwnd = PlutoAPRomAssessWindow(
            plutodev=self.pluto,
            assessinfo={
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "romtype": pfadef.ROMType.ACTIVE,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(self.protocol.mech, "AROM"),
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
            },
            modal=True,
            onclosecb=self._aromwnd_close_event,
        )
        self._romwnd.show()
        self._currwndclosed = False

    def _callback_skip_arom(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip AROM? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.AROM_SKIP,
                {"session": self.data.session, "comment": _skipcomment},
            )
        self.update_ui()

    def _callback_assess_prom(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.PROM_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        # PROM boundaries come from AROM (best cycle) for all mechanisms, HOC
        # included. If AROM was skipped/terminated (subject did not qualify),
        # no boundaries/centre are shown and PROM falls back to plain display.
        _arom = self.data.detailedsummary.get_arom_if_completed()
        self._romwnd = PlutoAPRomAssessWindow(
            plutodev=self.pluto,
            assessinfo={
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "romtype": pfadef.ROMType.PASSIVE,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(self.protocol.mech, "PROM"),
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": _arom,
            },
            modal=True,
            onclosecb=self._promwnd_close_event,
        )
        self._romwnd.show()
        self._currwndclosed = False

    def _callback_skip_prom(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip PROM? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.PROM_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_assess_aprom(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.APROM_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._romwnd = PlutoAssistPRomAssessWindow(
            plutodev=self.pluto,
            assessinfo={
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(
                    self.protocol.mech, "APROM"
                ),
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": self.data.detailedsummary.get_arom(),
                "duration": pfadef.get_task_constants("APROM").DURATION,
                "apromtype": pfadef.APROM.APROMTYPE,
            },
            modal=True,
            onclosecb=self._apromwnd_close_event,
        )
        self._romwnd.show()
        self._currwndclosed = False

    def _callback_skip_aprom(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip Assisted PROM? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.APROM_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_poshold(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.POSHOLD_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._discwnd = PlutoPositionHoldAssessWindow(
            plutodev=self.pluto,
            assessinfo={
                "subjid": self.data.subjid,
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(
                    self.protocol.mech, "POSHOLD"
                ),
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": self.data.detailedsummary.get_arom(),
            },
            modal=True,
            onclosecb=self._posholdhwnd_close_event,
        )
        self._discwnd.show()
        self._currwndclosed = False

    def _callback_skip_poshold(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip Position Hold? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.POSHOLD_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_disc_reach(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.DISCREACH_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._discwnd = PlutoDiscReachAssessWindow(
            plutodev=self.pluto,
            assessinfo={
                "subjid": self.data.subjid,
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(self.protocol.mech, "DISC"),
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": self.data.detailedsummary.get_arom(),
            },
            modal=True,
            onclosecb=self._discreachwnd_close_event,
        )
        self._discwnd.show()
        self._currwndclosed = False

    def _callback_skip_disc_reach(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip Discrete Reach? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.DISCREACH_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_assess_prop(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.PROP_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._discwnd = PlutoPropAssessWindow(
            plutodev=self.pluto,
            assessinfo={
                "subjid": self.data.subjid,
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(self.protocol.mech, "PROP"),
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": self.data.detailedsummary.get_arom(),
                "prom": self.data.detailedsummary.get_prom(),
            },
            modal=True,
            onclosecb=self._propasswnd_close_event,
        )
        self._discwnd.show()
        self._currwndclosed = False

    def _callback_skip_prop(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip Proprioception? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.PROP_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_assess_fctrllow(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.FCTRLLOW_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._discwnd = PlutoForceControlWindow(
            plutodev=self.pluto,
            assessinfo={
                "subjid": self.data.subjid,
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(
                    self.protocol.mech, "FCTRLLOW"
                ),
                "forcetgt": pfadef.get_task_constants("FCTRLLOW").TGT_FORCE,
                "forcetgtwidth": pfadef.get_task_constants("FCTRLLOW").TGT_FORCE_WIDTH,
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": self.data.detailedsummary.get_arom(),
            },
            modal=True,
            onclosecb=self._fctrllowwnd_close_event,
        )
        self._discwnd.show()
        self._currwndclosed = False

    def _callback_skip_fctrllow(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip Force Control Low? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.FCTRLLOW_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_assess_fctrlmed(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.FCTRLMED_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._discwnd = PlutoForceControlWindow(
            plutodev=self.pluto,
            assessinfo={
                "subjid": self.data.subjid,
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(
                    self.protocol.mech, "FCTRLMED"
                ),
                "forcetgt": pfadef.get_task_constants("FCTRLMED").TGT_FORCE,
                "forcetgtwidth": pfadef.get_task_constants("FCTRLMED").TGT_FORCE_WIDTH,
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": self.data.detailedsummary.get_arom(),
            },
            modal=True,
            onclosecb=self._fctrlmedwnd_close_event,
        )
        self._discwnd.show()
        self._currwndclosed = False

    def _callback_skip_fctrlmed(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip Force Control Low? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.FCTRLMED_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_assess_fctrlhigh(self):
        # Run the state machine.
        self._smachine.run_statemachine(Events.FCTRLHIGH_ASSESS, None)
        # Disable main controls
        self._maindisable = True
        self._discwnd = PlutoForceControlWindow(
            plutodev=self.pluto,
            assessinfo={
                "subjid": self.data.subjid,
                "type": "stroke",
                "limb": self.data.limb,
                "mechanism": self.protocol.mech,
                "session": self.data.session,
                "ntrials": self.protocol.get_no_of_trials(
                    self.protocol.mech, "FCTRLHIGH"
                ),
                "forcetgt": pfadef.get_task_constants("FCTRLHIGH").TGT_FORCE,
                "forcetgtwidth": pfadef.get_task_constants("FCTRLHIGH").TGT_FORCE_WIDTH,
                "rawfile": self.protocol.rawfilename,
                "summaryfile": self.protocol.summaryfilename,
                "arom": self.data.detailedsummary.get_arom(),
            },
            modal=True,
            onclosecb=self._fctrlhighwnd_close_event,
        )
        self._discwnd.show()
        self._currwndclosed = False

    def _callback_skip_fctrlhigh(self):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label=f"Sure you want to skip Force Control Low? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.FCTRLHIGH_SKIP,
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    def _callback_wfe_assess(self):
        self._callback_start_mech_assess("WFE")
        self.update_ui()

    def _callback_fps_assess(self):
        self._callback_start_mech_assess("FPS")
        self.update_ui()

    def _callback_hoc_assess(self):
        self._callback_start_mech_assess("HOC")
        self.update_ui()

    def _callback_wfe_skip(self):
        self._callback_skip_mech_assess("WFE")
        self.update_ui()

    def _callback_wurd_assess(self):
        self._callback_start_mech_assess("WURD")
        self.update_ui()

    def _callback_wurd_skip(self):
        self._callback_skip_mech_assess("WURD")
        self.update_ui()

    def _callback_fps_skip(self):
        self._callback_skip_mech_assess("FPS")
        self.update_ui()

    def _callback_hoc_skip(self):
        self._callback_skip_mech_assess("HOC")
        self.update_ui()

    def _callback_start_mech_assess(self, mech_chosen):
        # Dialog to confirm mechanism selection, with image.
        _img_map = {
            "WFE": "wfe.png",
            "WURD": "wfe.png",
            "FPS": "fps.png",
            "HOC": "hoc.png",
        }
        _imgpath = pathlib.Path(__file__).parent / "assets" / _img_map[mech_chosen]
        _dlg = MechStartDialog(self, mech_name=mech_chosen, img_path=_imgpath)
        if _dlg.exec() != QtWidgets.QDialog.Accepted:
            # Cancel the radio button selection.
            self._reset_mech_selection()
        # Run the state machine.
        # Get the appropriate event.
        _mechevent = {
            "WFE": Events.WFE_SET,
            "WURD": Events.WURD_SET,
            "FPS": Events.FPS_SET,
            "HOC": Events.HOC_SET,
        }
        self._smachine.run_statemachine(_mechevent[mech_chosen], {})
        self._flag = True
        self.update_ui()

    def _callback_skip_mech_assess(self, mech_chosen):
        # Check if the chosen mechanism is already assessed.
        _comment = MechTaskSkipDialog(
            label="Sure you want to skip? If so give the reason.",
        )
        if _comment.exec() == QtWidgets.QDialog.Accepted:
            _skipcomment = _comment.getText()
            # Run the state machine.
            # Get the appropriate event.
            _mechevent = {
                "WFE": Events.WFE_SKIP,
                "WURD": Events.WURD_SKIP,
                "FPS": Events.FPS_SKIP,
                "HOC": Events.HOC_SKIP,
            }

            self._smachine.run_statemachine(
                _mechevent[mech_chosen],
                {"comment": _skipcomment, "session": self.data.session},
            )
        self.update_ui()

    #
    # Timer callbacks
    #
    def _init_timers(self):
        # Status timer
        self.statustimer = QTimer()
        self.statustimer.timeout.connect(self._callback_status_timer)
        self.statustimer.start(1000)
        self.apptime = 0
        # Display timer
        self.displaytimer = QTimer()
        self.displaytimer.timeout.connect(self._callback_display_timer)
        self.displaytimer.start(pfadef.DISPLAY_INTERVAL)
        # Heartbeat timer
        self.heartbeattimer = QTimer()
        self.heartbeattimer.timeout.connect(lambda: self.pluto.send_heartbeat())
        self.heartbeattimer.start(250)

    def _callback_status_timer(self):
        self.apptime += 1
        _con = self.pluto.is_connected()
        self.statusBar().showMessage(
            " | ".join(
                (
                    f"{self.apptime:5d}s",
                    _con if _con != "" else "Disconnected",
                    f"FR: {self.pluto.framerate():4.1f}Hz",
                    f"{self.data.subjid}",
                    f"{self._smachine.state.name:<20}",
                )
            )
        )

    def _callback_display_timer(self):
        # Check if new data is available
        if self.pluto.is_data_available() is False:
            self.textPlutoData.setText("No data available.")
            return
        # New data available. Format and display
        _dispdata = [
            f"Dev Name  : {self.pluto.devname} | {self.pluto.version} ({self.pluto.compliedate})",
            f"Time      : {self.pluto.systime} | {self.pluto.currt:6.3f}s | {self.pluto.packetnumber:06d}",
        ]
        _statusstr = " | ".join(
            (
                pdef.get_name(pdef.OutDataType, self.pluto.datatype),
                pdef.get_name(pdef.ControlTypes, self.pluto.controltype),
                pdef.get_name(pdef.CalibrationStatus, self.pluto.calibration),
            )
        )
        _dispdata += [
            f"Status    : {_statusstr}",
            f"Error     : {pdef.get_name(pdef.ErrorTypes, self.pluto.error)}",
            f"Limb-Mech : {pdef.get_name(pdef.Mechanisms, self.pluto.mechanism):<6s} |  {pdef.get_name(pdef.CalibrationStatus, self.pluto.calibration)}",
            f"Button    : {self.pluto.button}",
            "",
        ]
        _dispdata += [
            "~ SENSOR DATA ~",
            f"Angle     : {self.pluto.angle:-07.2f}deg"
            + (
                f" [{self.pluto.hocdisp:05.2f}cm]"
                if self.pluto.calibration == 1
                else ""
            ),
        ]
        _dispdata += [
            f"Control   : {self.pluto.control:3.1f}",
            f"Target    : {self.pluto.target:3.1f} | Desired  : {self.pluto.desired:3.1f}",
        ]
        # Check if in DIAGNOSTICS mode.
        if pdef.get_name(pdef.OutDataType, self.pluto.datatype) == "DIAGNOSTICS":
            _dispdata += [
                f"Err       : {self.pluto.err:3.1f}",
                f"ErrDiff   : {self.pluto.errdiff:3.1f}",
                f"ErrSum    : {self.pluto.errsum:3.1f}",
            ]
        self.textPlutoData.setText("\n".join(_dispdata))

    #
    # Signal callbacks
    #
    def _callback_newdata(self):
        """Update the UI of the appropriate window."""
        # Update data viewer window.
        if np.random.rand() < 0.01:
            self.update_ui()

    def _callback_btn_pressed(self):
        pass

    def _callback_btn_released(self):
        pass

    def _callback_promset(self):
        """Set PROM."""
        self._romdata["PROM"] = self._romwnd.prom

    #
    # Other callbacks
    #
    def _calibwnd_close_event(self, data=None):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._calibwnd = None
            return
        # Window not closed.
        # Reenable main controls
        self._maindisable = False
        # Check of the calibration was successful.
        if (
            pdef.get_name(pdef.Mechanisms, self.pluto.mechanism) == self.protocol.mech
            and self.pluto.calibration == 1
        ):
            # Run the state machine.
            self._smachine.run_statemachine(
                Events.CALIB_DONE if data["done"] else Events.CALIB_NO_DONE,
                {"mech": pdef.get_name(pdef.Mechanisms, self.pluto.mechanism)},
            )
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _testwnd_close_event(self, data=None):
        self._testdevwnd = None
        # Reenable main controls
        self._maindisable = False

    def _aromwnd_close_event(self, data=None):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._romwnd = None
            return
        # Window not closed.
        # Handle assessor-initiated AROM skip.
        if data.get("status") == pfadef.AssessStatus.SKIPPED.value:
            self._smachine.run_statemachine(
                Events.AROM_SKIP,
                {
                    "session": self.data.session,
                    "comment": data.get("taskcomment", "Skipped by assessor"),
                },
            )
            self._maindisable = False
            self._updatetable = True
            self._currwndclosed = True
            self.update_ui()
            return
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.AROM_DONE if task_completed else Events.AROM_REJECT)
            if data["done"]
            else Events.AROM_NO_DONE,
            data,
        )
        # Auto-skip DISC if AROM range is below the movement threshold.
        if task_completed and data["done"] and "DISC" in self.data.protocol.task_not_completed:
            _mech = self.data.protocol.mech
            _threshold = 2.0 if _mech == "HOC" else 10.0
            _unit = "cm" if _mech == "HOC" else "deg"
            # No valid [min, max] recorded (e.g. every trial failed on the time
            # limit) — treat as not meeting the threshold rather than indexing nan.
            _arom = self.data.detailedsummary.get_arom_if_completed()
            if _arom is None:
                self._smachine.run_statemachine(
                    Events.DISCREACH_SKIP,
                    {
                        "comment": "No valid AROM recorded",
                        "session": self.data.session,
                    },
                )
            elif abs(_arom[1] - _arom[0]) < _threshold:
                _arom_range = abs(_arom[1] - _arom[0])
                self._smachine.run_statemachine(
                    Events.DISCREACH_SKIP,
                    {
                        "comment": f"AROM {_arom_range:.2f}{_unit} below {_threshold}{_unit} threshold",
                        "session": self.data.session,
                    },
                )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _promwnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._romwnd = None
            return
        # Window not closed.
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.PROM_DONE if task_completed else Events.PROM_REJECT)
            if data["done"]
            else Events.PROM_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _apromwnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._romwnd = None
            return
        # Window not closed.
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.APROM_DONE if task_completed else Events.APROM_REJECT)
            if data["done"]
            else Events.APROM_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _posholdhwnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._discwnd = None
            return
        # Window not closed.
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.POSHOLD_DONE if task_completed else Events.POSHOLD_REJECT)
            if data["done"]
            else Events.POSHOLD_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _discreachwnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._discwnd = None
            return
        # Window not closed.
        # Run the state machine.
        print(data)
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.DISCREACH_DONE if task_completed else Events.DISCREACH_REJECT)
            if data["done"]
            else Events.DISCREACH_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _propasswnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._discwnd = None
            return
        # Window not closed.
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.PROP_DONE if task_completed else Events.PROP_REJECT)
            if data["done"]
            else Events.PROP_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _fctrllowwnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._discwnd = None
            return
        # Window not closed.
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.FCTRLLOW_DONE if task_completed else Events.FCTRLLOW_REJECT)
            if data["done"]
            else Events.FCTRLLOW_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _fctrlmedwnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._discwnd = None
            return
        # Window not closed.
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.FCTRLMED_DONE if task_completed else Events.FCTRLMED_REJECT)
            if data["done"]
            else Events.FCTRLMED_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    def _fctrlhighwnd_close_event(self, data):
        # Check if the window is already closed.
        if self._currwndclosed is True:
            self._discwnd = None
            return
        # Window not closed.
        # Run the state machine.
        task_completed = data["status"] == pfadef.AssessStatus.COMPLETE.value
        self._smachine.run_statemachine(
            (Events.FCTRLHIGH_DONE if task_completed else Events.FCTRLHIGH_REJECT)
            if data["done"]
            else Events.FCTRLHIGH_NO_DONE,
            data,
        )
        # Reenable main controls
        self._maindisable = False
        # Update the Table.
        self._updatetable = True
        # Set the window closed flag.
        self._currwndclosed = True
        self.update_ui()

    #
    # UI Update function
    #
    def update_ui(self):
        self.setWindowTitle(self._title)
        # Session setup
        self.pbSetupSession.setEnabled(
            self._maindisable is False and self._smachine.state == States.SUBJ_SELECT
        )
        self.lblSubjDetails.setText(self._subjdetails)

        # Update the table.
        if self.protocol and self.protocol.df is not None and self._updatetable:
            self.tableProtocolProgress.setModel(DataFrameModel(self.protocol.df))
            self.tableProtocolProgress.setAlternatingRowColors(True)
            self.tableProtocolProgress.horizontalHeader().setStretchLastSection(True)
            # Optional: also shrink rows to contents
            self.tableProtocolProgress.resizeRowsToContents()
            # Set fixed row height for uniformity
            self.tableProtocolProgress.verticalHeader().setDefaultSectionSize(20)
            self._updatetable = False

        # Screening eligibility banner (screening mode only). Updates live as
        # each mechanism's AROM is recorded.
        if hasattr(self, "lblEligibility"):
            _screening = self.data is not None and self.data.is_screening
            self.lblEligibility.setVisible(_screening)
            self.pbViewStats.setVisible(_screening)
            if _screening and self.data.detailedsummary is not None:
                self._update_eligibility_label()

        # Mechanisms selection
        _mechflag = self._maindisable is False and (
            self._smachine.state == States.MECH_SELECT
            or self._smachine.state == States.MECH_OR_TASK_SELECT
        )
        self.gbMechanisms.setEnabled(_mechflag)

        # Enable the appropriate mechanisms.
        self._update_mech_controls()

        # Check if any mechanism is selected to enable the mechanism assessment start button.
        # self.pbStartMechAssessment.setEnabled(self._any_mechanism_selected())
        # self.pbSkipMechanismAssessment.setEnabled(self._any_incomplete_mechanism_selected())

        # Enable the calibration button.
        calibflag = (
            self._maindisable is False
            and self.protocol is not None
            and self.protocol.mech is not None
            and self.protocol.mech not in self.protocol.mech_completed
        )
        self.pbCalibrate.setEnabled(calibflag)
        if self.pbCalibrate.isEnabled():
            self.pbCalibrate.setStyleSheet(
                pfadef.STATUS_STYLESHEET[pfadef.AssessStatus.COMPLETE]
                if self.protocol.calibrated
                else pfadef.STATUS_STYLESHEET[pfadef.AssessStatus.INCOMPLETE]
            )
        else:
            self.pbCalibrate.setStyleSheet("")

        # Enable the task buttons.
        self._update_task_controls()

        # Update session information.
        self.lblSessionInfo.setText(self._get_session_info())

        # Nudge the background S3 sync (throttled).
        self._maybe_kick_sync()

    #
    # Screening eligibility
    #
    def _update_eligibility_label(self):
        """Refresh the eligibility label from recorded screening AROM values.
        Eligible if ANY mechanism meets its threshold; shows a partial verdict
        until all mechanisms are assessed."""
        _eligible, _stats = self.data.detailedsummary.get_screening_eligibility()
        _ndone = sum(1 for _s in _stats.values() if _s["done"])
        _ntot = len(_stats)
        if _ndone == 0:
            self.lblEligibility.setText("Eligibility: pending")
            self.lblEligibility.setStyleSheet(
                "color: rgb(120,120,120); font-weight: bold;"
            )
            return
        _verdict = "ELIGIBLE" if _eligible else "NOT ELIGIBLE"
        _suffix = "" if _ndone == _ntot else f" (partial {_ndone}/{_ntot})"
        self.lblEligibility.setText(f"{_verdict}{_suffix}")
        self.lblEligibility.setStyleSheet(
            "color: rgb(0,120,0); font-weight: bold;"
            if _eligible
            else "color: rgb(170,0,0); font-weight: bold;"
        )

    def _show_screening_stats(self):
        """Popup the per-mechanism screening AROM stats dialog."""
        if self.data is None or self.data.detailedsummary is None:
            return
        _eligible, _stats = self.data.detailedsummary.get_screening_eligibility()
        _dlg = ScreeningStatsDialog(
            _eligible, _stats, mech_labels=pfadef.MECH_LABELS, parent=self
        )
        _dlg.exec()

    #
    # S3 sync indicator
    #
    def _on_s3_status(self, state, pending, message):
        """Update the top-right sync indicator from S3SyncWorker signals."""
        _map = {
            "disabled": ("⚪ Sync off", "#9aa0a6"),
            "offline": ("⚪ Offline ↻", "#9aa0a6"),
            "syncing": (f"\U0001f535 Syncing… ({pending})", "#2563eb"),
            "synced": ("\U0001f7e2 Synced", "#0a7d00"),
            "error": ("\U0001f534 Sync error", "#c62828"),
        }
        _text, _color = _map.get(state, ("", "#000000"))
        self.lblS3Sync.setText(_text)
        self.lblS3Sync.setStyleSheet(f"color:{_color}; font-weight:600;")
        self.lblS3Sync.setToolTip(message or "")

    def _maybe_kick_sync(self):
        """Nudge the sync worker to sweep now (throttled to once per 5s).
        Called from update_ui so a just-finalised task uploads promptly without
        walking the tree on every UI refresh."""
        if getattr(self, "_s3sync", None) is None:
            return
        _now = time.monotonic()
        if _now - self._last_sync_kick >= 5.0:
            self._last_sync_kick = _now
            self._s3sync.request_sweep()

    #
    # Supporting functions
    #
    def _get_subject_details(self):
        """Get the subject details string."""
        _text = f"{self.data.subjid} | Aff: {self.data.afflimb}"
        if not self.data.is_screening:
            _text += f" | Dom: {self.data.domlimb}"
        return _text

    def _one_time_setup(self):
        font = QtGui.QFont()
        font.setFamily("Bahnschrift Light")
        font.setPointSize(12)
        self.pbWFE.setFont(font)
        self.pbWURD.setFont(font)
        self.pbFPS.setFont(font)
        self.pbHOC.setFont(font)
        self.pbWFESkip.setFont(font)
        self.pbWURDSkip.setFont(font)
        self.pbFPSSkip.setFont(font)
        self.pbHOCSkip.setFont(font)

        # Screening eligibility banner: an "Eligible/Not Eligible" label and a
        # "View Stats" button inserted above the protocol-progress table. Both
        # are shown only in screening mode (toggled in update_ui).
        self.lblEligibility = QtWidgets.QLabel("")
        self.pbViewStats = QtWidgets.QPushButton("View Stats")
        _elrow = QtWidgets.QHBoxLayout()
        _elrow.addWidget(self.lblEligibility)
        _elrow.addStretch(1)
        _elrow.addWidget(self.pbViewStats)
        self.verticalLayout_5.insertLayout(0, _elrow)
        self.pbViewStats.clicked.connect(self._show_screening_stats)
        self.lblEligibility.setVisible(False)
        self.pbViewStats.setVisible(False)

        # S3 sync status indicator, top-right above the protocol table.
        self.lblS3Sync = QtWidgets.QLabel("")
        _syncrow = QtWidgets.QHBoxLayout()
        _syncrow.addStretch(1)
        _syncrow.addWidget(self.lblS3Sync)
        self.verticalLayout_5.insertLayout(0, _syncrow)

    def _move_into(self, src_layout, dst_layout, item):
        """Move a widget or nested layout from src_layout to dst_layout."""
        if isinstance(item, QtWidgets.QWidget):
            src_layout.removeWidget(item)
            dst_layout.addWidget(item)
        else:
            # QLayout is-a QLayoutItem, so removeItem accepts it directly.
            src_layout.removeItem(item)
            dst_layout.addLayout(item)

    def _group_left_column(self):
        """Wrap the loose left-column controls into titled QGroupBoxes.

        Final order: "Subject & Session", existing "Mechanisms",
        "Tasks". gbMechanisms is left in place; everything above/below it is
        relocated, then the two new groups are inserted around it.
        """
        vl = self.verticalLayout

        # Subject & Session: a single Setup Session button + details label.
        self.gbSession = QtWidgets.QGroupBox("Subject && Session")
        sv = QtWidgets.QVBoxLayout(self.gbSession)
        sv.setSpacing(4)
        self.pbSetupSession = QtWidgets.QPushButton("Setup Session")
        self.pbSetupSession.setObjectName("btnPrimary")
        self.pbSetupSession.setMinimumHeight(34)
        sv.addWidget(self.pbSetupSession)
        self._move_into(vl, sv, self.lblSubjDetails)
        # Old per-field controls from the .ui are no longer used — drop them.
        # Holders keep the discarded nested layouts (and their child widgets)
        # owned/hidden so PySide does not garbage-collect them mid-teardown.
        self._discarded_widgets = []
        for _old in (
            self.pbCreateSeelectSubject, self.pbSelectSubject,
            self.horizontalLayout_2, self.pbSetLimb,
            self.horizontalLayout_timepoint, self.pbSetTimePoint,
        ):
            if isinstance(_old, QtWidgets.QWidget):
                _old.setParent(None)
            else:
                # Nested layout: detach from its parent layout first, then hand
                # it to a hidden holder widget (now legal — it has no parent).
                vl.removeItem(_old)
                _holder = QtWidgets.QWidget()
                _holder.setLayout(_old)
                self._discarded_widgets.append(_holder)

        # Tasks: calibrate + all per-task rows.
        self.gbTasks = QtWidgets.QGroupBox("Tasks")
        tv = QtWidgets.QVBoxLayout(self.gbTasks)
        tv.setSpacing(3)
        for _item in (
            self.pbCalibrate,
            self.horizontalLayout,       # AROM
            self.horizontalLayout_6,     # PROM
            self.horizontalLayout_7,     # APROM (slow)
            self.horizontalLayout_9,     # Discrete reach
            self.horizontalLayout_10,    # Position hold
            self.horizontalLayout_11,    # Proprioception
            self.horizontalLayout_12,    # Force control low
            self.horizontalLayout_13,    # Force control med
            self.horizontalLayout_14,    # Force control high
        ):
            self._move_into(vl, tv, _item)

        # Only gbMechanisms remains in vl now. Bracket it with the new groups.
        vl.insertWidget(0, self.gbSession)
        vl.addWidget(self.gbTasks)
        vl.addStretch(1)

    def _init_task_windowvariables(self):
        self._devdatawnd = None
        self._calibwnd = None
        self._testdevwnd = None
        self._romwnd = None
        self._discwnd = None
        self._propwnd = None
        self._currwndclosed = True
        self._wnddata = {}

    def _get_session_info(self):
        _str = [
            f"{'' if self.data.session is None else self.data.session:<20}",
            f"{'' if self.data.subjid is None else self.data.subjid:<8}",
            f"{(self.data.mode or ''):<10}",
            f"{(self.data.limb or ''):<8}",
            f"{(self.data.timepoint or ''):<4}",
        ]
        return ":".join(_str)

    def _reassess_requested(self, task):
        """ """
        if (
            self.protocol.index is not None
            and task not in self.protocol.task_enabled[:-1]
        ):
            return None
        # Ask the experimenter if this assessment is to be repeated.
        reply = QMessageBox.question(
            self,
            "Reassessment Confirmation",
            f"{task} has been assessed before.\nDo you want to reassess?",
            QMessageBox.Ok | QMessageBox.Cancel,
        )
        return reply == QMessageBox.Ok

    def _update_mech_controls(self):
        if self.protocol is None:
            return
        # Update the text of the radio buttons.
        _mctrl = {
            "WFE": [self.pbWFE, self.pbWFESkip],
            "WURD": [self.pbWURD, self.pbWURDSkip],
            "FPS": [self.pbFPS, self.pbFPSSkip],
            "HOC": [self.pbHOC, self.pbHOCSkip],
        }
        # Update complete/incomplete status of the mechanisms.
        for i, _m in enumerate(self.protocol.mech_enabled):
            _mctrl[_m][0].setEnabled(True)
            _mechstatus = self.protocol.get_mech_status(_m)
            _mctrl[_m][0].setStyleSheet(pfadef.STATUS_STYLESHEET[_mechstatus])
            _mctrl[_m][0].setText(
                f"{pfadef.MECH_LABELS[_m]} {pfadef.STATUS_TEXT[_mechstatus]}"
            )
            # Update the skip buttons
            _mctrl[_m][1].setEnabled(_mechstatus == pfadef.AssessStatus.INCOMPLETE)

    def _update_task_controls(self):
        if self.protocol is None:
            return
        _tctrl = {
            "AROM": [self.pbAROM, self.pbAROMSkip],
            "PROM": [self.pbPROM, self.pbPROMSkip],
            "APROM": [self.pbAPROMSlow, self.pbAPROMSlowSkip],
            "POSHOLD": [self.pbPosHold, self.pbPosHoldSkip],
            "DISC": [self.pbDiscReach, self.pbDiscReachSkip],
            "PROP": [self.pbProp, self.pbPropSkip],
            "FCTRLLOW": [self.pbForceCtrlLow, self.pbForceCtrlLowSkip],
            "FCTRLMED": [self.pbForceCtrlMed, self.pbForceCtrlMedSkip],
            "FCTRLHIGH": [self.pbForceCtrlHigh, self.pbForceCtrlHighSkip],
        }
        import debugconfig
        # Go through all tasks for the mechanism and enable/disable them appropriately.
        for i, _t in enumerate(pfadef.ALLTASKS):
            _taskstatus = self.protocol.get_task_status(_t)
            _task_gate = (
                _taskstatus == pfadef.AssessStatus.INCOMPLETE
                if debugconfig.DEBUG
                else self.protocol.calibrated and _t == self.protocol.task_enabled
            )
            if _task_gate:
                _tctrl[_t][0].setEnabled(_taskstatus == pfadef.AssessStatus.INCOMPLETE)
                _tctrl[_t][0].setStyleSheet(pfadef.STATUS_STYLESHEET[_taskstatus])
                _tctrl[_t][0].setText(
                    f"{pfadef.TASK_LABELS[_t]}{pfadef.STATUS_TEXT[_taskstatus]}"
                )
                _tctrl[_t][1].setEnabled(_taskstatus == pfadef.AssessStatus.INCOMPLETE)
            else:
                _tctrl[_t][0].setEnabled(False)
                _tctrl[_t][0].setStyleSheet(
                    pfadef.STATUS_STYLESHEET[None]
                    if _taskstatus is pfadef.AssessStatus.INCOMPLETE
                    else pfadef.STATUS_STYLESHEET[_taskstatus]
                )
                _tctrl[_t][0].setText(
                    f"{pfadef.TASK_LABELS[_t]}{pfadef.STATUS_TEXT[None]}"
                    if _taskstatus is pfadef.AssessStatus.INCOMPLETE
                    else f"{pfadef.TASK_LABELS[_t]}{pfadef.STATUS_TEXT[_taskstatus]}"
                )
                _tctrl[_t][1].setEnabled(False)

    def _any_mechanism_selected(self):
        """Check if any mechanism is selected."""
        return (
            self.rbWFE.isChecked() or self.rbFPS.isChecked() or self.rbHOC.isChecked()
        )

    def _any_incomplete_mechanism_selected(self):
        """Check if any incomplete mechanism is selected."""
        if self.protocol is None:
            return False
        _wfe_incomplete = (
            self.protocol.get_mech_status("WFE") == pfadef.AssessStatus.INCOMPLETE
        )
        _fps_incomplete = (
            self.protocol.get_mech_status("FPS") == pfadef.AssessStatus.INCOMPLETE
        )
        _hoc_incomplete = (
            self.protocol.get_mech_status("HOC") == pfadef.AssessStatus.INCOMPLETE
        )
        return (
            (self.rbWFE.isChecked() and _wfe_incomplete)
            or (self.rbFPS.isChecked() and _fps_incomplete)
            or (self.rbHOC.isChecked() and _hoc_incomplete)
        )

    def _reset_mech_selection(self):
        """Reset the mechanism selection."""
        for button in self.mechButtonGroup.buttons():
            self.mechButtonGroup.removeButton(button)
            button.setChecked(False)
            self.mechButtonGroup.addButton(button)

    def _get_chosen_mechanism_skip_event(self):
        """Get the event for skipping the selected mechanism."""
        if self.rbWFE.isChecked():
            return Events.WFE_SKIP
        elif self.rbFPS.isChecked():
            return Events.FPS_SKIP
        elif self.rbHOC.isChecked():
            return Events.HOC_SKIP
        else:
            return None

    #
    # Main window close event
    #
    def closeEvent(self, event):
        try:
            if getattr(self, "_s3sync", None) is not None:
                self._s3sync.stop()
                self._s3sync.wait(3000)
        except Exception as e:
            print(f"Error stopping S3 sync: {e}")
        try:
            self.pluto.set_control_type("NONE")
            self.pluto.close()
        except Exception as e:
            print(f"Error during close: {e}")
        # Accept the close event.
        event.accept()


def _build_palette() -> QtGui.QPalette:
    """Light clinical palette. Drives the Fusion style so every native control
    (combobox arrows, popups, scrollbars, spin boxes) renders consistently
    without per-widget stylesheet hacks."""
    c = QtGui.QColor
    pal = QtGui.QPalette()
    pal.setColor(QtGui.QPalette.Window, c("#f4f6f8"))
    pal.setColor(QtGui.QPalette.WindowText, c("#202124"))
    pal.setColor(QtGui.QPalette.Base, c("#ffffff"))
    pal.setColor(QtGui.QPalette.AlternateBase, c("#f7f9fb"))
    pal.setColor(QtGui.QPalette.Text, c("#202124"))
    pal.setColor(QtGui.QPalette.Button, c("#ffffff"))
    pal.setColor(QtGui.QPalette.ButtonText, c("#202124"))
    pal.setColor(QtGui.QPalette.Highlight, c("#2563eb"))
    pal.setColor(QtGui.QPalette.HighlightedText, c("#ffffff"))
    pal.setColor(QtGui.QPalette.ToolTipBase, c("#1f2937"))
    pal.setColor(QtGui.QPalette.ToolTipText, c("#ffffff"))
    pal.setColor(QtGui.QPalette.PlaceholderText, c("#9aa0a6"))
    for _role in (QtGui.QPalette.Text, QtGui.QPalette.ButtonText,
                  QtGui.QPalette.WindowText):
        pal.setColor(QtGui.QPalette.Disabled, _role, c("#9aa0a6"))
    return pal


def apply_theme(app: QtWidgets.QApplication):
    """Apply the Fusion style + palette + light stylesheet. Shared so the
    standalone Session Setup preview and the main app look identical."""
    app.setStyle("Fusion")
    app.setPalette(_build_palette())
    app.setStyleSheet(APP_STYLESHEET)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    apply_theme(app)
    mywin = PlutoFullAssesor(pfadef.PLUTOCOMM)
    # ImageUpdate()
    mywin.show()
    sys.exit(app.exec())

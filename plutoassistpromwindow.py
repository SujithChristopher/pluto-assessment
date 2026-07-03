"""
Module for handling the operation of the PLUTO active, passive, and assisted
passive range of motion assesmsent window.

Author: Sivakumar Balasubramanian
Date: 22 May 2025
Email: siva82kb@gmail.com
"""

import sys
import numpy as np

from qtpluto import QtPluto

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Signal
import pyqtgraph as pg
from enum import Enum

import plutodefs as pdef
import plutofullassessdef as pfadef
import misc
from uipy.ui_plutoapromassess import Ui_APRomAssessWindow
from myqt import CommentDialog

from plutodataviewwindow import PlutoDataViewWindow

import plutoapromwindow as apromwnd


class States(Enum):
    REST = 0
    WAIT_TO_MOVE = 1
    TORQ_DIR1 = 2
    TORQ_DIR2 = 3
    MOVING_DIR1 = 4
    DIR1_TO_REST = 5
    MOVING_DIR2 = 6
    DIR2_TO_REST = 7
    IN_STOPZONE = 8
    DONE = 9


class Actions(Enum):
    NO_CTRL = 0
    TORQ_CTRL = 1
    TORQ_TGT_DIR1 = 2
    TORQ_TGT_DIR2 = 3
    TORQ_TGT_ZERO = 4
    DO_NOTHING = 5
    TORQ_TGT_RAMP = 6  # ramp the torque 0 -> target, then hold


class AssistPRomData(object):
    def __init__(self, assessinfo: dict):
        self._assessinfo = assessinfo
        self._demomode = None
        # Trial variables
        self._currtrial = 0
        self._startpos = None
        self._trialrom = []
        self._trialdata = {"dt": [], "pos": [], "vel": []}
        self._currtrial = -1
        # ROM data
        self._rom = [[] for _ in range(self.ntrials)]
        # Logging variables
        self._logstate: apromwnd.RawDataLoggingState = (
            apromwnd.RawDataLoggingState.WAIT_FOR_LOG
        )
        self._rawfilewriter: misc.CSVBufferWriter = misc.CSVBufferWriter(
            self.rawfile, header=pfadef.APROM.RAW_HEADER
        )
        self._summaryfilewriter: misc.CSVBufferWriter = misc.CSVBufferWriter(
            self.summaryfile,
            header=pfadef.APROM.SUMMARY_HEADER,
            flush_interval=0.0,
            max_rows=1,
        )

    @property
    def type(self):
        return self._assessinfo["type"]

    @property
    def limb(self):
        return self._assessinfo["limb"]

    @property
    def mechanism(self):
        return self._assessinfo["mechanism"]

    @property
    def romtype(self):
        return pfadef.ROMType.ASSISTED_PASSIVE

    @property
    def session(self):
        return self._assessinfo["session"]

    @property
    def ntrials(self):
        return self._assessinfo["ntrials"]

    @property
    def duration(self):
        return self._assessinfo["duration"]

    @property
    def apromtype(self):
        return self._assessinfo["apromtype"]

    @property
    def rawfile(self):
        return self._assessinfo["rawfile"]

    @property
    def summaryfile(self):
        return self._assessinfo["summaryfile"]

    @property
    def current_trial(self):
        return self._currtrial

    @property
    def rom(self):
        return self._rom

    @property
    def startpos(self):
        return self._startpos

    @property
    def trialdata(self):
        return self._trialdata

    @property
    def demomode(self):
        return self._demomode

    @demomode.setter
    def demomode(self, value):
        self._demomode = value

    @property
    def logstate(self):
        return self._logstate

    @property
    def all_trials_done(self):
        """Check if all trials are done."""
        return self._currtrial >= self.ntrials

    @property
    def rawfilewriter(self):
        return self._rawfilewriter

    def start_newtrial(self, reset: bool = False):
        """Start a new trial."""
        if self._currtrial < self.ntrials:
            self._trialdata = {"dt": [], "pos": [], "vel": []}
            self._trialrom = []
            self._startpos = None
            self._currtrial = 0 if reset else self._currtrial + 1

    def add_newdata(self, dt, pos):
        """Add new data to the trial data."""
        self._trialdata["dt"].append(dt)
        self._trialdata["pos"].append(pos)
        self._trialdata["vel"].append(
            (pos - self._trialdata["pos"][-2]) / dt
            if len(self._trialdata["pos"]) > 1
            else 0
        )
        if len(self._trialdata["dt"]) > pfadef.BaseConstants.POS_VEL_WINDOW_LENGHT:
            self._trialdata["dt"].pop(0)
            self._trialdata["pos"].pop(0)
            self._trialdata["vel"].pop(0)

    def add_new_trialrom_data(self) -> bool:
        """Add new value to trial ROM only if its different from existing ROM,
        and outside AROM if AROM is given.
        """
        _pos = float(np.mean(self._trialdata["pos"]))
        # Check of the _pos is well outside the current limits of trialrom
        _th = (
            pfadef.BaseConstants.HOC_NEW_ROM_TH
            if self.mechanism == "HOC"
            else pfadef.BaseConstants.NOT_HOC_NEW_ROM_TH
        )
        _out_of_rom = misc.is_out_of_range(
            val=_pos, minval=self._trialrom[0], maxval=self._trialrom[-1], thres=_th
        )
        # AROM is not given
        if not _out_of_rom:
            return False
        self._trialrom.append(_pos)
        self._trialrom.sort()
        self._trialrom[:] = [self._trialrom[0], self._trialrom[-1]]
        return True

    def set_rom(self):
        """Set the ROM value for the given trial."""
        # Update ROM
        self._rom[self._currtrial] = [self._trialrom[0], self._trialrom[-1]]
        # Update the summary file.
        self._summaryfilewriter.write_row(
            [
                self.session,
                self.type,
                self.limb,
                self.mechanism,
                self.apromtype,
                self.current_trial,
                self._startpos,
                self._trialrom[0],
                self._trialrom[-1],
                self._trialrom[-1] - self._trialrom[0],
                pfadef.APROM.TORQUE_DIR1,
                pfadef.APROM.TORQUE_DIR2,
                self.duration,
            ]
        )

    def set_startpos(self):
        """Sets the start position as the average of trial data."""
        self._startpos = float(np.mean(self._trialdata["pos"]))
        self._trialrom = [self._startpos]

    def start_rawlogging(self):
        self._logstate = apromwnd.RawDataLoggingState.LOG_DATA

    def terminate_rawlogging(self):
        self._logstate = apromwnd.RawDataLoggingState.LOGGING_DONE
        self._rawfilewriter.close()
        self._rawfilewriter = None

    def terminate_summarylogging(self):
        self._summaryfilewriter.close()
        self._summaryfilewriter = None


class PlutoAssistPRomAssessmentStateMachine:
    def __init__(self, plutodev, data: AssistPRomData, instdisp):
        self._state = States.REST
        self._statetimer = 0
        self._data = data
        self._instruction = f""
        self._instdisp = instdisp
        self._pluto = plutodev
        # Torque ramp state: direction of the current ramp (+/- target) and the
        # last target value actually sent (to throttle serial traffic).
        self._ramp_dir = 0.0
        self._last_sent_target = None
        self._stateactions = {
            States.REST: self._handle_rest,
            States.TORQ_DIR1: self._handle_torq_dir1,
            States.TORQ_DIR2: self._handle_torq_dir2,
            States.MOVING_DIR1: self._handle_moving_dir1,
            States.DIR1_TO_REST: self._handle_dir1_to_rest,
            States.MOVING_DIR2: self._handle_moving_dir2,
            States.DIR2_TO_REST: self._handle_dir2_to_rest,
            States.IN_STOPZONE: self._handle_in_stopzone,
            States.DONE: self._handle_done,
        }
        # Instructions.
        self._stateinstructions = {
            States.REST: "Rest and press PLUTO Button to start.",
            States.TORQ_DIR1: "Relax and let the robot move you.",
            States.TORQ_DIR2: "Relax and let the robot move you.",
            States.MOVING_DIR1: "Relax and let the robot move you.",
            States.DIR1_TO_REST: "Relax and let the robot move you.",
            States.MOVING_DIR2: "Relax and let the robot move you.",
            States.DIR2_TO_REST: "Relax and let the robot move you.",
            States.IN_STOPZONE: "Hold to complete the trial.",
            States.DONE: f"Assisted PROM {self._data.apromtype} assessment done.",
        }
        # Action handlers
        self._actionhandlers = {
            Actions.NO_CTRL: self._act_no_ctrl,
            Actions.TORQ_CTRL: self._act_torq_ctrl,
            Actions.TORQ_TGT_DIR1: self._act_torq_tgt_dir1,
            Actions.TORQ_TGT_DIR2: self._act_torq_tgt_dir2,
            Actions.TORQ_TGT_ZERO: self._act_torq_tgt_zero,
            Actions.TORQ_TGT_RAMP: self._act_torq_tgt_ramp,
            Actions.DO_NOTHING: self._act_do_nothing,
        }
        # Start a new trial.
        self._data.start_newtrial()

        # Defining a few useful lambda functions.
        self._define_me_some_lambdas()

    @property
    def state(self):
        return self._state

    @property
    def _torqsign(self):
        """Limb-aware torque direction multiplier.

        The device applies torque as a fixed motor-frame value (TORQUE_DIR1 =
        +1, TORQUE_DIR2 = -1) and neither the firmware calibration nor the app
        flips it per limb. The LEFT and RIGHT mounts are physically mirrored,
        so a fixed +1 Nm that assists the intended direction on the LEFT
        drives the RIGHT limb the opposite way (into its end-stop -> "not
        activating"). LEFT is the correct reference, so RIGHT is inverted to
        match its anatomical direction. HOC is excluded: its direction is
        already handled by the position mirror (MAXHOC - pos), so its torque
        sign stays as-is.
        """
        _is_right = str(self._data.limb).strip().lower() == "right"
        return -1.0 if (_is_right and self._data.mechanism != "HOC") else 1.0

    @property
    def in_a_trial_state(self):
        return self._state in [
            States.WAIT_TO_MOVE,
            States.TORQ_DIR1,
            States.TORQ_DIR2,
            States.MOVING_DIR1,
            States.DIR1_TO_REST,
            States.MOVING_DIR2,
            States.DIR2_TO_REST,
            States.IN_STOPZONE,
        ]

    def reset_statemachine(self):
        self._state = States.REST
        self._statetimer = 0
        self._instruction = f""
        self._data.start_newtrial(reset=True)

    def run_statemachine(self, event, dt):
        """Execute the state machine depending on the given even that has occured."""
        _action = self._stateactions[self._state](event, dt)
        self._actionhandlers[_action]()
        self._display_instruction()

    def _handle_rest(self, event, dt) -> Actions:
        # Check if all trials are done.
        if not self._data.demomode and self._data.all_trials_done:
            # Set the logging state.
            if self._data.rawfilewriter is not None:
                self._data.terminate_rawlogging()
                self._data.terminate_summarylogging()
            self._instruction = f"{self._data.romtype} ROM Assessment Done. Press the PLUTO Button to exit."
            if event == pdef.PlutoEvents.RELEASED:
                self._state = States.DONE
                self._statetimer = 0
            return Actions.NO_CTRL

        # Wait for start.
        if event == pdef.PlutoEvents.RELEASED:
            # Make sure the joint is in rest before we can swtich.
            if self.subj_is_holding():
                self._data.set_startpos()
                if self._data.mechanism == "HOC":
                    self._state = States.TORQ_DIR2
                else:
                    self._state = States.TORQ_DIR1
                self._statetimer = 0.5
                # Set the logging state.
                if not self._data.demomode:
                    self._data.start_rawlogging()
                return Actions.TORQ_CTRL
        return Actions.NO_CTRL

    def _handle_torq_dir1(self, event, dt) -> Actions:
        if event == pdef.PlutoEvents.NEWDATA:
            self._statetimer -= dt
            if self._statetimer > 0:
                return Actions.DO_NOTHING
            # Begin the direction-1 torque ramp (0 -> TORQUE_DIR1).
            self._state = States.MOVING_DIR1
            self._statetimer = self._data.duration
            self._ramp_dir = pfadef.APROM.TORQUE_DIR1
            self._last_sent_target = None
            return Actions.TORQ_TGT_RAMP

    def _handle_moving_dir1(self, event, dt) -> Actions:
        # New data event — keep ramping the assist torque, record ROM while held.
        if event == pdef.PlutoEvents.NEWDATA:
            self._statetimer -= dt
            if self.subj_is_holding():
                # Subject is held by the (ramping) torque — record ROM.
                _ = self._data.add_new_trialrom_data()
            return Actions.TORQ_TGT_RAMP
        # PLUTO button release event
        if self._statetimer < 0 and event == pdef.PlutoEvents.RELEASED:
            # Nothing to do if the subject is moving.
            if self.subj_is_holding() is False:
                return Actions.TORQ_TGT_RAMP
            # Subject is holdin away from start.
            # Add the current position to trial ROM.
            _ = self._data.add_new_trialrom_data()
            if len(self._data._trialrom) > 1:
                # Check the mechanism.
                self._state = States.DIR1_TO_REST
                self._statetimer = self._data.duration
                return Actions.TORQ_TGT_ZERO
        return Actions.DO_NOTHING

    def _handle_dir1_to_rest(self, event, dt) -> Actions:
        if event == pdef.PlutoEvents.NEWDATA:
            self._statetimer -= dt
        # PLUTO button release event. Switching to direction 2 no longer
        # requires returning to the centre/start zone (kept inconsistent with
        # the AROM/PROM flow otherwise) — the duration timer + assessor button
        # press alone advance to direction 2.
        if self._statetimer < 0 and event == pdef.PlutoEvents.RELEASED:
            self._state = States.TORQ_DIR2
            self._statetimer = 0.5
            # Hold torque at zero here (do NOT step to full TORQUE_DIR2). The
            # MOVING_DIR2 ramp starts from 0, so pre-setting full torque only
            # caused a step -> 0.5s hold -> drop -> re-ramp jerk. Direction 1
            # enters via TORQ_CTRL (target 0) then ramps; this mirrors it.
            return Actions.TORQ_TGT_ZERO
        return Actions.DO_NOTHING

    def _handle_torq_dir2(self, event, dt) -> Actions:
        if event == pdef.PlutoEvents.NEWDATA:
            self._statetimer -= dt
            if self._statetimer > 0:
                return Actions.DO_NOTHING
            # Begin the direction-2 torque ramp (0 -> TORQUE_DIR2).
            self._state = States.MOVING_DIR2
            self._statetimer = self._data.duration
            self._ramp_dir = pfadef.APROM.TORQUE_DIR2
            self._last_sent_target = None
            return Actions.TORQ_TGT_RAMP
        return Actions.DO_NOTHING

    def _handle_moving_dir2(self, event, dt) -> Actions:
        # New data event — keep ramping the assist torque, record ROM while held.
        if event == pdef.PlutoEvents.NEWDATA:
            self._statetimer -= dt
            if self.subj_is_holding():
                # Subject is held by the (ramping) torque — record ROM.
                _ = self._data.add_new_trialrom_data()
            return Actions.TORQ_TGT_RAMP
        # PLUTO button release event
        if self._statetimer < 0 and event == pdef.PlutoEvents.RELEASED:
            # Nothing to do if the subject is moving.
            if self.subj_is_holding() is False:
                return Actions.TORQ_TGT_RAMP
            # Subject is holdin away from start.
            # Add the current position to trial ROM.
            _ = self._data.add_new_trialrom_data()
            if len(self._data._trialrom) > 1:
                self._state = States.DIR2_TO_REST
                self._statetimer = self._data.duration
                return Actions.TORQ_TGT_ZERO
        return Actions.DO_NOTHING

    def _handle_dir2_to_rest(self, event, dt) -> Actions:
        self._instruction = f"Come to rest and hold to complete the trial."
        # PLUTO new data event. Completion no longer requires returning to the
        # centre/start zone — the subject may stop anywhere. Coming to rest
        # (holding) after the duration is enough to enter the hold-to-complete.
        if event == pdef.PlutoEvents.NEWDATA:
            self._statetimer -= dt
            # Nothing to do if the subject is moving.
            if self.subj_is_holding() is False:
                return Actions.DO_NOTHING
            # Subject has come to rest (anywhere).
            if self._statetimer < 0:
                self._statetimer = pfadef.APROM.STOP_ZONE_DURATION_THRESHOLD
                self._state = States.IN_STOPZONE
                return Actions.DO_NOTHING
        return Actions.DO_NOTHING

    def _handle_in_stopzone(self, event, dt) -> Actions:
        self._instruction = f"Hold for {self._statetimer:1.1f}s to complete trial"
        self._instruction += (
            f"{self._data._currtrial + 1}/{self._data.ntrials}."
            if not self._data.demomode
            else " in demo mode."
        )
        # PLUTO new data event
        if event == pdef.PlutoEvents.NEWDATA:
            # Nothing to do if the subject is moving.
            if self.subj_is_holding() is False:
                self._state = States.DIR2_TO_REST
                return Actions.DO_NOTHING
            self._statetimer -= dt
            if self._statetimer <= 0:
                # Set the ROM for the current trial.
                if not self._data.demomode:
                    self._data.set_rom()
                    self._data.start_newtrial()
                self._state = States.REST
                return Actions.DO_NOTHING
        return Actions.DO_NOTHING

    def _handle_done(self, event, dt):
        return Actions.DO_NOTHING

    #
    # Actions handlers
    #
    def _act_no_ctrl(self):
        if self._ctrl_is_none():
            return
        self._pluto.set_control_type("NONE")

    def _act_torq_ctrl(self):
        if self._ctrl_is_torqlinear():
            return
        self._pluto.set_control_type("TORQUE")

    def _act_torq_tgt_dir1(self):
        _tgt = self._torqsign * pfadef.APROM.TORQUE_DIR1
        if self._tgt_set(_tgt):
            return
        self._pluto.set_control_target(target=_tgt)

    def _act_torq_tgt_dir2(self):
        _tgt = self._torqsign * pfadef.APROM.TORQUE_DIR2
        if self._tgt_set(_tgt):
            return
        self._pluto.set_control_target(target=_tgt)

    def _act_torq_tgt_zero(self):
        self._last_sent_target = None
        if self._tgt_set(0):
            return
        self._pluto.set_control_target(target=0)

    def _act_torq_tgt_ramp(self):
        """Ramp the torque target from 0 to self._ramp_dir over RAMP_DURATION,
        then hold. elapsed = duration - statetimer, so the ramp completes at
        RAMP_DURATION and is held for the remaining HOLD_DURATION. Sends are
        throttled to ~0.02 N steps to avoid flooding the serial link."""
        if not self._ctrl_is_torqlinear():
            self._pluto.set_control_type("TORQUE")
        _elapsed = self._data.duration - self._statetimer
        _frac = min(1.0, max(0.0, _elapsed / pfadef.APROM.RAMP_DURATION))
        _tgt = self._torqsign * self._ramp_dir * _frac
        if (
            self._last_sent_target is None
            or abs(_tgt - self._last_sent_target) >= 0.02
        ):
            self._pluto.set_control_target(target=_tgt)
            self._last_sent_target = _tgt

    def _act_do_nothing(self):
        pass

    def _display_instruction(self):
        if self._state != States.REST:
            self._instdisp.setText(
                self._stateinstructions[self._state]
                + (
                    f" [{np.max([0.0, self._statetimer]):1.1f}s]"
                    if self._statetimer is not None
                    else ""
                )
            )
        else:
            if self._data.demomode:
                self._instdisp.setText(f"Press the PLUTO button to start demo trial.")
            elif self._data.all_trials_done:
                self._instdisp.setText(
                    f"All trials done. Press the PLUTO button to quit."
                )
            else:
                self._instdisp.setText(
                    f"PLUTO button to start trial {self._data.current_trial + 1} / {self._data.ntrials}."
                )

    #
    # Supporting functions
    #
    def _define_me_some_lambdas(self):
        self._ctrl_is_none = (
            lambda: self._pluto.controltype == pdef.ControlTypes["NONE"]
        )
        self._ctrl_is_torqlinear = (
            lambda: self._pluto.controltype == pdef.ControlTypes["TORQUE"]
        )
        self._tgt_set = lambda tgt: np.isclose(
            self._pluto.target, tgt, rtol=1e-03, atol=1e-03
        )
        # self._tgt_set= lambda tgt : np.isclose(self._pluto.target, tgt, rtol=1e-03, atol=1e-03)
        # self._ctrl_hold = lambda : self._pluto.controlhold == pdef.ControlHoldTypes["HOLD"]
        # self._ctrl_decay = lambda : self._pluto.controlhold == pdef.ControlHoldTypes["DECAY"]

    def subj_is_holding(self):
        """Check if the subject is holding the position."""
        _th = (
            pfadef.BaseConstants.VEL_HOC_THRESHOLD
            if self._data.mechanism == "HOC"
            else pfadef.BaseConstants.VEL_NOT_HOC_THRESHOLD
        )
        return bool(np.all(np.abs(self._data.trialdata["vel"]) < _th))

    def away_from_start(self):
        """Check if the subject has moved away from the start position."""
        if self._data.mechanism == "HOC":
            return (
                np.abs(self._pluto.hocdisp - self._data.startpos)
                > pfadef.BaseConstants.START_POS_HOC_THRESHOLD
            )
        else:
            return (
                np.abs(self._pluto.angle - self._data.startpos)
                > pfadef.BaseConstants.START_POS_NOT_HOC_THRESHOLD
            )

class PlutoAssistPRomAssessWindow(QtWidgets.QMainWindow):
    """
    Class for handling the operation of the PLUTO ROM assessment window.
    """

    def __init__(
        self,
        parent=None,
        plutodev: QtPluto = None,
        assessinfo: dict = None,
        modal=False,
        dataviewer=False,
        onclosecb=None,
        heartbeat=False,
    ):
        """
        Constructor for the PlutoAssistPRomAssessWindow class.
        """
        super(PlutoAssistPRomAssessWindow, self).__init__(parent)
        self.ui = Ui_APRomAssessWindow()
        self.ui.setupUi(self)

        # Make layout responsive to window size
        _rlayout = QtWidgets.QVBoxLayout(self.ui.centralwidget)
        _rlayout.setContentsMargins(10, 10, 10, 10)
        _rlayout.addWidget(self.ui.verticalLayoutWidget)

        self.showMaximized()

        if modal:
            self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        # Set the title of the window.
        self.setWindowTitle(
            " | ".join(
                (
                    "PLUTO Full Assessment",
                    "Assisted PROM",
                    f"{assessinfo['subjid'] if 'subjid' in assessinfo else ''}",
                    f"{assessinfo['type'] if 'type' in assessinfo else ''}",
                    f"{assessinfo['limb'] if 'limb' in assessinfo else ''}",
                    f"{assessinfo['mechanism'] if 'mechanism' in assessinfo else ''}",
                    f"{assessinfo['session'] if 'session' in assessinfo else ''}",
                    f"{assessinfo['apromtype'] if 'apromtype' in assessinfo else ''}",
                )
            )
        )

        # PLUTO device
        self._pluto = plutodev

        # Set control to NONE
        self._pluto.set_control_type("NONE")

        # Visual feedback display timer
        self._visfeedtimer = QTimer()
        self._visfeedtimer.timeout.connect(self._update_visual_feedabck)
        self._visfeedtimer.start(pfadef.VISUAL_FEEDBACK_UPDATE_INTERVAL)

        # Heartbeat timer
        self._heartbeat = heartbeat
        if self._heartbeat:
            self.heartbeattimer = QTimer()
            self.heartbeattimer.timeout.connect(lambda: self.pluto.send_heartbeat())
            self.heartbeattimer.start(250)

        # APROM assessment data
        self.data: AssistPRomData = AssistPRomData(assessinfo=assessinfo)

        # Initialize graph for plotting
        self._romassess_add_graph()

        # Initialize the state machine.
        self._smachine = PlutoAssistPRomAssessmentStateMachine(
            self._pluto, self.data, self.ui.subjInst
        )

        # Attach callbacks
        self._attach_pluto_callbacks()

        # Attach control callbacks
        self.ui.cbTrialRun.clicked.connect(self._callback_trialrun_clicked)

        # Update UI.
        self.update_ui()

        # Set the callback when the window is closed.
        self.on_close_callback = onclosecb

        # Open the PLUTO data viewer window for sanity
        if dataviewer:
            # Open the device data viewer by default.
            self._open_devdata_viewer()

    @property
    def pluto(self):
        return self._pluto

    @property
    def statemachine(self):
        return self._smachine

    #
    # Update UI
    #
    def update_ui(self):
        # Trial run checkbox
        if self.ui.cbTrialRun.isEnabled():
            _cond1 = self.data.demomode is False
            _cond2 = (
                self.data.demomode is None and self._smachine.state == States.TORQ_DIR1
            )
            if _cond1 or _cond2:
                self.ui.cbTrialRun.setEnabled(False)

        # Update main text
        if self.pluto.angle is None:
            return
        _posstr = (
            f"[{self.pluto.hocdisp:5.2f}cm]"
            if self.data.mechanism == "HOC"
            else f"[{self.pluto.angle:5.2f}deg]"
        )
        self.ui.lblTitle.setText(f"PLUTO {self.data.romtype} ROM Assessment {_posstr}")

        # Update status message
        self.ui.lblStatus.setText(
            f"{self.pluto.error} | {self.pluto.controltype} | {self._smachine.state}"
        )

        # Close if needed
        if self._smachine.state == States.DONE:
            self.close()

    def _update_visual_feedabck(self):
        self._update_current_position_cursor()
        if self._smachine.in_a_trial_state:
            # After the trial starts there is no start/stop-zone reference any
            # more — only the boundary envelope (and the live cursor).
            self._clear_start_stop_visuals()
            self._update_aprom_cursor_position()
        elif self._smachine.state == States.REST:
            # Reset arom cursor position.
            self._reset_display()

    def _clear_start_stop_visuals(self):
        """Hide the start/stop-zone lines and the start-zone fill."""
        self.ui.stopLine1.setData([], [])
        self.ui.stopLine2.setData([], [])
        self.ui.strtZoneFill.setRect(
            0,
            pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
            0,
            pfadef.BaseConstants.CURSOR_UPPER_LIMIT
            - pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
        )

    def _update_current_position_cursor(self):
        if self.data.mechanism == "HOC":
            if self.pluto.hocdisp is None:
                return
            # Plot when there is data to be shown
            self.ui.currPosLine1.setData(
                [self.pluto.hocdisp, self.pluto.hocdisp],
                [
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                ],
            )
            self.ui.currPosLine2.setData(
                [-self.pluto.hocdisp, -self.pluto.hocdisp],
                [
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                ],
            )
        else:
            if self.pluto.angle is None:
                return
            self.ui.currPosLine1.setData(
                [self._dispsign * self.pluto.angle, self._dispsign * self.pluto.angle],
                [
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                ],
            )
            self.ui.currPosLine2.setData(
                [self._dispsign * self.pluto.angle, self._dispsign * self.pluto.angle],
                [
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                ],
            )

    def _update_aprom_cursor_position(self):
        if len(self.data._trialrom) == 0:
            return
        if self.data.mechanism == "HOC":
            if len(self.data._trialrom) > 1:
                self.ui.romLine1.setData(
                    [-self.data._trialrom[-1], -self.data._trialrom[-1]],
                    [
                        pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                        pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                    ],
                )
                self.ui.romLine2.setData(
                    [self.data._trialrom[-1], self.data._trialrom[-1]],
                    [
                        pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                        pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                    ],
                )
                self.ui.romFill.setRect(
                    -self.data._trialrom[-1],
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    2 * self.data._trialrom[-1],
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT
                    - pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                )
            else:
                self.ui.romLine1.setData(
                    [0, 0],
                    [
                        pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                        pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                    ],
                )
                self.ui.romLine2.setData(
                    [0, 0],
                    [
                        pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                        pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                    ],
                )
                self.ui.romFill.setRect(
                    0,
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    0,
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT
                    - pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                )
        else:
            _romdisp = list(map(lambda x: self._dispsign * x, self.data._trialrom))
            _romdisp.sort()
            self.ui.romLine1.setData(
                [_romdisp[0], _romdisp[0]],
                [
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                ],
            )
            self.ui.romLine2.setData(
                [_romdisp[-1], _romdisp[-1]],
                [
                    pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                    pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
                ],
            )
            # Fill between the two AROM lines
            self.ui.romFill.setRect(
                _romdisp[0],
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                _romdisp[-1] - _romdisp[0],
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT
                - pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
            )

    def _reset_display(self):
        # Reset ROM display
        self.ui.romLine1.setData(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
        )
        self.ui.romLine2.setData(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
        )
        # Fill between the two AROM lines
        self.ui.romFill.setRect(
            0,
            pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
            0,
            pfadef.BaseConstants.CURSOR_UPPER_LIMIT
            - pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
        )
        # Stop-zone lines are no longer used — keep them hidden.
        self.ui.stopLine1.setData([], [])
        self.ui.stopLine2.setData([], [])
        self.ui.strtZoneFill.setRect(
            0,
            pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
            0,
            pfadef.BaseConstants.CURSOR_UPPER_LIMIT
            - pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
        )

    #
    # Graph plot initialization
    #
    def _romassess_add_graph(self):
        """Function to add graph and other objects for displaying HOC movements."""
        _pgobj = pg.PlotWidget()
        _templayout = QtWidgets.QGridLayout()
        _templayout.addWidget(_pgobj)
        _pen = pg.mkPen(color=(255, 0, 0))
        self.ui.hocGraph.setLayout(_templayout)
        _pgobj.setYRange(-20, 20)
        if self.data.mechanism == "HOC":
            _pgobj.setXRange(-10, 10)
        else:
            _range = pdef.get_range_for_mechanism(self.data.mechanism)
            _pgobj.setXRange(_range[0], _range[1])
        _pgobj.getAxis("bottom").setStyle(showValues=False)
        _pgobj.getAxis("left").setStyle(showValues=False)

        # Current position lines
        self.ui.currPosLine1 = pg.PlotDataItem(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
            pen=pg.mkPen(color="#FFFFFF", width=2),
        )
        self.ui.currPosLine2 = pg.PlotDataItem(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
            pen=pg.mkPen(color="#FFFFFF", width=2),
        )
        _pgobj.addItem(self.ui.currPosLine1)
        _pgobj.addItem(self.ui.currPosLine2)

        # ROM Lines
        self.ui.romLine1 = pg.PlotDataItem(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
            pen=pg.mkPen(color="#FF8888", width=2),
        )
        self.ui.romLine2 = pg.PlotDataItem(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
            pen=pg.mkPen(color="#FF8888", width=2),
        )
        _pgobj.addItem(self.ui.romLine1)
        _pgobj.addItem(self.ui.romLine2)

        # ROM Fill
        self.ui.romFill = QGraphicsRectItem()
        self.ui.romFill.setBrush(
            QColor(255, 136, 136, 80)
        )  # match AROM color, alpha=80
        self.ui.romFill.setPen(pg.mkPen(None))  # No border
        _pgobj.addItem(self.ui.romFill)

        # Stop zone Lines
        self.ui.stopLine1 = pg.PlotDataItem(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
            pen=pg.mkPen(color="#FFFFFF", width=1, style=QtCore.Qt.PenStyle.DotLine),
        )
        self.ui.stopLine2 = pg.PlotDataItem(
            [0, 0],
            [
                pfadef.BaseConstants.CURSOR_LOWER_LIMIT,
                pfadef.BaseConstants.CURSOR_UPPER_LIMIT,
            ],
            pen=pg.mkPen(color="#FFFFFF", width=1, style=QtCore.Qt.PenStyle.DotLine),
        )
        _pgobj.addItem(self.ui.stopLine1)
        _pgobj.addItem(self.ui.stopLine2)

        # Start zone Fill
        self.ui.strtZoneFill = QGraphicsRectItem()
        self.ui.strtZoneFill.setBrush(QColor(136, 255, 136, 80))
        self.ui.strtZoneFill.setPen(pg.mkPen(None))  # No border
        _pgobj.addItem(self.ui.strtZoneFill)

        # Angle display sign for the limb.
        self._dispsign = 1.0

        # AROM lines when appropriate.
        # if self.data.arom is not None:
        #     _pos = ([-self.data.arom[1], -self.data.arom[1]]
        #             if self.data.mechanism == "HOC"
        #             else [self._dispsign * self.data.arom[0], self._dispsign * self.data.arom[0]])
        #     self.ui.aromPosLine1 = pg.PlotDataItem(
        #         _pos,
        #         [pfadef.BaseConstants.CURSOR_LOWER_LIMIT, pfadef.BaseConstants.CURSOR_UPPER_LIMIT],
        #         pen=pg.mkPen(color = "#1EFF00", width=1, style=QtCore.Qt.PenStyle.DotLine)
        #     )
        #     _pos = ([self.data.arom[1], self.data.arom[1]]
        #             if self.data.mechanism == "HOC"
        #             else [self._dispsign * self.data.arom[1], self._dispsign * self.data.arom[1]])
        #     self.ui.aromPosLine2 = pg.PlotDataItem(
        #         _pos,
        #         [pfadef.BaseConstants.CURSOR_LOWER_LIMIT, pfadef.BaseConstants.CURSOR_UPPER_LIMIT],
        #         pen=pg.mkPen(color = '#1EFF00', width=1, style=QtCore.Qt.PenStyle.DotLine)
        #     )
        #     _pgobj.addItem(self.ui.aromPosLine1)
        #     _pgobj.addItem(self.ui.aromPosLine2)

        # Angle display sign for the limb.
        self._dispsign = 1.0

        # Instruction text
        self.ui.subjInst = pg.TextItem(text="", color="w", anchor=(0.5, 0.5))
        self.ui.subjInst.setPos(0, 15)  # Set position (x, y)
        # Set font and size
        self.ui.subjInst.setFont(QtGui.QFont("Cascadia Mono Light", 18))
        _pgobj.addItem(self.ui.subjInst)

    #
    # Device Data Viewer Functions
    #
    def _open_devdata_viewer(self):
        self._devdatawnd = PlutoDataViewWindow(plutodev=self.pluto, pos=(50, 300))
        self._devdatawnd.show()

    #
    # Signal Callbacks
    #
    def _attach_pluto_callbacks(self):
        self.pluto.newdata.connect(self._callback_pluto_newdata)
        self.pluto.btnreleased.connect(self._callback_pluto_btn_released)

    def _detach_pluto_callbacks(self):
        self.pluto.newdata.disconnect(self._callback_pluto_newdata)
        self.pluto.btnreleased.disconnect(self._callback_pluto_btn_released)

    def _callback_pluto_newdata(self):
        # Update trial data.
        self.data.add_newdata(
            dt=self.pluto.delt(),
            pos=self.pluto.hocdisp
            if self.data.mechanism == "HOC"
            else self.pluto.angle,
        )
        # Run the statemachine
        _action = self._smachine.run_statemachine(
            pdef.PlutoEvents.NEWDATA, dt=self.pluto.delt()
        )
        # self._perform_action(_action)
        # Update the GUI only at 1/10 the data rate
        if np.random.rand() < 0.05:
            self.update_ui()
        #
        # Log data
        if self.data.logstate == apromwnd.RawDataLoggingState.LOG_DATA:
            self.data.rawfilewriter.write_row(
                [
                    self.pluto.systime,
                    self.pluto.currt,
                    self.pluto.packetnumber,
                    self.pluto.status,
                    self.pluto.controltype,
                    self.pluto.error,
                    self.pluto.limb,
                    self.pluto.mechanism,
                    self.pluto.angle,
                    self.pluto.hocdisp,
                    self.pluto.torque,
                    0,
                    self.pluto.control,
                    self.pluto.target,
                    self.pluto.desired,
                    self.pluto.controlbound,
                    self.pluto.controldir,
                    self.pluto.controlgain,
                    self.pluto.button,
                    self.data.current_trial,
                    f"{self._smachine.state.name}",
                ]
            )

    def _callback_pluto_btn_released(self):
        print("Pluto Button Released!")
        # Run the statemachine
        _action = self._smachine.run_statemachine(
            pdef.PlutoEvents.RELEASED, dt=self.pluto.delt()
        )
        # self._perform_action(_action)
        self.update_ui()

    #
    # Others
    #
    # def _perform_action(self, action: Actions) -> None:
    #     if action == Actions.NO_CTRL:
    #         # Check if the current control type is not NONE.
    #         if self.pluto.controltype != pdef.ControlTypes["NONE"]:
    #             self.pluto.set_control_type("NONE")
    #     elif action == Actions.TORQ_CTRL:
    #         # Check if the current control type is not TORQUE.
    #         if self.pluto.controltype != pdef.ControlTypes["TORQUE"]:
    #             self.pluto.set_control_type("TORQUE")
    #         self.pluto.set_control_target(target=0, dur=2.0)
    #     elif action == Actions.TORQ_TGT_ZERO:
    #         if self.pluto.controltype != pdef.ControlTypes["TORQUE"]:
    #             self.pluto.set_control_type("TORQUE")
    #         self.pluto.set_control_target(target=0, dur=2.0)
    #     elif action == Actions.TORQ_TGT_DIR1:
    #         if self.pluto.controltype != pdef.ControlTypes["TORQUE"]:
    #             self.pluto.set_control_type("TORQUE")
    #         self.pluto.set_control_target(target=1.0, dur=2.0)
    #     elif action == Actions.TORQ_TGT_DIR2:
    #         if self.pluto.controltype != pdef.ControlTypes["TORQUE"]:
    #             self.pluto.set_control_type("TORQUE")
    #         self.pluto.set_control_target(target=-1.0, dur=2.0)

    #
    # Control Callbacks
    #
    def _callback_trialrun_clicked(self):
        if self.data.demomode is None and self.ui.cbTrialRun.isChecked():
            self.data.demomode = True
        if self.data.demomode and not self.ui.cbTrialRun.isChecked():
            self.data.demomode = False
            # Restart ROM assessment statemachine
            self._smachine.reset_statemachine()

    def closeEvent(self, event):
        # Get comment from the experimenter.
        data = {"romval": self.data.rom, "done": self.data.all_trials_done}
        self.pluto.set_control_type("NONE")
        if self.data.all_trials_done:
            _comment = CommentDialog(
                label="Assisted PROM completed. Add optional comment.", optionyesno=True
            )
            if _comment.exec() == QtWidgets.QDialog.Accepted:
                data["status"] = pfadef.AssessStatus.COMPLETE.value
            else:
                data["status"] = pfadef.AssessStatus.REJECTED.value
            data["taskcomment"] = _comment.getText()
        else:
            _comment = CommentDialog(
                label="Assisted PROM incomplete. Why?", optionyesno=False
            )
            if _comment.exec() == QtWidgets.QDialog.Rejected:
                data["taskcomment"] = _comment.getText()
                data["status"] = pfadef.AssessStatus.TERMINATED.value
        if self.on_close_callback:
            self.on_close_callback(data=data)
        # Detach PLUTO callbacks.
        self._detach_pluto_callbacks()
        try:
            self._devdatawnd.close()
        except:
            pass
        return super().closeEvent(event)


if __name__ == "__main__":
    import qtjedi

    qtjedi._OUTDEBUG = False
    app = QtWidgets.QApplication(sys.argv)
    plutodev = QtPluto("COM5")
    pcalib = PlutoAssistPRomAssessWindow(
        plutodev=plutodev,
        assessinfo={
            "subjid": "",
            "type": "Stroke",
            "limb": "Left",
            "mechanism": "FPS",
            "session": "testing",
            "ntrials": 1,
            "rawfile": "rawfiletest.csv",
            "summaryfile": "summaryfiletest.csv",
            "duration": pfadef.get_task_constants("APROM").DURATION,
            "apromtype": pfadef.APROM.APROMTYPE,
        },
        dataviewer=True,
        onclosecb=lambda data: print(f"ROM set: {data}"),
        heartbeat=True,
    )
    pcalib.show()
    sys.exit(app.exec())

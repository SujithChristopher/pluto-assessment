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
from PySide6.QtGui import QColor
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Signal
import pyqtgraph as pg
from enum import Enum, auto

import plutodefs as pdef
import plutofullassessdef as pfadef
from plutofullassessdef import AROM
from uipy.ui_plutoapromassess import Ui_APRomAssessWindow
from myqt import CommentDialog

import misc


class RawDataLoggingState(Enum):
    WAIT_FOR_LOG = 0
    LOG_DATA = 1
    LOGGING_DONE = 2


class States(Enum):
    REST = 0
    WAIT_TO_MOVE = auto()
    MOVING = auto()
    HOLDING = auto()
    HOLDING_IN_STOP_ZONE = auto()
    CYCLING = auto()       # AROM non-HOC only
    WAIT_FOR_REST = auto() # AROM non-HOC only
    NEW_ROM_SET = auto()
    DONE = auto()


class APRomData(object):
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
        # AROM cycling fields (non-HOC AROM only)
        self._curr_left = None            # this cycle's left hold position
        self._curr_right = None           # this cycle's right hold position
        self._last_cycle_left = None      # left extreme of last completed cycle
        self._last_cycle_right = None     # right extreme of last completed cycle
        self._cycles_completed = 0
        self._was_holding = False
        self._held_left_this_cycle = False
        self._held_right_this_cycle = False
        self._rest_position = None
        self._rest_locked = False
        self._disp_left = None            # left boundary for display
        self._disp_right = None           # right boundary for display
        # Logging variables
        self._logstate: RawDataLoggingState = RawDataLoggingState.WAIT_FOR_LOG
        self._rawfilewriter: misc.CSVBufferWriter = misc.CSVBufferWriter(
            self.rawfile, header=AROM.RAW_HEADER
        )
        _hdr = (
            AROM.SUMMARY_HEADER_CYCLING
            if assessinfo["romtype"] == pfadef.ROMType.ACTIVE
               and assessinfo.get("mechanism") != "HOC"
            else AROM.SUMMARY_HEADER
        )
        self._summaryfilewriter: misc.CSVBufferWriter = misc.CSVBufferWriter(
            self.summaryfile, header=_hdr, flush_interval=0.0, max_rows=1
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
        return self._assessinfo["romtype"]

    @property
    def session(self):
        return self._assessinfo["session"]

    @property
    def ntrials(self):
        return self._assessinfo["ntrials"]

    @property
    def rawfile(self):
        return self._assessinfo["rawfile"]

    @property
    def summaryfile(self):
        return self._assessinfo["summaryfile"]

    @property
    def arom(self):
        return (
            self._assessinfo["arom"]
            if (
                self._assessinfo["romtype"] != pfadef.ROMType.ACTIVE
                and "arom" in self._assessinfo
                and self._assessinfo["arom"]
            )
            else None
        )

    @property
    def currtrial(self):
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
        return bool(self._currtrial >= self.ntrials)

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
            # Reset cycling fields
            self._curr_left = None
            self._curr_right = None
            self._last_cycle_left = None
            self._last_cycle_right = None
            self._cycles_completed = 0
            self._was_holding = False
            self._held_left_this_cycle = False
            self._held_right_this_cycle = False
            self._rest_position = None
            self._rest_locked = False
            self._disp_left = None
            self._disp_right = None

    def add_newdata(self, dt, pos):
        """Add new data to the trial data."""
        self._trialdata["dt"].append(dt)
        self._trialdata["pos"].append(pos)
        self._trialdata["vel"].append(
            (pos - self._trialdata["pos"][-2]) / dt
            if len(self._trialdata["pos"]) > 1
            else 0
        )
        if len(self._trialdata["dt"]) > AROM.POS_VEL_WINDOW_LENGHT:
            self._trialdata["dt"].pop(0)
            self._trialdata["pos"].pop(0)
            self._trialdata["vel"].pop(0)

    def add_new_trialrom_data(self) -> bool:
        """Add new value to trial ROM only if its different from existing ROM,
        and outside AROM if AROM is given.
        """
        _pos = float(self._trialdata["pos"][int(np.argmin(np.abs(self._trialdata["vel"])))])
        # Check of the _pos is well outside the current limits of trialrom
        _th = (
            AROM.HOC_NEW_ROM_TH if self.mechanism == "HOC" else AROM.NOT_HOC_NEW_ROM_TH
        )
        _out_of_rom = misc.is_out_of_range(
            val=_pos, minval=self._trialrom[0], maxval=self._trialrom[-1], thres=_th
        )
        # AROM is not given
        if self.arom is None:
            if _out_of_rom:
                self._trialrom.append(_pos)
                self._trialrom.sort()
                self._trialrom[:] = [self._trialrom[0], self._trialrom[-1]]
                return True
            else:
                return False
        # AROM is given
        _out_of_arom = misc.is_out_of_range(
            val=_pos, minval=self.arom[0], maxval=self.arom[1], thres=0
        )
        if _out_of_rom and _out_of_arom:
            self._trialrom.append(_pos)
            self._trialrom.sort()
            self._trialrom[:] = [self._trialrom[0], self._trialrom[-1]]
            return True
        return False

    def is_trialrom_valid(self) -> bool:
        """Check if the trial ROM is valid."""
        if len(self._trialrom) < 2:
            return False
        # Check if the trial ROM is outside the start position.
        _th = (
            AROM.STOP_POS_HOC_THRESHOLD
            if self.mechanism == "HOC"
            else AROM.STOP_POS_NOT_HOC_THRESHOLD
        )
        if self.mechanism == "HOC":
            return self._trialrom[-1] - self._startpos > _th
        else:
            return (
                self._trialrom[0] - self._startpos < -_th
                and self._trialrom[-1] - self._startpos > _th
            )

    def update_cycling_data(self, is_holding: bool) -> bool:
        """Capture left/right extremes at rest (hold) transitions.
        Returns True when a full cycle (hold left + hold right) completes."""
        if not self._trialdata["pos"]:
            return False

        if not is_holding:
            self._was_holding = False
            return False

        # Only process the moving→holding transition once
        if self._was_holding:
            return False
        self._was_holding = True

        rest_pos = float(self._trialdata["pos"][int(np.argmin(np.abs(self._trialdata["vel"])))])

        if rest_pos < self._startpos:
            self._curr_left = rest_pos
            self._disp_left = rest_pos
            self._held_left_this_cycle = True
        else:
            self._curr_right = rest_pos
            self._disp_right = rest_pos
            self._held_right_this_cycle = True

        if self._held_left_this_cycle and self._held_right_this_cycle:
            self._cycles_completed += 1
            self._last_cycle_left = self._curr_left
            self._last_cycle_right = self._curr_right
            self._curr_left = None
            self._curr_right = None
            self._held_left_this_cycle = False
            self._held_right_this_cycle = False
            return True

        return False

    @property
    def cycles_done(self):
        return self._cycles_completed >= AROM.NO_OF_CYCLES

    def compute_rest_position(self):
        """Midpoint estimate used as display guide only; actual rest captured later."""
        self._rest_position = (self._last_cycle_left + self._last_cycle_right) / 2.0

    def capture_rest_position(self):
        """Lock in rest position at the lowest-velocity sample in the current window."""
        self._rest_position = float(self._trialdata["pos"][int(np.argmin(np.abs(self._trialdata["vel"])))])
        self._rest_locked = True

    def set_rom(self):
        """Set the ROM value for the given trial."""
        if (self._assessinfo["romtype"] == pfadef.ROMType.ACTIVE
                and self._assessinfo.get("mechanism") != "HOC"):
            # AROM cycling path
            self._rom[self._currtrial] = [self._last_cycle_left, self._last_cycle_right]
            self._summaryfilewriter.write_row([
                self.session,
                self.type,
                self.limb,
                self.mechanism,
                self.currtrial,
                self._last_cycle_left,
                self._last_cycle_right,
                self._last_cycle_right - self._last_cycle_left,
                self._rest_position,
                self._cycles_completed,
            ])
        else:
            # PROM / HOC path — unchanged
            self._rom[self._currtrial] = [self._trialrom[0], self._trialrom[-1]]
            self._summaryfilewriter.write_row(
                [
                    self.session,
                    self.type,
                    self.limb,
                    self.mechanism,
                    self.currtrial,
                    self._startpos,
                    self._trialrom[0],
                    self._trialrom[-1],
                    self._trialrom[-1] - self._trialrom[0],
                ]
            )

    def set_startpos(self):
        """Sets the start position at the sample of lowest velocity in the window."""
        self._startpos = float(self._trialdata["pos"][int(np.argmin(np.abs(self._trialdata["vel"])))])
        self._trialrom = [self._startpos]

    def start_rawlogging(self):
        self._logstate = RawDataLoggingState.LOG_DATA

    def terminate_rawlogging(self):
        self._logstate = RawDataLoggingState.LOGGING_DONE
        self._rawfilewriter.close()
        self._rawfilewriter = None

    def terminate_summarylogging(self):
        self._summaryfilewriter.close()
        self._summaryfilewriter = None


class PlutoAPRomAssessmentStateMachine:
    def __init__(self, plutodev, data: APRomData, instdisp):
        self._state = States.REST
        self._statetimer = 0
        self._data = data
        self._instruction = f""
        self._instdisp = instdisp
        self._pluto = plutodev
        self._rest_motion_seen = False
        self._stateactions = {
            States.REST: self._handle_rest,
            States.WAIT_TO_MOVE: self._handle_wait_to_move,
            States.MOVING: self._handle_moving,
            States.HOLDING: self._handle_holding,
            States.HOLDING_IN_STOP_ZONE: self._handle_holding_stop_zone,
            States.CYCLING: self._handle_cycling,
            States.WAIT_FOR_REST: self._handle_wait_for_rest,
            States.DONE: self._handle_done,
        }
        # Start a new trial.
        self._data.start_newtrial()

    @property
    def state(self):
        return self._state

    @property
    def _is_arom_cycling(self):
        return (self._data.romtype == pfadef.ROMType.ACTIVE
                and self._data.mechanism != "HOC")

    @property
    def in_a_trial_state(self):
        return self._state in [
            States.MOVING,
            States.HOLDING,
            States.HOLDING_IN_STOP_ZONE,
            States.CYCLING,
            States.WAIT_FOR_REST,
        ]

    def reset_statemachine(self):
        self._state = States.REST
        self._statetimer = 0
        self._instruction = f""
        self._data.start_newtrial(reset=True)

    def run_statemachine(self, event, dt):
        """Execute the state machine depending on the given even that has occured."""
        retval = self._stateactions[self._state](event, dt)
        self._instdisp.setText(self._instruction)
        return retval

    def _handle_rest(self, event, dt):
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
            return

        # Wait for start.
        if self._data.demomode:
            self._instruction = f"Hold and press PLUTO Button to demo trial."
        else:
            self._instruction = f"Hold and press PLUTO Button to start trial {self._data._currtrial + 1}/{self._data.ntrials}."
        if event == pdef.PlutoEvents.RELEASED:
            # Make sure the joint is in rest before we can swtich.
            if self.subj_is_holding():
                if self._is_arom_cycling:
                    # Record start position for away_from_start(), but don't use it as ROM ref.
                    self._data.set_startpos()
                    self._data._trialrom = []
                    self._state = States.WAIT_TO_MOVE
                    self._statetimer = 0
                    if not self._data.demomode:
                        self._data.start_rawlogging()
                else:
                    self._data.set_startpos()
                    self._trialrom = (
                        []
                        if self._data.mechanism != "HOC"
                        else [
                            0,
                        ]
                    )
                    self._state = States.WAIT_TO_MOVE
                    self._statetimer = 0
                    if not self._data.demomode:
                        self._data.start_rawlogging()

    def _handle_wait_to_move(self, event, dt):
        if self._is_arom_cycling:
            self._instruction = "Move LEFT ◄ first, then cycle back and forth"
            if event == pdef.PlutoEvents.NEWDATA:
                if not self.subj_is_holding():
                    self._state = States.CYCLING
        else:
            self._instruction = f"Move an hold to record ROM."
            if event == pdef.PlutoEvents.NEWDATA:
                if self.subj_is_holding() is False and self.away_from_start():
                    self._state = States.MOVING

    def _handle_moving(self, event, dt):
        self._instruction = f"Move and hold to record ROM position."
        if event == pdef.PlutoEvents.NEWDATA:
            # Nothing to do if the subject is moving.
            if self.subj_is_holding() is False:
                return
            # Subject is holding away from start.
            if self.subj_in_the_stop_zone() and self._data.is_trialrom_valid():
                # Holding in the stop zone.
                self._state = States.HOLDING_IN_STOP_ZONE
                self._statetimer = AROM.STOP_ZONE_DURATION_THRESHOLD
            else:
                # Add the current position to trial ROM.
                _trialromset = self._data.add_new_trialrom_data()
                if _trialromset:
                    self._state = States.HOLDING

    def _handle_holding(self, event, dt):
        # Check if the subject is in the stopping zone.
        self._instruction = (
            f"{self._data.romtype} Move and hold to record ROM position."
        )
        if event == pdef.PlutoEvents.NEWDATA:
            # Check if the subject is moving again.
            if self.subj_is_holding() is False:
                # Subject is moving again. Go back to moving state.
                self._state = States.MOVING

    def _handle_holding_stop_zone(self, event, dt):
        # Check if the subject is in the stopping zone.
        if event == pdef.PlutoEvents.NEWDATA:
            if self.subj_is_holding() is True:
                self._statetimer -= dt
                self._instruction = f"Hold for {self._statetimer:2.1f}sec to stop."
                # Check if the subject is moving again.
                if self._statetimer <= 0:
                    # Done with the trial.
                    self._state = States.REST
                    # Set the ROM for the current trial.
                    if not self._data.demomode:
                        self._data.set_rom()
                        self._data.start_newtrial()
            else:
                # Go back to the moving state.
                # Subject is moving again. Go back to moving state.
                self._state = States.MOVING

    def _handle_cycling(self, event, dt):
        if event != pdef.PlutoEvents.NEWDATA:
            return
        self._data.update_cycling_data(self.subj_is_holding())
        n = self._data._cycles_completed
        self._instruction = f"Keep cycling! {n}/{AROM.NO_OF_CYCLES} cycles done"
        if self._data.cycles_done:
            self._data.compute_rest_position()
            self._statetimer = AROM.REST_ZONE_HOLD_DURATION
            self._rest_motion_seen = False
            self._state = States.WAIT_FOR_REST

    def _handle_wait_for_rest(self, event, dt):
        if event != pdef.PlutoEvents.NEWDATA:
            return
        rp = self._data._rest_position
        if self.subj_is_holding():
            if not self._rest_motion_seen:
                # Still at cycling extreme — must move first
                self._instruction = f"Move to rest position ({rp:.1f} deg) and hold"
                return
            # Movement seen; lock rest position on first hold
            if not self._data._rest_locked:
                self._data.capture_rest_position()
            self._statetimer -= dt
            self._instruction = f"Hold for {self._statetimer:2.1f}s at rest ({self._data._rest_position:.1f} deg)"
            if self._statetimer <= 0:
                if not self._data.demomode:
                    self._data.set_rom()
                    self._data.start_newtrial()
                self._state = States.REST
        else:
            self._rest_motion_seen = True
            self._statetimer = AROM.REST_ZONE_HOLD_DURATION
            self._instruction = f"Move to rest position ({rp:.1f} deg) and hold"

    def _handle_done(self, event, dt):
        pass

    #
    # Supporting functions
    #
    def subj_is_holding(self):
        """Check if the subject is holding the position."""
        _th = (
            AROM.VEL_HOC_THRESHOLD
            if self._data.mechanism == "HOC"
            else AROM.VEL_NOT_HOC_THRESHOLD
        )
        return bool(np.all(np.abs(self._data.trialdata["vel"]) < _th))

    def away_from_start(self):
        """Check if the subject has moved away from the start position."""
        if self._data.mechanism == "HOC":
            return (
                np.abs(self._pluto.hocdisp - self._data.startpos)
                > AROM.START_POS_HOC_THRESHOLD
            )
        else:
            return (
                np.abs(self._pluto.angle - self._data.startpos)
                > AROM.START_POS_NOT_HOC_THRESHOLD
            )

    def subj_in_the_stop_zone(self):
        """Check if the subject is in the stop zone."""
        if self._data.mechanism == "HOC":
            return (
                self._pluto.hocdisp - self._data.startpos
            ) < AROM.STOP_POS_HOC_THRESHOLD
        else:
            return (
                np.abs(self._pluto.angle - self._data.startpos)
                < AROM.STOP_POS_NOT_HOC_THRESHOLD
            )

    # def trial_rom_outside_frobidden_zones(self):
    #     """Ensures that the AROM tiral ROM values are away from the start
    #     position, and that of the PROM is outside the AROM.s
    #     """
    #     if self._data.mechanism == "HOC":
    #         return (self._data._trialrom[1] - self._data.startpos) > AROM.STOP_POS_HOC_THRESHOLD
    #     else:
    #         # _trialrom[0]
    #         _tr0 = abs(self._data._trialrom[0] - self._data.startpos) > AROM.STOP_POS_NOT_HOC_THRESHOLD
    #         #_trialrom[1]
    #         _tr1 = abs(self._data._trialrom[1] - self._data.startpos) > AROM.STOP_POS_NOT_HOC_THRESHOLD
    #         return _tr0 and _tr1


class PlutoAPRomAssessWindow(QtWidgets.QMainWindow):
    """
    Class for handling the operation of the PLUTO ROM assessment window.
    """

    def __init__(
        self,
        parent=None,
        plutodev: QtPluto = None,
        assessinfo: dict = None,
        modal=False,
        onclosecb=None,
    ):
        """
        Constructor for the PlutoAPRomAssessWindow class.
        """
        super(PlutoAPRomAssessWindow, self).__init__(parent)
        self.ui = Ui_APRomAssessWindow()
        self.ui.setupUi(self)

        # Make layout responsive to window size
        _rlayout = QtWidgets.QVBoxLayout(self.ui.centralwidget)
        _rlayout.setContentsMargins(10, 10, 10, 10)
        _rlayout.addWidget(self.ui.verticalLayoutWidget)

        self.showMaximized()

        if modal:
            self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        # Skip AROM flag
        self._arom_skipped = False

        # PLUTO device
        self._pluto = plutodev
        self._pluto.send_heartbeat()
        self._pluto.start_sensorstream()
        QTimer.singleShot(500, lambda: None)

        # APROM assessment data
        self.data: APRomData = APRomData(assessinfo=assessinfo)

        # Set control to NONE
        self._pluto.set_control_type("NONE")

        # Visual feedback display timer
        self._visfeedtimer = QTimer()
        self._visfeedtimer.timeout.connect(self._update_visual_feedabck)
        self._visfeedtimer.start(pfadef.VISUAL_FEEDBACK_UPDATE_INTERVAL)

        # Initialize graph for plotting
        self._romassess_add_graph()

        # Initialize the state machine.
        self._smachine = PlutoAPRomAssessmentStateMachine(
            self._pluto, self.data, self.ui.subjInst
        )

        # Attach callbacks
        self._attach_pluto_callbacks()

        # Skip AROM button (ACTIVE romtype only)
        if self.data.romtype == pfadef.ROMType.ACTIVE:
            self.ui.pbSkipArom = QtWidgets.QPushButton("Skip AROM")
            self.ui.pbSkipArom.setStyleSheet("color: rgb(200, 100, 0);")
            self.ui.horizontalLayout.addWidget(self.ui.pbSkipArom)
            self.ui.pbSkipArom.clicked.connect(self._callback_skip_arom_clicked)

        # Attach control callbacks
        self.ui.cbTrialRun.clicked.connect(self._callback_trialrun_clicked)

        # Update UI.
        self.update_ui()

        # Set the callback when the window is closed.
        self.on_close_callback = onclosecb

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
                self.data.demomode is None
                and self._smachine.state == States.WAIT_TO_MOVE
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
        self.ui.lblStatus.setText(f"{self._smachine.state}")

        # Skip AROM button state
        if hasattr(self.ui, "pbSkipArom"):
            self.ui.pbSkipArom.setEnabled(
                self._smachine.state in (States.REST, States.WAIT_TO_MOVE, States.CYCLING, States.WAIT_FOR_REST)
                and not self.data.all_trials_done
            )

        # Close if needed
        if self._smachine.state == States.DONE:
            self.close()

    def _update_visual_feedabck(self):
        self._update_current_position_cursor()
        _show_arrow = (
            self.ui.dirIndicator is not None
            and self._smachine.state == States.WAIT_TO_MOVE
            and self._smachine._is_arom_cycling
            and self.data._currtrial == 0
        )
        if self.ui.dirIndicator is not None:
            self.ui.dirIndicator.setVisible(_show_arrow)
        if self._smachine.state in (States.CYCLING, States.WAIT_FOR_REST):
            self._update_arom_cursor_position()
            self._update_rest_pos_line()
        elif self._smachine.in_a_trial_state:
            self._draw_stop_zone_lines()
            self._highlight_start_zone()
            self._update_arom_cursor_position()
        elif self._smachine.state == States.REST:
            self._reset_display()

    def _update_current_position_cursor(self):
        if self.data.mechanism == "HOC":
            if self.pluto.hocdisp is None:
                return
            # Plot when there is data to be shown
            self.ui.currPosLine1.setData(
                [self.pluto.hocdisp, self.pluto.hocdisp],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
            self.ui.currPosLine2.setData(
                [-self.pluto.hocdisp, -self.pluto.hocdisp],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
        else:
            if self.pluto.angle is None:
                return
            self.ui.currPosLine1.setData(
                [self._dispsign * self.pluto.angle, self._dispsign * self.pluto.angle],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
            self.ui.currPosLine2.setData(
                [self._dispsign * self.pluto.angle, self._dispsign * self.pluto.angle],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )

    def _draw_stop_zone_lines(self):
        _th = (
            AROM.STOP_POS_HOC_THRESHOLD
            if self.data.mechanism == "HOC"
            else AROM.STOP_POS_NOT_HOC_THRESHOLD
        )
        if self.data.mechanism == "HOC":
            self.ui.stopLine1.setData(
                [self.data.startpos + _th, self.data.startpos + _th],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
            self.ui.stopLine2.setData(
                [-self.data.startpos - _th, -self.data.startpos - _th],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
        else:
            self.ui.stopLine1.setData(
                [
                    self._dispsign * (self.data.startpos - _th),
                    self._dispsign * (self.data.startpos - _th),
                ],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
            self.ui.stopLine2.setData(
                [
                    self._dispsign * (self.data.startpos + _th),
                    self._dispsign * (self.data.startpos + _th),
                ],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )

    def _update_arom_cursor_position(self):
        if self.data.mechanism == "HOC":
            if len(self.data._trialrom) > 1:
                self.ui.romLine1.setData(
                    [-self.data._trialrom[-1], -self.data._trialrom[-1]],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
                self.ui.romLine2.setData(
                    [self.data._trialrom[-1], self.data._trialrom[-1]],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
                self.ui.romFill.setRect(
                    -self.data._trialrom[-1],
                    AROM.CURSOR_LOWER_LIMIT,
                    2 * self.data._trialrom[-1],
                    AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
                )
            return

        # AROM cycling: draw left/right independently from _disp_left/_disp_right
        if self._smachine._is_arom_cycling:
            _dl  = self.data._disp_left
            _dr  = self.data._disp_right
            _gcl = self.data._last_cycle_left
            _gcr = self.data._last_cycle_right
            _h   = AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT

            # Solid boundary lines
            if _dl is not None:
                self.ui.romLine1.setData(
                    [self._dispsign * _dl, self._dispsign * _dl],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
            else:
                self.ui.romLine1.setData([], [])
            if _dr is not None:
                self.ui.romLine2.setData(
                    [self._dispsign * _dr, self._dispsign * _dr],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
            else:
                self.ui.romLine2.setData([], [])

            # Base fill between current boundaries
            if _dl is not None and _dr is not None:
                _l = self._dispsign * min(_dl, _dr)
                _r = self._dispsign * max(_dl, _dr)
                self.ui.romFill.setRect(_l, AROM.CURSOR_LOWER_LIMIT, _r - _l, _h)

            # Ghost lines — previous cycle's extremes
            if _gcl is not None:
                self.ui.ghostLeftLine.setData(
                    [self._dispsign * _gcl, self._dispsign * _gcl],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
            else:
                self.ui.ghostLeftLine.setData([], [])
            if _gcr is not None:
                self.ui.ghostRightLine.setData(
                    [self._dispsign * _gcr, self._dispsign * _gcr],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
            else:
                self.ui.ghostRightLine.setData([], [])

            # Green extension fills — range beyond previous cycle
            if _dl is not None and _gcl is not None and _dl < _gcl:
                _lx = self._dispsign * min(_dl, _gcl)
                self.ui.extFillLeft.setRect(
                    _lx, AROM.CURSOR_LOWER_LIMIT,
                    self._dispsign * abs(_gcl - _dl), _h,
                )
            else:
                self.ui.extFillLeft.setRect(0, AROM.CURSOR_LOWER_LIMIT, 0, _h)
            if _dr is not None and _gcr is not None and _dr > _gcr:
                _lx = self._dispsign * min(_dr, _gcr)
                self.ui.extFillRight.setRect(
                    _lx, AROM.CURSOR_LOWER_LIMIT,
                    self._dispsign * abs(_dr - _gcr), _h,
                )
            else:
                self.ui.extFillRight.setRect(0, AROM.CURSOR_LOWER_LIMIT, 0, _h)
            return

        # PROM / HOC fallback
        if len(self.data._trialrom) == 0:
            return
        _romdisp = sorted(self._dispsign * x for x in self.data._trialrom)
        self.ui.romLine1.setData(
            [_romdisp[0], _romdisp[0]],
            [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
        )
        self.ui.romLine2.setData(
            [_romdisp[-1], _romdisp[-1]],
            [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
        )
        self.ui.romFill.setRect(
            _romdisp[0],
            AROM.CURSOR_LOWER_LIMIT,
            _romdisp[-1] - _romdisp[0],
            AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
        )

    def _highlight_start_zone(self):
        if len(self.data._trialrom) == 0:
            return
        # Fill the start zone
        if self._smachine.state == States.HOLDING_IN_STOP_ZONE:
            if self.data.mechanism == "HOC":
                self.ui.strtZoneFill.setRect(
                    -self.data.startpos - AROM.STOP_POS_HOC_THRESHOLD,
                    AROM.CURSOR_LOWER_LIMIT,
                    2 * (self.data.startpos + AROM.STOP_POS_HOC_THRESHOLD),
                    AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
                )
            else:
                self.ui.strtZoneFill.setRect(
                    self._dispsign * self.data.startpos
                    - AROM.STOP_POS_NOT_HOC_THRESHOLD,
                    AROM.CURSOR_LOWER_LIMIT,
                    2 * AROM.STOP_POS_NOT_HOC_THRESHOLD,
                    AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
                )
        else:
            self.ui.strtZoneFill.setRect(
                0,
                AROM.CURSOR_LOWER_LIMIT,
                0,
                AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
            )

    def _update_rest_pos_line(self):
        if self.ui.restPosLine is None:
            return
        rp = self.data._rest_position
        if rp is not None:
            self.ui.restPosLine.setData(
                [self._dispsign * rp, self._dispsign * rp],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
        else:
            self.ui.restPosLine.setData([], [])

    def _reset_display(self):
        # Reset ROM display
        self.ui.romLine1.setData([], [])
        self.ui.romLine2.setData([], [])
        # Fill between the two AROM lines
        self.ui.romFill.setRect(
            0,
            AROM.CURSOR_LOWER_LIMIT,
            0,
            AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
        )
        # Reset stop zone.
        self.ui.stopLine1.setData([], [])
        self.ui.stopLine2.setData([], [])
        self.ui.strtZoneFill.setRect(
            0,
            AROM.CURSOR_LOWER_LIMIT,
            0,
            AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
        )
        # Reset rest position line
        if self.ui.restPosLine is not None:
            self.ui.restPosLine.setData([], [])
        # Reset ghost lines and extension fills
        _h = AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT
        if self.ui.ghostLeftLine is not None:
            self.ui.ghostLeftLine.setData([], [])
        if self.ui.ghostRightLine is not None:
            self.ui.ghostRightLine.setData([], [])
        if self.ui.extFillLeft is not None:
            self.ui.extFillLeft.setRect(0, AROM.CURSOR_LOWER_LIMIT, 0, _h)
        if self.ui.extFillRight is not None:
            self.ui.extFillRight.setRect(0, AROM.CURSOR_LOWER_LIMIT, 0, _h)
        # Hide direction indicator
        if self.ui.dirIndicator is not None:
            self.ui.dirIndicator.setVisible(False)

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
        _pgobj.hideAxis("bottom")
        _pgobj.hideAxis("left")
        _pgobj.showGrid(x=False, y=False)

        # Current position lines
        self.ui.currPosLine1 = pg.PlotDataItem(
            [0, 0],
            [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            pen=pg.mkPen(color="#FFFFFF", width=2),
        )
        self.ui.currPosLine2 = pg.PlotDataItem(
            [0, 0],
            [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            pen=pg.mkPen(color="#FFFFFF", width=2),
        )
        _pgobj.addItem(self.ui.currPosLine1)
        _pgobj.addItem(self.ui.currPosLine2)

        # ROM Lines — left=orange, right=blue (AROM cycling), both same for PROM/HOC
        _arom_cycling = (self.data.romtype == pfadef.ROMType.ACTIVE
                         and self.data.mechanism != "HOC")
        _left_color  = "#FF8800" if _arom_cycling else "#FF8888"
        _right_color = "#0088FF" if _arom_cycling else "#FF8888"
        self.ui.romLine1 = pg.PlotDataItem(
            [], [],
            pen=pg.mkPen(color=_left_color, width=2),
        )
        self.ui.romLine2 = pg.PlotDataItem(
            [], [],
            pen=pg.mkPen(color=_right_color, width=2),
        )
        _pgobj.addItem(self.ui.romLine1)
        _pgobj.addItem(self.ui.romLine2)

        # ROM Fill
        self.ui.romFill = QGraphicsRectItem()
        self.ui.romFill.setBrush(QColor(180, 160, 255, 60))
        self.ui.romFill.setPen(pg.mkPen(None))
        _pgobj.addItem(self.ui.romFill)

        # Stop zone Lines
        self.ui.stopLine1 = pg.PlotDataItem(
            [0, 0],
            [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            pen=pg.mkPen(color="#FFFFFF", width=1, style=QtCore.Qt.PenStyle.DotLine),
        )
        self.ui.stopLine2 = pg.PlotDataItem(
            [0, 0],
            [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            pen=pg.mkPen(color="#FFFFFF", width=1, style=QtCore.Qt.PenStyle.DotLine),
        )
        _pgobj.addItem(self.ui.stopLine1)
        _pgobj.addItem(self.ui.stopLine2)

        # Start zone Fill
        self.ui.strtZoneFill = QGraphicsRectItem()
        self.ui.strtZoneFill.setBrush(QColor(136, 255, 136, 80))
        self.ui.strtZoneFill.setPen(pg.mkPen(None))  # No border
        _pgobj.addItem(self.ui.strtZoneFill)

        # Rest position line + ghost lines + extension fills (AROM non-HOC cycling only)
        if self.data.romtype == pfadef.ROMType.ACTIVE and self.data.mechanism != "HOC":
            self.ui.restPosLine = pg.PlotDataItem(
                [], [],
                pen=pg.mkPen(color="#00FFFF", width=3),
            )
            _pgobj.addItem(self.ui.restPosLine)
            # Ghost lines — previous cycle's boundaries (dashed, same hue as solid lines)
            self.ui.ghostLeftLine = pg.PlotDataItem(
                [], [],
                pen=pg.mkPen(color=QColor(255, 136, 0, 140), width=1,
                             style=QtCore.Qt.PenStyle.DashLine),
            )
            self.ui.ghostRightLine = pg.PlotDataItem(
                [], [],
                pen=pg.mkPen(color=QColor(0, 136, 255, 140), width=1,
                             style=QtCore.Qt.PenStyle.DashLine),
            )
            _pgobj.addItem(self.ui.ghostLeftLine)
            _pgobj.addItem(self.ui.ghostRightLine)
            # Extension fills — green for range beyond previous cycle
            self.ui.extFillLeft = QGraphicsRectItem()
            self.ui.extFillLeft.setBrush(QColor(0, 220, 80, 90))
            self.ui.extFillLeft.setPen(pg.mkPen(None))
            _pgobj.addItem(self.ui.extFillLeft)
            self.ui.extFillRight = QGraphicsRectItem()
            self.ui.extFillRight.setBrush(QColor(0, 220, 80, 90))
            self.ui.extFillRight.setPen(pg.mkPen(None))
            _pgobj.addItem(self.ui.extFillRight)
            # Direction indicator — shown once at first trial WAIT_TO_MOVE
            self.ui.dirIndicator = pg.TextItem(
                text="◄ Move LEFT first", color="#FFFF00", anchor=(0.5, 0.5)
            )
            self.ui.dirIndicator.setPos(0, 0)
            self.ui.dirIndicator.setFont(QtGui.QFont("Cascadia Mono Light", 20))
            self.ui.dirIndicator.setVisible(False)
            _pgobj.addItem(self.ui.dirIndicator)
            # Z-order: fills → ghost lines → solid boundary lines → cursor → text
            self.ui.romFill.setZValue(1)
            self.ui.extFillLeft.setZValue(2)
            self.ui.extFillRight.setZValue(2)
            self.ui.ghostLeftLine.setZValue(3)
            self.ui.ghostRightLine.setZValue(3)
            self.ui.romLine1.setZValue(4)
            self.ui.romLine2.setZValue(4)
            self.ui.currPosLine1.setZValue(5)
            self.ui.currPosLine2.setZValue(5)
            self.ui.dirIndicator.setZValue(6)
        else:
            self.ui.restPosLine = None
            self.ui.ghostLeftLine = None
            self.ui.ghostRightLine = None
            self.ui.extFillLeft = None
            self.ui.extFillRight = None
            self.ui.dirIndicator = None

        # Angle display sign for the limb.
        self._dispsign = 1.0

        # AROM lines when appropriate.
        if self.data.arom is not None:
            _pos = (
                [-self.data.arom[1], -self.data.arom[1]]
                if self.data.mechanism == "HOC"
                else [
                    self._dispsign * self.data.arom[0],
                    self._dispsign * self.data.arom[0],
                ]
            )
            self.ui.aromPosLine1 = pg.PlotDataItem(
                _pos,
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                pen=pg.mkPen(
                    color="#1EFF00", width=1, style=QtCore.Qt.PenStyle.DotLine
                ),
            )
            _pos = (
                [self.data.arom[1], self.data.arom[1]]
                if self.data.mechanism == "HOC"
                else [
                    self._dispsign * self.data.arom[1],
                    self._dispsign * self.data.arom[1],
                ]
            )
            self.ui.aromPosLine2 = pg.PlotDataItem(
                _pos,
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                pen=pg.mkPen(
                    color="#1EFF00", width=1, style=QtCore.Qt.PenStyle.DotLine
                ),
            )
            _pgobj.addItem(self.ui.aromPosLine1)
            _pgobj.addItem(self.ui.aromPosLine2)

        # Instruction text
        self.ui.subjInst = pg.TextItem(text="", color="w", anchor=(0.5, 0.5))
        self.ui.subjInst.setPos(0, 15)
        self.ui.subjInst.setFont(QtGui.QFont("Cascadia Mono Light", 14))
        _pgobj.addItem(self.ui.subjInst)

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
        self._smachine.run_statemachine(pdef.PlutoEvents.NEWDATA, dt=self.pluto.delt())
        # Update the GUI only at 1/10 the data rate
        if np.random.rand() < 0.05:
            self.update_ui()
        #
        # Log data
        if self.data.logstate == RawDataLoggingState.LOG_DATA:
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
                    self.pluto.button,
                    self.data.currtrial,
                    f"{self._smachine.state.name}",
                ]
            )

    def _callback_pluto_btn_released(self):
        # Run the statemachine
        apromset = self._smachine.run_statemachine(
            pdef.PlutoEvents.RELEASED, dt=self.pluto.delt()
        )
        self.update_ui()

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

    def _callback_skip_arom_clicked(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Skip AROM",
            "Skip AROM assessment?\nDiscrete reaching will be disabled for this mechanism.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self._arom_skipped = True
            self.close()

    def closeEvent(self, event):
        # Skip AROM was requested — bypass normal dialogs.
        if self._arom_skipped:
            data = {
                "romval": self.data.rom,
                "done": False,
                "status": pfadef.AssessStatus.SKIPPED.value,
                "taskcomment": "Skipped by assessor from ROM assessment window",
            }
            if self.on_close_callback:
                self.on_close_callback(data=data)
            self._detach_pluto_callbacks()
            return super().closeEvent(event)

        # Get comment from the experimenter.
        data = {"romval": self.data.rom, "done": self.data.all_trials_done}
        if self.data.all_trials_done:
            _comment = CommentDialog(
                label="AROM completed. Accept or reject?", optionyesno=True
            )
            if _comment.exec() == QtWidgets.QDialog.Accepted:
                data["status"] = pfadef.AssessStatus.COMPLETE.value
            else:
                data["status"] = pfadef.AssessStatus.REJECTED.value
            data["taskcomment"] = _comment.getText()
        else:
            _comment = CommentDialog(label="AROM incomplete. Why?", optionyesno=False)
            if _comment.exec() == QtWidgets.QDialog.Rejected:
                data["taskcomment"] = _comment.getText()
                data["status"] = pfadef.AssessStatus.TERMINATED.value
        if self.on_close_callback:
            self.on_close_callback(data=data)
        # Detach PLUTO callbacks.
        self._detach_pluto_callbacks()
        return super().closeEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    plutodev = QtPluto("COM4")
    plutodev.start_sensorstream()
    plutodev.send_heartbeat()
    pcalib = PlutoAPRomAssessWindow(
        plutodev=plutodev,
        assessinfo={
            "type": "Stroke",
            "limb": "RIGHT",
            "mechanism": "FPS",
            "romtype": pfadef.ROMType.ACTIVE,
            "session": "testing",
            "ntrials": 1,
            "rawfile": "rawfiletest.csv",
            "summaryfile": "summaryfiletest.csv",
            "arom": None,
        },
        onclosecb=lambda data: print(f"Data: {data}"),
    )
    pcalib.show()
    sys.exit(app.exec())

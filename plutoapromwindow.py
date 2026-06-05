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
        # AROM cycling fields (non-HOC AROM only) — rest-driven marking.
        # Nothing is drawn while moving; a boundary is marked when the subject
        # comes to rest (|vel| ~ 0). Side is decided by displacement.
        self._cycle_left = None              # committed left extreme, current cycle
        self._cycle_right = None             # committed right extreme, current cycle
        self._rest_committed = False         # guard: mark once per rest
        self._last_rest_pos = None           # position of last marked rest (side reference)
        self._cycle_history = []          # (left, right) per completed cycle, max 3
        self._all_cycles = []             # (left, right) per completed cycle, all of them
        self._cycles_completed = 0
        self._rest_position = None
        self._disp_left = None            # left boundary for display
        self._disp_right = None           # right boundary for display
        # Cycling: which side is currently being marked, switched by a position
        # threshold. _lo/_hi hold the measured low/high extremes of the pending
        # cycle (non-HOC pairing). Cycles are built only from measured movement
        # extremes — the start/centre is never marked.
        self._active_side = None
        self._lo = None
        self._hi = None
        # Logging variables
        self._logstate: RawDataLoggingState = RawDataLoggingState.WAIT_FOR_LOG
        self._rawfilewriter: misc.CSVBufferWriter = misc.CSVBufferWriter(
            self.rawfile, header=AROM.RAW_HEADER
        )
        _hdr = (
            AROM.SUMMARY_HEADER_CYCLING
            if assessinfo["romtype"] == pfadef.ROMType.ACTIVE
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
    def arom_center(self):
        """Midpoint of the AROM range, or None if no AROM was provided."""
        _a = self.arom
        return None if _a is None else (_a[0] + _a[1]) / 2.0

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
            self._currtrial = 0 if reset else self._currtrial + 1
            self._reset_trial_fields()

    def redo_current_trial(self):
        """Repeat the current trial (index unchanged) — clear its data only.
        Used when a trial times out but the assessor wants to retry it (e.g. a
        device/setup problem rather than a patient limitation)."""
        self._reset_trial_fields()

    def _reset_trial_fields(self):
        """Clear all trial-local data (does not touch the trial index)."""
        self._trialdata = {"dt": [], "pos": [], "vel": []}
        self._trialrom = []
        self._startpos = None
        # Reset cycling fields
        self._cycle_left = None
        self._cycle_right = None
        self._rest_committed = False
        self._last_rest_pos = None
        self._cycle_history = []
        self._all_cycles = []
        self._cycles_completed = 0
        self._rest_position = None
        self._disp_left = None
        self._disp_right = None
        self._active_side = None
        self._lo = None
        self._hi = None

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
        # HOC PROM is open-only from the pinned closed end (0): record the max
        # open freely (no AROM constraint); the closed end stays at 0.
        if self.mechanism == "HOC" and self.romtype == pfadef.ROMType.PASSIVE:
            if _out_of_rom:
                self._trialrom.append(_pos)
                self._trialrom.sort()
                self._trialrom[:] = [self._trialrom[0], self._trialrom[-1]]
                return True
            return False
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
        # HOC: the closed end is bounded at fully closed (~0). When the AROM
        # closed boundary already sits at fully closed, the passive range cannot
        # be pushed beyond it, so accept a closed point that reaches within
        # FULLY_CLOSED_HOC_THRESHOLD of fully closed even though it is not
        # outside the (already fully-closed) AROM. Open side is unaffected.
        _near_fully_closed = (
            self.mechanism == "HOC"
            and _pos <= AROM.FULLY_CLOSED_HOC_THRESHOLD
        )
        if _out_of_rom and (_out_of_arom or _near_fully_closed):
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
        # HOC is one-sided: open-only from the closed start (0). Non-HOC is
        # two-sided about the start/centre.
        if self.mechanism == "HOC":
            return self._trialrom[-1] - self._startpos > _th
        return (
            self._trialrom[0] - self._startpos < -_th
            and self._trialrom[-1] - self._startpos > _th
        )

    def _update_cycling_hoc(self, pos) -> bool:
        """HOC open/close cycling, determined ONLY by back-and-forth movement.

        Both boundaries are measured movement extremes — the fully-closed start
        position is NEVER marked or used as a boundary. startpos serves only to
        detect the first opening direction (and a small dead zone so tremor at
        the start does not seed anything).

        Extremes are marked with the velocity/rest rule (the part that works):
        the active boundary's value updates only while at rest. Which boundary
        is active flips by a position threshold from the current extreme
        (CYCLING_MIN_EXCURSION_HOC), checked every sample:

          - OPENING: extend the open mark at rest. Reverse-close past
            (open - threshold) -> open is final; start measuring the close.
          - CLOSING: extend the close mark at rest. Reverse-open past
            (close + threshold) -> the close is final, so a full cycle
            (measured close + measured open) is COUNTED; start the next open.

        A cycle therefore needs a measured open AND a measured close — the first
        cycle is not counted until the hand has actually closed and reversed, so
        nothing is ever pinned at the start. Returns True when a cycle counts."""
        if not self._trialdata["vel"]:
            return False
        _n = AROM.CYCLING_HOLD_SAMPLES
        vel_mean = float(np.mean(self._trialdata["vel"][-_n:]))
        _rest_th = AROM.CYCLING_REST_VEL_THRESHOLD_HOC
        _switch_th = AROM.CYCLING_MIN_EXCURSION_HOC
        _at_rest = abs(vel_mean) <= _rest_th

        # Wait for the first real opening (past a dead zone above the start) to
        # begin. The start position itself is never recorded.
        if self._active_side is None:
            if _at_rest and pos > self._startpos + _switch_th:
                self._active_side = "OPENING"
                self._cycle_right = pos
                self._disp_right = pos
            return False

        if self._active_side == "OPENING":
            # Extend the open extreme only at rest.
            if _at_rest and (self._cycle_right is None or pos > self._cycle_right):
                self._cycle_right = pos
                self._disp_right = pos
            # Reversed toward closed past the threshold -> open is final; begin
            # measuring the close (no mark yet — set by the first close rest).
            if self._cycle_right is not None and pos < self._cycle_right - _switch_th:
                self._active_side = "CLOSING"
                self._cycle_left = None
                self._disp_left = None
        else:  # CLOSING
            # Extend the close extreme only at rest.
            if _at_rest and (self._cycle_left is None or pos < self._cycle_left):
                self._cycle_left = pos
                self._disp_left = pos
            # Reversed toward open past the threshold -> close is final. Both
            # extremes are now measured: count the cycle and start the next open.
            if self._cycle_left is not None and pos > self._cycle_left + _switch_th:
                self._cycles_completed += 1
                _cyc = (self._cycle_left, self._cycle_right)
                self._cycle_history.append(_cyc)
                self._all_cycles.append(_cyc)
                if len(self._cycle_history) > 3:
                    self._cycle_history.pop(0)
                self._active_side = "OPENING"
                self._cycle_right = pos
                self._disp_right = pos
                return True
        return False

    def _record_cycle(self) -> bool:
        """Record the current (low, high) extreme pair as a completed cycle and
        arm the next pair. Both extremes are measured movement extremes."""
        self._cycles_completed += 1
        _cyc = (self._lo, self._hi)
        self._cycle_history.append(_cyc)
        self._all_cycles.append(_cyc)
        if len(self._cycle_history) > 3:
            self._cycle_history.pop(0)
        self._lo = None
        self._hi = None
        return True

    def _update_cycling_nonhoc(self, pos) -> bool:
        """Non-HOC AROM cycling (FPS / WFE / WURD): back-and-forth about the
        centre, same principle as HOC (see _update_cycling_hoc).

        The extreme VALUE is marked by the velocity/rest rule (updated only
        while at rest); which side is active flips by a position threshold
        reversal from the current extreme (no rest required). Both extremes lie
        on opposite sides of the centre (the start), which is never itself a
        boundary. A cycle = one low-side extreme + one high-side extreme, both
        measured; it is counted when the second of the pair is finalized, so it
        is robust to which side the subject moves to first. Returns True on the
        cycle-counting reversal."""
        if not self._trialdata["vel"]:
            return False
        _n = AROM.CYCLING_HOLD_SAMPLES
        vel_mean = float(np.mean(self._trialdata["vel"][-_n:]))
        _rest_th = AROM.CYCLING_REST_VEL_THRESHOLD
        _switch_th = AROM.CYCLING_MIN_EXCURSION
        _at_rest = abs(vel_mean) <= _rest_th

        # Seed the first active side from the first rested movement away from the
        # centre (dead zone = switch threshold). The centre is never marked.
        if self._active_side is None:
            if _at_rest and abs(pos - self._startpos) >= _switch_th:
                if pos >= self._startpos:
                    self._active_side = "HI"
                    self._cycle_right = pos
                    self._disp_right = pos
                else:
                    self._active_side = "LO"
                    self._cycle_left = pos
                    self._disp_left = pos
            return False

        if self._active_side == "HI":
            # Track the high-side extreme only at rest.
            if _at_rest and (self._cycle_right is None or pos > self._cycle_right):
                self._cycle_right = pos
                self._disp_right = pos
            # Reversed below the high extreme past the threshold -> it is final.
            if self._cycle_right is not None and pos < self._cycle_right - _switch_th:
                self._hi = self._cycle_right
                self._active_side = "LO"
                if self._lo is not None:
                    # Pair complete: count, then start the low side fresh here.
                    self._cycle_left = pos
                    self._disp_left = pos
                    return self._record_cycle()
                self._cycle_left = None
                self._disp_left = None
        else:  # LO
            # Track the low-side extreme only at rest.
            if _at_rest and (self._cycle_left is None or pos < self._cycle_left):
                self._cycle_left = pos
                self._disp_left = pos
            # Reversed above the low extreme past the threshold -> it is final.
            if self._cycle_left is not None and pos > self._cycle_left + _switch_th:
                self._lo = self._cycle_left
                self._active_side = "HI"
                if self._hi is not None:
                    self._cycle_right = pos
                    self._disp_right = pos
                    return self._record_cycle()
                self._cycle_right = None
                self._disp_right = None
        return False

    def update_cycling_data(self, pos) -> bool:
        """Cycling boundary marking, routed by mechanism. HOC opens from a
        closed start (_update_cycling_hoc); FPS/WFE/WURD oscillate about a centre
        (_update_cycling_nonhoc). Both build cycles only from measured movement
        extremes — the start/centre is never a boundary — with the extreme value
        marked at rest and the active side switched by a position threshold."""
        if self.mechanism == "HOC":
            return self._update_cycling_hoc(pos)
        return self._update_cycling_nonhoc(pos)

    @property
    def all_cycles(self):
        """Every completed cycle as (left, right), left <= right."""
        return [(min(c), max(c)) for c in self._all_cycles]

    @property
    def cycles_done(self):
        return self._cycles_completed >= AROM.NO_OF_CYCLES

    @property
    def best_cycle(self):
        """Best cycle in the current window (last <=3 completed): the one with
        the widest AROM range. Window grows 1 -> 2 -> 3 then slides. Returned
        as (left, right) with left <= right regardless of mark order."""
        if not self._cycle_history:
            return None
        _bc = max(self._cycle_history, key=lambda c: abs(c[1] - c[0]))
        return (min(_bc), max(_bc))

    @property
    def ghost_left(self):
        bc = self.best_cycle
        return None if bc is None else bc[0]

    @property
    def ghost_right(self):
        bc = self.best_cycle
        return None if bc is None else bc[1]

    def compute_rest_position(self):
        """Rest position = midpoint of the best cycle's AROM in the window."""
        self._rest_position = (self.ghost_left + self.ghost_right) / 2.0

    def set_rom(self):
        """Set the ROM value for the given trial."""
        if self._assessinfo["romtype"] == pfadef.ROMType.ACTIVE:
            # AROM cycling path — AROM = best cycle in window (widest range).
            _bl, _br = self.best_cycle
            self._rom[self._currtrial] = [_bl, _br]
            self._summaryfilewriter.write_row([
                self.session,
                self.type,
                self.limb,
                self.mechanism,
                self.currtrial,
                _bl,
                _br,
                _br - _bl,
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

    def write_failed_trial(self):
        """Log the current trial as failed ("did not qualify") when the trial
        time limit expires. Mirrors set_rom's header choice so the row width
        matches. No valid ROM is recorded for the trial."""
        _dnq = "did not qualify"
        if self._assessinfo["romtype"] == pfadef.ROMType.ACTIVE:
            # Cycling header (10 cols)
            self._summaryfilewriter.write_row([
                self.session, self.type, self.limb, self.mechanism,
                self.currtrial, _dnq, _dnq, _dnq, _dnq, self._cycles_completed,
            ])
        else:
            # PROM / HOC header (9 cols)
            self._summaryfilewriter.write_row([
                self.session, self.type, self.limb, self.mechanism,
                self.currtrial, self._startpos, _dnq, _dnq, _dnq,
            ])
        if 0 <= self._currtrial < self.ntrials:
            self._rom[self._currtrial] = []

    def set_startpos(self):
        """Sets the start position at the sample of lowest velocity in the window."""
        self._startpos = float(self._trialdata["pos"][int(np.argmin(np.abs(self._trialdata["vel"])))])
        self._trialrom = [self._startpos]

    def set_startpos_center(self):
        """Pin the start position to the AROM centre (centred PROM). All zone
        and validity logic then pivots on the AROM centre instead of the live
        start position."""
        self._startpos = float(self.arom_center)
        self._trialrom = [self._startpos]

    def set_startpos_closed(self):
        """Pin the closed reference to fully closed (0) for open-only HOC PROM.
        PROM is then recorded as [0, max-open]."""
        self._startpos = 0.0
        self._trialrom = [0.0]

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
        return self._data.romtype == pfadef.ROMType.ACTIVE

    @property
    def _is_prom_centered(self):
        """PROM that is centred on the AROM centre: passive and AROM was
        completed (so an AROM range/centre is available). Non-HOC only — HOC
        PROM is open-only (see _is_hoc_prom)."""
        return (self._data.romtype == pfadef.ROMType.PASSIVE
                and self._data.arom is not None
                and self._data.mechanism != "HOC")

    @property
    def _is_hoc_prom(self):
        """HOC PROM: open-only from the fully-closed start (0). No centre, no
        return-to-rest; the trial records the max open and the assessor ends it
        with the PLUTO button."""
        return (self._data.mechanism == "HOC"
                and self._data.romtype == pfadef.ROMType.PASSIVE)

    def _pos(self):
        """Live mechanism position (cm for HOC, deg otherwise)."""
        return (
            self._pluto.hocdisp
            if self._data.mechanism == "HOC"
            else self._pluto.angle
        )

    @property
    def _center_threshold(self):
        """Start-gate / stop-zone half-width in the mechanism's units."""
        return (
            AROM.STOP_POS_HOC_THRESHOLD
            if self._data.mechanism == "HOC"
            else AROM.STOP_POS_NOT_HOC_THRESHOLD
        )

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

    def fail_current_trial(self):
        """Abandon the current trial (time limit hit) and advance to the next.
        The failed trial has already been logged by the window; here we just
        move the trial index forward and return to REST."""
        self._state = States.REST
        self._statetimer = 0
        self._instruction = f""
        self._data.start_newtrial()

    def redo_current_trial(self):
        """Repeat the current trial (time limit hit but the assessor chose to
        retry). Resets to REST without advancing the trial index."""
        self._state = States.REST
        self._statetimer = 0
        self._instruction = f""
        self._data.redo_current_trial()

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
        _centered = self._is_prom_centered
        _center = self._data.arom_center
        _trial_tag = (
            "demo trial"
            if self._data.demomode
            else f"trial {self._data._currtrial + 1}/{self._data.ntrials}"
        )
        _unit = "cm" if self._data.mechanism == "HOC" else "deg"
        if self._is_hoc_prom:
            self._instruction = (
                f"Close the hand fully, hold and press PLUTO Button to start "
                f"{_trial_tag}."
            )
        elif _centered:
            self._instruction = (
                f"Move to centre ({_center:.1f} {_unit}), hold and press PLUTO "
                f"Button to start {_trial_tag}."
            )
        else:
            self._instruction = f"Hold and press PLUTO Button to start {_trial_tag}."
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
                    # Centred PROM must begin at the AROM centre — gate on it.
                    if _centered and not self.subj_near_center():
                        return
                    if self._is_hoc_prom:
                        # Open-only: pin the closed end at 0, record max open.
                        self._data.set_startpos_closed()
                    elif _centered:
                        self._data.set_startpos_center()
                    else:
                        self._data.set_startpos()
                    self._state = States.WAIT_TO_MOVE
                    self._statetimer = 0
                    if not self._data.demomode:
                        self._data.start_rawlogging()

    def _handle_wait_to_move(self, event, dt):
        if self._is_arom_cycling:
            self._instruction = (
                "Open the hand, then close — repeat"
                if self._data.mechanism == "HOC"
                else "Move LEFT ◄ first, then cycle back and forth"
            )
            if event == pdef.PlutoEvents.NEWDATA:
                # Start on position displacement, not speed, so a slow mover
                # (never crossing the draw threshold) still begins cycling.
                if self.away_from_start():
                    self._state = States.CYCLING
        else:
            self._instruction = (
                "Open the hand — press the PLUTO Button when done."
                if self._is_hoc_prom
                else "Move an hold to record ROM."
            )
            if event == pdef.PlutoEvents.NEWDATA:
                if self.subj_is_holding() is False and self.away_from_start():
                    self._state = States.MOVING

    def _handle_moving(self, event, dt):
        # HOC PROM is open-only: record the max open continuously and let the
        # assessor end the trial with the PLUTO button (no return-to-rest).
        if self._is_hoc_prom:
            self._instruction = "Open the hand — press the PLUTO Button when done."
            if event == pdef.PlutoEvents.NEWDATA:
                _ = self._data.add_new_trialrom_data()
            elif event == pdef.PlutoEvents.RELEASED and self._data.is_trialrom_valid():
                if not self._data.demomode:
                    self._data.set_rom()
                    self._data.start_newtrial()
                self._state = States.REST
            return
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
        _pos = (
            self._pluto.hocdisp
            if self._data.mechanism == "HOC"
            else self._pluto.angle
        )
        self._data.update_cycling_data(_pos)
        n = self._data._cycles_completed
        self._instruction = f"Keep cycling! {n}/{AROM.NO_OF_CYCLES} cycles done"
        if self._data.cycles_done:
            self._data.compute_rest_position()
            self._statetimer = AROM.REST_ZONE_HOLD_DURATION
            self._state = States.WAIT_FOR_REST

    def _handle_wait_for_rest(self, event, dt):
        # The 5 cycles are done and the clock is stopped — this rest-hold step
        # is untimed. The assessor may finish the trial at any moment with the
        # PLUTO button, or it completes after a brief hold inside the rest zone.
        if event == pdef.PlutoEvents.RELEASED:
            self._complete_cycling_trial()
            return
        if event != pdef.PlutoEvents.NEWDATA:
            return
        rp = self._data._rest_position
        _unit = "cm" if self._data.mechanism == "HOC" else "deg"
        if self.subj_is_holding() and self.subj_in_rest_zone():
            self._statetimer -= dt
            self._instruction = (
                f"Hold for {self._statetimer:2.1f}s at rest ({rp:.1f} {_unit}),"
                f" or press the PLUTO Button"
            )
            if self._statetimer <= 0:
                self._complete_cycling_trial()
        else:
            self._statetimer = AROM.REST_ZONE_HOLD_DURATION
            self._instruction = (
                f"Move to rest position ({rp:.1f} {_unit}) and hold,"
                f" or press the PLUTO Button"
            )

    def _complete_cycling_trial(self):
        """Finalise the current cycling trial (5 cycles already done): log it
        and advance. Demo trials are not logged."""
        if not self._data.demomode:
            self._data.set_rom()
            self._data.start_newtrial()
        self._state = States.REST
        self._statetimer = 0

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
        # Centred PROM stops in a band around the AROM centre (two-sided) for
        # every mechanism. Non-centred HOC keeps its one-sided check.
        if self._is_prom_centered:
            return bool(np.abs(self._pos() - self._data.startpos) < self._center_threshold)
        if self._data.mechanism == "HOC":
            return (
                self._pluto.hocdisp - self._data.startpos
            ) < AROM.STOP_POS_HOC_THRESHOLD
        else:
            return (
                np.abs(self._pluto.angle - self._data.startpos)
                < AROM.STOP_POS_NOT_HOC_THRESHOLD
            )

    def subj_near_center(self):
        """Check if the limb is held within the start zone around the AROM
        centre (used to gate the start of a centred PROM trial)."""
        c = self._data.arom_center
        if c is None:
            return False
        return bool(np.abs(self._pos() - c) <= self._center_threshold)

    def subj_in_rest_zone(self):
        """Check if subject is within the rest-zone half-width of the rest
        position (HOC uses the cm twin and hocdisp)."""
        rp = self._data._rest_position
        if rp is None:
            return False
        if self._data.mechanism == "HOC":
            return bool(
                np.abs(self._pluto.hocdisp - rp) <= AROM.REST_ZONE_HALF_WIDTH_HOC
            )
        return bool(np.abs(self._pluto.angle - rp) <= AROM.REST_ZONE_HALF_WIDTH)

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

        # Per-trial time limit (AROM only). A wall-clock countdown is shown on
        # the top bar; if a trial is not completed within AROM.TRIAL_TIME_LIMIT
        # the trial is failed. MAX_FAILED_TRIALS failures terminate the AROM
        # assessment (which disables discrete reaching for this mechanism).
        self._is_arom = self.data.romtype == pfadef.ROMType.ACTIVE
        self._failed_trials = 0
        self._trial_active = False
        self._trial_secs_left = AROM.TRIAL_TIME_LIMIT
        if self._is_arom:
            self.ui.lblCountdown = QtWidgets.QLabel("")
            self.ui.lblCountdown.setStyleSheet("color: rgb(0, 170, 0);")
            self.ui.lblCountdown.setFont(QtGui.QFont("Cascadia Mono Light", 16))
            self.ui.horizontalLayout.addWidget(self.ui.lblCountdown)
            self._trialtimer = QTimer()
            self._trialtimer.timeout.connect(self._trial_timer_tick)
            self._trialtimer.start(1000)

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

    @property
    def _is_hoc_cycling(self):
        """HOC driven by the cycling engine (HOC + AROM/ACTIVE). PROM/APROM-HOC
        stay on the old single-value path."""
        return (
            self.data.mechanism == "HOC"
            and self.data.romtype == pfadef.ROMType.ACTIVE
        )

    @property
    def _is_prom_centered(self):
        """Centred PROM: passive and AROM completed (range/centre available).
        Non-HOC only — HOC PROM is open-only (see _is_hoc_prom). Drives the
        single-line centred display, resting reference, and centre start gate."""
        return (
            self.data.romtype == pfadef.ROMType.PASSIVE
            and self.data.arom is not None
            and self.data.mechanism != "HOC"
        )

    @property
    def _is_hoc_prom(self):
        """HOC PROM: open-only, corner-anchored 0 -> open display."""
        return (
            self.data.mechanism == "HOC"
            and self.data.romtype == pfadef.ROMType.PASSIVE
        )

    def _xpos(self, pos):
        """Map a mechanism position to an x-coordinate for drawing.

        HOC pins the closed end (~0) to a corner by hand side: right hand ->
        closed at the left corner (x = pos); left hand -> closed at the right
        corner (x = MAXHOC - pos). Non-HOC uses the display sign."""
        if self.data.mechanism == "HOC":
            _is_left = str(self.data.limb).strip().lower() == "left"
            return (AROM.MAXHOC - pos) if _is_left else pos
        return self._dispsign * pos

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
            self._update_cycle_history_lines()
            self._update_rest_pos_line()
        elif self._smachine.in_a_trial_state:
            self._draw_stop_zone_lines()
            self._highlight_start_zone()
            self._update_arom_cursor_position()
            if self._is_prom_centered:
                self._draw_center_rest_line()
        elif self._smachine.state == States.REST:
            self._reset_display()
            if self._is_prom_centered:
                self._draw_center_guide()
                self._draw_center_rest_line()

    def _update_current_position_cursor(self):
        if self.data.mechanism == "HOC":
            if self.pluto.hocdisp is None:
                return
            if self._is_hoc_cycling or self._is_prom_centered or self._is_hoc_prom:
                # Single corner-anchored cursor line (cycling AROM, centred PROM
                # and open-only HOC PROM all use the 0..MAXHOC view).
                _x = self._xpos(self.pluto.hocdisp)
                self.ui.currPosLine1.setData(
                    [_x, _x],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
                self.ui.currPosLine2.setData([], [])
                return
            # PROM / APROM HOC (no AROM) — old symmetric two-line display.
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

    def _draw_center_guide(self):
        """Show the start zone around the AROM centre during REST so the
        assessor can move the limb into the gate before starting the trial."""
        c = self.data.arom_center
        if c is None:
            return
        _th = (
            AROM.STOP_POS_HOC_THRESHOLD
            if self.data.mechanism == "HOC"
            else AROM.STOP_POS_NOT_HOC_THRESHOLD
        )
        _y = [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT]
        self.ui.stopLine1.setData([self._xpos(c - _th)] * 2, _y)
        self.ui.stopLine2.setData([self._xpos(c + _th)] * 2, _y)

    def _draw_center_rest_line(self):
        """Persistent resting/centre reference for centred PROM: a solid cyan
        line at the AROM centre with a shaded rest band, shown through REST and
        the trial states. Works for every mechanism via _xpos."""
        if self.ui.restPosLine is None:
            return
        c = self.data.arom_center
        if c is None:
            return
        _hw = (
            AROM.REST_ZONE_HALF_WIDTH_HOC
            if self.data.mechanism == "HOC"
            else AROM.REST_ZONE_HALF_WIDTH
        )
        _h = AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT
        _xc = self._xpos(c)
        self.ui.restPosLine.setData(
            [_xc, _xc], [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT]
        )
        self.ui.restZoneFill.setRect(_xc - _hw, AROM.CURSOR_LOWER_LIMIT, 2 * _hw, _h)

    def _draw_stop_zone_lines(self):
        # Open-only HOC PROM has no stop zone (no return-to-rest).
        if self._is_hoc_prom:
            self.ui.stopLine1.setData([], [])
            self.ui.stopLine2.setData([], [])
            return
        _th = (
            AROM.STOP_POS_HOC_THRESHOLD
            if self.data.mechanism == "HOC"
            else AROM.STOP_POS_NOT_HOC_THRESHOLD
        )
        # Centred PROM: a symmetric band about the AROM centre (= startpos),
        # mapped through _xpos so HOC and non-HOC share one path.
        if self._is_prom_centered:
            _sp = self.data.startpos
            _y = [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT]
            self.ui.stopLine1.setData([self._xpos(_sp - _th)] * 2, _y)
            self.ui.stopLine2.setData([self._xpos(_sp + _th)] * 2, _y)
            return
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
        if (
            self.data.mechanism == "HOC"
            and not self._is_hoc_cycling
            and not self._is_prom_centered
            and not self._is_hoc_prom
        ):
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

        # AROM cycling: solid lines = current L/R rest marks; filled band =
        # best of the last <=3 cycles.
        if self._smachine._is_arom_cycling:
            _h  = AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT

            # Current boundary marks (updated each time the subject rests L/R)
            _dl = self.data._disp_left
            _dr = self.data._disp_right
            if _dl is not None:
                self.ui.romLine1.setData(
                    [self._xpos(_dl), self._xpos(_dl)],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
            else:
                self.ui.romLine1.setData([], [])
            if _dr is not None:
                self.ui.romLine2.setData(
                    [self._xpos(_dr), self._xpos(_dr)],
                    [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                )
            else:
                self.ui.romLine2.setData([], [])

            # Best-of-3 envelope band — shown ONLY at the end (after the 5th
            # cycle, i.e. in WAIT_FOR_REST), not on every cycle.
            _bl = self.data.ghost_left
            _br = self.data.ghost_right
            if (self._smachine.state == States.WAIT_FOR_REST
                    and _bl is not None and _br is not None):
                _l = min(self._xpos(_bl), self._xpos(_br))
                _r = max(self._xpos(_bl), self._xpos(_br))
                self.ui.romFill.setRect(_l, AROM.CURSOR_LOWER_LIMIT, _r - _l, _h)
            else:
                self.ui.romFill.setRect(0, AROM.CURSOR_LOWER_LIMIT, 0, _h)
            return

        # PROM / HOC fallback (incl. centred PROM). _xpos handles the HOC
        # corner anchoring and reduces to _dispsign*x for the other mechanisms.
        if len(self.data._trialrom) == 0:
            return
        _romdisp = sorted(self._xpos(x) for x in self.data._trialrom)
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
            if self._is_prom_centered:
                # Band about the AROM centre (= startpos), mapped via _xpos.
                _th = (
                    AROM.STOP_POS_HOC_THRESHOLD
                    if self.data.mechanism == "HOC"
                    else AROM.STOP_POS_NOT_HOC_THRESHOLD
                )
                _sp = self.data.startpos
                _x0 = min(self._xpos(_sp - _th), self._xpos(_sp + _th))
                self.ui.strtZoneFill.setRect(
                    _x0,
                    AROM.CURSOR_LOWER_LIMIT,
                    2 * _th,
                    AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT,
                )
            elif self.data.mechanism == "HOC":
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

    def _update_cycle_history_lines(self):
        """Draw every completed cycle as a pair of dotted lines: left extreme
        orange, right extreme blue."""
        if not self.ui.cycleLeftLines:
            return
        _cycles = self.data.all_cycles
        _y = [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT]
        for _i, (_ll, _rl) in enumerate(
            zip(self.ui.cycleLeftLines, self.ui.cycleRightLines)
        ):
            if _i < len(_cycles):
                _l, _r = _cycles[_i]
                _ll.setData([self._xpos(_l), self._xpos(_l)], _y)
                _rl.setData([self._xpos(_r), self._xpos(_r)], _y)
            else:
                _ll.setData([], [])
                _rl.setData([], [])
        # Top-right readout: ROM per completed cycle (cm for HOC, deg otherwise).
        if self.ui.cycleListText is not None:
            _unit = "cm" if self.data.mechanism == "HOC" else "deg"
            _lines = [
                f"Cycle {_i + 1}: {abs(_r - _l):.1f} {_unit}"
                for _i, (_l, _r) in enumerate(_cycles)
            ]
            # Final AROM = best of last 3 cycles, shown only once cycling done.
            _bc = self.data.best_cycle
            if self.data.cycles_done and _bc is not None:
                _lines.append("")
                _lines.append(f"AROM: {abs(_bc[1] - _bc[0]):.1f} {_unit}")
            self.ui.cycleListText.setText("\n".join(_lines))

    def _update_rest_pos_line(self):
        if self.ui.restPosLine is None:
            return
        rp = self.data._rest_position
        _h = AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT
        _hw = (
            AROM.REST_ZONE_HALF_WIDTH_HOC
            if self.data.mechanism == "HOC"
            else AROM.REST_ZONE_HALF_WIDTH
        )
        if rp is not None:
            self.ui.restPosLine.setData(
                [self._xpos(rp), self._xpos(rp)],
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
            )
            self.ui.restZoneFill.setRect(
                self._xpos(rp) - _hw,
                AROM.CURSOR_LOWER_LIMIT,
                2 * _hw,
                _h,
            )
        else:
            self.ui.restPosLine.setData([], [])
            self.ui.restZoneFill.setRect(0, AROM.CURSOR_LOWER_LIMIT, 0, _h)

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
        # Reset rest position line and zone
        if self.ui.restPosLine is not None:
            self.ui.restPosLine.setData([], [])
        if self.ui.restZoneFill is not None:
            _h = AROM.CURSOR_UPPER_LIMIT - AROM.CURSOR_LOWER_LIMIT
            self.ui.restZoneFill.setRect(0, AROM.CURSOR_LOWER_LIMIT, 0, _h)
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
        # Reset completed-cycle dotted lines
        for _ll in self.ui.cycleLeftLines:
            _ll.setData([], [])
        for _rl in self.ui.cycleRightLines:
            _rl.setData([], [])
        if self.ui.cycleListText is not None:
            self.ui.cycleListText.setText("")
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
            # Corner-anchored axis 0..MAXHOC for cycling AROM and centred PROM;
            # old symmetric axis about 0 for plain (no-AROM) HOC PROM/APROM.
            _range = (
                [-0.5, AROM.MAXHOC + 0.5]
                if (self._is_hoc_cycling or self._is_prom_centered)
                else [-10, 10]
            )
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

        # ROM Lines — left=orange, right=blue (AROM cycling, incl. HOC closed/
        # open), both same pink for PROM/APROM.
        _arom_cycling = self.data.romtype == pfadef.ROMType.ACTIVE
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

        # Rest position line (AROM cycling, incl. HOC). Best-of-3 boundary is
        # shown with romLine1/romLine2/romFill; no ghost or extension visuals.
        if self.data.romtype == pfadef.ROMType.ACTIVE:
            self.ui.restZoneFill = QGraphicsRectItem()
            self.ui.restZoneFill.setBrush(QColor(0, 255, 255, 40))
            self.ui.restZoneFill.setPen(pg.mkPen(None))
            _pgobj.addItem(self.ui.restZoneFill)
            self.ui.restPosLine = pg.PlotDataItem(
                [], [],
                pen=pg.mkPen(color="#00FFFF", width=3),
            )
            _pgobj.addItem(self.ui.restPosLine)
            # Completed-cycle dotted lines — left extremes orange, right blue.
            # One pair per possible cycle; drawn as a cycle completes.
            # Per-cycle AROM readout in the top-right corner.
            self.ui.cycleListText = pg.TextItem(
                text="", color="#FFFFFF", anchor=(1, 0)
            )
            self.ui.cycleListText.setPos(_range[1], 19)
            self.ui.cycleListText.setFont(QtGui.QFont("Cascadia Mono Light", 11))
            self.ui.cycleListText.setZValue(8)
            _pgobj.addItem(self.ui.cycleListText)
            self.ui.cycleLeftLines = []
            self.ui.cycleRightLines = []
            for _ in range(AROM.NO_OF_CYCLES):
                _ll = pg.PlotDataItem(
                    [], [],
                    pen=pg.mkPen(color="#FF8800", width=1,
                                 style=QtCore.Qt.PenStyle.DotLine),
                )
                _rl = pg.PlotDataItem(
                    [], [],
                    pen=pg.mkPen(color="#0088FF", width=1,
                                 style=QtCore.Qt.PenStyle.DotLine),
                )
                _ll.setZValue(4)
                _rl.setZValue(4)
                _pgobj.addItem(_ll)
                _pgobj.addItem(_rl)
                self.ui.cycleLeftLines.append(_ll)
                self.ui.cycleRightLines.append(_rl)
            # Direction indicator — shown once at first trial WAIT_TO_MOVE
            _dirtext = (
                "Open hand first"
                if self.data.mechanism == "HOC"
                else "◄ Move LEFT first"
            )
            self.ui.dirIndicator = pg.TextItem(
                text=_dirtext, color="#FFFF00", anchor=(0.5, 0.5)
            )
            self.ui.dirIndicator.setPos((_range[0] + _range[1]) / 2.0, 0)
            self.ui.dirIndicator.setFont(QtGui.QFont("Cascadia Mono Light", 20))
            self.ui.dirIndicator.setVisible(False)
            _pgobj.addItem(self.ui.dirIndicator)
            # Unused (removed ghost/extension visuals)
            self.ui.ghostLeftLine = None
            self.ui.ghostRightLine = None
            self.ui.extFillLeft = None
            self.ui.extFillRight = None
            # Z-order: fill → zone → boundary lines → cursor → text
            self.ui.romFill.setZValue(1)
            self.ui.restZoneFill.setZValue(3)
            self.ui.romLine1.setZValue(5)
            self.ui.romLine2.setZValue(5)
            self.ui.restPosLine.setZValue(6)
            self.ui.currPosLine1.setZValue(7)
            self.ui.currPosLine2.setZValue(7)
            self.ui.dirIndicator.setZValue(8)
        else:
            self.ui.ghostLeftLine = None
            self.ui.ghostRightLine = None
            self.ui.extFillLeft = None
            self.ui.extFillRight = None
            self.ui.dirIndicator = None
            self.ui.cycleListText = None
            self.ui.cycleLeftLines = []
            self.ui.cycleRightLines = []
            # Centred PROM shows a persistent resting (centre) line + band;
            # plain PROM has neither.
            if self._is_prom_centered:
                self.ui.restZoneFill = QGraphicsRectItem()
                self.ui.restZoneFill.setBrush(QColor(0, 255, 255, 40))
                self.ui.restZoneFill.setPen(pg.mkPen(None))
                _pgobj.addItem(self.ui.restZoneFill)
                self.ui.restPosLine = pg.PlotDataItem(
                    [], [], pen=pg.mkPen(color="#00FFFF", width=3),
                )
                _pgobj.addItem(self.ui.restPosLine)
                self.ui.romFill.setZValue(1)
                self.ui.restZoneFill.setZValue(3)
                self.ui.romLine1.setZValue(5)
                self.ui.romLine2.setZValue(5)
                self.ui.restPosLine.setZValue(6)
                self.ui.currPosLine1.setZValue(7)
                self.ui.currPosLine2.setZValue(7)
            else:
                self.ui.restZoneFill = None
                self.ui.restPosLine = None

        # Angle display sign for the limb.
        self._dispsign = 1.0

        # AROM reference lines (green dotted), shown when an AROM range exists.
        # Both boundaries map through _xpos so HOC (corner-anchored, incl.
        # open-only PROM) and non-HOC share one path. For HOC PROM this puts the
        # AROM-open line where the therapist should open a little past.
        if self.data.arom is not None:
            self.ui.aromPosLine1 = pg.PlotDataItem(
                [self._xpos(self.data.arom[0])] * 2,
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                pen=pg.mkPen(
                    color="#1EFF00", width=1, style=QtCore.Qt.PenStyle.DotLine
                ),
            )
            self.ui.aromPosLine2 = pg.PlotDataItem(
                [self._xpos(self.data.arom[1])] * 2,
                [AROM.CURSOR_LOWER_LIMIT, AROM.CURSOR_UPPER_LIMIT],
                pen=pg.mkPen(
                    color="#1EFF00", width=1, style=QtCore.Qt.PenStyle.DotLine
                ),
            )
            _pgobj.addItem(self.ui.aromPosLine1)
            _pgobj.addItem(self.ui.aromPosLine2)

        # Instruction text — centred on the axis (HOC axis is not symmetric
        # about 0, so x=0 would sit at the left edge).
        self.ui.subjInst = pg.TextItem(text="", color="w", anchor=(0.5, 0.5))
        self.ui.subjInst.setPos((_range[0] + _range[1]) / 2.0, 15)
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
        # Track the per-trial countdown window (AROM only).
        self._update_trial_timer_state()
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

    #
    # Per-trial time limit
    #
    def _update_trial_timer_state(self):
        """Arm the countdown when a trial begins (leaves REST) and disarm it
        when the trial ends (returns to REST / DONE)."""
        if not self._is_arom:
            return
        # The per-trial clock covers only the cycling phase. Once the 5 cycles
        # are done (WAIT_FOR_REST), the rest-hold is untimed and cannot
        # time-fail — completing 5 cycles within the limit is the sole pass
        # criterion.
        _in_trial = self._smachine.state not in (
            States.REST,
            States.DONE,
            States.WAIT_FOR_REST,
        )
        if _in_trial and not self._trial_active:
            self._trial_active = True
            self._trial_secs_left = AROM.TRIAL_TIME_LIMIT
        elif not _in_trial and self._trial_active:
            self._trial_active = False

    def _trial_timer_tick(self):
        """Tick once per second; count down only while a trial is active."""
        if not self._trial_active:
            self.ui.lblCountdown.setText("")
            return
        self._trial_secs_left -= 1
        self.ui.lblCountdown.setText(f"{int(self._trial_secs_left)}s")
        self.ui.lblCountdown.setStyleSheet(
            "color: rgb(200, 0, 0);"
            if self._trial_secs_left <= 10
            else "color: rgb(0, 170, 0);"
        )
        if self._trial_secs_left <= 0:
            self._handle_trial_timeout()

    def _handle_trial_timeout(self):
        """Trial time limit hit. The assessor chooses to redo the trial (e.g. a
        device/setup problem) or move on. Moving on logs the trial as failed and
        advances; MAX_FAILED_TRIALS failures terminate AROM (disabling discrete
        reaching for this mechanism). Demo trials just restart.

        Device callbacks are detached while the modal is open so streaming data
        cannot finish or restart the trial underneath the dialog."""
        self._trial_active = False
        self.ui.lblCountdown.setText("")
        self._detach_pluto_callbacks()
        try:
            # Demo / trial-run: don't penalise, just restart the demo trial.
            if self.data.demomode:
                self._smachine.reset_statemachine()
                self.update_ui()
                QtWidgets.QMessageBox.warning(
                    self,
                    "Time up",
                    "Demo trial time limit reached. Restarting demo.",
                )
                return
            # Real trial — let the assessor redo it or move on.
            box = QtWidgets.QMessageBox(self)
            box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            box.setWindowTitle("Trial not completed")
            box.setText(
                "Trial not completed within the time limit.\n"
                "Redo this trial, or move on to the next one?"
            )
            _redo = box.addButton(
                "Redo Trial", QtWidgets.QMessageBox.ButtonRole.ActionRole
            )
            _next = box.addButton(
                "Next Trial", QtWidgets.QMessageBox.ButtonRole.AcceptRole
            )
            box.setDefaultButton(_next)
            box.exec()
            if box.clickedButton() is _redo:
                # Repeat the same trial; nothing logged, no failure counted.
                self._smachine.redo_current_trial()
                self.update_ui()
                return
            # Move on — log the trial as failed and advance.
            self.data.write_failed_trial()
            self._failed_trials += 1
            self._smachine.fail_current_trial()
            self.update_ui()
        finally:
            self._attach_pluto_callbacks()
        # Too many failures — terminate AROM (skip path disables DISC).
        if self._failed_trials >= AROM.MAX_FAILED_TRIALS:
            self._arom_skipped = True
            self.close()

    def closeEvent(self, event):
        # Stop the per-trial countdown timer.
        if self._is_arom and hasattr(self, "_trialtimer"):
            self._trialtimer.stop()
        # AROM terminated (too many failed trials) — bypass normal dialogs.
        if self._arom_skipped:
            data = {
                "romval": self.data.rom,
                "done": False,
                "status": pfadef.AssessStatus.SKIPPED.value,
                "taskcomment": (
                    f"Patient unable to perform {self._failed_trials} trials "
                    f"within {int(AROM.TRIAL_TIME_LIMIT)}s; AROM terminated, "
                    f"discrete reaching disabled."
                ),
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
    plutodev = QtPluto("COM5")
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

"""
Module for handling the operation of the PLUTO calibration window.

Author: Sivakumar Balasubramanian
Date: 02 August 2024
Email: siva82kb@gmail.com
"""

import sys
import numpy as np
from datetime import datetime as dt

from qtpluto import QtPluto

from PySide6 import (
    QtCore,
    QtWidgets,
)
from PySide6.QtCore import QTimer
from enum import Enum

import plutodefs as pdef
from plutodataviewwindow import PlutoDataViewWindow
from uipy.ui_plutocalib import Ui_CalibrationWindow

# Some timing constants
CALIB_DUMMY_TIME = 0.25  # Time to wait for dummy calibration
HIT_LIMIT_TIME = 1.50  # Time to wait to hit the limit
CALIB_TIME = 1.00  # Calibrate

# Limit hitting torques
LIMIT_HIT_TORQUE = 0.08  # Torque to hit the limit
LIMIT_HIT_TORQUE_HOC = 0.20  # Torque to hit the limit

# Status pill: (text, foreground, background) per phase of the calibration.
CALIB_STATUS_STYLES = {
    "idle": ("Not started", "#5f6368", "#eceff1", "#d6dbe0"),
    "busy": ("Calibrating…", "#1d4ed8", "#e8efff", "#c7d7fb"),
    "done": ("Calibration done", "#0a7d00", "#e7f5e7", "#bfe0bf"),
    "error": ("Error", "#c62828", "#fdeaea", "#f3c5c5"),
}

CALIB_CARD_QSS = """
QWidget#calibCard {
    background-color: #ffffff;
    border: 1px solid #e3e7ec;
    border-radius: 14px;
}
QWidget#calibCard QLabel {
    background: transparent;
    font-family: "Segoe UI", "Bahnschrift Light";
}
QLabel#calibHeading {
    font-size: 22pt;
    font-weight: 600;
    color: #1f2937;
}
QLabel#calibFieldName {
    font-size: 13pt;
    color: #6b7280;
}
QLabel#calibReading {
    font-size: 26pt;
    font-weight: 600;
    color: #1f2937;
}
QLabel#calibStep {
    font-size: 15pt;
    color: #2563eb;
}
"""


class PlutoCalibStates(Enum):
    # WAIT_FOR_ZERO_SET = 0
    # WAIT_FOR_ROM_SET = 1
    # WAIT_FOR_CLOSE = 2
    # CALIB_DONE = 3
    # CALIB_ERROR = 4
    WAIT_FOR_START = 0
    DUMMY_CALIB_START = 1
    DUMMY_CALIB_END = 2
    HIT_CCWISE_LIMIT = 4
    SET_CALIB_START = 5
    HIT_CWISE_LIMIT = 6
    CHECK_CALIB_ANGLE = 7
    SET_CALIB_END = 8
    CALIB_DONE = 9
    CALIB_ERROR = 10
    EXIT = 11


class PlutoCalibrationStateMachine:
    def __init__(self, plutodev: QtPluto, mech: str = "NONE"):
        self._state = PlutoCalibStates.WAIT_FOR_START
        self._pluto = plutodev
        self._stateactions = {
            PlutoCalibStates.WAIT_FOR_START: self._calib_start,
            PlutoCalibStates.DUMMY_CALIB_START: self._dummy_calib_start,
            PlutoCalibStates.DUMMY_CALIB_END: self._dummy_calib_end,
            PlutoCalibStates.HIT_CCWISE_LIMIT: self._hit_ccwise_limit,
            PlutoCalibStates.SET_CALIB_START: self._set_calib_start,
            PlutoCalibStates.HIT_CWISE_LIMIT: self._hit_cwise_limit,
            PlutoCalibStates.CHECK_CALIB_ANGLE: self._check_calib_angle,
            PlutoCalibStates.SET_CALIB_END: self._calib_end,
            PlutoCalibStates.CALIB_ERROR: self._calib_error,
            PlutoCalibStates.CALIB_DONE: self._calib_done,
            PlutoCalibStates.EXIT: self._exit,
        }
        self._mech = mech
        self._state_t0 = 0
        # Set control mode to TORQUE
        self._pluto.set_control_type("TORQUE")

    @property
    def state(self):
        return self._state

    def run_statemachine(self, event):
        """Execute the state machine depending on the given even that has occured."""
        print(
            f"Calib SM: State={self._state}, Event={event}, Time={self._pluto.currt - self._state_t0:0.2f}s"
        )
        self._stateactions[self._state](event)

    def _calib_start(self, event):
        # Check if the button release event has happened.
        if event == pdef.PlutoEvents.RELEASED:
            self._pluto.calibrate_start(self._mech)
            self._state = PlutoCalibStates.DUMMY_CALIB_START
            self._state_t0 = self._pluto.currt
            return

    def _dummy_calib_start(self, event):
        # Set a dummy calibration to start with.
        if (self._pluto.currt - self._state_t0) > CALIB_DUMMY_TIME:
            self._pluto.calibrate_end(self._mech)
            self._state = PlutoCalibStates.DUMMY_CALIB_END
            self._state_t0 = self._pluto.currt
        return

    def _dummy_calib_end(self, event):
        # Wait for some time after dummy calib end.
        if (self._pluto.currt - self._state_t0) > CALIB_DUMMY_TIME:
            # Move to torque control mode
            self._pluto.set_control_type("TORQUE")
            self._state = PlutoCalibStates.HIT_CCWISE_LIMIT
            self._state_t0 = self._pluto.currt
        return

    def _hit_ccwise_limit(self, event):
        # Set a torque to move to CCWISE direction
        if (self._pluto.currt - self._state_t0) > CALIB_DUMMY_TIME:
            self._pluto.set_control_target(
                LIMIT_HIT_TORQUE_HOC if self._mech == "HOC" else -LIMIT_HIT_TORQUE
            )
            self._state_t0 = self._pluto.currt
            self._state = PlutoCalibStates.SET_CALIB_START
        return

    def _set_calib_start(self, event):
        # Set a torque to move to CCWISE direction
        if (self._pluto.currt - self._state_t0) > HIT_LIMIT_TIME:
            self._pluto.calibrate_start(self._mech)
            self._state_t0 = self._pluto.currt
            self._state = PlutoCalibStates.HIT_CWISE_LIMIT
        return

    def _hit_cwise_limit(self, event):
        # Set a torque to move to CCWISE direction
        if (self._pluto.currt - self._state_t0) > CALIB_DUMMY_TIME:
            self._pluto.set_control_target(
                -LIMIT_HIT_TORQUE_HOC if self._mech == "HOC" else LIMIT_HIT_TORQUE
            )
            self._state_t0 = self._pluto.currt
            self._state = PlutoCalibStates.CHECK_CALIB_ANGLE
        return

    def _check_calib_angle(self, event):
        if (self._pluto.currt - self._state_t0) > HIT_LIMIT_TIME:
            _angval = self._pluto.angle + pdef.PlutoAngleOffset[self._mech]
            if (abs(_angval) < (0.9 * pdef.PlutoAngleRanges[self._mech])) or (
                abs(_angval) > (1.1 * pdef.PlutoAngleRanges[self._mech])
            ):
                # Calibration error
                self._state = PlutoCalibStates.CALIB_ERROR
            else:
                self._pluto.calibrate_end(self._mech)
                self._state_t0 = self._pluto.currt
                self._state = PlutoCalibStates.SET_CALIB_END
        return

    def _calib_end(self, event):
        # Set a torque to move to CCWISE direction
        if (self._pluto.currt - self._state_t0) > CALIB_TIME:
            self._pluto.set_control_type("NONE")
            self._state = PlutoCalibStates.CALIB_DONE
            return

    def _calib_error(self, event):
        self._pluto.calibrate_start("NOMECH")
        self._pluto.calibrate_end("NOMECH")
        if event == pdef.PlutoEvents.RELEASED:
            # Calibration all done.
            self._state = PlutoCalibStates.EXIT
        pass

    def _calib_done(self, event):
        if event == pdef.PlutoEvents.RELEASED:
            self._state = PlutoCalibStates.EXIT

    def _exit(self, event):
        """Handle events in EXIT state - calibration is complete, ignore further events."""
        pass


class PlutoCalibrationWindow(QtWidgets.QMainWindow):
    """
    Class for handling the operation of the PLUTO calibration window.
    """

    def __init__(
        self,
        parent=None,
        plutodev: QtPluto = None,
        limb=None,
        mechanism: str = None,
        modal=False,
        dataviewer=False,
        onclosecb=None,
        heartbeat=False,
        embedded=False,
    ):
        """
        Constructor for the PlutoCalibrationWindow class.
        """
        super(PlutoCalibrationWindow, self).__init__(parent)
        self.ui = Ui_CalibrationWindow()
        self.ui.setupUi(self)

        # Fix UI accessibility - remove fixed size constraints
        self.setMinimumSize(451, 90)
        self.setMaximumSize(16777215, 16777215)
        self.resize(500, 150)

        # Embedded mode: this window is used as a page inside the guided GUI's
        # stacked widget, so it must not become a top-level modal.
        self._embedded = embedded
        if embedded:
            # The .ui pins its content to a 431x73 box at (10, 10); on a
            # maximised page that leaves the operator reading 9pt text in the
            # top-left corner of a mostly empty screen.
            self.setMinimumSize(0, 0)
            self._build_embedded_layout()

        if modal and not embedded:
            self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        # PLUTO device
        self._pluto = plutodev
        self._limb = limb if limb else "NOLIMB"
        self._mechanism = mechanism

        # Heartbeat timer
        self._heartbeat = heartbeat
        if self._heartbeat:
            self.heartbeattimer = QTimer()
            self.heartbeattimer.timeout.connect(lambda: self.pluto.send_heartbeat())
            self.heartbeattimer.start(500)

        # Set to NOMECH to start with
        self.pluto.send_heartbeat()
        self._pluto.set_limb(self._limb.upper())
        self._pluto.calibrate_start("NOMECH")
        # Pause for 0.5sec
        QTimer.singleShot(500, lambda: None)

        # Initialize the state machine.
        self._smachine = PlutoCalibrationStateMachine(self._pluto, mech=self._mechanism)

        # Attach callbacks
        self._attach_pluto_callbacks()

        # Update UI.
        self.update_ui()
        # Set label for position display.
        if self._mechanism == "HOC":
            self.ui.lblPositionTitle.setText("Hand Aperture:")
        else:
            self.ui.lblPositionTitle.setText("Joint Position:")
        self.ui.lblInstruction.setText(
            f"{self._mechanism} calibration · {self._limb} limb"
            if self._embedded
            else f"Calibration for {self._mechanism} mechanism for {self._limb} limb."
        )

        # Open the PLUTO data viewer window for sanity
        if dataviewer:
            # Open the device data viewer by default.
            self._open_devdata_viewer()

        # Set the callback when the window is closed.
        self.on_close_callback = onclosecb

    #
    # Embedded layout
    #
    def _build_embedded_layout(self):
        """Re-home the .ui's labels into a centred card.

        The labels themselves are kept — update_ui() writes to them by name —
        so only their arrangement and type scale change here.
        """
        _ui = self.ui
        _card = QtWidgets.QWidget()
        _card.setObjectName("calibCard")
        # A plain QWidget ignores stylesheet backgrounds/borders without this.
        _card.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        _card.setStyleSheet(CALIB_CARD_QSS)
        _card.setMinimumWidth(520)
        _card.setMaximumWidth(680)
        _card.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )
        _lay = QtWidgets.QVBoxLayout(_card)
        _lay.setContentsMargins(36, 30, 36, 30)
        _lay.setSpacing(18)

        # Heading: which mechanism and limb are being calibrated.
        _ui.lblInstruction.setObjectName("calibHeading")
        _ui.lblInstruction.setStyleSheet("")   # drop the .ui's 12pt font rule
        _ui.lblInstruction.setWordWrap(True)
        _ui.lblInstruction.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _lay.addWidget(_ui.lblInstruction)

        _sep = QtWidgets.QFrame()
        _sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        _sep.setStyleSheet("color: #edf0f3;")
        _lay.addWidget(_sep)

        # Status pill on its own line — the one thing the operator glances at.
        _ui.lblInstruction_2.setObjectName("calibFieldName")
        _ui.lblInstruction_2.setStyleSheet("")
        _ui.lblCalibStatus.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _statusrow = QtWidgets.QHBoxLayout()
        _statusrow.setSpacing(12)
        _statusrow.addStretch(1)
        _statusrow.addWidget(_ui.lblInstruction_2)
        _statusrow.addWidget(_ui.lblCalibStatus)
        _statusrow.addStretch(1)
        _lay.addLayout(_statusrow)

        # Live reading.
        _ui.lblPositionTitle.setObjectName("calibFieldName")
        _ui.lblPositionTitle.setStyleSheet("")
        _ui.lblPositionDisplay.setObjectName("calibReading")
        _ui.lblPositionDisplay.setStyleSheet("")
        _ui.lblPositionTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _ui.lblPositionDisplay.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _lay.addWidget(_ui.lblPositionTitle)
        _lay.addWidget(_ui.lblPositionDisplay)

        # What the device is doing right now / what to do next.
        _ui.lblInstruction2.setObjectName("calibStep")
        _ui.lblInstruction2.setStyleSheet("")
        _ui.lblInstruction2.setWordWrap(True)
        _ui.lblInstruction2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _lay.addWidget(_ui.lblInstruction2)

        _page = QtWidgets.QWidget()
        _col = QtWidgets.QVBoxLayout(_page)
        _col.setContentsMargins(24, 16, 24, 24)
        _col.addStretch(1)
        _row = QtWidgets.QHBoxLayout()
        _row.addStretch(1)
        _row.addWidget(_card)
        _row.addStretch(1)
        _col.addLayout(_row)
        _col.addStretch(2)
        # Replaces (and destroys) the .ui's fixed-geometry central widget; the
        # labels above already live on the card and so survive it.
        self.setCentralWidget(_page)

    def _status_phase(self):
        if self._smachine.state == PlutoCalibStates.WAIT_FOR_START:
            return "idle"
        if self._smachine.state == PlutoCalibStates.CALIB_DONE:
            return "done"
        if self._smachine.state == PlutoCalibStates.CALIB_ERROR:
            return "error"
        return "busy"

    def _update_status_pill(self):
        """Colour the status label by phase. The state machine's own wording is
        replaced with one plain-language line per phase."""
        _text, _fg, _bg, _border = CALIB_STATUS_STYLES[self._status_phase()]
        self.ui.lblCalibStatus.setText(_text)
        self.ui.lblCalibStatus.setStyleSheet(
            f"color: {_fg}; background-color: {_bg};"
            f" border: 1px solid {_border}; border-radius: 13px;"
            " padding: 4px 16px; font-size: 14pt; font-weight: 600;"
        )

    @property
    def pluto(self):
        return self._pluto

    @property
    def mechanism(self):
        return self._mechanism

    @property
    def statemachine(self):
        return self._smachine

    #
    # Update UI
    #
    def update_ui(self):
        # Update based on the current state of the Calib statemachine
        if self._smachine.state == PlutoCalibStates.WAIT_FOR_START:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText("Press the PLUTO button start calibration.")
        elif self._smachine.state == PlutoCalibStates.DUMMY_CALIB_START:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText("Dummy Calibration Started.")
        elif self._smachine.state == PlutoCalibStates.DUMMY_CALIB_END:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText(
                f"Dummy Calibration Done [Mechanism = {pdef.get_name(pdef.Mechanisms, self.pluto.mechanism)}]."
            )
        elif self._smachine.state == PlutoCalibStates.HIT_CCWISE_LIMIT:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText(
                f"Going to CCW Limit [{self._pluto.angle:4.2f}]."
            )
        elif self._smachine.state == PlutoCalibStates.SET_CALIB_START:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText(
                f"Setting Calibration Start [{self._pluto.angle:4.2f}]."
            )
        elif self._smachine.state == PlutoCalibStates.HIT_CWISE_LIMIT:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText(
                f"Going to CW Limit [{self._pluto.angle:4.2f}]."
            )
        elif self._smachine.state == PlutoCalibStates.CHECK_CALIB_ANGLE:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText(
                f"Checking Angle Range [{self._pluto.angle:4.2f}]."
            )
        elif self._smachine.state == PlutoCalibStates.CHECK_CALIB_ANGLE:
            self.ui.lblCalibStatus.setText("Not done.")
            self.ui.lblPositionDisplay.setText("- NA- ")
            self.ui.lblInstruction2.setText(
                f"Checking Angle Range [{self._pluto.angle:4.2f}]."
            )
        elif self._smachine.state == PlutoCalibStates.CALIB_DONE:
            self.ui.lblCalibStatus.setText("Calibration done.")
            self.ui.lblPositionDisplay.setText(
                f"{self.pluto.hocdisp:5.2f}cm"
                if self.mechanism == "HOC"
                else f"{self.pluto.angle:5.2f}deg"
            )
            self.ui.lblInstruction2.setText(f"Press PLUTO button to exit.")
        elif self._smachine.state == PlutoCalibStates.CALIB_ERROR:
            self.ui.lblCalibStatus.setText("Error!")
            self.ui.lblInstruction2.setText("Press the PLUTO button to close window.")
        elif self._smachine.state == PlutoCalibStates.EXIT:
            try:
                self._devdatawnd.close()
            except:
                pass
            self.close()
            return
        # The embedded card shows the phase as a coloured pill instead of the
        # cramped "Not done." text the small window uses.
        if self._embedded:
            self._update_status_pill()

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
        self._smachine.run_statemachine(pdef.PlutoEvents.NEWDATA)
        self.update_ui()

    def _callback_pluto_btn_released(self):
        # Run the statemachine
        self._smachine.run_statemachine(pdef.PlutoEvents.RELEASED)
        self.update_ui()

    #
    # Close event
    #
    def closeEvent(self, event):
        # Run the callback
        if self.on_close_callback:
            self.on_close_callback(
                data={
                    "done": self.pluto.calibration == pdef.CalibrationStatus["YESCALIB"]
                }
            )
        # Disconnect the PLUTO callbacks.
        self._detach_pluto_callbacks()
        return super().closeEvent(event)


if __name__ == "__main__":
    import qtjedi

    app = QtWidgets.QApplication(sys.argv)
    plutodev = QtPluto("COM5")
    pcalib = PlutoCalibrationWindow(
        plutodev=plutodev,
        limb="LEFT",
        mechanism="FPS",
        dataviewer=True,
        heartbeat=True,
        onclosecb=lambda data: print(dt.now()),
    )
    pcalib.show()
    sys.exit(app.exec())

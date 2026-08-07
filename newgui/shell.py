"""The single window of the guided PLUTO assessment GUI.

One QMainWindow, one QStackedWidget. The PLUTO hardware button advances the
flow; the mouse is used only for setup, Accept and Redo."""

import pathlib
import time

from PySide6 import QtCore, QtGui, QtWidgets

import plutofullassessdef as pfadef
from async_workers import SessionSetupWorker
from myqt import load_mech_pixmap
from plutofullassesssdata import PlutoAssessmentData
from qtpluto import QtPluto
from s3sync import S3SyncWorker, load_s3_config

from newgui import errors
from newgui.pages import build_page
from newgui.sequencer import (
    CALIB,
    Sequencer,
    Step,
    disc_skip_reason,
    mechanisms_for_mode,
)
from newgui.setup import EmbeddedSetupPage

# WURD has no artwork of its own; it reuses the wrist flexion/extension image,
# matching the old GUI.
MECH_IMAGES = {
    "FPS": "fps.png",
    "WFE": "wfe.png",
    "WURD": "wfe.png",
    "HOC": "hoc.png",
}

TASK_INSTRUCTIONS = {
    CALIB: "Fit the {mech} mechanism, then press the PLUTO button to calibrate.",
    "AROM": "Active range of motion. Press the PLUTO button to start.",
    "PROM": "Passive range of motion. Press the PLUTO button to start.",
    "APROM": "Assisted passive range of motion. Press the PLUTO button to start.",
    "DISC": "Discrete reaching. Press the PLUTO button to start.",
}

STEP_LABELS = dict(pfadef.TASK_LABELS)
STEP_LABELS[CALIB] = "Calibration"

# Post-trial review panel. Accept is the affirmative action (green), Redo the
# neutral one — the pair must not read as "primary vs cancel", since redoing a
# bad trial is just as normal an outcome as keeping a good one.
REVIEW_BOX_QSS = """
QWidget#reviewBox {
    background-color: #ffffff;
    border: 1px solid #e3e7ec;
    border-radius: 14px;
}
QLabel#reviewPrompt {
    font-size: 13pt;
    font-weight: 600;
    color: #3c4043;
    background: transparent;
}
QPushButton#btnAccept, QPushButton#btnRedo {
    font-size: 13pt;
    font-weight: 600;
    border-radius: 8px;
}
QPushButton#btnAccept {
    background-color: #0a7d00;
    color: #ffffff;
    border: 1px solid #0a6b00;
}
QPushButton#btnAccept:hover   { background-color: #0a6b00; }
QPushButton#btnAccept:pressed { background-color: #085a00; }
QPushButton#btnRedo {
    background-color: #ffffff;
    color: #b45309;
    border: 1px solid #e0b070;
}
QPushButton#btnRedo:hover   { background-color: #fff7ec; border-color: #d09a4e; }
QPushButton#btnRedo:pressed { background-color: #fdeed7; }
"""


class ReadyPage(QtWidgets.QWidget):
    """Between-steps screen: what is coming and how to start it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        _lay = QtWidgets.QVBoxLayout(self)
        _lay.setContentsMargins(40, 30, 40, 30)
        _lay.setSpacing(18)
        _lay.addStretch(1)

        self.lblImage = QtWidgets.QLabel()
        self.lblImage.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _lay.addWidget(self.lblImage)

        self.lblWhat = QtWidgets.QLabel()
        self.lblWhat.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblWhat.setStyleSheet("font-size: 22pt; font-weight: 600;")
        _lay.addWidget(self.lblWhat)

        self.lblHow = QtWidgets.QLabel()
        self.lblHow.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblHow.setWordWrap(True)
        self.lblHow.setStyleSheet("font-size: 14pt; color: #2563eb;")
        _lay.addWidget(self.lblHow)
        _lay.addStretch(1)

    def show_step(self, step: Step, resumed: bool = False):
        _label = STEP_LABELS.get(step.task, step.task)
        _mechlabel = pfadef.MECH_LABELS.get(step.mech, step.mech)
        self.lblWhat.setText(
            f"{_mechlabel} — {_label}" + ("  (resumed)" if resumed else "")
        )
        self.lblHow.setText(TASK_INSTRUCTIONS[step.task].format(mech=step.mech))
        _img = pathlib.Path(__file__).resolve().parent.parent / "assets" / MECH_IMAGES[step.mech]
        if step.is_calib and _img.exists():
            _pix = load_mech_pixmap(_img)
            self.lblImage.setPixmap(
                _pix.scaledToHeight(320, QtCore.Qt.TransformationMode.SmoothTransformation)
            )
            self.lblImage.setVisible(True)
        else:
            self.lblImage.setVisible(False)


class DonePage(QtWidgets.QWidget):
    """End of session."""

    def __init__(self, parent=None):
        super().__init__(parent)
        _lay = QtWidgets.QVBoxLayout(self)
        _lay.addStretch(1)
        self.lblTitle = QtWidgets.QLabel("Session complete")
        self.lblTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblTitle.setStyleSheet("font-size: 24pt; font-weight: 600;")
        _lay.addWidget(self.lblTitle)
        self.lblDetail = QtWidgets.QLabel("")
        self.lblDetail.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblDetail.setStyleSheet("font-size: 15pt;")
        _lay.addWidget(self.lblDetail)
        # Per-mechanism screening scores. The verdict above is a single word; on
        # its own it does not say which mechanism carried it, which is what the
        # operator needs when a borderline subject has to be explained later.
        self.lblScores = QtWidgets.QLabel("")
        self.lblScores.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblScores.setTextFormat(QtCore.Qt.TextFormat.RichText)
        # Without this a rich-text label takes the full page width and the table
        # columns drift apart; Maximum makes it hug the table so the centring
        # below actually centres something table-sized.
        self.lblScores.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )
        self.lblScores.setVisible(False)
        _lay.addSpacing(18)
        _lay.addWidget(self.lblScores, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        _lay.addStretch(1)

    def show_screening_scores(self, stats: dict, order):
        """Render the AROM reached per mechanism against its threshold.

        stats comes straight from get_screening_eligibility(); order is the
        mechanism order the session was run in, so the table reads in the order
        the operator saw them."""
        _rows = []
        for _mech in order:
            _s = stats.get(_mech)
            if _s is None:
                continue
            if not _s["done"]:
                _val, _verdict, _color = "—", "not recorded", "#9aa0a6"
            else:
                _val = f"{_s['value']:.1f} {_s['unit']}"
                _verdict = "pass" if _s["pass"] else "below threshold"
                _color = "#0a7d00" if _s["pass"] else "#aa0000"
            _rows.append(
                f"<tr>"
                f"<td style='padding:6px 22px 6px 0;'>"
                f"{pfadef.MECH_LABELS.get(_mech, _mech)}</td>"
                f"<td style='padding:6px 22px 6px 0; text-align:right;"
                f" font-weight:600; color:{_color};'>{_val}</td>"
                f"<td style='padding:6px 22px 6px 0; text-align:right;"
                f" color:#6b7280;'>&ge; {_s['threshold']:g} {_s['unit']}</td>"
                f"<td style='padding:6px 0; color:{_color};'>{_verdict}</td>"
                f"</tr>"
            )
        self.lblScores.setText(
            "<div style='font-size:13pt;'>"
            "<table cellspacing='0' cellpadding='0'>"
            "<tr style='color:#6b7280;'>"
            "<th style='text-align:left; padding:0 22px 8px 0;'>Mechanism</th>"
            "<th style='text-align:right; padding:0 22px 8px 0;'>AROM</th>"
            "<th style='text-align:right; padding:0 22px 8px 0;'>Threshold</th>"
            "<th style='text-align:left; padding:0 0 8px 0;'></th>"
            "</tr>" + "".join(_rows) + "</table></div>"
        )
        self.lblScores.setVisible(bool(_rows))

    def clear_screening_scores(self):
        self.lblScores.setText("")
        self.lblScores.setVisible(False)


class PlutoGuidedAssessor(QtWidgets.QMainWindow):
    """The single window."""

    def __init__(self, port: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PLUTO Guided Assessment")

        # Device.
        self.pluto = QtPluto(port)
        self.pluto.btnreleased.connect(self._callback_btn_released)
        self.pluto.get_version()
        self.pluto.start_sensorstream()

        # Session data and flow.
        self.data = PlutoAssessmentData()
        self.seq: Sequencer | None = None
        self._setup_worker = None
        self._taskpage = None
        self._resumed = False
        self._lastpayload = {}

        self._build_ui()
        self._init_timers()
        self._init_s3sync()

        self.stack.setCurrentWidget(self.pageSetup)
        self._set_footer_hint("Fill in the session details, then press Start.")
        self.showMaximized()

    #
    # UI construction
    #
    def _build_ui(self):
        _central = QtWidgets.QWidget()
        self.setCentralWidget(_central)
        _outer = QtWidgets.QVBoxLayout(_central)
        _outer.setContentsMargins(0, 0, 0, 0)
        _outer.setSpacing(0)

        # Header: where we are.
        _head = QtWidgets.QHBoxLayout()
        _head.setContentsMargins(18, 12, 18, 12)
        self.lblHeader = QtWidgets.QLabel("Session setup")
        self.lblHeader.setStyleSheet("font-size: 16pt; font-weight: 600;")
        self.lblCounter = QtWidgets.QLabel("")
        self.lblCounter.setStyleSheet("font-size: 13pt; color: #6b7280;")
        self.lblS3Sync = QtWidgets.QLabel("")
        _head.addWidget(self.lblHeader)
        _head.addStretch(1)
        _head.addWidget(self.lblCounter)
        _head.addSpacing(20)
        _head.addWidget(self.lblS3Sync)
        _outer.addLayout(_head)

        # Pages.
        self.stack = QtWidgets.QStackedWidget()
        _outer.addWidget(self.stack, 1)

        self.pageSetup = EmbeddedSetupPage(onstartcb=self._on_setup_start)
        self.pageReady = ReadyPage()
        self.pageDone = DonePage()
        for _p in (self.pageSetup, self.pageReady, self.pageDone):
            self.stack.addWidget(_p)

        # Footer: hint line, or the review box with Accept / Redo.
        _foot = QtWidgets.QHBoxLayout()
        _foot.setContentsMargins(18, 10, 18, 14)
        self.lblHint = QtWidgets.QLabel("")
        self.lblHint.setStyleSheet("font-size: 13pt; color: #6b7280;")
        self.reviewBox = self._build_review_box()
        # The hint and the review box are never shown together, so the pair of
        # stretches centres whichever one is visible: the box lands in the
        # middle of the footer, the hint keeps its left margin.
        _foot.addWidget(self.lblHint)
        _foot.addStretch(1)
        _foot.addWidget(self.reviewBox)
        _foot.addStretch(1)
        _outer.addLayout(_foot)
        self._set_footer_hint("")

        self.pbAccept.clicked.connect(self._on_accept)
        self.pbRedo.clicked.connect(self._on_redo)

    def _build_review_box(self):
        """The decision the operator makes after every trial, in one panel:
        a prompt and the two actions, so it reads as a question rather than as
        two loose buttons on a toolbar."""
        _box = QtWidgets.QWidget()
        _box.setObjectName("reviewBox")
        # A plain QWidget ignores stylesheet backgrounds/borders without this.
        _box.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        _box.setStyleSheet(REVIEW_BOX_QSS)
        _lay = QtWidgets.QVBoxLayout(_box)
        _lay.setContentsMargins(28, 14, 28, 18)
        _lay.setSpacing(10)

        self.lblReview = QtWidgets.QLabel("Keep this trial?")
        self.lblReview.setObjectName("reviewPrompt")
        self.lblReview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        _lay.addWidget(self.lblReview)

        self.pbAccept = QtWidgets.QPushButton("Accept")
        self.pbAccept.setObjectName("btnAccept")
        self.pbAccept.setMinimumSize(180, 48)
        self.pbAccept.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.pbRedo = QtWidgets.QPushButton("Redo")
        self.pbRedo.setObjectName("btnRedo")
        self.pbRedo.setMinimumSize(180, 48)
        self.pbRedo.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        _btns = QtWidgets.QHBoxLayout()
        _btns.setSpacing(16)
        _btns.addWidget(self.pbRedo)
        _btns.addWidget(self.pbAccept)
        _lay.addLayout(_btns)

        _shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        _shadow.setBlurRadius(24)
        _shadow.setOffset(0, 4)
        _shadow.setColor(QtGui.QColor(15, 23, 42, 36))
        _box.setGraphicsEffect(_shadow)
        return _box

    def _set_footer_hint(self, text: str):
        self.lblHint.setText(text)
        self.lblHint.setVisible(True)
        self.reviewBox.setVisible(False)

    def _set_footer_review(self):
        self.lblHint.setVisible(False)
        self.reviewBox.setVisible(True)

    #
    # Timers, status bar, sync
    #
    def _init_timers(self):
        self.apptime = 0
        self.statustimer = QtCore.QTimer()
        self.statustimer.timeout.connect(self._callback_status_timer)
        self.statustimer.start(1000)
        self.heartbeattimer = QtCore.QTimer()
        self.heartbeattimer.timeout.connect(lambda: self.pluto.send_heartbeat())
        self.heartbeattimer.start(250)

    def _callback_status_timer(self):
        self.apptime += 1
        _con = self.pluto.is_connected()
        _step = self.seq.current() if self.seq else None
        self.statusBar().showMessage(
            " | ".join((
                f"{self.apptime:5d}s",
                _con if _con != "" else "Disconnected",
                f"FR: {self.pluto.framerate():4.1f}Hz",
                f"{self.data.subjid}",
                f"{_step.mech}/{_step.task}" if _step else "-",
            ))
        )

    def _init_s3sync(self):
        self._last_sync_kick = 0.0
        self._s3sync = S3SyncWorker(
            root=pfadef.homer_data_root(), config=load_s3_config()
        )
        self._s3sync.status.connect(self._on_s3_status)
        self._s3sync.start()

    def _on_s3_status(self, state, pending, message):
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

    def _kick_sync(self):
        _now = time.monotonic()
        if _now - self._last_sync_kick >= 5.0:
            self._last_sync_kick = _now
            self._s3sync.request_sweep()

    #
    # Setup
    #
    def _on_setup_start(self, setup: dict):
        # The setup page stays on screen while the worker runs, so a second
        # Start would launch a second worker and create a stray session folder.
        if self._setup_worker is not None:
            return
        self.data.setup_session(setup)
        self.seq = Sequencer(setup["mode"])
        self.statusBar().showMessage("Creating session folder and protocol...")
        self._set_footer_hint("Creating session folder and protocol...")
        self._setup_worker = SessionSetupWorker(self.data)
        self._setup_worker.finished.connect(self._on_setup_finished)
        self._setup_worker.error.connect(self._on_setup_error)
        self._setup_worker.start()

    def _on_setup_finished(self):
        self._setup_worker = None
        self.pluto.send_heartbeat()
        self.pluto.set_limb(self.data.limb)
        self.setWindowTitle(
            " | ".join((
                "PLUTO Guided Assessment", self.data.subjid, self.data.mode,
                f"Limb: {self.data.limb}",
                "screening" if self.data.is_screening else f"TP: {self.data.timepoint}",
            ))
        )
        # The protocol is the authority on which tasks this session runs — the
        # unaffected limb, for one, gets DISC only — so trim the step list to it
        # before walking anything.
        self.seq.restrict_to(self._protocol_pairs())
        _completed = self._completed_pairs()
        if _completed:
            self.seq.resume_from(_completed)
            self._resumed = True
        self._show_ready()

    def _protocol_pairs(self):
        """Every (mechanism, task) pair the session's protocol CSV contains."""
        _df = self.data.protocol.df
        if _df is None:
            return []
        return list(
            dict.fromkeys(zip(_df["mechanism"].tolist(), _df["task"].tolist()))
        )

    def _completed_pairs(self):
        """(mechanism, task) pairs whose protocol row already has a session —
        completed, skipped or excluded, all of them finished as far as the flow
        is concerned."""
        _df = self.data.protocol.df
        if _df is None:
            return []
        _done = _df[_df["session"].notna()]
        return list(
            dict.fromkeys(zip(_done["mechanism"].tolist(), _done["task"].tolist()))
        )

    def _on_setup_error(self, message: str):
        self._setup_worker = None
        QtWidgets.QMessageBox.critical(
            self, "Error", f"Error during session setup:\n{message}"
        )
        self.stack.setCurrentWidget(self.pageSetup)
        self._set_footer_hint("Fix the session details and press Start again.")

    #
    # Flow
    #
    def _show_ready(self):
        """Park on the ready screen for the current step."""
        _step = self.seq.current()
        if _step is None:
            self._show_done()
            return
        self.pageReady.show_step(_step, resumed=self._resumed)
        self._resumed = False
        self.stack.setCurrentWidget(self.pageReady)
        self._update_header()
        self._set_footer_hint("Press the PLUTO button to continue.")
        self._kick_sync()

    def _show_done(self):
        self.stack.setCurrentWidget(self.pageDone)
        self.lblHeader.setText("Done")
        self.lblCounter.setText("")
        if self.data.is_screening and self.data.detailedsummary is not None:
            _eligible, _stats = self.data.detailedsummary.get_screening_eligibility()
            self.pageDone.lblDetail.setText(
                "ELIGIBLE" if _eligible else "NOT ELIGIBLE"
            )
            self.pageDone.lblDetail.setStyleSheet(
                "font-size: 20pt; font-weight: 600; color: "
                + ("rgb(0,120,0);" if _eligible else "rgb(170,0,0);")
            )
            self.pageDone.show_screening_scores(
                _stats, mechanisms_for_mode(self.data.mode)
            )
        else:
            self.pageDone.lblDetail.setText(
                f"{self.data.subjid} · {self.data.limb}"
            )
            self.pageDone.clear_screening_scores()
        self._set_footer_hint("You can close the window.")
        self._kick_sync()

    def _update_header(self):
        _step = self.seq.current()
        if _step is None:
            return
        _n, _total = self.seq.position()
        self.lblHeader.setText(
            f"{_step.mech} · {STEP_LABELS.get(_step.task, _step.task)}"
        )
        self.lblCounter.setText(f"{_n} / {_total}")

    def _start_current_step(self):
        """Build and show the task widget for the current step."""
        _step = self.seq.current()
        if _step is None:
            self._show_done()
            return
        # A new mechanism: select it in both data stores before anything else.
        if _step.mech != self.data.protocol.mech:
            self.data.protocol.set_mechanism(_step.mech)
            self.data.detailedsummary.set_mechanism(_step.mech)
        _cb = self._on_calib_closed if _step.is_calib else self._on_task_closed
        try:
            if not _step.is_calib:
                # set_task stamps the task time that the raw/summary filenames
                # use, so it must happen before the page is built.
                self.data.protocol.set_task(_step.task)
                self.data.detailedsummary.set_task(_step.task)
            self._taskpage = build_page(_step, self.pluto, self.data, _cb)
        except Exception as _exc:
            # Park on the ready screen rather than leaving a half-built page in
            # the stack; the operator can press the button to try again.
            errors.log_exception(f"Starting {_step.mech}/{_step.task}", _exc)
            self._taskpage = None
            errors.show_error(
                "Could not start this task",
                f"{_step.mech} · {STEP_LABELS.get(_step.task, _step.task)} "
                f"could not be started.\n\n{type(_exc).__name__}: {_exc}",
            )
            self._show_ready()
            return
        self.stack.addWidget(self._taskpage)
        self.stack.setCurrentWidget(self._taskpage)
        self._update_header()
        self._set_footer_hint("")

    def _discard_taskpage(self):
        """Remove and destroy the current task widget.

        Deleting a widget does not send it a closeEvent, so a page dropped from
        here (Redo, or the window closing mid-task) never runs its own CSV
        clean-up. Close the writers explicitly first: the raw writer buffers up
        to a flush interval of samples, and those rows are lost if its handle is
        collected unflushed. close_logging() is idempotent, so pages that
        already closed themselves are unaffected. Calibration has no writers."""
        if self._taskpage is None:
            return
        _data = getattr(self._taskpage, "data", None)
        if hasattr(_data, "close_logging"):
            try:
                _data.close_logging()
            except Exception as _exc:
                errors.log_exception("Closing the task's CSV writers", _exc)
        self.stack.removeWidget(self._taskpage)
        self._taskpage.deleteLater()
        self._taskpage = None

    def _on_calib_closed(self, data=None):
        """Calibration has no review: success advances, failure retries."""
        _done = bool(data and data.get("done"))
        _step = self.seq.current()
        self._discard_taskpage()
        if _done:
            self.data.protocol.set_mechanism_calibrated(_step.mech)
            self.seq.advance()
        self._show_ready()

    def _on_task_closed(self, data=None):
        """A task page finished. Keep its display on screen and swap the footer
        to Accept / Redo. closeEvent() only hides an embedded widget, so it is
        re-shown here to freeze the final display for the operator."""
        self._lastpayload = dict(data or {})
        # The task terminated itself (too many failed AROM trials): no review.
        if self._lastpayload.get("status") == pfadef.AssessStatus.SKIPPED.value:
            self._handle_task_terminated(self._lastpayload)
            return
        if self._taskpage is not None:
            self._taskpage.show()
            self.stack.setCurrentWidget(self._taskpage)
        self._set_footer_review()

    def _on_accept(self):
        _step = self.seq.current()
        if not self._persist(
            status=pfadef.AssessStatus.COMPLETE.value,
            payload=self._lastpayload,
            write_protocol=True,
        ):
            # Nothing was recorded — stay on the review so the operator can
            # retry rather than losing the trial to a write failure.
            return
        self._discard_taskpage()
        self.seq.mark_completed(_step)
        self._after_accept(_step)

    def _on_redo(self):
        """Log the attempt as rejected (details JSON only, so the protocol row
        stays open) and run the same step again."""
        # A failed write is logged and shown by _persist; the retry still runs,
        # since the attempt being redone is the one that would have been
        # recorded as rejected anyway.
        self._persist(
            status=pfadef.AssessStatus.REJECTED.value,
            payload=self._lastpayload,
            write_protocol=False,
        )
        self._discard_taskpage()
        self._start_current_step()

    def _persist(self, status: str, payload: dict, write_protocol: bool) -> bool:
        """Record the finished attempt. Returns False if nothing was written —
        a full disk or a locked CSV must not be swallowed, and must not let the
        flow move on as though the trial had been saved."""
        _protocol = self.data.protocol
        try:
            # Protocol first, details JSON second. The protocol write overwrites
            # one row and is safe to repeat, while the details write appends a
            # new attempt record and is not: with the old order, a protocol write
            # that failed left the operator pressing Accept again and logging the
            # same attempt twice in the JSON.
            if write_protocol:
                _protocol.update(
                    session=self.data.session,
                    rawfile=_protocol.rawfilename,
                    summaryfile=_protocol.summaryfilename,
                    taskcomment="",
                    status=status,
                )
            self.data.detailedsummary.update(
                romval=payload.get("romval"),
                session=self.data.session,
                tasktime=_protocol.tasktime,
                rawfile=_protocol.rawfilename,
                summaryfile=_protocol.summaryfilename,
                taskcomment="",
                status=status,
            )
        except Exception as _exc:
            errors.log_exception(f"Saving {_protocol.mech}/{_protocol.task}", _exc)
            errors.show_error(
                "Could not save this task",
                f"{type(_exc).__name__}: {_exc}\n\n"
                "Nothing was recorded. Close any program holding the CSV files "
                "open and press Accept again.",
            )
            return False
        return True

    def _skip_step(self, task: str, reason: str):
        """Record a task as skipped and step the sequencer past it. skip_task
        also marks dependent tasks EXCLUDED (DISC depends on AROM), matching the
        old GUI."""
        _mech = self.data.protocol.mech
        self.data.protocol.skip_task(task, self.data.session, reason)
        self.data.detailedsummary.skip_task(task, self.data.session, reason)
        self.seq.mark_completed(Step(_mech, task))

    def _after_accept(self, step):
        # After AROM, decide whether discrete reaching is worth running.
        if step.task == "AROM" and "DISC" in self.data.protocol.task_not_completed:
            _reason = disc_skip_reason(
                step.mech, self.data.detailedsummary.get_arom_if_completed()
            )
            if _reason is not None:
                self._skip_step("DISC", _reason)
        self.seq.advance()
        self._show_ready()

    def _handle_task_terminated(self, payload):
        """AROM terminated itself after too many timed-out trials. Log the skip
        (which excludes DISC via the task dependencies) and move on."""
        _step = self.seq.current()
        self._discard_taskpage()
        _reason = payload.get("taskcomment") or "Terminated by trial time limit"
        self._skip_step(_step.task, _reason)
        if _step.task == "AROM":
            self.seq.mark_completed(Step(_step.mech, "DISC"))
        self.seq.advance()
        self._show_ready()

    #
    # Device button
    #
    def _callback_btn_released(self):
        # Navigation only while a task page is not running; task pages attach
        # their own handler and own the button while live.
        if self._taskpage is not None:
            return
        if self.stack.currentWidget() is self.pageReady:
            self._start_current_step()

    def closeEvent(self, event):
        """Shut the background threads down before their objects are destroyed.

        JediComm (inside QtPluto) and S3SyncWorker are QThreads. Destroying a
        running QThread is fatal to Qt — "QThread: Destroyed while thread is
        still running" — so each one is asked to stop and then waited for."""
        errors.log("Closing the guided GUI")
        self.statustimer.stop()
        self.heartbeattimer.stop()
        # Drop the task page first: it holds device callbacks and CSV writers.
        try:
            self._discard_taskpage()
        except Exception as _exc:
            errors.log_exception("Discarding the task page on close", _exc)
        try:
            self.pluto.stop_sensorstream()
            self.pluto.close()
        except Exception as _exc:
            errors.log_exception("Closing the PLUTO connection", _exc)
        try:
            self._s3sync.stop()
            self._s3sync.wait(5000)
        except Exception as _exc:
            errors.log_exception("Stopping the S3 sync worker", _exc)
        return super().closeEvent(event)

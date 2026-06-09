"""Combined Session Setup window: pick Screening or Assessment, choose/create a
subject, and set limb / affected side / dominant hand / time point in one modal.
Replaces SubjectCreator and SubjectSelector.

Built programmatically (no .ui) so the whole window is self-contained.
"""

import os
import sys
import pandas as pd
from datetime import datetime as dt

from PySide6 import QtCore, QtWidgets

import plutofullassessdef as pfadef


class SubjectsListFile:
    """A subjects-list CSV with a mode-specific header."""

    def __init__(self, filename, header):
        self.filename = filename
        self.header = header
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        if not os.path.exists(self.filename):
            self.subjlist = pd.DataFrame(columns=self.header)
            self.subjlist.to_csv(self.filename, index=False)
        else:
            self.subjlist = pd.read_csv(self.filename, dtype=str).fillna("")

    def subject_exists(self, subjid):
        return subjid in self.subjlist["subjid"].values

    def get_subject_info(self, subjid):
        if self.subject_exists(subjid):
            return self.subjlist[self.subjlist["subjid"] == subjid].iloc[0].to_dict()
        return {}

    def add_subject(self, subjinfo: dict):
        if not self.subject_exists(subjinfo["subjid"]):
            self.subjlist = pd.concat(
                [self.subjlist, pd.DataFrame([subjinfo])], ignore_index=True
            )
            self.subjlist.to_csv(self.filename, index=False)


def _list_file(mode):
    if mode == "screening":
        return SubjectsListFile(pfadef.SCREENING_SUBJLIST_FILE,
                                pfadef.SCREENING_SUBJECT_HEADER)
    return SubjectsListFile(pfadef.SUBJLIST_FILE, pfadef.ASSESS_SUBJECT_HEADER)


class SessionSetupWindow(QtWidgets.QMainWindow):
    """One-stop setup. On Start, returns a dict via onclosecb; on Cancel returns {}."""

    SIDES = ["", "Left", "Right"]

    def __init__(self, parent=None, modal=True, onclosecb=None):
        super().__init__(parent)
        self.setWindowTitle("Session Setup")
        self.on_close_callback = onclosecb
        self.result = {}
        if modal:
            self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self._build_ui()
        self._wire()
        self._on_mode_changed()
        self.update_ui()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(20, 18, 20, 16)
        outer.setSpacing(12)

        # Header
        title = QtWidgets.QLabel("Session Setup")
        title.setObjectName("lblTitle")
        subtitle = QtWidgets.QLabel(
            "Choose a mode, create or select a subject, and configure the session."
        )
        subtitle.setObjectName("lblSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(title)
        outer.addWidget(subtitle)

        sep = QtWidgets.QFrame()
        sep.setObjectName("hsep")
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        outer.addWidget(sep)

        # Mode radios
        self.rbScreening = QtWidgets.QRadioButton("Screening")
        self.rbAssessment = QtWidgets.QRadioButton("Assessment")
        self.rbAssessment.setChecked(True)
        self.modeGroup = QtWidgets.QButtonGroup(self)
        self.modeGroup.addButton(self.rbScreening)
        self.modeGroup.addButton(self.rbAssessment)
        self.rbScreening.setMinimumWidth(self.rbScreening.sizeHint().width())
        self.rbAssessment.setMinimumWidth(self.rbAssessment.sizeHint().width())
        _moderow = QtWidgets.QHBoxLayout()
        _moderow.setSpacing(8)
        _moderow.addWidget(QtWidgets.QLabel("Mode:"))
        _moderow.addSpacing(8)
        _moderow.addWidget(self.rbScreening)
        _moderow.addSpacing(28)
        _moderow.addWidget(self.rbAssessment)
        _moderow.addStretch(1)
        outer.addLayout(_moderow)

        # Subject details card
        self.gbDetails = QtWidgets.QGroupBox("Subject details")
        form = QtWidgets.QFormLayout(self.gbDetails)
        form.setLabelAlignment(QtCore.Qt.AlignRight)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        form.setContentsMargins(14, 14, 14, 12)

        # Editable combobox: pick an existing subject from the dropdown OR type
        # a new id. Autocomplete filters as you type.
        self.txtSubjID = QtWidgets.QComboBox()
        self.txtSubjID.setEditable(True)
        self.txtSubjID.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.txtSubjID.lineEdit().setPlaceholderText("Pick existing or type new (e.g. p001)")
        _comp = self.txtSubjID.completer()
        _comp.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        _comp.setFilterMode(QtCore.Qt.MatchContains)
        _comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        form.addRow("Subject ID:", self.txtSubjID)

        self.lblExisting = QtWidgets.QLabel("")
        self.lblExisting.setObjectName("lblHint")
        form.addRow("", self.lblExisting)

        self.cbAff = QtWidgets.QComboBox(); self.cbAff.addItems(self.SIDES)
        self.lblAff = QtWidgets.QLabel("Affected side:")
        form.addRow(self.lblAff, self.cbAff)

        self.cbLimb = QtWidgets.QComboBox(); self.cbLimb.addItems(self.SIDES)
        self.lblLimb = QtWidgets.QLabel("Limb assessed:")
        form.addRow(self.lblLimb, self.cbLimb)

        self.cbDom = QtWidgets.QComboBox(); self.cbDom.addItems(self.SIDES)
        self.lblDom = QtWidgets.QLabel("Dominant hand:")
        form.addRow(self.lblDom, self.cbDom)

        self.cbTP = QtWidgets.QComboBox(); self.cbTP.addItems([""] + list(pfadef.TIMEPOINTS))
        self.lblTP = QtWidgets.QLabel("Time point:")
        form.addRow(self.lblTP, self.cbTP)

        outer.addWidget(self.gbDetails)
        outer.addStretch(1)

        # Buttons
        _btnrow = QtWidgets.QHBoxLayout()
        self.pbStart = QtWidgets.QPushButton("Start")
        self.pbStart.setObjectName("btnPrimary")
        self.pbStart.setMinimumHeight(34)
        self.pbStart.setMinimumWidth(110)
        self.pbCancel = QtWidgets.QPushButton("Cancel")
        self.pbCancel.setMinimumHeight(34)
        _btnrow.addStretch(1)
        _btnrow.addWidget(self.pbCancel)
        _btnrow.addWidget(self.pbStart)
        outer.addLayout(_btnrow)

        self.setMinimumWidth(440)

    def _wire(self):
        self.rbScreening.toggled.connect(self._on_mode_changed)
        # editingFinished: typed an id and left the box. activated: picked from
        # the dropdown. Both re-run the existing-subject lookup.
        self.txtSubjID.lineEdit().editingFinished.connect(self._on_subjid_changed)
        self.txtSubjID.activated.connect(lambda *_: self._on_subjid_changed())
        self.txtSubjID.currentTextChanged.connect(self.update_ui)
        for _cb in (self.cbAff, self.cbLimb, self.cbDom, self.cbTP):
            _cb.currentIndexChanged.connect(self.update_ui)
        self.pbStart.clicked.connect(self._on_start)
        self.pbCancel.clicked.connect(self.close)

    def _reload_subject_list(self):
        """Populate the dropdown with existing subject ids for the current mode,
        preserving whatever the operator has typed so far."""
        _typed = self.txtSubjID.currentText()
        listfile = _list_file(self.mode)
        _ids = sorted(listfile.subjlist["subjid"].astype(str).tolist())
        self.txtSubjID.blockSignals(True)
        self.txtSubjID.clear()
        self.txtSubjID.addItems(_ids)
        self.txtSubjID.setCurrentIndex(-1)
        self.txtSubjID.setEditText(_typed)
        self.txtSubjID.blockSignals(False)

    @property
    def mode(self):
        return "screening" if self.rbScreening.isChecked() else "assessment"

    def _assessment_fields_visible(self, vis):
        for w in (self.lblLimb, self.cbLimb, self.lblDom, self.cbDom,
                  self.lblTP, self.cbTP):
            w.setVisible(vis)

    def _on_mode_changed(self, *_):
        # Screening: only affected side. Assessment: limb, dominant, timepoint too.
        self._assessment_fields_visible(self.mode == "assessment")
        self._reload_subject_list()  # the two modes have separate subject lists
        self._on_subjid_changed()    # re-lookup against the mode's list
        self.update_ui()

    def _on_subjid_changed(self, *_):
        subjid = self.txtSubjID.currentText().strip().lower()
        listfile = _list_file(self.mode)
        if subjid and listfile.subject_exists(subjid):
            info = listfile.get_subject_info(subjid)
            self.lblExisting.setText("Existing subject — details locked.")
            self.cbAff.setCurrentText((info.get("afflimb", "") or "").capitalize())
            self.cbAff.setEnabled(False)
            if self.mode == "assessment":
                self.cbDom.setCurrentText((info.get("domlimb", "") or "").capitalize())
                self.cbDom.setEnabled(False)
        else:
            self.lblExisting.setText("New subject — will be created on Start." if subjid else "")
            self.cbAff.setEnabled(True)
            self.cbDom.setEnabled(True)
        self.update_ui()

    def update_ui(self):
        ok = self.txtSubjID.currentText().strip() != "" and self.cbAff.currentText() != ""
        if self.mode == "assessment":
            ok = ok and self.cbLimb.currentText() != "" \
                and self.cbDom.currentText() != "" and self.cbTP.currentText() != ""
        self.pbStart.setEnabled(ok)

    def _on_start(self):
        subjid = self.txtSubjID.currentText().strip().lower()
        afflimb = self.cbAff.currentText().lower()
        mode = self.mode
        if mode == "assessment":
            limb = self.cbLimb.currentText().lower()
            domlimb = self.cbDom.currentText().lower()
            timepoint = self.cbTP.currentText()
            # Enforce timepoint ordering: previous timepoint must be complete.
            tp_idx = list(pfadef.TIMEPOINTS).index(timepoint)
            if tp_idx > 0:
                prev = pfadef.TIMEPOINTS[tp_idx - 1]
                if not pfadef.is_assessment_timepoint_completed(subjid, limb, prev):
                    QtWidgets.QMessageBox.warning(
                        self, "Timepoint Order Error",
                        f"Cannot select {timepoint}: {prev} is not complete for this limb.",
                    )
                    return
            if pfadef.is_assessment_timepoint_completed(subjid, limb, timepoint):
                QtWidgets.QMessageBox.warning(
                    self, "Already Completed",
                    f"{timepoint} is already complete for {subjid} / {limb}.",
                )
                return
        else:
            limb = afflimb  # screening screens the affected limb
            domlimb = ""
            timepoint = ""

        # Create the subject record if new.
        listfile = _list_file(mode)
        if not listfile.subject_exists(subjid):
            if mode == "screening":
                listfile.add_subject({
                    "subjid": subjid, "afflimb": afflimb,
                    "createdat": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            else:
                listfile.add_subject({
                    "subjid": subjid, "domlimb": domlimb, "afflimb": afflimb,
                    "createdat": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

        self.result = {
            "mode": mode, "subjid": subjid, "limb": limb,
            "afflimb": afflimb, "domlimb": domlimb, "timepoint": timepoint,
        }
        self.close()

    def showEvent(self, event):
        super().showEvent(event)
        # Center on screen the first time the window is shown (geometry is only
        # final once the layout has been applied at show time).
        if not getattr(self, "_centered", False):
            self._center_on_screen()
            self._centered = True

    def _center_on_screen(self):
        self.adjustSize()
        parent = self.parentWidget()
        screen = (parent.screen() if parent is not None else None) \
            or QtWidgets.QApplication.primaryScreen()
        geo = self.frameGeometry()
        geo.moveCenter(screen.availableGeometry().center())
        self.move(geo.topLeft())

    def closeEvent(self, event):
        if self.on_close_callback:
            self.on_close_callback(data=self.result)
        return super().closeEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = SessionSetupWindow(onclosecb=lambda data: print(data))
    w.show()
    sys.exit(app.exec())

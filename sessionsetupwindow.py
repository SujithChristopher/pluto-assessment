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
        form = QtWidgets.QFormLayout(central)

        # Mode radios
        self.rbScreening = QtWidgets.QRadioButton("Screening")
        self.rbAssessment = QtWidgets.QRadioButton("Assessment")
        self.rbAssessment.setChecked(True)
        self.modeGroup = QtWidgets.QButtonGroup(self)
        self.modeGroup.addButton(self.rbScreening)
        self.modeGroup.addButton(self.rbAssessment)
        _moderow = QtWidgets.QHBoxLayout()
        _moderow.addWidget(self.rbScreening)
        _moderow.addWidget(self.rbAssessment)
        form.addRow("Mode:", _moderow)

        self.txtSubjID = QtWidgets.QLineEdit()
        form.addRow("Subject ID:", self.txtSubjID)

        self.lblExisting = QtWidgets.QLabel("")
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

        _btnrow = QtWidgets.QHBoxLayout()
        self.pbStart = QtWidgets.QPushButton("Start")
        self.pbCancel = QtWidgets.QPushButton("Cancel")
        _btnrow.addWidget(self.pbStart); _btnrow.addWidget(self.pbCancel)
        form.addRow(_btnrow)

    def _wire(self):
        self.rbScreening.toggled.connect(self._on_mode_changed)
        self.txtSubjID.editingFinished.connect(self._on_subjid_changed)
        for _cb in (self.cbAff, self.cbLimb, self.cbDom, self.cbTP):
            _cb.currentIndexChanged.connect(self.update_ui)
        self.pbStart.clicked.connect(self._on_start)
        self.pbCancel.clicked.connect(self.close)

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
        self._on_subjid_changed()  # re-lookup against the mode's list
        self.update_ui()

    def _on_subjid_changed(self, *_):
        subjid = self.txtSubjID.text().strip().lower()
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
        ok = self.txtSubjID.text().strip() != "" and self.cbAff.currentText() != ""
        if self.mode == "assessment":
            ok = ok and self.cbLimb.currentText() != "" \
                and self.cbDom.currentText() != "" and self.cbTP.currentText() != ""
        self.pbStart.setEnabled(ok)

    def _on_start(self):
        subjid = self.txtSubjID.text().strip().lower()
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

    def closeEvent(self, event):
        if self.on_close_callback:
            self.on_close_callback(data=self.result)
        return super().closeEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = SessionSetupWindow(onclosecb=lambda data: print(data))
    w.show()
    sys.exit(app.exec())

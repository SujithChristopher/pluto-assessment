"""Module containing some of my custom PySide6 widgets.

Author: Sivakumar Balasubramanian
Date: 08 June 2025
"""

from PySide6 import QtGui, QtCore
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QGraphicsPathItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtGui import QPainterPath, QBrush, QColor, QFont
from PySide6.QtCore import QPointF
import pyqtgraph as pg
import math
import sys


class SingleLineWrapTextEdit(QTextEdit):
    """A QTextEdit that behaves like a single-line input with visual word wrapping."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptRichText(False)
        self.setWordWrapMode(QtGui.QTextOption.WordWrap)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFixedHeight(130)  # Simulates single-line height

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            event.ignore()  # Block newline entry
        else:
            super().keyPressEvent(event)


class CommentDialog(QDialog):
    def __init__(
        self,
        parent=None,
        label="Commemnt: ",
        optionyesno=False,
    ):
        super().__init__(parent)
        self.setFixedSize(300, 200)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint)
        self.setWindowTitle(f"Comment Logger.")

        # Set global font
        font = QtGui.QFont()
        font.setFamily("Cascadia Mono Light")
        font.setPointSize(8)
        self.setFont(font)

        # Create label
        self.label = QLabel(label, self)

        # Create visually wrapping single-line input
        self.text_edit = SingleLineWrapTextEdit(self)
        self.text_edit.setPlaceholderText("Type comment...")

        # OK/Cancel buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            if optionyesno
            else QDialogButtonBox.Cancel,
            self,
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Rename the buttons
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Reject")
        cancel_button.setAutoDefault(False)

        if optionyesno:
            ok_button = self.button_box.button(QDialogButtonBox.Ok)
            ok_button.setText("Accept")
            ok_button.setAutoDefault(False)

        # Prevent Return key from triggering OK
        self.button_box.button(QDialogButtonBox.Cancel).setAutoDefault(False)
        if optionyesno:
            self.button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)

    def getText(self):
        # Just in case, ensure newlines are removed
        return self.text_edit.toPlainText().replace("\n", " ").strip()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            event.ignore()  # Block dialog-level return behavior
        else:
            super().keyPressEvent(event)

    def accept(self):
        self.text_edit.setStyleSheet("")
        super().accept()

    def reject(self):
        comment = self.getText()
        if not comment:
            QMessageBox.warning(
                self, "Empty Comment", "Please enter a comment before continuing."
            )
            # You can also show a QMessageBox if you want feedback
            self.text_edit.setFocus()
            self.text_edit.setStyleSheet("border: 1px solid red;")
        else:
            self.text_edit.setStyleSheet("")  # Reset border
            super().reject()


class MechStartDialog(QDialog):
    """Confirm dialog shown before starting a mechanism assessment.
    Displays the mechanism image above the confirmation text."""

    def __init__(self, parent=None, mech_name="", img_path=""):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint)
        self.setWindowTitle("Confirm")

        font = QtGui.QFont()
        font.setFamily("Cascadia Mono Light")
        font.setPointSize(9)
        self.setFont(font)

        # Image
        self._img_label = QLabel(self)
        self._img_label.setAlignment(QtCore.Qt.AlignCenter)
        pixmap = QtGui.QPixmap(str(img_path))
        if not pixmap.isNull():
            self._img_label.setPixmap(
                pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            )

        # Text
        self._txt_label = QLabel(f"Start {mech_name} assessment?", self)
        self._txt_label.setAlignment(QtCore.Qt.AlignCenter)

        # Buttons
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._img_label)
        layout.addWidget(self._txt_label)
        layout.addWidget(self._buttons)
        self.adjustSize()


class MechTaskSkipDialog(QDialog):
    def __init__(self, parent=None, label="Commemnt: "):
        super().__init__(parent)
        self.setFixedSize(300, 200)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint)
        self.setWindowTitle(f"Skip Mechanism/Task.")

        # Set global font
        font = QtGui.QFont()
        font.setFamily("Cascadia Mono Light")
        font.setPointSize(8)
        self.setFont(font)

        # Create label
        self.label = QLabel(label, self)

        # Create visually wrapping single-line input
        self.text_edit = SingleLineWrapTextEdit(self)
        self.text_edit.setPlaceholderText("Type comment...")

        # OK/Cancel buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Rename the buttons
        ok_button = self.button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Skip")
        ok_button.setAutoDefault(False)
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Don't Skip")
        cancel_button.setAutoDefault(False)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)

    def getText(self):
        # Just in case, ensure newlines are removed
        return self.text_edit.toPlainText().replace("\n", " ").strip()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            event.ignore()  # Block dialog-level return behavior
        else:
            super().keyPressEvent(event)

    def accept(self):
        comment = self.getText()
        if not comment:
            QMessageBox.warning(
                self, "Empty Comment", "Please enter a comment before skipping."
            )
            # You can also show a QMessageBox if you want feedback
            self.text_edit.setFocus()
            self.text_edit.setStyleSheet("border: 1px solid red;")
        else:
            self.text_edit.setStyleSheet("")  # Reset border
            super().accept()

    def reject(self):
        self.text_edit.setStyleSheet("")
        super().reject()


class ScreeningStatsDialog(QDialog):
    """Popup listing each mechanism's recorded screening AROM, its threshold and
    pass/fail, plus the overall eligibility verdict. `stats` is the dict returned
    by PlutoAssessmentProtocolData.get_screening_eligibility()."""

    def __init__(self, eligible, stats, mech_labels=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint)
        self.setWindowTitle("Screening AROM Stats")
        mech_labels = mech_labels or {}

        font = QtGui.QFont()
        font.setFamily("Cascadia Mono Light")
        font.setPointSize(9)
        self.setFont(font)

        # Verdict banner.
        self._verdict = QLabel(
            "ELIGIBLE" if eligible else "NOT ELIGIBLE", self
        )
        self._verdict.setAlignment(QtCore.Qt.AlignCenter)
        self._verdict.setStyleSheet(
            "color: rgb(0,120,0); font-weight: bold;"
            if eligible
            else "color: rgb(170,0,0); font-weight: bold;"
        )

        # Per-mechanism table.
        self._table = QTableWidget(len(stats), 4, self)
        self._table.setHorizontalHeaderLabels(
            ["Mechanism", "AROM", "Threshold", "Result"]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        for _row, (_mech, _s) in enumerate(stats.items()):
            _unit = _s["unit"]
            if not _s["done"]:
                _aromtxt, _restxt, _color = "—", "pending", QColor(120, 120, 120)
            else:
                _aromtxt = f"{_s['value']:.1f} {_unit}"
                _restxt = "PASS" if _s["pass"] else "FAIL"
                _color = QColor(0, 120, 0) if _s["pass"] else QColor(170, 0, 0)
            _cells = [
                mech_labels.get(_mech, _mech),
                _aromtxt,
                f"{_s['threshold']:.1f} {_unit}",
                _restxt,
            ]
            for _col, _txt in enumerate(_cells):
                _item = QTableWidgetItem(_txt)
                if _col == 3:
                    _item.setForeground(QBrush(_color))
                self._table.setItem(_row, _col, _item)
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )

        self._buttons = QDialogButtonBox(QDialogButtonBox.Close, self)
        self._buttons.rejected.connect(self.reject)
        self._buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._verdict)
        layout.addWidget(self._table)
        layout.addWidget(self._buttons)
        self.resize(420, 220)


def create_sector(
    center, radius, start_angle_deg, span_angle_deg, color=QColor(255, 0, 0, 100)
):
    """
    Create a QGraphicsPathItem representing a filled sector.

    Parameters:
        center (QPointF): Center of the sector.
        radius (float): Radius of the sector.
        start_angle_deg (float): Starting angle in degrees (0° = right, counterclockwise).
        span_angle_deg (float): Angular span in degrees.
        color (QColor): Fill color of the sector.

    Returns:
        QGraphicsPathItem
    """
    path = QPainterPath()
    path.moveTo(center)

    # Add arc
    path.arcTo(
        center.x() - radius,
        center.y() - radius,
        2 * radius,
        2 * radius,
        -start_angle_deg,
        -span_angle_deg,
    )  # Negative for clockwise

    path.lineTo(center)  # Close back to center

    item = QGraphicsPathItem(path)
    item.setBrush(QBrush(color))
    item.setPen(pg.mkPen(None))
    return item


# Example usage
if __name__ == "__main__":
    app = QApplication(sys.argv)
    f""
    dialog = CommentDialog(
        label="Reason for skipping Left limb HOC for 1234:", optionyesno=False
    )
    if dialog.exec() == QDialog.Accepted:
        print("Input:", dialog.getText())
    else:
        print("Cancelled")

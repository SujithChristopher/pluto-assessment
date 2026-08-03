"""Entry point for the guided PLUTO assessment GUI.

Run: uv run python newgui/main.py"""

import pathlib
import sys

# Make the repository root importable when run as a script from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from PySide6 import QtWidgets

import plutofullassessdef as pfadef
from plutofullassessment import APP_STYLESHEET
from newgui.shell import PlutoGuidedAssessor


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    window = PlutoGuidedAssessor(port=pfadef.PLUTOCOMM)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

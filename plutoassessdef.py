"""
Module containing definitions for the PLUTO assessment protocol.

Author: Sivakumar Balasubramanian
Date: 02 September 2024
Email: siva82kb@gmail.com
"""

import numpy as np
import pathlib
from enum import Enum
from PySide6.QtCore import QStandardPaths


def _homer_data_root() -> pathlib.Path:
    """Base folder for all HOMER-PLUTO data: <Documents>/homerpluto (Windows;
    OneDrive-safe via QStandardPaths, falling back to ~/Documents)."""
    _docs = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    if not _docs:
        _docs = str(pathlib.Path.home() / "Documents")
    return pathlib.Path(_docs) / "homerpluto"


# Module level constants.
DATA_DIR = str(_homer_data_root() / "propassessment")
PROTOCOL_FILE = str(pathlib.Path(DATA_DIR) / "propassess_protocol.json")
PROPASS_CTRL_TIMER_DELTA = 0.01

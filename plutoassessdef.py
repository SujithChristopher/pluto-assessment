"""
Module containing definitions for the PLUTO assessment protocol.

Author: Sivakumar Balasubramanian
Date: 02 September 2024
Email: siva82kb@gmail.com
"""

import numpy as np
import pathlib
from enum import Enum
from plutofullassessdef import homer_data_root as _homer_data_root


# Module level constants.
DATA_DIR = str(_homer_data_root() / "propassessment")
PROTOCOL_FILE = str(pathlib.Path(DATA_DIR) / "propassess_protocol.json")
PROPASS_CTRL_TIMER_DELTA = 0.01

"""
Module for async worker threads to handle blocking I/O operations.

Author: Sivakumar Balasubramanian
Date: 2025
Email: siva82kb@gmail.com
"""

from PySide6.QtCore import QThread, Signal
import traceback


class SessionSetupWorker(QThread):
    """Worker thread for the blocking I/O of session setup:
    folder creation + protocol initialization (both screening and assessment)."""

    started = Signal()
    finished = Signal()
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, data_obj, parent=None):
        super().__init__(parent)
        self.data_obj = data_obj

    def run(self):
        try:
            self.started.emit()
            self.progress.emit("Creating session folder...")
            self.data_obj.create_session_folder()
            self.progress.emit("Initializing protocol...")
            self.data_obj.start_protocol()
            self.finished.emit()
        except Exception as e:
            self.error.emit(
                f"Error during session setup: {str(e)}\n{traceback.format_exc()}"
            )


# Backwards-compatible alias (old name still referenced until main window is updated).
LimbSetupWorker = SessionSetupWorker

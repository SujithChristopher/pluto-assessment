"""Session setup as an embedded page.

Reuses SessionSetupWindow wholesale — mode radios, subject list handling,
timepoint ordering checks — and only strips its window behaviour so it can sit
inside the guided GUI's stacked widget."""

from PySide6 import QtCore, QtWidgets

from sessionsetupwindow import SessionSetupWindow


class EmbeddedSetupPage(SessionSetupWindow):
    """SessionSetupWindow as a page widget. Calls onstartcb(setupdict) when the
    operator presses Start; the dict is the same one the old GUI receives."""

    def __init__(self, onstartcb, parent=None):
        # modal=False and no close callback: the guided shell reacts to Start
        # directly rather than to the window closing.
        super().__init__(parent=parent, modal=False, onclosecb=None)
        self._onstartcb = onstartcb
        # Suppress the one-shot centring in showEvent — meaningless (and
        # disruptive) for a widget inside a layout.
        self._centered = True
        self.setWindowFlags(QtCore.Qt.WindowType.Widget)
        # Cancel makes no sense as the first screen of the flow.
        self.pbCancel.setVisible(False)

    def _on_start(self):
        # This page instance is long-lived: after a failed session setup the
        # shell switches back to it and the operator tries again. The base
        # class only assigns self.result on the success path and returns
        # early on validation failure, so without this reset a validation
        # failure here would leave the previous attempt's dict in place and
        # the guard below would fire on stale data.
        self.result = {}
        super()._on_start()          # validates, creates the subject record
        if self.result:
            self._onstartcb(dict(self.result))

    def closeEvent(self, event):
        # The base class calls close() at the end of _on_start, which would hide
        # this page. Embedded, the shell owns page switching — swallow it, so
        # the page stays available if setup fails and we come back to it.
        event.ignore()

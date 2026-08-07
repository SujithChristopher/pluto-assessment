"""Session setup as an embedded page.

Reuses SessionSetupWindow wholesale — mode radios, subject list handling,
timepoint ordering checks — and only strips its window behaviour so it can sit
inside the guided GUI's stacked widget."""

from PySide6 import QtCore, QtGui, QtWidgets

from sessionsetupwindow import SessionSetupWindow

# The setup form is a form, not a dashboard: stretched across a maximised
# window its fields become unreadably wide. It sits in a fixed-width card,
# centred in the page instead.
CARD_MIN_WIDTH = 480
CARD_MAX_WIDTH = 560

CARD_QSS = """
QWidget#setupCard {
    background-color: #ffffff;
    border: 1px solid #e3e7ec;
    border-radius: 14px;
}
/* The card is already a white panel — the group box only needs to be a
   labelled section inside it, not a second nested panel. */
QWidget#setupCard QGroupBox {
    background: transparent;
    border: none;
    border-top: 1px solid #edf0f3;
    border-radius: 0;
    margin-top: 14px;
    padding: 14px 0 0 0;
}
QWidget#setupCard QGroupBox::title {
    left: 0px;
    padding: 0 6px 0 0;
    color: #6b7280;
    font-size: 9pt;
    text-transform: uppercase;
}
QWidget#setupCard QComboBox {
    min-height: 26px;
}
QWidget#setupCard QLabel {
    color: #3c4043;
}
"""


class EmbeddedSetupPage(SessionSetupWindow):
    """SessionSetupWindow as a page widget. Calls onstartcb(setupdict) when the
    operator presses Start; the dict is the same one the old GUI receives.

    If the selected session is already finished there is nothing to start, so
    onviewstatscb is called instead with {mode, subjid, limb, timepoint} and the
    shell shows what was recorded."""

    def __init__(self, onstartcb, onviewstatscb=None, parent=None):
        # modal=False and no close callback: the guided shell reacts to Start
        # directly rather than to the window closing.
        super().__init__(parent=parent, modal=False, onclosecb=None)
        self._onstartcb = onstartcb
        self._onviewstatscb = onviewstatscb
        # Suppress the one-shot centring in showEvent — meaningless (and
        # disruptive) for a widget inside a layout.
        self._centered = True
        self.setWindowFlags(QtCore.Qt.WindowType.Widget)
        # Cancel makes no sense as the first screen of the flow.
        self.pbCancel.setVisible(False)
        self._build_card()

    def _build_card(self):
        """Re-home the form built by the base class into a centred card."""
        # takeCentralWidget() hands over ownership; setCentralWidget() would
        # otherwise delete the form we are trying to keep.
        _form = self.takeCentralWidget()
        _form.setObjectName("setupCard")
        # A plain QWidget ignores stylesheet backgrounds/borders without this.
        _form.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        _form.setStyleSheet(CARD_QSS)
        _form.setMinimumWidth(CARD_MIN_WIDTH)
        _form.setMaximumWidth(CARD_MAX_WIDTH)
        _form.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )
        _form.layout().setContentsMargins(28, 24, 28, 22)
        _form.layout().setSpacing(14)
        self._formlayout = self.gbDetails.layout()
        self._hintrow = self._formlayout.getWidgetPosition(self.lblExisting)[0]
        self._set_hint_visible(False)

        _shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        _shadow.setBlurRadius(28)
        _shadow.setOffset(0, 6)
        _shadow.setColor(QtGui.QColor(15, 23, 42, 38))
        _form.setGraphicsEffect(_shadow)

        # The base class pads the form's bottom with a stretch so the buttons
        # sit at the window's foot; in a hug-your-content card that only adds
        # dead space.
        _lay = _form.layout()
        for _i in reversed(range(_lay.count())):
            if _lay.itemAt(_i).spacerItem() is not None:
                _lay.takeAt(_i)

        # Start is the only button left, and the primary action of the page.
        self.pbStart.setMinimumHeight(40)
        self.pbStart.setMinimumWidth(150)

        _page = QtWidgets.QWidget()
        _col = QtWidgets.QVBoxLayout(_page)
        _col.setContentsMargins(24, 16, 24, 24)
        _col.addStretch(1)
        _row = QtWidgets.QHBoxLayout()
        _row.addStretch(1)
        _row.addWidget(_form)
        _row.addStretch(1)
        _col.addLayout(_row)
        _col.addStretch(2)
        self.setCentralWidget(_page)

    def _set_hint_visible(self, visible: bool):
        """Collapse the existing/new-subject hint row while it has nothing to
        say, rather than leaving a blank gap under the Subject ID field."""
        self._formlayout.setRowVisible(self._hintrow, visible)

    def _on_subjid_changed(self, *_):
        super()._on_subjid_changed()
        # _build_card has not run yet during the base class's __init__.
        if hasattr(self, "_hintrow"):
            self._set_hint_visible(self.lblExisting.text() != "")

    def _on_already_completed(self, info):
        """Show the recorded stats instead of the base class's dialog. Falls
        back to the dialog if the shell did not supply a viewer."""
        if self._onviewstatscb is None:
            return super()._on_already_completed(info)
        self._onviewstatscb(dict(info))

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

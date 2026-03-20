# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutotestcontrol.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QRadioButton, QSizePolicy, QSlider,
    QVBoxLayout, QWidget)

class Ui_PlutoTestControlWindow(object):
    def setupUi(self, PlutoTestControlWindow):
        if not PlutoTestControlWindow.objectName():
            PlutoTestControlWindow.setObjectName(u"PlutoTestControlWindow")
        PlutoTestControlWindow.resize(395, 296)
        PlutoTestControlWindow.setMinimumSize(QSize(395, 296))
        PlutoTestControlWindow.setMaximumSize(QSize(395, 296))
        self.centralwidget = QWidget(PlutoTestControlWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 371, 271))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.gbControlType = QGroupBox(self.verticalLayoutWidget)
        self.gbControlType.setObjectName(u"gbControlType")
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(12)
        self.gbControlType.setFont(font)
        self.horizontalLayoutWidget = QWidget(self.gbControlType)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(10, 20, 347, 25))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.radioNone = QRadioButton(self.horizontalLayoutWidget)
        self.radioNone.setObjectName(u"radioNone")

        self.horizontalLayout.addWidget(self.radioNone)

        self.radioTorque = QRadioButton(self.horizontalLayoutWidget)
        self.radioTorque.setObjectName(u"radioTorque")

        self.horizontalLayout.addWidget(self.radioTorque)

        self.radioPosition = QRadioButton(self.horizontalLayoutWidget)
        self.radioPosition.setObjectName(u"radioPosition")

        self.horizontalLayout.addWidget(self.radioPosition)


        self.verticalLayout.addWidget(self.gbControlType)

        self.lblFeedforwardTorqueValue = QLabel(self.verticalLayoutWidget)
        self.lblFeedforwardTorqueValue.setObjectName(u"lblFeedforwardTorqueValue")
        self.lblFeedforwardTorqueValue.setMinimumSize(QSize(0, 20))
        self.lblFeedforwardTorqueValue.setMaximumSize(QSize(16777215, 20))
        self.lblFeedforwardTorqueValue.setFont(font)
        self.lblFeedforwardTorqueValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout.addWidget(self.lblFeedforwardTorqueValue)

        self.hSliderTorqTgtValue = QSlider(self.verticalLayoutWidget)
        self.hSliderTorqTgtValue.setObjectName(u"hSliderTorqTgtValue")
        self.hSliderTorqTgtValue.setMaximum(1000)
        self.hSliderTorqTgtValue.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.hSliderTorqTgtValue)

        self.lblPositionTargetValue = QLabel(self.verticalLayoutWidget)
        self.lblPositionTargetValue.setObjectName(u"lblPositionTargetValue")
        self.lblPositionTargetValue.setMinimumSize(QSize(0, 20))
        self.lblPositionTargetValue.setMaximumSize(QSize(16777215, 20))
        self.lblPositionTargetValue.setFont(font)
        self.lblPositionTargetValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout.addWidget(self.lblPositionTargetValue)

        self.hSliderPosTgtValue = QSlider(self.verticalLayoutWidget)
        self.hSliderPosTgtValue.setObjectName(u"hSliderPosTgtValue")
        self.hSliderPosTgtValue.setMaximum(1000)
        self.hSliderPosTgtValue.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.hSliderPosTgtValue)

        self.lblControlBoundValue = QLabel(self.verticalLayoutWidget)
        self.lblControlBoundValue.setObjectName(u"lblControlBoundValue")
        self.lblControlBoundValue.setMinimumSize(QSize(0, 20))
        self.lblControlBoundValue.setMaximumSize(QSize(16777215, 20))
        self.lblControlBoundValue.setFont(font)
        self.lblControlBoundValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout.addWidget(self.lblControlBoundValue)

        self.hSliderCtrlBndValue = QSlider(self.verticalLayoutWidget)
        self.hSliderCtrlBndValue.setObjectName(u"hSliderCtrlBndValue")
        self.hSliderCtrlBndValue.setMaximum(255)
        self.hSliderCtrlBndValue.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.hSliderCtrlBndValue)

        self.lblControlGainValue = QLabel(self.verticalLayoutWidget)
        self.lblControlGainValue.setObjectName(u"lblControlGainValue")
        self.lblControlGainValue.setMinimumSize(QSize(0, 20))
        self.lblControlGainValue.setMaximumSize(QSize(16777215, 20))
        self.lblControlGainValue.setFont(font)
        self.lblControlGainValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout.addWidget(self.lblControlGainValue)

        self.hSliderCtrlGainValue = QSlider(self.verticalLayoutWidget)
        self.hSliderCtrlGainValue.setObjectName(u"hSliderCtrlGainValue")
        self.hSliderCtrlGainValue.setMaximum(255)
        self.hSliderCtrlGainValue.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.hSliderCtrlGainValue)

        PlutoTestControlWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(PlutoTestControlWindow)

        QMetaObject.connectSlotsByName(PlutoTestControlWindow)
    # setupUi

    def retranslateUi(self, PlutoTestControlWindow):
        PlutoTestControlWindow.setWindowTitle(QCoreApplication.translate("PlutoTestControlWindow", u"PLUTO Test Window", None))
        self.gbControlType.setTitle(QCoreApplication.translate("PlutoTestControlWindow", u"Choose Control Type", None))
        self.radioNone.setText(QCoreApplication.translate("PlutoTestControlWindow", u"No Control", None))
        self.radioTorque.setText(QCoreApplication.translate("PlutoTestControlWindow", u"Torque", None))
        self.radioPosition.setText(QCoreApplication.translate("PlutoTestControlWindow", u"Position", None))
        self.lblFeedforwardTorqueValue.setText(QCoreApplication.translate("PlutoTestControlWindow", u"Feedforward Torque Value (Nm):", None))
        self.lblPositionTargetValue.setText(QCoreApplication.translate("PlutoTestControlWindow", u"Target Position Value (deg):", None))
        self.lblControlBoundValue.setText(QCoreApplication.translate("PlutoTestControlWindow", u"Control Bound:", None))
        self.lblControlGainValue.setText(QCoreApplication.translate("PlutoTestControlWindow", u"Control Gain:", None))
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutocontroltester.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QRadioButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PlutoControlTesterWindow(object):
    def setupUi(self, PlutoControlTesterWindow):
        if not PlutoControlTesterWindow.objectName():
            PlutoControlTesterWindow.setObjectName(u"PlutoControlTesterWindow")
        PlutoControlTesterWindow.resize(452, 419)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PlutoControlTesterWindow.sizePolicy().hasHeightForWidth())
        PlutoControlTesterWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(PlutoControlTesterWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 431, 397))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.gbControlType = QGroupBox(self.verticalLayoutWidget)
        self.gbControlType.setObjectName(u"gbControlType")
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(12)
        self.gbControlType.setFont(font)
        self.verticalLayout_4 = QVBoxLayout(self.gbControlType)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.radioPosition = QRadioButton(self.gbControlType)
        self.radioPosition.setObjectName(u"radioPosition")
        self.radioPosition.setFont(font)

        self.gridLayout.addWidget(self.radioPosition, 0, 2, 1, 1)

        self.radioPositionLinear = QRadioButton(self.gbControlType)
        self.radioPositionLinear.setObjectName(u"radioPositionLinear")
        self.radioPositionLinear.setEnabled(False)
        self.radioPositionLinear.setFont(font)

        self.gridLayout.addWidget(self.radioPositionLinear, 1, 2, 1, 1)

        self.radioNone = QRadioButton(self.gbControlType)
        self.radioNone.setObjectName(u"radioNone")
        self.radioNone.setFont(font)

        self.gridLayout.addWidget(self.radioNone, 0, 0, 1, 1)

        self.radioTorque = QRadioButton(self.gbControlType)
        self.radioTorque.setObjectName(u"radioTorque")
        self.radioTorque.setFont(font)

        self.gridLayout.addWidget(self.radioTorque, 1, 0, 1, 1)

        self.radioObjectSim = QRadioButton(self.gbControlType)
        self.radioObjectSim.setObjectName(u"radioObjectSim")
        self.radioObjectSim.setEnabled(False)

        self.gridLayout.addWidget(self.radioObjectSim, 2, 0, 1, 1)


        self.verticalLayout_4.addLayout(self.gridLayout)


        self.verticalLayout.addWidget(self.gbControlType)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.lblTargetDuration = QLabel(self.verticalLayoutWidget)
        self.lblTargetDuration.setObjectName(u"lblTargetDuration")
        self.lblTargetDuration.setMinimumSize(QSize(320, 20))
        self.lblTargetDuration.setMaximumSize(QSize(320, 20))
        self.lblTargetDuration.setFont(font)
        self.lblTargetDuration.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lblTargetDuration)

        self.dsbTgtDur = QDoubleSpinBox(self.verticalLayoutWidget)
        self.dsbTgtDur.setObjectName(u"dsbTgtDur")
        font1 = QFont()
        font1.setFamilies([u"Cascadia Mono Light"])
        font1.setPointSize(10)
        self.dsbTgtDur.setFont(font1)
        self.dsbTgtDur.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbTgtDur.setDecimals(2)
        self.dsbTgtDur.setMinimum(0.000000000000000)
        self.dsbTgtDur.setMaximum(10.000000000000000)
        self.dsbTgtDur.setSingleStep(0.100000000000000)

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.dsbTgtDur)

        self.lblFeedforwardTorqueValue = QLabel(self.verticalLayoutWidget)
        self.lblFeedforwardTorqueValue.setObjectName(u"lblFeedforwardTorqueValue")
        self.lblFeedforwardTorqueValue.setMinimumSize(QSize(320, 20))
        self.lblFeedforwardTorqueValue.setMaximumSize(QSize(320, 20))
        self.lblFeedforwardTorqueValue.setFont(font)
        self.lblFeedforwardTorqueValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lblFeedforwardTorqueValue)

        self.dsbTorqTgtValue = QDoubleSpinBox(self.verticalLayoutWidget)
        self.dsbTorqTgtValue.setObjectName(u"dsbTorqTgtValue")
        self.dsbTorqTgtValue.setFont(font1)
        self.dsbTorqTgtValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbTorqTgtValue.setMinimum(-1.000000000000000)
        self.dsbTorqTgtValue.setMaximum(1.000000000000000)
        self.dsbTorqTgtValue.setSingleStep(0.010000000000000)

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.dsbTorqTgtValue)

        self.lblPositionTargetValue = QLabel(self.verticalLayoutWidget)
        self.lblPositionTargetValue.setObjectName(u"lblPositionTargetValue")
        self.lblPositionTargetValue.setMinimumSize(QSize(320, 20))
        self.lblPositionTargetValue.setMaximumSize(QSize(320, 20))
        self.lblPositionTargetValue.setFont(font)
        self.lblPositionTargetValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lblPositionTargetValue)

        self.dsbPosTgtValue = QDoubleSpinBox(self.verticalLayoutWidget)
        self.dsbPosTgtValue.setObjectName(u"dsbPosTgtValue")
        self.dsbPosTgtValue.setFont(font1)
        self.dsbPosTgtValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbPosTgtValue.setMinimum(-1.000000000000000)
        self.dsbPosTgtValue.setMaximum(1.000000000000000)
        self.dsbPosTgtValue.setSingleStep(0.010000000000000)

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.FieldRole, self.dsbPosTgtValue)

        self.lblControlBoundValue = QLabel(self.verticalLayoutWidget)
        self.lblControlBoundValue.setObjectName(u"lblControlBoundValue")
        self.lblControlBoundValue.setMinimumSize(QSize(320, 20))
        self.lblControlBoundValue.setMaximumSize(QSize(320, 20))
        self.lblControlBoundValue.setFont(font)
        self.lblControlBoundValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.LabelRole, self.lblControlBoundValue)

        self.dsbCtrlBndValue = QDoubleSpinBox(self.verticalLayoutWidget)
        self.dsbCtrlBndValue.setObjectName(u"dsbCtrlBndValue")
        self.dsbCtrlBndValue.setFont(font1)
        self.dsbCtrlBndValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbCtrlBndValue.setMinimum(0.000000000000000)
        self.dsbCtrlBndValue.setMaximum(1.000000000000000)
        self.dsbCtrlBndValue.setSingleStep(0.010000000000000)

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.FieldRole, self.dsbCtrlBndValue)

        self.lblControlGainValue = QLabel(self.verticalLayoutWidget)
        self.lblControlGainValue.setObjectName(u"lblControlGainValue")
        self.lblControlGainValue.setMinimumSize(QSize(320, 20))
        self.lblControlGainValue.setMaximumSize(QSize(320, 20))
        self.lblControlGainValue.setFont(font)
        self.lblControlGainValue.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.formLayout_3.setWidget(4, QFormLayout.ItemRole.LabelRole, self.lblControlGainValue)

        self.dsbCtrlGainValue = QDoubleSpinBox(self.verticalLayoutWidget)
        self.dsbCtrlGainValue.setObjectName(u"dsbCtrlGainValue")
        self.dsbCtrlGainValue.setFont(font1)
        self.dsbCtrlGainValue.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbCtrlGainValue.setDecimals(2)
        self.dsbCtrlGainValue.setMinimum(1.000000000000000)
        self.dsbCtrlGainValue.setMaximum(10.000000000000000)
        self.dsbCtrlGainValue.setSingleStep(0.010000000000000)

        self.formLayout_3.setWidget(4, QFormLayout.ItemRole.FieldRole, self.dsbCtrlGainValue)

        self.lblObjectPosition = QLabel(self.verticalLayoutWidget)
        self.lblObjectPosition.setObjectName(u"lblObjectPosition")
        self.lblObjectPosition.setMinimumSize(QSize(320, 20))
        self.lblObjectPosition.setMaximumSize(QSize(320, 20))
        self.lblObjectPosition.setFont(font)
        self.lblObjectPosition.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.formLayout_3.setWidget(5, QFormLayout.ItemRole.LabelRole, self.lblObjectPosition)

        self.lblObjectDelPos = QLabel(self.verticalLayoutWidget)
        self.lblObjectDelPos.setObjectName(u"lblObjectDelPos")
        self.lblObjectDelPos.setMinimumSize(QSize(320, 20))
        self.lblObjectDelPos.setMaximumSize(QSize(320, 20))
        self.lblObjectDelPos.setFont(font)
        self.lblObjectDelPos.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.formLayout_3.setWidget(6, QFormLayout.ItemRole.LabelRole, self.lblObjectDelPos)

        self.dsbObjPos = QDoubleSpinBox(self.verticalLayoutWidget)
        self.dsbObjPos.setObjectName(u"dsbObjPos")
        self.dsbObjPos.setEnabled(False)
        self.dsbObjPos.setFont(font1)
        self.dsbObjPos.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbObjPos.setDecimals(2)
        self.dsbObjPos.setMinimum(-90.000000000000000)
        self.dsbObjPos.setMaximum(0.000000000000000)
        self.dsbObjPos.setSingleStep(1.000000000000000)
        self.dsbObjPos.setValue(0.000000000000000)

        self.formLayout_3.setWidget(5, QFormLayout.ItemRole.FieldRole, self.dsbObjPos)

        self.dsbObjDelPos = QDoubleSpinBox(self.verticalLayoutWidget)
        self.dsbObjDelPos.setObjectName(u"dsbObjDelPos")
        self.dsbObjDelPos.setEnabled(False)
        self.dsbObjDelPos.setFont(font1)
        self.dsbObjDelPos.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.dsbObjDelPos.setDecimals(2)
        self.dsbObjDelPos.setMinimum(1.000000000000000)
        self.dsbObjDelPos.setMaximum(40.000000000000000)
        self.dsbObjDelPos.setSingleStep(1.000000000000000)
        self.dsbObjDelPos.setValue(40.000000000000000)

        self.formLayout_3.setWidget(6, QFormLayout.ItemRole.FieldRole, self.dsbObjDelPos)


        self.verticalLayout.addLayout(self.formLayout_3)

        self.pbSetTarget = QPushButton(self.verticalLayoutWidget)
        self.pbSetTarget.setObjectName(u"pbSetTarget")
        self.pbSetTarget.setFont(font)

        self.verticalLayout.addWidget(self.pbSetTarget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pbCtrlHold = QPushButton(self.verticalLayoutWidget)
        self.pbCtrlHold.setObjectName(u"pbCtrlHold")
        self.pbCtrlHold.setEnabled(False)
        self.pbCtrlHold.setFont(font)

        self.horizontalLayout_2.addWidget(self.pbCtrlHold)

        self.pbCtrlDecay = QPushButton(self.verticalLayoutWidget)
        self.pbCtrlDecay.setObjectName(u"pbCtrlDecay")
        self.pbCtrlDecay.setEnabled(False)
        self.pbCtrlDecay.setFont(font)

        self.horizontalLayout_2.addWidget(self.pbCtrlDecay)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        PlutoControlTesterWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(PlutoControlTesterWindow)

        QMetaObject.connectSlotsByName(PlutoControlTesterWindow)
    # setupUi

    def retranslateUi(self, PlutoControlTesterWindow):
        PlutoControlTesterWindow.setWindowTitle(QCoreApplication.translate("PlutoControlTesterWindow", u"PLUTO Test Window", None))
        self.gbControlType.setTitle(QCoreApplication.translate("PlutoControlTesterWindow", u"Choose Control Type", None))
        self.radioPosition.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Position", None))
        self.radioPositionLinear.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Position Linear", None))
        self.radioNone.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"No Control", None))
        self.radioTorque.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Torque", None))
        self.radioObjectSim.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Object Sim", None))
        self.lblTargetDuration.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Target Duration (s):", None))
        self.lblFeedforwardTorqueValue.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Feedforward Torque Value (Nm):", None))
        self.lblPositionTargetValue.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Target Position Value (deg):", None))
        self.lblControlBoundValue.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Control Bound:", None))
        self.lblControlGainValue.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Control Gain:", None))
        self.lblObjectPosition.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Object Position:", None))
        self.lblObjectDelPos.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Transition Width:", None))
        self.pbSetTarget.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Set Target", None))
        self.pbCtrlHold.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Control Hold", None))
        self.pbCtrlDecay.setText(QCoreApplication.translate("PlutoControlTesterWindow", u"Control Decay", None))
    # retranslateUi


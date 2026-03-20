# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutofullassessment.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QComboBox,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QStatusBar,
    QTableView, QTextEdit, QVBoxLayout, QWidget)

class Ui_PlutoFullAssessor(object):
    def setupUi(self, PlutoFullAssessor):
        if not PlutoFullAssessor.objectName():
            PlutoFullAssessor.setObjectName(u"PlutoFullAssessor")
        PlutoFullAssessor.setEnabled(True)
        PlutoFullAssessor.resize(1200, 607)
        PlutoFullAssessor.setMinimumSize(QSize(1200, 607))
        PlutoFullAssessor.setMaximumSize(QSize(1200, 607))
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(12)
        PlutoFullAssessor.setFont(font)
        self.centralwidget = QWidget(PlutoFullAssessor)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_4 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pbCreateSeelectSubject = QPushButton(self.centralwidget)
        self.pbCreateSeelectSubject.setObjectName(u"pbCreateSeelectSubject")
        self.pbCreateSeelectSubject.setEnabled(False)
        self.pbCreateSeelectSubject.setFont(font)

        self.verticalLayout.addWidget(self.pbCreateSeelectSubject)

        self.pbSelectSubject = QPushButton(self.centralwidget)
        self.pbSelectSubject.setObjectName(u"pbSelectSubject")
        self.pbSelectSubject.setEnabled(False)
        self.pbSelectSubject.setFont(font)

        self.verticalLayout.addWidget(self.pbSelectSubject)

        self.lblSubjDetails = QLabel(self.centralwidget)
        self.lblSubjDetails.setObjectName(u"lblSubjDetails")
        self.lblSubjDetails.setMinimumSize(QSize(300, 28))
        self.lblSubjDetails.setMaximumSize(QSize(16777215, 32))
        font1 = QFont()
        font1.setFamilies([u"Cascadia Code Light"])
        font1.setPointSize(11)
        self.lblSubjDetails.setFont(font1)

        self.verticalLayout.addWidget(self.lblSubjDetails)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lblLimb = QLabel(self.centralwidget)
        self.lblLimb.setObjectName(u"lblLimb")
        self.lblLimb.setEnabled(False)

        self.horizontalLayout_2.addWidget(self.lblLimb)

        self.cbLimb = QComboBox(self.centralwidget)
        self.cbLimb.addItem("")
        self.cbLimb.addItem("")
        self.cbLimb.addItem("")
        self.cbLimb.setObjectName(u"cbLimb")
        self.cbLimb.setEnabled(False)

        self.horizontalLayout_2.addWidget(self.cbLimb)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.pbSetLimb = QPushButton(self.centralwidget)
        self.pbSetLimb.setObjectName(u"pbSetLimb")
        self.pbSetLimb.setEnabled(False)

        self.verticalLayout.addWidget(self.pbSetLimb)

        self.gbMechanisms = QGroupBox(self.centralwidget)
        self.gbMechanisms.setObjectName(u"gbMechanisms")
        self.gbMechanisms.setEnabled(False)
        self.gbMechanisms.setMinimumSize(QSize(270, 120))
        self.verticalLayout_4 = QVBoxLayout(self.gbMechanisms)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setSpacing(0)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.pbFPS = QPushButton(self.gbMechanisms)
        self.pbFPS.setObjectName(u"pbFPS")
        self.pbFPS.setEnabled(False)
        self.pbFPS.setFont(font)
        self.pbFPS.setStyleSheet(u"")

        self.horizontalLayout_17.addWidget(self.pbFPS)

        self.pbFPSSkip = QPushButton(self.gbMechanisms)
        self.pbFPSSkip.setObjectName(u"pbFPSSkip")
        self.pbFPSSkip.setEnabled(False)
        self.pbFPSSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_17.addWidget(self.pbFPSSkip)


        self.verticalLayout_4.addLayout(self.horizontalLayout_17)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setSpacing(0)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.pbWFE = QPushButton(self.gbMechanisms)
        self.pbWFE.setObjectName(u"pbWFE")
        self.pbWFE.setEnabled(False)
        self.pbWFE.setFont(font)
        self.pbWFE.setStyleSheet(u"")

        self.horizontalLayout_16.addWidget(self.pbWFE)

        self.pbWFESkip = QPushButton(self.gbMechanisms)
        self.pbWFESkip.setObjectName(u"pbWFESkip")
        self.pbWFESkip.setEnabled(False)
        self.pbWFESkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_16.addWidget(self.pbWFESkip)


        self.verticalLayout_4.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setSpacing(0)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.pbHOC = QPushButton(self.gbMechanisms)
        self.pbHOC.setObjectName(u"pbHOC")
        self.pbHOC.setEnabled(False)
        self.pbHOC.setFont(font)
        self.pbHOC.setStyleSheet(u"")

        self.horizontalLayout_15.addWidget(self.pbHOC)

        self.pbHOCSkip = QPushButton(self.gbMechanisms)
        self.pbHOCSkip.setObjectName(u"pbHOCSkip")
        self.pbHOCSkip.setEnabled(False)
        self.pbHOCSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_15.addWidget(self.pbHOCSkip)


        self.verticalLayout_4.addLayout(self.horizontalLayout_15)


        self.verticalLayout.addWidget(self.gbMechanisms)

        self.pbCalibrate = QPushButton(self.centralwidget)
        self.pbCalibrate.setObjectName(u"pbCalibrate")
        self.pbCalibrate.setEnabled(False)
        self.pbCalibrate.setFont(font)
        self.pbCalibrate.setStyleSheet(u"")

        self.verticalLayout.addWidget(self.pbCalibrate)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pbAROM = QPushButton(self.centralwidget)
        self.pbAROM.setObjectName(u"pbAROM")
        self.pbAROM.setEnabled(False)
        self.pbAROM.setFont(font)
        self.pbAROM.setStyleSheet(u"")

        self.horizontalLayout.addWidget(self.pbAROM)

        self.pbAROMSkip = QPushButton(self.centralwidget)
        self.pbAROMSkip.setObjectName(u"pbAROMSkip")
        self.pbAROMSkip.setEnabled(False)
        self.pbAROMSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout.addWidget(self.pbAROMSkip)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.pbPROM = QPushButton(self.centralwidget)
        self.pbPROM.setObjectName(u"pbPROM")
        self.pbPROM.setEnabled(False)
        self.pbPROM.setFont(font)
        self.pbPROM.setStyleSheet(u"")

        self.horizontalLayout_6.addWidget(self.pbPROM)

        self.pbPROMSkip = QPushButton(self.centralwidget)
        self.pbPROMSkip.setObjectName(u"pbPROMSkip")
        self.pbPROMSkip.setEnabled(False)
        self.pbPROMSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_6.addWidget(self.pbPROMSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.pbAPROMSlow = QPushButton(self.centralwidget)
        self.pbAPROMSlow.setObjectName(u"pbAPROMSlow")
        self.pbAPROMSlow.setEnabled(False)
        self.pbAPROMSlow.setFont(font)
        self.pbAPROMSlow.setStyleSheet(u"")

        self.horizontalLayout_7.addWidget(self.pbAPROMSlow)

        self.pbAPROMSlowSkip = QPushButton(self.centralwidget)
        self.pbAPROMSlowSkip.setObjectName(u"pbAPROMSlowSkip")
        self.pbAPROMSlowSkip.setEnabled(False)
        self.pbAPROMSlowSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_7.addWidget(self.pbAPROMSlowSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.pbAPROMFast = QPushButton(self.centralwidget)
        self.pbAPROMFast.setObjectName(u"pbAPROMFast")
        self.pbAPROMFast.setEnabled(False)
        self.pbAPROMFast.setFont(font)
        self.pbAPROMFast.setStyleSheet(u"")

        self.horizontalLayout_8.addWidget(self.pbAPROMFast)

        self.pbAPROMFastSkip = QPushButton(self.centralwidget)
        self.pbAPROMFastSkip.setObjectName(u"pbAPROMFastSkip")
        self.pbAPROMFastSkip.setEnabled(False)
        self.pbAPROMFastSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_8.addWidget(self.pbAPROMFastSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.pbDiscReach = QPushButton(self.centralwidget)
        self.pbDiscReach.setObjectName(u"pbDiscReach")
        self.pbDiscReach.setEnabled(False)
        self.pbDiscReach.setFont(font)
        self.pbDiscReach.setStyleSheet(u"")

        self.horizontalLayout_9.addWidget(self.pbDiscReach)

        self.pbDiscReachSkip = QPushButton(self.centralwidget)
        self.pbDiscReachSkip.setObjectName(u"pbDiscReachSkip")
        self.pbDiscReachSkip.setEnabled(False)
        self.pbDiscReachSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_9.addWidget(self.pbDiscReachSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.pbPosHold = QPushButton(self.centralwidget)
        self.pbPosHold.setObjectName(u"pbPosHold")
        self.pbPosHold.setEnabled(False)
        self.pbPosHold.setFont(font)
        self.pbPosHold.setStyleSheet(u"")

        self.horizontalLayout_10.addWidget(self.pbPosHold)

        self.pbPosHoldSkip = QPushButton(self.centralwidget)
        self.pbPosHoldSkip.setObjectName(u"pbPosHoldSkip")
        self.pbPosHoldSkip.setEnabled(False)
        self.pbPosHoldSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_10.addWidget(self.pbPosHoldSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setSpacing(0)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.pbProp = QPushButton(self.centralwidget)
        self.pbProp.setObjectName(u"pbProp")
        self.pbProp.setEnabled(False)
        self.pbProp.setFont(font)
        self.pbProp.setStyleSheet(u"")

        self.horizontalLayout_11.addWidget(self.pbProp)

        self.pbPropSkip = QPushButton(self.centralwidget)
        self.pbPropSkip.setObjectName(u"pbPropSkip")
        self.pbPropSkip.setEnabled(False)
        self.pbPropSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_11.addWidget(self.pbPropSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setSpacing(0)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.pbForceCtrlLow = QPushButton(self.centralwidget)
        self.pbForceCtrlLow.setObjectName(u"pbForceCtrlLow")
        self.pbForceCtrlLow.setEnabled(False)
        self.pbForceCtrlLow.setFont(font)
        self.pbForceCtrlLow.setStyleSheet(u"")

        self.horizontalLayout_12.addWidget(self.pbForceCtrlLow)

        self.pbForceCtrlLowSkip = QPushButton(self.centralwidget)
        self.pbForceCtrlLowSkip.setObjectName(u"pbForceCtrlLowSkip")
        self.pbForceCtrlLowSkip.setEnabled(False)
        self.pbForceCtrlLowSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_12.addWidget(self.pbForceCtrlLowSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setSpacing(0)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.pbForceCtrlMed = QPushButton(self.centralwidget)
        self.pbForceCtrlMed.setObjectName(u"pbForceCtrlMed")
        self.pbForceCtrlMed.setEnabled(False)
        self.pbForceCtrlMed.setFont(font)
        self.pbForceCtrlMed.setStyleSheet(u"")

        self.horizontalLayout_13.addWidget(self.pbForceCtrlMed)

        self.pbForceCtrlMedSkip = QPushButton(self.centralwidget)
        self.pbForceCtrlMedSkip.setObjectName(u"pbForceCtrlMedSkip")
        self.pbForceCtrlMedSkip.setEnabled(False)
        self.pbForceCtrlMedSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_13.addWidget(self.pbForceCtrlMedSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setSpacing(0)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.pbForceCtrlHigh = QPushButton(self.centralwidget)
        self.pbForceCtrlHigh.setObjectName(u"pbForceCtrlHigh")
        self.pbForceCtrlHigh.setEnabled(False)
        self.pbForceCtrlHigh.setFont(font)
        self.pbForceCtrlHigh.setStyleSheet(u"")

        self.horizontalLayout_14.addWidget(self.pbForceCtrlHigh)

        self.pbForceCtrlHighSkip = QPushButton(self.centralwidget)
        self.pbForceCtrlHighSkip.setObjectName(u"pbForceCtrlHighSkip")
        self.pbForceCtrlHighSkip.setEnabled(False)
        self.pbForceCtrlHighSkip.setMaximumSize(QSize(45, 16777215))

        self.horizontalLayout_14.addWidget(self.pbForceCtrlHighSkip)


        self.verticalLayout.addLayout(self.horizontalLayout_14)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)
        self.label_4.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout_2.addWidget(self.label_4)

        self.textPlutoData = QTextEdit(self.centralwidget)
        self.textPlutoData.setObjectName(u"textPlutoData")
        self.textPlutoData.setEnabled(False)
        self.textPlutoData.setStyleSheet(u"background-color: rgb(0, 0, 0);\n"
"color: rgb(0, 255, 60);\n"
"font: 10pt \"Cascadia Mono\";\n"
"border: none;")
        self.textPlutoData.setReadOnly(True)

        self.verticalLayout_2.addWidget(self.textPlutoData)

        self.lblSessionInfo = QLabel(self.centralwidget)
        self.lblSessionInfo.setObjectName(u"lblSessionInfo")
        font2 = QFont()
        font2.setFamilies([u"Cascadia Mono"])
        font2.setPointSize(10)
        self.lblSessionInfo.setFont(font2)
        self.lblSessionInfo.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout_2.addWidget(self.lblSessionInfo)

        self.textProtocolDetails = QTextEdit(self.centralwidget)
        self.textProtocolDetails.setObjectName(u"textProtocolDetails")
        self.textProtocolDetails.setEnabled(False)
        font3 = QFont()
        font3.setFamilies([u"Cascadia Mono"])
        font3.setPointSize(10)
        font3.setBold(False)
        font3.setItalic(False)
        self.textProtocolDetails.setFont(font3)
        self.textProtocolDetails.setStyleSheet(u"font: 10pt \"Cascadia Mono\";\n"
"background: transparent;\n"
"color: ;\n"
"color: rgb(130, 130, 130);\n"
"border: none;")

        self.verticalLayout_2.addWidget(self.textProtocolDetails)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout_5.addWidget(self.label_3)

        self.tableProtocolProgress = QTableView(self.centralwidget)
        self.tableProtocolProgress.setObjectName(u"tableProtocolProgress")
        self.tableProtocolProgress.setFont(font)
        self.tableProtocolProgress.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableProtocolProgress.setCornerButtonEnabled(False)

        self.verticalLayout_5.addWidget(self.tableProtocolProgress)


        self.horizontalLayout_3.addLayout(self.verticalLayout_5)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)

        PlutoFullAssessor.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(PlutoFullAssessor)
        self.statusbar.setObjectName(u"statusbar")
        font4 = QFont()
        font4.setFamilies([u"Cascadia Mono"])
        font4.setPointSize(11)
        self.statusbar.setFont(font4)
        PlutoFullAssessor.setStatusBar(self.statusbar)

        self.retranslateUi(PlutoFullAssessor)

        QMetaObject.connectSlotsByName(PlutoFullAssessor)
    # setupUi

    def retranslateUi(self, PlutoFullAssessor):
        PlutoFullAssessor.setWindowTitle(QCoreApplication.translate("PlutoFullAssessor", u"PLUTO Full Assessment", None))
#if QT_CONFIG(tooltip)
        self.pbCreateSeelectSubject.setToolTip(QCoreApplication.translate("PlutoFullAssessor", u"Select the subject to assess", None))
#endif // QT_CONFIG(tooltip)
        self.pbCreateSeelectSubject.setText(QCoreApplication.translate("PlutoFullAssessor", u"Create and Select Subject", None))
#if QT_CONFIG(tooltip)
        self.pbSelectSubject.setToolTip(QCoreApplication.translate("PlutoFullAssessor", u"Select the subject to assess", None))
#endif // QT_CONFIG(tooltip)
        self.pbSelectSubject.setText(QCoreApplication.translate("PlutoFullAssessor", u"Select Subject", None))
        self.lblSubjDetails.setText(QCoreApplication.translate("PlutoFullAssessor", u"TextLabel", None))
        self.lblLimb.setText(QCoreApplication.translate("PlutoFullAssessor", u"Limb:", None))
        self.cbLimb.setItemText(0, "")
        self.cbLimb.setItemText(1, QCoreApplication.translate("PlutoFullAssessor", u"Left", None))
        self.cbLimb.setItemText(2, QCoreApplication.translate("PlutoFullAssessor", u"Right", None))

        self.pbSetLimb.setText(QCoreApplication.translate("PlutoFullAssessor", u"Set Limb", None))
        self.gbMechanisms.setTitle(QCoreApplication.translate("PlutoFullAssessor", u"Mechanisms", None))
        self.pbFPS.setText(QCoreApplication.translate("PlutoFullAssessor", u"Forearm Pronation Supination", None))
        self.pbFPSSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbWFE.setText(QCoreApplication.translate("PlutoFullAssessor", u"Wrist Flexion/Extension", None))
        self.pbWFESkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbHOC.setText(QCoreApplication.translate("PlutoFullAssessor", u"Hand Opening/Closing", None))
        self.pbHOCSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbCalibrate.setText(QCoreApplication.translate("PlutoFullAssessor", u"Calibrate Mechanism", None))
#if QT_CONFIG(shortcut)
        self.pbCalibrate.setShortcut(QCoreApplication.translate("PlutoFullAssessor", u"Ctrl+S, Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.pbAROM.setText(QCoreApplication.translate("PlutoFullAssessor", u"Assess AROM", None))
        self.pbAROMSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbPROM.setText(QCoreApplication.translate("PlutoFullAssessor", u"Assess PROM", None))
        self.pbPROMSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbAPROMSlow.setText(QCoreApplication.translate("PlutoFullAssessor", u"Assisted Pasive ROM (Slow)", None))
        self.pbAPROMSlowSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbAPROMFast.setText(QCoreApplication.translate("PlutoFullAssessor", u"Assisted Pasive ROM (Fast)", None))
        self.pbAPROMFastSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbDiscReach.setText(QCoreApplication.translate("PlutoFullAssessor", u"Discrete Reaching", None))
        self.pbDiscReachSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbPosHold.setText(QCoreApplication.translate("PlutoFullAssessor", u"Position Hold", None))
        self.pbPosHoldSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbProp.setText(QCoreApplication.translate("PlutoFullAssessor", u"Proprioception", None))
        self.pbPropSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbForceCtrlLow.setText(QCoreApplication.translate("PlutoFullAssessor", u"Force Control (Low)", None))
        self.pbForceCtrlLowSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbForceCtrlMed.setText(QCoreApplication.translate("PlutoFullAssessor", u"Force Control (Med)", None))
        self.pbForceCtrlMedSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.pbForceCtrlHigh.setText(QCoreApplication.translate("PlutoFullAssessor", u"Force Control (High)", None))
        self.pbForceCtrlHighSkip.setText(QCoreApplication.translate("PlutoFullAssessor", u"X", None))
        self.label_4.setText(QCoreApplication.translate("PlutoFullAssessor", u"PLUTO Device Data", None))
        self.lblSessionInfo.setText("")
        self.label_3.setText(QCoreApplication.translate("PlutoFullAssessor", u"Assessment Protocol Progress", None))
    # retranslateUi


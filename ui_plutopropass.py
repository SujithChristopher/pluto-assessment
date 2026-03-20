# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutopropass.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QLayout, QMainWindow, QPushButton, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_PlutoPropAssessor(object):
    def setupUi(self, PlutoPropAssessor):
        if not PlutoPropAssessor.objectName():
            PlutoPropAssessor.setObjectName(u"PlutoPropAssessor")
        PlutoPropAssessor.resize(344, 241)
        PlutoPropAssessor.setMinimumSize(QSize(344, 241))
        PlutoPropAssessor.setMaximumSize(QSize(344, 241))
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(10)
        PlutoPropAssessor.setFont(font)
        self.centralwidget = QWidget(PlutoPropAssessor)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 321, 194))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.pbCalibration = QPushButton(self.verticalLayoutWidget)
        self.pbCalibration.setObjectName(u"pbCalibration")
        self.pbCalibration.setFont(font)

        self.verticalLayout.addWidget(self.pbCalibration)

        self.pbSubject = QPushButton(self.verticalLayoutWidget)
        self.pbSubject.setObjectName(u"pbSubject")
        self.pbSubject.setFont(font)

        self.verticalLayout.addWidget(self.pbSubject)

        self.pbTestDevice = QPushButton(self.verticalLayoutWidget)
        self.pbTestDevice.setObjectName(u"pbTestDevice")
        self.pbTestDevice.setFont(font)

        self.verticalLayout.addWidget(self.pbTestDevice)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.cbSubjectType = QComboBox(self.verticalLayoutWidget)
        self.cbSubjectType.addItem("")
        self.cbSubjectType.addItem("")
        self.cbSubjectType.addItem("")
        self.cbSubjectType.setObjectName(u"cbSubjectType")

        self.horizontalLayout.addWidget(self.cbSubjectType)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_2 = QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_2.addWidget(self.label_2)

        self.cbLimb = QComboBox(self.verticalLayoutWidget)
        self.cbLimb.addItem("")
        self.cbLimb.addItem("")
        self.cbLimb.addItem("")
        self.cbLimb.setObjectName(u"cbLimb")

        self.horizontalLayout_2.addWidget(self.cbLimb)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.verticalLayoutWidget)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.cbGripType = QComboBox(self.verticalLayoutWidget)
        self.cbGripType.addItem("")
        self.cbGripType.addItem("")
        self.cbGripType.addItem("")
        self.cbGripType.addItem("")
        self.cbGripType.setObjectName(u"cbGripType")

        self.horizontalLayout_3.addWidget(self.cbGripType)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.pbRomAssess = QPushButton(self.verticalLayoutWidget)
        self.pbRomAssess.setObjectName(u"pbRomAssess")
        self.pbRomAssess.setFont(font)

        self.verticalLayout.addWidget(self.pbRomAssess)

        self.pbPropAssessment = QPushButton(self.verticalLayoutWidget)
        self.pbPropAssessment.setObjectName(u"pbPropAssessment")
        self.pbPropAssessment.setFont(font)

        self.verticalLayout.addWidget(self.pbPropAssessment)

        PlutoPropAssessor.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(PlutoPropAssessor)
        self.statusbar.setObjectName(u"statusbar")
        font1 = QFont()
        font1.setFamilies([u"Cascadia Mono"])
        font1.setPointSize(9)
        self.statusbar.setFont(font1)
        PlutoPropAssessor.setStatusBar(self.statusbar)

        self.retranslateUi(PlutoPropAssessor)

        QMetaObject.connectSlotsByName(PlutoPropAssessor)
    # setupUi

    def retranslateUi(self, PlutoPropAssessor):
        PlutoPropAssessor.setWindowTitle(QCoreApplication.translate("PlutoPropAssessor", u"PLUTO Proprioception Assessment", None))
        self.pbCalibration.setText(QCoreApplication.translate("PlutoPropAssessor", u"Calibrate PLUTO", None))
#if QT_CONFIG(tooltip)
        self.pbSubject.setToolTip(QCoreApplication.translate("PlutoPropAssessor", u"Select the subject to assess", None))
#endif // QT_CONFIG(tooltip)
        self.pbSubject.setText(QCoreApplication.translate("PlutoPropAssessor", u"Select Subject", None))
        self.pbTestDevice.setText(QCoreApplication.translate("PlutoPropAssessor", u"Test Device", None))
        self.label.setText(QCoreApplication.translate("PlutoPropAssessor", u"Subject Type:", None))
        self.cbSubjectType.setItemText(0, "")
        self.cbSubjectType.setItemText(1, QCoreApplication.translate("PlutoPropAssessor", u"Healthy", None))
        self.cbSubjectType.setItemText(2, QCoreApplication.translate("PlutoPropAssessor", u"Stroke", None))

        self.label_2.setText(QCoreApplication.translate("PlutoPropAssessor", u"Limb:", None))
        self.cbLimb.setItemText(0, "")
        self.cbLimb.setItemText(1, QCoreApplication.translate("PlutoPropAssessor", u"Left", None))
        self.cbLimb.setItemText(2, QCoreApplication.translate("PlutoPropAssessor", u"Right", None))

        self.label_3.setText(QCoreApplication.translate("PlutoPropAssessor", u"Grip Type:", None))
        self.cbGripType.setItemText(0, "")
        self.cbGripType.setItemText(1, QCoreApplication.translate("PlutoPropAssessor", u"Gross", None))
        self.cbGripType.setItemText(2, QCoreApplication.translate("PlutoPropAssessor", u"Pinch", None))
        self.cbGripType.setItemText(3, QCoreApplication.translate("PlutoPropAssessor", u"Three Finger", None))

        self.pbRomAssess.setText(QCoreApplication.translate("PlutoPropAssessor", u"Assess ROM", None))
#if QT_CONFIG(shortcut)
        self.pbRomAssess.setShortcut(QCoreApplication.translate("PlutoPropAssessor", u"Ctrl+S, Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.pbPropAssessment.setText(QCoreApplication.translate("PlutoPropAssessor", u"Proprioception Assessment", None))
    # retranslateUi


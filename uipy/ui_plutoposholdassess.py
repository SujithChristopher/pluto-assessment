# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutoposholdassess.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGraphicsView, QHBoxLayout,
    QLabel, QMainWindow, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PosHoldAssessWindow(object):
    def setupUi(self, PosHoldAssessWindow):
        if not PosHoldAssessWindow.objectName():
            PosHoldAssessWindow.setObjectName(u"PosHoldAssessWindow")
        PosHoldAssessWindow.resize(522, 451)
        PosHoldAssessWindow.setMinimumSize(QSize(522, 451))
        PosHoldAssessWindow.setMaximumSize(QSize(522, 451))
        font = QFont()
        font.setFamilies([u"Cascadia Mono Light"])
        PosHoldAssessWindow.setFont(font)
        self.centralwidget = QWidget(PosHoldAssessWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.lblTitle = QLabel(self.centralwidget)
        self.lblTitle.setObjectName(u"lblTitle")
        font1 = QFont()
        font1.setFamilies([u"Cascadia Mono Light"])
        font1.setPointSize(12)
        self.lblTitle.setFont(font1)
        self.lblTitle.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.horizontalLayout.addWidget(self.lblTitle)

        self.cbTrialRun = QCheckBox(self.centralwidget)
        self.cbTrialRun.setObjectName(u"cbTrialRun")
        self.cbTrialRun.setMaximumSize(QSize(90, 16777215))
        font2 = QFont()
        font2.setFamilies([u"Cascadia Mono Light"])
        font2.setPointSize(10)
        self.cbTrialRun.setFont(font2)
        self.cbTrialRun.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.horizontalLayout.addWidget(self.cbTrialRun)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.hocGraph = QGraphicsView(self.centralwidget)
        self.hocGraph.setObjectName(u"hocGraph")
        self.hocGraph.setMaximumSize(QSize(500, 375))

        self.verticalLayout.addWidget(self.hocGraph)

        self.lblStatus = QLabel(self.centralwidget)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setFont(font2)

        self.verticalLayout.addWidget(self.lblStatus)

        PosHoldAssessWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(PosHoldAssessWindow)

        QMetaObject.connectSlotsByName(PosHoldAssessWindow)
    # setupUi

    def retranslateUi(self, PosHoldAssessWindow):
        PosHoldAssessWindow.setWindowTitle(QCoreApplication.translate("PosHoldAssessWindow", u"Position Hold Assessment", None))
        self.lblTitle.setText(QCoreApplication.translate("PosHoldAssessWindow", u"PLUTO ROM Assessment", None))
        self.cbTrialRun.setText(QCoreApplication.translate("PosHoldAssessWindow", u"Trial Run", None))
        self.lblStatus.setText(QCoreApplication.translate("PosHoldAssessWindow", u"TextLabel", None))
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutoromassess.ui'
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
from PySide6.QtWidgets import (QApplication, QGraphicsView, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QStatusBar,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_RomAssessWindow(object):
    def setupUi(self, RomAssessWindow):
        if not RomAssessWindow.objectName():
            RomAssessWindow.setObjectName(u"RomAssessWindow")
        RomAssessWindow.resize(751, 329)
        self.centralwidget = QWidget(RomAssessWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 731, 291))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.verticalLayout.addWidget(self.label)

        self.hocGraph = QGraphicsView(self.verticalLayoutWidget)
        self.hocGraph.setObjectName(u"hocGraph")

        self.verticalLayout.addWidget(self.hocGraph)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pbArom = QPushButton(self.verticalLayoutWidget)
        self.pbArom.setObjectName(u"pbArom")
        font1 = QFont()
        font1.setFamilies([u"Bahnschrift Light"])
        font1.setPointSize(10)
        self.pbArom.setFont(font1)

        self.horizontalLayout_2.addWidget(self.pbArom)

        self.pbProm = QPushButton(self.verticalLayoutWidget)
        self.pbProm.setObjectName(u"pbProm")
        self.pbProm.setFont(font1)

        self.horizontalLayout_2.addWidget(self.pbProm)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.textInstruction = QTextEdit(self.verticalLayoutWidget)
        self.textInstruction.setObjectName(u"textInstruction")
        self.textInstruction.setEnabled(False)
        self.textInstruction.setMinimumSize(QSize(729, 71))
        self.textInstruction.setMaximumSize(QSize(729, 71))
        self.textInstruction.setFont(font)
        self.textInstruction.setStyleSheet(u"color: rgb(0, 0, 127);\n"
"background-color: rgb(240, 240, 240);")

        self.verticalLayout.addWidget(self.textInstruction)

        RomAssessWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(RomAssessWindow)
        self.statusbar.setObjectName(u"statusbar")
        RomAssessWindow.setStatusBar(self.statusbar)

        self.retranslateUi(RomAssessWindow)

        QMetaObject.connectSlotsByName(RomAssessWindow)
    # setupUi

    def retranslateUi(self, RomAssessWindow):
        RomAssessWindow.setWindowTitle(QCoreApplication.translate("RomAssessWindow", u"PLUTO ROM Assessment", None))
        self.label.setText(QCoreApplication.translate("RomAssessWindow", u"PLUTO ROM Assessment", None))
        self.pbArom.setText(QCoreApplication.translate("RomAssessWindow", u"Assess AROM", None))
        self.pbProm.setText(QCoreApplication.translate("RomAssessWindow", u"Assess PROM", None))
    # retranslateUi


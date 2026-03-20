# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutocalib.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_CalibrationWindow(object):
    def setupUi(self, CalibrationWindow):
        if not CalibrationWindow.objectName():
            CalibrationWindow.setObjectName(u"CalibrationWindow")
        CalibrationWindow.resize(451, 90)
        CalibrationWindow.setMinimumSize(QSize(451, 90))
        CalibrationWindow.setMaximumSize(QSize(451, 90))
        self.centralwidget = QWidget(CalibrationWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 431, 73))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.lblInstruction = QLabel(self.verticalLayoutWidget)
        self.lblInstruction.setObjectName(u"lblInstruction")
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(12)
        self.lblInstruction.setFont(font)

        self.verticalLayout.addWidget(self.lblInstruction)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lblInstruction_2 = QLabel(self.verticalLayoutWidget)
        self.lblInstruction_2.setObjectName(u"lblInstruction_2")
        self.lblInstruction_2.setFont(font)
        self.lblInstruction_2.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.horizontalLayout.addWidget(self.lblInstruction_2)

        self.lblCalibStatus = QLabel(self.verticalLayoutWidget)
        self.lblCalibStatus.setObjectName(u"lblCalibStatus")
        self.lblCalibStatus.setFont(font)

        self.horizontalLayout.addWidget(self.lblCalibStatus)

        self.lblPositionTitle = QLabel(self.verticalLayoutWidget)
        self.lblPositionTitle.setObjectName(u"lblPositionTitle")
        self.lblPositionTitle.setFont(font)
        self.lblPositionTitle.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.horizontalLayout.addWidget(self.lblPositionTitle)

        self.lblPositionDisplay = QLabel(self.verticalLayoutWidget)
        self.lblPositionDisplay.setObjectName(u"lblPositionDisplay")
        self.lblPositionDisplay.setFont(font)

        self.horizontalLayout.addWidget(self.lblPositionDisplay)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.lblInstruction2 = QLabel(self.verticalLayoutWidget)
        self.lblInstruction2.setObjectName(u"lblInstruction2")
        self.lblInstruction2.setFont(font)
        self.lblInstruction2.setStyleSheet(u"color: rgb(0, 0, 127);")
        self.lblInstruction2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.lblInstruction2)

        CalibrationWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(CalibrationWindow)

        QMetaObject.connectSlotsByName(CalibrationWindow)
    # setupUi

    def retranslateUi(self, CalibrationWindow):
        CalibrationWindow.setWindowTitle(QCoreApplication.translate("CalibrationWindow", u"MainWindow", None))
        self.lblInstruction.setText(QCoreApplication.translate("CalibrationWindow", u"Bring the two handles together and press the PLUTO Button", None))
        self.lblInstruction_2.setText(QCoreApplication.translate("CalibrationWindow", u"Calibration:", None))
        self.lblCalibStatus.setText("")
        self.lblPositionTitle.setText(QCoreApplication.translate("CalibrationWindow", u"Handle Distance:", None))
        self.lblPositionDisplay.setText("")
        self.lblInstruction2.setText("")
    # retranslateUi


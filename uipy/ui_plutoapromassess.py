# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutoapromassess.ui'
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

class Ui_APRomAssessWindow(object):
    def setupUi(self, APRomAssessWindow):
        if not APRomAssessWindow.objectName():
            APRomAssessWindow.setObjectName(u"APRomAssessWindow")
        APRomAssessWindow.resize(751, 329)
        font = QFont()
        font.setFamilies([u"Cascadia Mono Light"])
        APRomAssessWindow.setFont(font)
        self.centralwidget = QWidget(APRomAssessWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 731, 311))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.lblTitle = QLabel(self.verticalLayoutWidget)
        self.lblTitle.setObjectName(u"lblTitle")
        font1 = QFont()
        font1.setFamilies([u"Cascadia Mono Light"])
        font1.setPointSize(12)
        self.lblTitle.setFont(font1)
        self.lblTitle.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.horizontalLayout.addWidget(self.lblTitle)

        self.cbTrialRun = QCheckBox(self.verticalLayoutWidget)
        self.cbTrialRun.setObjectName(u"cbTrialRun")
        self.cbTrialRun.setMaximumSize(QSize(90, 16777215))
        font2 = QFont()
        font2.setFamilies([u"Cascadia Mono Light"])
        font2.setPointSize(10)
        self.cbTrialRun.setFont(font2)
        self.cbTrialRun.setStyleSheet(u"color: rgb(170, 0, 0);")

        self.horizontalLayout.addWidget(self.cbTrialRun)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.hocGraph = QGraphicsView(self.verticalLayoutWidget)
        self.hocGraph.setObjectName(u"hocGraph")

        self.verticalLayout.addWidget(self.hocGraph)

        self.lblStatus = QLabel(self.verticalLayoutWidget)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setFont(font2)

        self.verticalLayout.addWidget(self.lblStatus)

        APRomAssessWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(APRomAssessWindow)

        QMetaObject.connectSlotsByName(APRomAssessWindow)
    # setupUi

    def retranslateUi(self, APRomAssessWindow):
        APRomAssessWindow.setWindowTitle(QCoreApplication.translate("APRomAssessWindow", u"PLUTO A/P/AP ROM Assessment", None))
        self.lblTitle.setText(QCoreApplication.translate("APRomAssessWindow", u"PLUTO ROM Assessment", None))
        self.cbTrialRun.setText(QCoreApplication.translate("APRomAssessWindow", u"Trial Run", None))
        self.lblStatus.setText(QCoreApplication.translate("APRomAssessWindow", u"TextLabel", None))
    # retranslateUi


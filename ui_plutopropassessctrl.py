# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutopropassessctrl.ui'
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
    QLabel, QMainWindow, QPushButton, QSizePolicy,
    QStatusBar, QTextEdit, QVBoxLayout, QWidget)

class Ui_ProprioceptionAssessWindow(object):
    def setupUi(self, ProprioceptionAssessWindow):
        if not ProprioceptionAssessWindow.objectName():
            ProprioceptionAssessWindow.setObjectName(u"ProprioceptionAssessWindow")
        ProprioceptionAssessWindow.resize(751, 429)
        ProprioceptionAssessWindow.setMinimumSize(QSize(751, 429))
        ProprioceptionAssessWindow.setMaximumSize(QSize(751, 429))
        self.centralwidget = QWidget(ProprioceptionAssessWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 731, 391))
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
        self.pbStartStopProtocol = QPushButton(self.verticalLayoutWidget)
        self.pbStartStopProtocol.setObjectName(u"pbStartStopProtocol")
        self.pbStartStopProtocol.setFont(font)

        self.horizontalLayout_2.addWidget(self.pbStartStopProtocol)

        self.checkBoxPauseProtocol = QCheckBox(self.verticalLayoutWidget)
        self.checkBoxPauseProtocol.setObjectName(u"checkBoxPauseProtocol")
        self.checkBoxPauseProtocol.setFont(font)

        self.horizontalLayout_2.addWidget(self.checkBoxPauseProtocol)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.textInformation = QTextEdit(self.verticalLayoutWidget)
        self.textInformation.setObjectName(u"textInformation")
        self.textInformation.setEnabled(False)
        self.textInformation.setMinimumSize(QSize(729, 71))
        self.textInformation.setMaximumSize(QSize(729, 120))
        font1 = QFont()
        font1.setFamilies([u"Cascadia Mono"])
        font1.setPointSize(8)
        font1.setBold(False)
        font1.setItalic(False)
        self.textInformation.setFont(font1)
        self.textInformation.setStyleSheet(u"color: rgb(85, 255, 0);\n"
"background-color: rgb(0, 0, 0);\n"
"font: 8pt \"Cascadia Mono\";")

        self.verticalLayout.addWidget(self.textInformation)

        ProprioceptionAssessWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(ProprioceptionAssessWindow)
        self.statusbar.setObjectName(u"statusbar")
        ProprioceptionAssessWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ProprioceptionAssessWindow)

        QMetaObject.connectSlotsByName(ProprioceptionAssessWindow)
    # setupUi

    def retranslateUi(self, ProprioceptionAssessWindow):
        ProprioceptionAssessWindow.setWindowTitle(QCoreApplication.translate("ProprioceptionAssessWindow", u"PLUTO Proprioception Assessment Control Window", None))
        self.label.setText(QCoreApplication.translate("ProprioceptionAssessWindow", u"PLUTO Proprioception Assessment", None))
        self.pbStartStopProtocol.setText(QCoreApplication.translate("ProprioceptionAssessWindow", u"Start Protocol", None))
        self.checkBoxPauseProtocol.setText(QCoreApplication.translate("ProprioceptionAssessWindow", u"Pause Protocol", None))
    # retranslateUi


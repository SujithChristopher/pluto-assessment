# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutopropvis.ui'
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
    QSpacerItem, QStatusBar, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_PropriceptionAssessmentWindow(object):
    def setupUi(self, PropriceptionAssessmentWindow):
        if not PropriceptionAssessmentWindow.objectName():
            PropriceptionAssessmentWindow.setObjectName(u"PropriceptionAssessmentWindow")
        PropriceptionAssessmentWindow.setWindowModality(Qt.NonModal)
        PropriceptionAssessmentWindow.resize(820, 417)
        PropriceptionAssessmentWindow.setMinimumSize(QSize(820, 417))
        PropriceptionAssessmentWindow.setMaximumSize(QSize(820, 417))
        self.centralwidget = QWidget(PropriceptionAssessmentWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 801, 381))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.hocGraph = QGraphicsView(self.verticalLayoutWidget)
        self.hocGraph.setObjectName(u"hocGraph")

        self.verticalLayout.addWidget(self.hocGraph)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.pdStartStopProtocol = QPushButton(self.verticalLayoutWidget)
        self.pdStartStopProtocol.setObjectName(u"pdStartStopProtocol")
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(12)
        self.pdStartStopProtocol.setFont(font)

        self.horizontalLayout_3.addWidget(self.pdStartStopProtocol)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.checkBoxPauseProtocol = QCheckBox(self.verticalLayoutWidget)
        self.checkBoxPauseProtocol.setObjectName(u"checkBoxPauseProtocol")
        self.checkBoxPauseProtocol.setFont(font)

        self.horizontalLayout_3.addWidget(self.checkBoxPauseProtocol)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.lblInformation = QLabel(self.verticalLayoutWidget)
        self.lblInformation.setObjectName(u"lblInformation")
        self.lblInformation.setFont(font)

        self.verticalLayout.addWidget(self.lblInformation)

        self.textDetails = QTextEdit(self.verticalLayoutWidget)
        self.textDetails.setObjectName(u"textDetails")
        self.textDetails.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout.addWidget(self.textDetails)

        PropriceptionAssessmentWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(PropriceptionAssessmentWindow)
        self.statusbar.setObjectName(u"statusbar")
        PropriceptionAssessmentWindow.setStatusBar(self.statusbar)

        self.retranslateUi(PropriceptionAssessmentWindow)

        QMetaObject.connectSlotsByName(PropriceptionAssessmentWindow)
    # setupUi

    def retranslateUi(self, PropriceptionAssessmentWindow):
        PropriceptionAssessmentWindow.setWindowTitle(QCoreApplication.translate("PropriceptionAssessmentWindow", u"Proprioception Assessment Control Window", None))
        self.pdStartStopProtocol.setText(QCoreApplication.translate("PropriceptionAssessmentWindow", u"Start Assessment Protocol", None))
        self.checkBoxPauseProtocol.setText(QCoreApplication.translate("PropriceptionAssessmentWindow", u"Pause Assessment Protocol", None))
        self.lblInformation.setText(QCoreApplication.translate("PropriceptionAssessmentWindow", u"TextLabel", None))
    # retranslateUi


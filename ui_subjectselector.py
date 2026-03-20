# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'subjectselector.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PlutoSubjectSelectorWindow(object):
    def setupUi(self, PlutoSubjectSelectorWindow):
        if not PlutoSubjectSelectorWindow.objectName():
            PlutoSubjectSelectorWindow.setObjectName(u"PlutoSubjectSelectorWindow")
        PlutoSubjectSelectorWindow.resize(321, 78)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PlutoSubjectSelectorWindow.sizePolicy().hasHeightForWidth())
        PlutoSubjectSelectorWindow.setSizePolicy(sizePolicy)
        PlutoSubjectSelectorWindow.setMinimumSize(QSize(321, 78))
        PlutoSubjectSelectorWindow.setMaximumSize(QSize(321, 78))
        self.centralwidget = QWidget(PlutoSubjectSelectorWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setFamilies([u"Bahnschrift Light"])
        font.setPointSize(10)
        self.label.setFont(font)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.cbSubjID = QComboBox(self.centralwidget)
        self.cbSubjID.setObjectName(u"cbSubjID")
        self.cbSubjID.setFont(font)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.cbSubjID)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.pbSelect = QPushButton(self.centralwidget)
        self.pbSelect.setObjectName(u"pbSelect")
        self.pbSelect.setFont(font)

        self.verticalLayout.addWidget(self.pbSelect)

        PlutoSubjectSelectorWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(PlutoSubjectSelectorWindow)

        QMetaObject.connectSlotsByName(PlutoSubjectSelectorWindow)
    # setupUi

    def retranslateUi(self, PlutoSubjectSelectorWindow):
        PlutoSubjectSelectorWindow.setWindowTitle(QCoreApplication.translate("PlutoSubjectSelectorWindow", u"PLUTO Full Assessment Subject Selector", None))
        self.label.setText(QCoreApplication.translate("PlutoSubjectSelectorWindow", u"Subject ID: ", None))
        self.pbSelect.setText(QCoreApplication.translate("PlutoSubjectSelectorWindow", u"Select Subject", None))
    # retranslateUi


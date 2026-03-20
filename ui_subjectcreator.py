# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'subjectcreator.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_PlutoSubjectCreatorWindow(object):
    def setupUi(self, PlutoSubjectCreatorWindow):
        if not PlutoSubjectCreatorWindow.objectName():
            PlutoSubjectCreatorWindow.setObjectName(u"PlutoSubjectCreatorWindow")
        PlutoSubjectCreatorWindow.resize(310, 161)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PlutoSubjectCreatorWindow.sizePolicy().hasHeightForWidth())
        PlutoSubjectCreatorWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(PlutoSubjectCreatorWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 291, 142))
        font = QFont()
        font.setPointSize(10)
        self.verticalLayoutWidget.setFont(font)
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label = QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setFamilies([u"Bahnschrift Light"])
        font1.setPointSize(10)
        self.label.setFont(font1)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.textSubjID = QLineEdit(self.verticalLayoutWidget)
        self.textSubjID.setObjectName(u"textSubjID")
        self.textSubjID.setFont(font1)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.textSubjID)

        self.label_2 = QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font1)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.cbSubjType = QComboBox(self.verticalLayoutWidget)
        self.cbSubjType.addItem("")
        self.cbSubjType.addItem("")
        self.cbSubjType.setObjectName(u"cbSubjType")
        self.cbSubjType.setFont(font1)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cbSubjType)

        self.label_3 = QLabel(self.verticalLayoutWidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font1)

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.cbDomLimb = QComboBox(self.verticalLayoutWidget)
        self.cbDomLimb.addItem("")
        self.cbDomLimb.addItem("")
        self.cbDomLimb.setObjectName(u"cbDomLimb")
        self.cbDomLimb.setFont(font1)

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.cbDomLimb)

        self.label_4 = QLabel(self.verticalLayoutWidget)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font1)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.cbAffLimb = QComboBox(self.verticalLayoutWidget)
        self.cbAffLimb.addItem("")
        self.cbAffLimb.addItem("")
        self.cbAffLimb.setObjectName(u"cbAffLimb")
        self.cbAffLimb.setFont(font1)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.cbAffLimb)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pbCreate = QPushButton(self.verticalLayoutWidget)
        self.pbCreate.setObjectName(u"pbCreate")
        self.pbCreate.setFont(font1)

        self.horizontalLayout.addWidget(self.pbCreate)

        self.pbCancel = QPushButton(self.verticalLayoutWidget)
        self.pbCancel.setObjectName(u"pbCancel")
        self.pbCancel.setFont(font1)

        self.horizontalLayout.addWidget(self.pbCancel)


        self.verticalLayout.addLayout(self.horizontalLayout)

        PlutoSubjectCreatorWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(PlutoSubjectCreatorWindow)

        QMetaObject.connectSlotsByName(PlutoSubjectCreatorWindow)
    # setupUi

    def retranslateUi(self, PlutoSubjectCreatorWindow):
        PlutoSubjectCreatorWindow.setWindowTitle(QCoreApplication.translate("PlutoSubjectCreatorWindow", u"PLUTO Full Assessment Subject Creator", None))
        self.label.setText(QCoreApplication.translate("PlutoSubjectCreatorWindow", u"Subject ID: ", None))
        self.label_2.setText(QCoreApplication.translate("PlutoSubjectCreatorWindow", u"Subject Type:", None))
        self.cbSubjType.setItemText(0, QCoreApplication.translate("PlutoSubjectCreatorWindow", u"HEALTHY", None))
        self.cbSubjType.setItemText(1, QCoreApplication.translate("PlutoSubjectCreatorWindow", u"STROKE", None))

        self.label_3.setText(QCoreApplication.translate("PlutoSubjectCreatorWindow", u"Dominant Side:", None))
        self.cbDomLimb.setItemText(0, QCoreApplication.translate("PlutoSubjectCreatorWindow", u"LEFT", None))
        self.cbDomLimb.setItemText(1, QCoreApplication.translate("PlutoSubjectCreatorWindow", u"RIGHT", None))

        self.label_4.setText(QCoreApplication.translate("PlutoSubjectCreatorWindow", u"Affected Side:", None))
        self.cbAffLimb.setItemText(0, QCoreApplication.translate("PlutoSubjectCreatorWindow", u"LEFT", None))
        self.cbAffLimb.setItemText(1, QCoreApplication.translate("PlutoSubjectCreatorWindow", u"RIGHT", None))

        self.pbCreate.setText(QCoreApplication.translate("PlutoSubjectCreatorWindow", u"Create", None))
        self.pbCancel.setText(QCoreApplication.translate("PlutoSubjectCreatorWindow", u"Cancel", None))
    # retranslateUi


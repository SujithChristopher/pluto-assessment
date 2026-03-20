# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plutodataview.ui'
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
from PySide6.QtWidgets import (QApplication, QMainWindow, QSizePolicy, QTextEdit,
    QWidget)

class Ui_DevDataWindow(object):
    def setupUi(self, DevDataWindow):
        if not DevDataWindow.objectName():
            DevDataWindow.setObjectName(u"DevDataWindow")
        DevDataWindow.setEnabled(False)
        DevDataWindow.resize(500, 420)
        DevDataWindow.setMinimumSize(QSize(500, 420))
        DevDataWindow.setMaximumSize(QSize(500, 420))
        self.centralwidget = QWidget(DevDataWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.textDevData = QTextEdit(self.centralwidget)
        self.textDevData.setObjectName(u"textDevData")
        self.textDevData.setEnabled(False)
        self.textDevData.setGeometry(QRect(10, 10, 481, 401))
        font = QFont()
        font.setFamilies([u"Cascadia Mono"])
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        self.textDevData.setFont(font)
        self.textDevData.setStyleSheet(u"background-color: rgb(0, 0, 0);\n"
"color: rgb(0, 255, 60);\n"
"font: 10pt \"Cascadia Mono\";")
        DevDataWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(DevDataWindow)

        QMetaObject.connectSlotsByName(DevDataWindow)
    # setupUi

    def retranslateUi(self, DevDataWindow):
        DevDataWindow.setWindowTitle(QCoreApplication.translate("DevDataWindow", u"PLUTO Data Window", None))
        self.textDevData.setMarkdown("")
        self.textDevData.setHtml(QCoreApplication.translate("DevDataWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Cascadia Mono'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'Space Mono';\"><br /></p></body></html>", None))
    # retranslateUi


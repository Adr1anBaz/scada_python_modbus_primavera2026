# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'horner_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 300)
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(50, 10, 91, 31))
        self.ledQ10 = QLabel(Form)
        self.ledQ10.setObjectName(u"ledQ10")
        self.ledQ10.setGeometry(QRect(50, 40, 91, 31))
        self.ledQ10.setStyleSheet(u"background-color: red;\n"
"color: white;\n"
"font-weight: bold;\n"
"border-radius: 10px;\n"
"min-height: 24px;")
        self.btnT1Momentary = QPushButton(Form)
        self.btnT1Momentary.setObjectName(u"btnT1Momentary")
        self.btnT1Momentary.setGeometry(QRect(40, 80, 131, 26))
        self.ledQ10_2 = QLabel(Form)
        self.ledQ10_2.setObjectName(u"ledQ10_2")
        self.ledQ10_2.setGeometry(QRect(50, 120, 91, 31))
        self.lblR1Value = QLabel(Form)
        self.lblR1Value.setObjectName(u"lblR1Value")
        self.lblR1Value.setGeometry(QRect(50, 150, 91, 31))
        self.inputR1 = QLineEdit(Form)
        self.inputR1.setObjectName(u"inputR1")
        self.inputR1.setGeometry(QRect(210, 70, 113, 26))
        self.btnWriteR1 = QPushButton(Form)
        self.btnWriteR1.setObjectName(u"btnWriteR1")
        self.btnWriteR1.setGeometry(QRect(220, 110, 81, 26))
        self.btnReadR1 = QPushButton(Form)
        self.btnReadR1.setObjectName(u"btnReadR1")
        self.btnReadR1.setGeometry(QRect(220, 150, 81, 26))

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"Estado Q10", None))
        self.ledQ10.setText(QCoreApplication.translate("Form", u"OFF", None))
        self.btnT1Momentary.setText(QCoreApplication.translate("Form", u"T1 moment\u00e1neo", None))
        self.ledQ10_2.setText(QCoreApplication.translate("Form", u"Valor R1", None))
        self.lblR1Value.setText(QCoreApplication.translate("Form", u"desconocido", None))
        self.btnWriteR1.setText(QCoreApplication.translate("Form", u"Escribir R1", None))
        self.btnReadR1.setText(QCoreApplication.translate("Form", u"Leer R1", None))
    # retranslateUi


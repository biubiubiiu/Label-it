# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\author_info.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(722, 575)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/svg/qt.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        Form.setWindowIcon(icon)
        self.label_6 = QtWidgets.QLabel(Form)
        self.label_6.setGeometry(QtCore.QRect(320, 30, 381, 411))
        self.label_6.setText("")
        self.label_6.setPixmap(QtGui.QPixmap(":/jpg/author.jpg"))
        self.label_6.setObjectName("label_6")
        self.label_9 = QtWidgets.QLabel(Form)
        self.label_9.setGeometry(QtCore.QRect(30, 290, 241, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift Light")
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.label_7 = QtWidgets.QLabel(Form)
        self.label_7.setGeometry(QtCore.QRect(30, 170, 251, 41))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift Light")
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(Form)
        self.label_8.setGeometry(QtCore.QRect(30, 230, 241, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift Light")
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.label_11 = QtWidgets.QLabel(Form)
        self.label_11.setGeometry(QtCore.QRect(30, 470, 351, 41))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift Light")
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_9.setText(_translate("Form", "Id:            U201716998"))
        self.label_7.setText(_translate("Form", "Author:  Raymond Wong"))
        self.label_8.setText(_translate("Form", "Class:    1702"))
        self.label_11.setText(_translate("Form", "Description:   2019年秋 数字图像处理大作业"))
import img_rc

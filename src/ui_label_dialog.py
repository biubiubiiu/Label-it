# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\set_label_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog_set_label(object):
    def setupUi(self, Dialog_set_label):
        Dialog_set_label.setObjectName("Dialog_set_label")
        Dialog_set_label.resize(300, 298)
        self.widget = QtWidgets.QWidget(Dialog_set_label)
        self.widget.setGeometry(QtCore.QRect(10, 16, 281, 271))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.widget)
        self.lineEdit.setObjectName("lineEdit")
        self.verticalLayout.addWidget(self.lineEdit)
        self.listWidget = QtWidgets.QListWidget(self.widget)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.widget)
        self.buttonBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.buttonBox.setAutoFillBackground(False)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog_set_label)
        self.buttonBox.accepted.connect(Dialog_set_label.accept)
        self.buttonBox.rejected.connect(Dialog_set_label.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog_set_label)

    def retranslateUi(self, Dialog_set_label):
        _translate = QtCore.QCoreApplication.translate
        Dialog_set_label.setWindowTitle(_translate("Dialog_set_label", "Dialog"))
        self.lineEdit.setPlaceholderText(_translate("Dialog_set_label", "Enter object label"))

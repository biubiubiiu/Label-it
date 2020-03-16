from ui_label_dialog import Ui_Dialog_set_label
from PyQt5.QtWidgets import QDialog, QToolTip


class LabelDialog(QDialog, Ui_Dialog_set_label):

    def __init__(self, parent=None, labels=[]):
        super(LabelDialog, self).__init__(parent)
        self.setupUi(self)
        self.updateUi()
        if labels:
            self.listWidget.addItems(labels)

    def updateUi(self):
        self.initSignal()

    def initSignal(self):
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.listWidget.currentItemChanged.connect(self.labelSelected)

    def labelSelected(self, item):
        self.lineEdit.setText(item.text())

    def accept(self):
        text = self.lineEdit.text().strip()
        if text:
            super().accept()
        else:
            QToolTip.showText(self.lineEdit, 'label name must not be empty')

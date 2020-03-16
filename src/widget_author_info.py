from ui_author_info import Ui_Form
from PyQt5.QtWidgets import QWidget


class AuthorWidget(QWidget, Ui_Form):

    def __init__(self, parent=None, labels=[]):
        super(AuthorWidget, self).__init__(parent)
        self.setupUi(self)

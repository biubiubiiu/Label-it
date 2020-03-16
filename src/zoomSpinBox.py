from PyQt5.QtGui import QFontMetrics
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QSpinBox, QAbstractSpinBox


class zoomSpinBox(QSpinBox):

    def __init__(self, value=100):
        super(zoomSpinBox, self).__init__()
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setRange(1, 500)
        self.setSuffix(' %')
        self.setValue(value)
        self.setToolTip(u'Zoom Level')
        self.setStatusTip(self.toolTip())
        self.setAlignment(Qt.AlignCenter)
        self.setInputMethodHints(Qt.ImhDigitsOnly)
        self.setAttribute(Qt.WA_InputMethodEnabled, False)

    def minimumSizeHint(self):
        height = super(zoomSpinBox, self).minimumSizeHint().height()
        fm = QFontMetrics(self.font())
        width = fm.width(str(self.maximum()))
        return QSize(width, height)

# -*- coding: utf-8 -*-

"""
图像标注软件
2019年秋 数字图像处理课程大作业

author: Raymond Wong
created on: 2019.12.19
last edited: 2019.12.28
"""

import sys
from PyQt5.QtWidgets import QApplication
import window


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = window.MainWindow()
    main.show()
    sys.exit(app.exec_())

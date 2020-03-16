from ui_mainwindow import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QListWidgetItem
from PyQt5.QtGui import QImageReader, QPixmap
from PyQt5.QtCore import Qt, QFile
import os

from enum import Enum
from zoomSpinBox import zoomSpinBox
from label_dialog import LabelDialog
from widget_author_info import AuthorWidget
from tools import getImageData, saveJsonFile, loadJsonFile, json_to_dataset


class zoomMode(Enum):
    FIT_WINDOW = 0
    FIT_WIDTH = 1
    MANUAL_ZOOM = 2


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.updateUi()
        self.dirty = False
        self.filename = ''      # 记录当前正在处理图像的文件名
        self.image = None       # 记录当前正在处理的源图像 类型为QImage
        self.zoomMode = zoomMode.FIT_WINDOW
        self.initAction()

        # 保存label与shape之间的对应关系
        # example: {'label1':[shape1, shape2], 'label2':[shape3], ...}
        self.itemToShapes = {}

    def initAction(self):
        '''
        初始化各个action的状态
        '''
        self.actionCreate_Rectangle.setEnabled(False)
        self.actionCreate_Polygons.setEnabled(False)
        self.actionCreate_Circle.setEnabled(False)
        # TODO 继续完善

    def initSignal(self):
        # Toolbar 部分
        self.actionClose.triggered.connect(self.closeFile)  # 关闭文件
        self.actionQuit.triggered.connect(self.close)   # 退出
        self.actionOpen.triggered.connect(
            self.openFile)  # 打开文件
        self.actionOpen_Dir.triggered.connect(
            self.openDir)   # 打开文件夹

        self.actionCreate_Polygons.triggered.connect(
            lambda: self.toggleDrawMode(False, 'polygon'))  # 创建多边形区域
        self.actionCreate_Circle.triggered.connect(
            lambda: self.toggleDrawMode(False, 'circle'))   # 创建矩形区域
        self.actionCreate_Rectangle.triggered.connect(
            lambda: self.toggleDrawMode(False, 'rectangle'))    # 创建圆形区域

        self.actionEdit_Polygon.triggered.connect(
            lambda: self.toggleDrawMode(True))  # 切换至编辑状态
        self.actionDelete_Polygon.triggered.connect(
            self.deleteSelectedShape)   # 删除一个区域
        self.actionDuplicate_Polygon.triggered.connect(
            self.copySelectedShape)  # 复制一个区域

        self.actionSave.triggered.connect(lambda: self.saveFile(True))  # 保存
        self.actionSave_as.triggered.connect(
            lambda: self.saveFile(False))  # 另存为
        self.actionFit_Window.triggered.connect(
            lambda: self.changeZoomMode(zoomMode.FIT_WINDOW))   # 根据窗口大小适配
        self.actionFit_Width.triggered.connect(
            lambda: self.changeZoomMode(zoomMode.FIT_WIDTH))    # 根据宽度适配

        self.actionZoom_in.triggered.connect(lambda: self.zoom(True))   # 放大
        self.actionZoom_out.triggered.connect(lambda: self.zoom(False))  # 缩小
        self.spinbox_scale.valueChanged.connect(self.paintCanvas)   # 调整放缩比利

        self.actionNext_Image.triggered.connect(self.nextImage)  # 下一张图片
        self.actionPrev_Image.triggered.connect(self.prevImage)  # 上一张图片

        # View 子菜单
        self.actionLabel_List.triggered.connect(
            self.dock_label_list.toggleViewAction)  # 显示右侧label列表，此功能可能有问题
        self.actionFill_List.triggered.connect(
            self.dock_file_list.toggleViewAction)   # 显示右侧文件列表，此功能可能有问题

        self.listWidget_files.itemSelectionChanged.connect(
            self.fileSelectionChanged)  # 切换文件
        # self.listWidget_labels.itemClicked.connect(self.selectLabel)  # 点击右侧label时，高亮对应区域。此功能暂时搁置

        # Tools子菜单
        self.actionconvert_to_dataset.triggered.connect(
            self.json2Dataset)  # 转换 Json 文件

        # Help 子菜单
        self.actionAbout.triggered.connect(self.showAuthorInfo)  # Emmm

        # 来自中央部件 canvas 的信号
        self.canvas.newShape.connect(self.newShape)
        self.canvas.paintingShape.connect(self.toggleDrawingSensitive)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.scrollRequest.connect(
            self.scrollRequest)   # canvas的滚动请求转发到此进行处理
        self.canvas.zoomRequest.connect(self.zoomRequest)  # canvas的放缩请求

    @property
    # 图片列表中的内容
    def imageList(self):
        count = self.listWidget_files.count()
        return [self.listWidget_files.item(i).text() for i in range(count)]

    def zoom(self, isZoomIn=True):
        self.canvas.scale += 0.1 * (1 if isZoomIn else -1)
        self.spinbox_scale.setValue(int(self.canvas.scale * 100))
        self.zoomMode = zoomMode.MANUAL_ZOOM
        self.canvas.repaint()

    def adjustScale(self):
        value = self.computeScale(self.image)
        self.canvas.scale = value
        self.spinbox_scale.setValue(int(100 * value))

    def paintCanvas(self):
        self.canvas.scale = 0.01 * self.spinbox_scale.value()
        self.canvas.repaint()

    def changeZoomMode(self, mode):
        '''
        槽函数
        切换显示模式
        '''
        if not isinstance(mode, zoomMode) or mode == self.zoomMode:
            return
        self.zoomMode = mode
        self.updateZoomBtn()
        self.adjustScale()

    def updateZoomBtn(self):
        actions = (self.actionFit_Width, self.actionFit_Window)
        modes = (zoomMode.FIT_WIDTH, zoomMode.FIT_WINDOW)
        for action, mode in zip(actions, modes):
            action.setChecked(True if mode == self.zoomMode else False)

    def updateUi(self):
        '''
        初始化一些默认状态
        '''
        self.setCentralWidget(self.centralwidget)
        self.spinbox_scale = zoomSpinBox()
        self.toolBar.insertWidget(self.actionZoom_out, self.spinbox_scale)
        self.zoomMode = zoomMode.FIT_WIDTH
        self.initSignal()
        self.authorInfo = AuthorWidget()
        self.authorInfo.hide()

    def openFile(self):
        if not self.leaving():
            return
        path = os.path.dirname(str(self.filename)) if self.filename else '.'
        formats = ['*.{}'.format(fmt.data().decode())
                   for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(
            formats + ['*.json'])
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Choose Image or Label file',
            path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.listWidget_files.clear()
            self.loadFile(str(filename))

    def openDir(self):
        if not self.leaving():
            return

        path = os.path.dirname(str(self.filename)) if self.filename else '.'
        dir_ = QFileDialog.getExistingDirectory(
            None, 'Open Folder', path, QFileDialog.ShowDirsOnly)
        self.loadDir(dir_)

    def loadDir(self, filepath=None):
        if not filepath:
            return
        self.filename = ''
        self.listWidget_files.clear()

        def scanImages(filepath):
            extensions = ['.%s' % fmt.data().decode("ascii").lower()
                          for fmt in QImageReader.supportedImageFormats()]
            images = []

            for root, dirs, files in os.walk(filepath):
                for file in files:
                    if file.lower().endswith(tuple(extensions)):
                        relativePath = os.path.join(root, file)
                        images.append(relativePath)
            return sorted(images, key=lambda x: x.lower())

        for filename in scanImages(filepath):
            # label_file = osp.splitext(filename)[0] + '.json'
            # if self.output_dir:
            #     label_file_without_path = osp.basename(label_file)
            #     label_file = osp.join(self.output_dir, label_file_without_path)
            item = QListWidgetItem(filename)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.listWidget_files.addItem(item)

        self.filename = self.imageList[0] if self.imageList else ''

    def loadFile(self, filename=None):
        '''
        根据文件名加载文件
        并在canvas中显示
        '''
        if not filename:
            return
        # 如果该文件已经被加载 则直接返回
        if filename in self.imageList and self.listWidget_files.currentRow() != self.imageList.index(filename):
            self.listWidget_files.setCurrentRow(self.imageList.index(filename))
            self.listWidget_files.repaint()
            return

        self.statusbar.showMessage('opening {}'.format(filename))
        self.resetState()
        self.canvas.setEnabled(False)

        # 使用QIamgeReader读取图像
        reader = QImageReader(filename)
        reader.setAutoTransform(True)
        image = reader.read()

        if image.isNull():
            self.statusbar.showMessage('Error loading {}'.format(filename))
            return

        # 假设该图像已经被标记
        # 那么应该存在同名 Json 文件
        label_file = os.path.splitext(filename)[0] + '.json'

        # 如果存在同名 Json文件
        # TODO: 进行 Json 合法性检查 这里直接忽略了
        if QFile.exists(label_file):
            # 从 Json 文件中提取标注区域信息
            shapes = loadJsonFile(label_file)

            # 交给 canvas 类处理
            self.canvas.retrieveAndLoadShape(shapes)

            # 更新右侧的label列表
            # labels 记录所有的标注信息
            # Python Set 用于去重
            labels = list(shape.label for shape in self.canvas.shapes)
            for label in set(labels):
                self.listWidget_labels.addItem(label)

            # 更新 itemToShapes 字典
            for shape in self.canvas.shapes:
                self.itemToShapes[shape.label] = \
                    self.itemToShapes.get(shape.label, []) + [shape]

        self.image = image
        self.filename = filename
        self.canvas.scale = self.computeScale(image)
        self.spinbox_scale.setValue(int(self.canvas.scale * 100))
        self.canvas.loadPixmap(QPixmap.fromImage(image))
        self.canvas.setEnabled(True)
        self.statusbar.showMessage('{}'.format(filename))
        self.setClean()
        self.actionCreate_Polygons.setEnabled(True)
        self.actionCreate_Rectangle.setEnabled(True)
        self.actionCreate_Circle.setEnabled(True)

    def closeFile(self):
        if not self.leaving():
            return
        self.resetState()
        self.setClean()

    def setDirty(self):
        self.dirty = True
        self.actionSave.setEnabled(True)

    def computeScale(self, image):
        if self.zoomMode == zoomMode.FIT_WINDOW:
            e = 2.0
            w1 = self.centralWidget().width() - e
            h1 = self.centralWidget().height() - e
            a1 = w1 / h1

            w2 = image.width()
            h2 = image.height()
            a2 = w2 / h2
            return w1 / w2 if a2 >= a1 else h1 / h2
        elif self.zoomMode == zoomMode.FIT_WIDTH:
            w = self.centralWidget().width() - 2.0
            return w / image.width()
        elif self.zoomMode == zoomMode.MANUAL_ZOOM:
            return 1.0

    def setClean(self):
        self.dirty = False
        self.actionSave.setEnabled(False)
        self.actionSave_as.setEnabled(False)

    def leaving(self):
        '''
        在切换任务前检查是否有未保存的修改
        如果有 弹出对话框进行询问
        '''
        if not self.dirty:
            return True
        mb = QMessageBox
        title = 'Save Annotations? - Label-it'
        content = 'Do you want to save the changes to this document before closing?\n' \
            'If you don\'t save, your changes will be lost'
        answer = mb.question(self, title,
                             content,
                             mb.Save | mb.Discard | mb.Cancel,
                             mb.Save)
        if answer == mb.Discard:
            return True
        elif answer == mb.Cancel:
            return False
        elif answer == mb.Save:
            self.saveFile(True)
            return True

    def resetState(self):
        self.listWidget_labels.clear()
        self.filename = ''
        self.canvas.resetState()

    def fileSelectionChanged(self):
        '''
        listWidget_file 的槽函数

        切换文件时触发
        离开前当前文件是否为脏状态
        同时准备下一文件的加载
        '''
        items = self.listWidget_files.selectedItems()
        if not items:
            return

        # 在切换前询问是否保存
        if not self.leaving():
            return

        filename = str(items[0].text())
        self.loadFile(filename)

    def updateToolBar(self):
        if len(self.imageList) <= 1:
            self.actionNext_Image.setEnabled(False)
            self.actionPrev_Image.setEnabled(False)
        else:
            self.actionNext_Image.setEnabled(True)
            self.actionPrev_Image.setEnabled(True)

        self.actionSave.setEnabled(True if self.dirty else False)
        self.actionSave_as.setEnabled(True if self.dirty else False)

    def toggleDrawMode(self, edit=True, createMode='polygon'):
        '''
        槽函数

        当点击创建多边形/矩形/圆形按钮时触发
         - 如果为编辑状态 那么...
         - 如果为空闲状态 那么开始绘制
         - 如果之前处于绘制状态 那么清除之前的标注区域

        edit: 当前是否为edit状态
        '''

        if edit:
            self.canvas.editing = True
        else:
            if not self.canvas.drawing:
                self.canvas.drawing = True
            self.canvas.current = None
            self.canvas.line = None
            self.canvas.repaint()
        self.canvas.createMode = createMode
        # TODO setAction Availablity

    def toggleDrawingSensitive(self, drawing):
        # TODO setAction Availablity
        pass

    def newShape(self):
        '''
        槽函数
        用来处理canvas传来的信号
        弹出对话框来添加新的label
        '''
        def iterAllItems(listwidget):
            items = []
            for i in range(listwidget.count()):
                items.append(listwidget.item(i).text())
            return items

        items = iterAllItems(self.listWidget_labels)
        label_dialog = LabelDialog(self, items)

        # 检测dialog的返回值
        result = label_dialog.exec_()
        if result:
            label = label_dialog.lineEdit.text()
            self.canvas.setLastLabel(label)
            self.addLabel(self.canvas.shapes[-1])
            self.setDirty()
        else:
            self.canvas.undoLastLine()

    def deleteSelectedShape(self):
        '''
        槽函数
        删除选中的标注区域
        '''
        if not self.canvas.selectedShapes:
            return

        # 弹出提示框确认操作
        mb = QMessageBox
        msg = 'You are about to permanently delete {} polygons, ' \
              'proceed anyway?'.format(len(self.canvas.selectedShapes))
        result = mb.warning(self, 'Attention', msg, mb.Yes | mb.No)
        if result == mb.Yes:
            deleted_shapes = self.canvas.deleteSelected()
            for shape in deleted_shapes:
                # 更新内部字典
                self.itemToShapes[shape.label].remove(shape)

            # 再次遍历
            # 更新右侧 labelList
            for shape in deleted_shapes:
                # 如果该label下已经没有标注区域
                if not self.itemToShapes[shape.label]:
                    # 从 labelList 中移除
                    items = self.listWidget_labels.findItems(
                        shape.label, Qt.MatchExactly)
                    self.listWidget_labels.removeItemWidget(items[0])
            self.setDirty()

    def copySelectedShape(self):
        '''
        槽函数
        复制某个标注区域
        '''
        self.canvas.copySelectedShapes()
        self.setDirty()

    def saveFile(self, silentSave=False):
        '''
        槽函数
        保存文件时触发

        - silentSave: 是否弹出文件选择框来指定保存路径
        '''
        assert not self.image.isNull()

        # 保存文件时弹出对话框
        def saveFileDialog():
            path = os.path.dirname(
                str(self.filename)) if self.filename else '.'
            caption = 'Save As'
            suffix = '.json'
            filters = 'Label files (*.json)'
            dlg = QFileDialog(
                self, caption, path, filters)
            dlg.setDefaultSuffix('json')
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            dlg.setOption(QFileDialog.DontConfirmOverwrite, False)
            dlg.setOption(QFileDialog.DontUseNativeDialog, False)
            basename = os.path.basename(os.path.splitext(self.filename)[0])
            default_labelfile_name = os.path.join(
                path, basename + suffix
            )
            filename, _ = dlg.getSaveFileName(
                self, 'Choose File', default_labelfile_name,
                'Label files (*%s)' % suffix)
            return str(filename)

        # 有进行过标注时，才继续处理
        if self.hasLabels():

            # 检查同名 Json 文件
            label_file = os.path.splitext(self.filename)[0] + '.json'

            # 如果存在同名 Json文件
            if silentSave and QFile.exists(label_file):
                filename = label_file
            else:
                filename = saveFileDialog()

            # filename: 最终json文件的文件名
            if filename:
                self.saveLabels(filename)
                self.setClean()

    def hasLabels(self):
        return True if self.itemToShapes else False

    def saveLabels(self, filename):
        assert filename

        def format_shape(s):
            '''
            将shape转换为json格式中的内容

            包括label、构成区域的所有点以及区域形状
            '''
            return dict(
                label=s.label,
                points=[(p.x(), p.y()) for p in s.points],
                shape_type=s.shape_type,
            )

        # 标注信息
        shapes = [format_shape(shape) for shape in self.canvas.shapes]

        # 图像路径
        imagePath = self.filename

        # 获得源图像的base64编码
        imageData = getImageData(imagePath)
        if os.path.dirname(filename) and not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        # 保存为 Json 格式
        saveJsonFile(filename, shapes, imagePath, imageData,
                     self.image.height(), self.image.width())

    def addLabel(self, shape):
        item = QListWidgetItem(shape.label)
        item.setCheckState(Qt.Checked)

        # 存储同一标签的所有标注区域
        shapes = self.itemToShapes.get(item.text(), []) + [shape]
        self.itemToShapes[item.text()] = shapes

        if not self.listWidget_labels.findItems(shape.label, Qt.MatchExactly):
            self.listWidget_labels.addItem(shape.label)

    def shapeSelectionChanged(self, selected_shapes):
        for shape in self.canvas.selectedShapes:
            shape.selected = False
            shape.hovered = False
        self.canvas.selectedShapes = selected_shapes
        for shape in self.canvas.selectedShapes:
            shape.selected = True
            item = self.listWidget_labels.findItems(shape.label, Qt.MatchExactly)[0]   # 只会匹配一个结果
            self.listWidget_labels.setCurrentItem(item)
        # TODO: set action availablity
    
    def selectLabel(self, item):
        '''
        槽函数
        当点击右侧labellist的一个标签时
        高亮显示对应的标注区域
        '''
        if not item:
            return
        
        shapes = self.itemToShapes.get(item.text(), [])
        
        for shape in self.canvas.shapes:
            shape.hovered = False
            self.canvas.repaint()
        for shape in shapes:
            shape.hovered = True
            self.canvas.repaint()

    def showAuthorInfo(self):
        '''
        槽函数
        显示作者信息

        稍微皮一下
        '''
        self.authorInfo.show()

    def scrollRequest(self, delta, orientation):
        '''
        槽函数
        调整scrollArea
        进行窗口的放缩

        -delta: 移动值
        -orientation: Qt.Horizontal | Qt.Vertical
        '''
        units = - delta * 0.1
        bar = self.centralwidget.verticalScrollBar() \
            if orientation == Qt.Vertical \
            else self.centralwidget.horizontalScrollBar()
        bar.setValue(bar.value() + bar.singleStep() * units)

    def zoomRequest(self, delta, pos):
        '''
        槽函数
        调整scrollArea
        进行上下滚动

        -delta: 滚轮移动值
        -pos: QPoint
        '''
        canvas_width_old = self.canvas.width()

        # 根据滚动方向判断时放大还是缩小
        self.zoom(True if delta > 0 else False)

        canvas_width_new = self.canvas.width()
        if canvas_width_old != canvas_width_new:
            canvas_scale_factor = canvas_width_new / canvas_width_old

            x_shift = round(pos.x() * canvas_scale_factor) - pos.x()
            y_shift = round(pos.y() * canvas_scale_factor) - pos.y()

            hScrollBar = self.centralwidget.horizontalScrollBar()
            vScrollBar = self.centralwidget.verticalScrollBar()

            hScrollBar.setValue(hScrollBar.value() + x_shift)
            vScrollBar.setValue(vScrollBar.value() + y_shift)

    def nextImage(self):
        '''
        槽函数
        切换到下一个图片文件
        '''
        if not self.leaving():
            return

        if not len(self.imageList) > 1:
            return

        if not self.filename:
            filename = self.imageList[0]
        currIndex = self.imageList.index(self.filename)

        if currIndex == len(self.imageList) - 1:
            return

        filename = self.imageList[currIndex + 1]
        self.filename = filename

        if self.filename:
            self.loadFile(self.filename)

    def prevImage(self):
        '''
        槽函数
        切换到上一个图片文件
        '''
        if not self.leaving():
            return

        if not len(self.imageList) > 1:
            return

        if not self.filename:
            filename = self.imageList[0]
        currIndex = self.imageList.index(self.filename)

        if currIndex == 0:
            return

        filename = self.imageList[currIndex - 1]
        self.filename = filename

        if self.filename:
            self.loadFile(self.filename)

    def json2Dataset(self):
        path = os.path.dirname(
            str(self.filename)) if self.filename else '.'
        caption = 'Choose Json File'
        filters = 'Label files (*.json)'
        filename, _ = QFileDialog.getOpenFileNames(  # 允许多选
            self, caption,
            path, filters)

        if filename:
            result = json_to_dataset(filename)

            mb = QMessageBox
            title = 'Convert end'
            content = 'Conversion end.\n\n{} successed\n{} failed'.format(
                result[0], result[1])
            mb.information(self, title, content,
                           QMessageBox.Ok, QMessageBox.Ok)

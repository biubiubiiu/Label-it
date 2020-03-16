from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QPointF
from PyQt5.QtGui import QColor, QPixmap, QPainter
from PyQt5.QtWidgets import QWidget, QApplication
from tools import *
from shape import ShapeFactory, highlightMode
from enum import Enum


class cursorType(Enum):
    CURSOR_DEFAULT = Qt.ArrowCursor
    CURSOR_POINT = Qt.PointingHandCursor
    CURSOR_DRAW = Qt.CrossCursor
    CURSOR_MOVE = Qt.ClosedHandCursor
    CURSOR_GRAB = Qt.OpenHandCursor


class mode(Enum):
    CREATE = 0
    EDIT = 1


class Canvas(QWidget):
    zoomRequest = pyqtSignal(int, QPoint)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(list)
    shapeMoved = pyqtSignal()
    paintingShape = pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)

        self.mode = mode.EDIT
        self.shapes = []    # 所有标注区域
        self.current = None  # 正在绘制的图形
        self.selectedShapes = []  # 被选中的标注区域
        self.hoverShape = None  # 鼠标悬浮的标注区域
        self.selectedVertex = None  # 选中的图形顶点
        self.hasMovedShape = False  # 记录有没有发生图形移动操作
        self.drawingLineColor = QColor(0, 0, 255)
        self.prevPoint = QPoint()
        self.offsets = QPoint(), QPoint()
        self._scale = 1.0
        self.pixmap = QPixmap()

        self._painter = QPainter()
        self.line = None
        self._cursor = cursorType.CURSOR_DEFAULT.value
        self._createMode = 'polygon'

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

    @property
    def createMode(self):
        return self._createMode

    @createMode.setter
    def createMode(self, value):
        if value in ['polygon', 'rectangle', 'circle']:
            self._createMode = value
        else:
            raise ValueError('Unsupported createMode: %s' % value)

    @property
    def drawing(self):
        return self.mode == mode.CREATE

    @drawing.setter
    def drawing(self, value):
        if value:
            self.mode = mode.CREATE

    @property
    def editing(self):
        return self.mode == mode.EDIT

    @editing.setter
    def editing(self, value):
        if value:
            self.mode = mode.EDIT
        else:
            self.mode = mode.CREATE
            if self.hoverShape:
                self.hoverShape.highlightClear()
            self.hoverShape = self.selectedVertex = None
            self.deSelectShape()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        if value < 0:
            return
        self._scale = value

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.repaint()

    # @Overrides(QWidget)
    def focusOutEvent(self, QFocusEvent):
        self.restoreCursor()

    # @Overrides(QWidget)
    def leaveEvent(self, QEvent):
        self.restoreCursor()

    # @Overrides(QWidget)
    def wheelEvent(self, QWheelEvent):
        '''
        鼠标滚轮时间处理`
        进行画面放缩
        使用了labelme的源码
        '''
        mods = QWheelEvent.modifiers()
        delta = QWheelEvent.angleDelta()
        if Qt.ControlModifier == int(mods):
            # with Ctrl/Command key
            # 放缩
            self.zoomRequest.emit(delta.y(), QWheelEvent.pos())
        else:
            # 滚动
            self.scrollRequest.emit(delta.x(), Qt.Horizontal)
            self.scrollRequest.emit(delta.y(), Qt.Vertical)
        QWheelEvent.accept()

    # @Overrides(QWidget)
    def mouseMoveEvent(self, QMouseEvent):
        if not self.pixmap:
            return

        pos = self.transformPos(QMouseEvent.pos())
        self.restoreCursor()

        if self.drawing:
            if not self.line:
                self.line = ShapeFactory.genShape(
                    self.createMode, label=None, points=[])
            self.overrideCursor(cursorType.CURSOR_DRAW.value)

            if not self.current:
                return

            # 如果鼠标位置超出了图片范围
            # 则计算当前操作点的正确位置
            if outOfPixmap(self.pixmap, pos):
                pos = intersectionPoint(self.pixmap, self.current[-1], pos)

            # 如果最后两点足够接近
            elif len(self.current) > 1 \
                    and self.createMode == 'polygon' \
                    and closeEnough(self.current[0], pos, 10.0 / self.scale):
                # 那么形成闭合多边形
                pos = self.current[0]
                self.overrideCursor(cursorType.CURSOR_POINT.value)
                # 突出显示最后一个顶点
                self.current.highlightVertex(0, highlightMode.NEAT_VERTEX)

            # 否则 还未形成闭合多边形
            # 那么点的显示位置为鼠标位置
            if self.createMode == 'polygon':
                self.line[0] = self.current[-1]
                self.line[1] = pos

            # 当创建矩形或圆时
            # 默认认为它是闭合状态
            elif self.createMode == 'rectangle' or self.createMode == 'circle':
                self.line.points = [self.current[0], pos]
                self.line.close()
            self.repaint()
            self.current.highlightClear()

        elif self.editing:
            # self.hasMovedShape = False

            # 鼠标处于拖动状态
            if Qt.LeftButton & QMouseEvent.buttons():

                # 如果选中的是一个顶点
                if self.selectedVertex:
                    self.overrideCursor(cursorType.CURSOR_MOVE.value)
                    index, shape = self.selectedVertex, self.hoverShape    # 正在处理的顶点序号 正在处理的图形
                    point = shape[index]    # 找到对应点
                    if outOfPixmap(self.pixmap, pos):
                        pos = intersectionPoint(self.pixmap, point, pos)
                    shape.moveVertexBy(index, pos - point)  # 调整该顶点位置
                    self.repaint()
                    self.hasMovedShape = True

                # 如果选中的是一个图形
                elif self.selectedShapes and self.prevPoint:
                    self.overrideCursor(cursorType.CURSOR_MOVE.value)
                    if outOfPixmap(self.pixmap, pos):
                        return

                    # 计算点的正确位置
                    o1 = pos + self.offsets[0]
                    if outOfPixmap(self.pixmap, o1):
                        pos -= QPoint(min(0, o1.x()), min(0, o1.y()))
                    o2 = pos + self.offsets[1]
                    if outOfPixmap(self.pixmap, o2):
                        pos += QPoint(min(0, self.pixmap.width() - o2.x()),
                                      min(0, self.pixmap.height() - o2.y()))

                    for shape in self.selectedShapes:
                        shape.moveBy(pos - self.prevPoint)
                    self.prevPoint = pos
                    self.repaint()
                    self.hasMovedShape = True

            # 鼠标悬浮
            else:
                for shape in reversed([s for s in self.shapes]):
                    # 寻找与当前鼠标位置最接近的顶点
                    index = nearestVertex(
                        shape, pos, self.scale)
                    if index:
                        if self.selectedVertex:
                            self.hoverShape.highlightClear()
                        self.selectedVertex = index
                        self.hoverShape = shape
                        shape.highlightVertex(index, highlightMode.MOVE_VERTEX)
                        self.overrideCursor(cursorType.CURSOR_POINT.value)
                        self.setToolTip("Click & drag to move point")
                        self.update()

                        # 找到一个满足条件的标注区域后
                        # 直接退出
                        break
                    elif shape.containsPoint(pos):
                        if self.selectedVertex:
                            self.hoverShape.highlightClear()
                        self.selectedVertex = None
                        self.hoverShape = shape
                        self.setToolTip(
                            "Click & drag to move shape '%s'" % shape.label)
                        self.overrideCursor(cursorType.CURSOR_GRAB.value)
                        self.update()
                        break
                else:  # 鼠标在空白区域
                    if self.hoverShape:
                        # 清除之前区域的高亮显示
                        self.hoverShape.highlightClear()
                        self.update()
                    self.selectedVertex = self.hoverShape = None
        # TODO 完善功能

    # @Overrides(QWidget)
    def mousePressEvent(self, QMouseEvent):
        if not self.pixmap:
            return

        pos = self.transformPos(QMouseEvent.pos())

        if QMouseEvent.button() == Qt.LeftButton:
            if self.drawing:
                self.handleDrawing(pos)
            elif self.editing:
                self.selectShapePoint(pos)
                self.prevPoint = pos
                self.repaint()

    # @Overrides(QWidget)
    def mouseReleaseEvent(self, QMouseEvent):
        if not self.pixmap:
            return
        if QMouseEvent.button() == Qt.LeftButton and self.selectedShapes:
            self.overrideCursor(cursorType.CURSOR_GRAB.value)
        if self.hasMovedShape:
            self.shapeMoved.emit()

    # @Overrides(QWidget)
    def keyPressEvent(self, QKeyEvent):
        key = QKeyEvent.key()

        # 按下 Esc 时 中止绘制
        if key == Qt.Key_Escape:
            if self.current:
                self.current = None
                self.paintingShape.emit(False)
                self.update()
            else:
                self.editing = True

    def handleDrawing(self, pos):
        if self.current:
            if self.createMode == 'polygon':
                self.current.addPoint(self.line[1])
                self.line[0] = self.current[-1]
                if self.current.isClosed():
                    self.finalise()
            elif self.createMode in ['rectangle', 'circle']:
                assert len(self.current.points) == 1
                self.current.points = self.line.points
                self.finalise()

        # 开始一个新图形
        elif not outOfPixmap(self.pixmap, pos):
            self.current = ShapeFactory.genShape(
                self.createMode, label=None, points=[])
            self.current.addPoint(pos)
            self.line.points = [pos, pos]
            self.paintingShape.emit(True)
            self.update()

    def selectShapePoint(self, point):
        '''
        选择包含了传入点坐标的图形
        '''
        self.deSelectShape()
        if self.selectedVertex:
            index, shape = self.selectedVertex, self.hoverShape
            shape.selected = True
            shape.highlightVertex(index, highlightMode.MOVE_VERTEX)
        else:
            for shape in reversed(self.shapes):
                if shape.containsPoint(point):
                    self.calculateOffsets(shape, point)
                    self.selectionChanged.emit([shape])
                    return

    def deSelectShape(self):
        '''
        取消选择某个图形
        '''
        if self.selectedShapes:
            self.selectionChanged.emit([])
            self.update()

    def deleteSelected(self):
        '''
        删除选中的图形
        '''
        deleted_shapes = []
        if self.selectedShapes:
            for shape in self.selectedShapes:
                self.shapes.remove(shape)
                deleted_shapes.append(shape)
            self.selectedShapes = []
            self.update()
        return deleted_shapes

    def copySelectedShapes(self):
        '''
        复制选中的图形
        '''
        if not self.selectedShapes:
            return
        selectedShapesCopy = [s.copy() for s in self.selectedShapes]
        for i, shape in enumerate(selectedShapesCopy):
            self.shapes.append(shape)
            self.selectedShapes[i].selected = False
            self.selectedShapes[i] = shape

    def calculateOffsets(self, shape, point):
        '''
        定位点在图形中的位置
        '''
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width() - 1) - point.x()
        y2 = (rect.y() + rect.height() - 1) - point.y()
        self.offsets = QPoint(x1, y1), QPoint(x2, y2)

    def finalise(self):
        '''
        结束一个图形的绘制
        '''
        assert self.current
        self.current.close()
        self.shapes.append(self.current)
        self.current = None
        self.line = None
        self.newShape.emit()
        self.update()

    def transformPos(self, point):
        '''
        将屏幕坐标转换为图片坐标
        '''
        return point / self.scale - self.getCenter()

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.open()
        if not self.line:
            self.line = ShapeFactory.genShape(
                self.createMode, label=None, points=[])
        if self.createMode == 'polygon':
            self.line.points = [self.current[-1], self.current[0]]
        elif self.createMode == 'rectangle'or self.createMode == 'circle':
            self.current.points = self.current.points[0:1]
        self.paintingShape.emit(True)

    def setLastLabel(self, label):
        assert label
        assert self.shapes[-1]
        self.shapes[-1].label = label

    def selectShapes(self, shapes):
        self.selectionChanged.emit(shapes)
        self.update()

    # @Overrides(QWidget)
    def paintEvent(self, paintEvent):
        '''
        重载 QWidget中的 paintEvent 方法
        用来显示 pixmap 图片
        '''
        if not self.pixmap:
            return super(Canvas, self).paintEvent(paintEvent)

        # 使用 begin 方法开始绘制
        p = self._painter
        p.begin(self)

        # 设置渲染时的属性
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        # 对坐标系进行放缩
        p.scale(self._scale, self._scale)

        # 对坐标系进行平移
        # 在后续的渲染中将以这个平移后的坐标系为基准
        p.translate(self.getCenter())

        # 在上一步中已经平移过坐标系
        # 因此这里直接从(0, 0)开始画
        p.drawPixmap(0, 0, self.pixmap)

        # 设置图形的显示比例与图像的放缩比例一致
        ShapeFactory.setScale(self.scale)
        for shape in self.shapes:
            shape.hovered = shape == self.hoverShape
            shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)

        # 结束绘制
        p.end()

    def getCenter(self):
        '''
        计算放缩后图片的中心显示位置
        '''
        s = self._scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def overrideCursor(self, cursor):
        self.restoreCursor()
        self._cursor = cursor
        QApplication.setOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def resetState(self):
        self.pixmap = None
        self.shapes = []
        self.update()

    def retrieveAndLoadShape(self, shape_info):

        def reformat_shape(s):
            '''
            将json格式中的内容转换为shape
            包括label、构成区域的所有点以及区域形状
            '''
            result = []

            # shapes = ((
            #     s['label'],
            #     s['points'],
            #     s.get('shape_type', 'polygon'))
            # for s in data['shapes']

            for shape in s:
                label = shape[0]
                name = shape[2]
                points = []
                for point in shape[1]:
                    x, y = point
                    points.append(QPointF(x, y))
                result.append(ShapeFactory.genShape(
                    name=name, label=label, points=points))

            return result

        # 加载到 canvas 中
        result = reformat_shape(shape_info)
        self.shapes = result

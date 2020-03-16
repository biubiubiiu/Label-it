from copy import deepcopy
from PyQt5.QtGui import QColor, QPainterPath, QPen
from PyQt5.QtCore import QRectF
from enum import Enum
import math


DEFAULT_LINE_COLOR = QColor(234, 240, 72)    # 浅黄
DEFAULT_FILL_COLOR = QColor(246, 214, 255, 125)    # 淡粉

DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(159, 240, 72, 125)    # 浅绿
DEFAULT_VERTEX_FILL_COLOR = QColor(42, 82, 0, 125)  # 深绿
DEFAULT_HVERTEX_FILL_COLOR = QColor(199, 179, 229)    # 淡紫


class highlightMode(Enum):
    NEAT_VERTEX = 0
    MOVE_VERTEX = 1


class Shape(object):

    scale = 1.0
    point_size = 8

    def __init__(self, label=None, points=[]):
        super().__init__()

        self.label = label
        self.points = points
        self.selected = False   # 是否选中
        self.hovered = False    # 鼠标是否悬浮在图形上
        self._closed = False    # 是否闭合

        self._highlightIndex = None  # 突出显示的顶点序号
        self._highlightMode = highlightMode.NEAT_VERTEX

    def addPoint(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def popPoint(self):
        return self.points.pop() if self.points else None

    def paint(self, painter):
        '''
        Shape的绘制函数
        使用QPen以及QPainterPath进行绘制
        其中modifyPath方法在不同子类中进行重写
        '''
        if not self.points:
            return

        color = DEFAULT_SELECT_LINE_COLOR if self.selected else DEFAULT_LINE_COLOR
        pen = QPen(color)
        pen.setWidth(max(1, int(round(2.0 / self.scale))))
        painter.setPen(pen)

        line_path = QPainterPath()
        vrtx_path = QPainterPath()

        self.modifyPath(line_path, vrtx_path)

        painter.drawPath(line_path)
        painter.drawPath(vrtx_path)
        painter.fillPath(
            vrtx_path, DEFAULT_HVERTEX_FILL_COLOR if self.hovered else DEFAULT_VERTEX_FILL_COLOR)

        if self.selected or self.hovered:
            color = DEFAULT_SELECT_FILL_COLOR if self.selected else DEFAULT_FILL_COLOR
            painter.fillPath(line_path, color)

    def modifyPath(self, line_path, vrtx_path):
        '''
        在子类中进行重写
        '''
        pass

    def close(self):
        self._closed = True

    def open(self):
        self._closed = False

    def isClosed(self):
        return self._closed

    def copy(self):
        return deepcopy(self)

    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def makePath(self):
        pass

    def boundingRect(self):
        return self.makePath().boundingRect()

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        point = self.points[i]
        if i == self._highlightIndex:
            d *= 4 if self._highlightMode == highlightMode.NEAT_VERTEX else 1.5
        path.addEllipse(point, d / 2.0, d / 2.0)

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        if key > len(self.points):
            raise IndexError('index out of range')
        return self.points[key]

    def __setitem__(self, key, val):
        if key > len(self.points):
            raise IndexError('assignment index out of range')
        self.points[key] = val


class Rectangle(Shape):
    def __init__(self, label=None, points=[]):
        super().__init__(label=label, points=points)
        self.shape_type = 'rectangle'

    def makePath(self):
        path = QPainterPath()
        assert len(self.points) == 2
        rectangle = self.getRectFromPoints(self.points)
        path.addRect(rectangle)
        return path

    def getRectFromPoints(self, pts):
        pt1, pt2 = pts[0], pts[1]
        x1, y1 = pt1.x(), pt1.y()
        x2, y2 = pt2.x(), pt2.y()
        return QRectF(x1, y1, x2 - x1, y2 - y1)

    # @Overrides(Shape)
    def modifyPath(self, line_path, vrtx_path):
        assert len(self.points) == 1 or len(self.points) == 2
        if len(self.points) == 2:
            rectangle = self.getRectFromPoints(self.points)
            line_path.addRect(rectangle)
        for i in range(len(self.points)):
            self.drawVertex(vrtx_path, i)


class Polygon(Shape):
    def __init__(self, label=None, points=[]):
        super().__init__(label=label, points=points)
        self.shape_type = 'polygon'

    # @Overrides(Shape)
    def modifyPath(self, line_path, vrtx_path):
        line_path.moveTo(self.points[0])
        for i, p in enumerate(self.points):
            line_path.lineTo(p)
            self.drawVertex(vrtx_path, i)
        if self.isClosed():
            line_path.lineTo(self.points[0])

    def makePath(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        return path


class Circle(Shape):
    def __init__(self, label=None, points=[]):
        super().__init__(label=label, points=points)
        self.shape_type = 'circle'

    # @Overrides(Shape)
    def modifyPath(self, line_path, vrtx_path):
        assert len(self.points) == 1 or len(self.points) == 2
        if len(self.points) == 2:
            rectangle = self.getCircleFromPoints(self.points)
            line_path.addEllipse(rectangle)
        for i in range(len(self.points)):
            self.drawVertex(vrtx_path, i)

    def makePath(self):
        path = QPainterPath()
        assert len(self.points) == 2
        circle = self.getCircleFromPoints(self.points)
        path.addEllipse(circle)
        return path

    def getCircleFromPoints(self, pts):
        center = pts[0]
        r = pts[1] - pts[0]
        d = math.sqrt(math.pow(r.x(), 2) + math.pow(r.y(), 2))
        rectangle = QRectF(center.x() - d, center.y() - d, 2 * d, 2 * d)
        return rectangle


class ShapeFactory(object):

    @staticmethod
    def setScale(scale):
        Shape.scale = scale

    @staticmethod
    def genShape(name='polygon', label=None, points=[]):
        if name == 'rectangle':
            return Rectangle(label=label, points=points)
        elif name == 'polygon':
            return Polygon(label=label, points=points)
        elif name == 'circle':
            return Circle(label=label, points=points)

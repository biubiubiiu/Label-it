import math
from PyQt5.QtCore import QPoint
import PIL.Image
import PIL.ImageDraw
import io
import os
import json
import base64
import numpy as np
import yaml


def distance(point):
    '''
    计算一点坐标到原点的长度

    -point: QPoint / QPointF
    '''
    return math.sqrt(point.x()**2 + point.y()**2)


def closeEnough(p1, p2, epsilon):
    '''
    判断两个点是否足够接近

    如果两个点的距离 < epsilon
    则返回 True；否则返回 False
    '''
    return distance(p1 - p2) < epsilon


def nearestVertex(shape, pos, scale):
    min_distance = float('inf')
    min_i = None
    for i, p in enumerate(shape.points):
        dist = distance(p - pos)
        if dist <= 10.0 / scale and dist < min_distance:
            min_distance = dist
            min_i = i
    return min_i


def outOfPixmap(pixmap, pos):
    '''
    计算点的位置是否超出图片范围

    -pixmap: QPixmap
    -pos: QPoint / QPointF
    '''
    if not pixmap or not pos:
        raise TypeError('None Type detected')
    w, h = pixmap.width(), pixmap.height()
    x, y = pos.x(), pos.y()
    return x < 0 or x >= w or y < 0 or y >= h


def intersectionPoint(pixmap, p1, p2):
    '''
    References: Labelme source code

    当鼠标位置超出图片范围时
    计算点的正确显示位置
    此段代码来源于 Labelme 的源代码
    '''
    # Cycle through each image edge in clockwise fashion,
    # and find the one intersecting the current line segment.
    # http://paulbourke.net/geometry/lineline2d/

    def intersectingEdges(point1, point2, points):
        """
        Find intersecting edges.

        For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen.
        """
        (x1, y1) = point1
        (x2, y2) = point2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QPoint((x3 + x4) / 2, (y3 + y4) / 2)
                d = distance(m - QPoint(x2, y2))
                yield d, i, (x, y)

    size = pixmap.size()
    points = [(0, 0),
              (size.width() - 1, 0),
              (size.width() - 1, size.height() - 1),
              (0, size.height() - 1)]
    x1, y1 = p1.x(), p1.y()
    x2, y2 = p2.x(), p2.y()
    d, i, (x, y) = min(intersectingEdges((x1, y1), (x2, y2), points))
    x3, y3 = points[i]
    x4, y4 = points[(i + 1) % 4]
    if (x, y) == (x1, y1):
        # Handle cases where previous point is on one of the edges.
        if x3 == x4:
            return QPoint(x3, min(max(0, y2), max(y3, y4)))
        else:  # y3 == y4
            return QPoint(min(max(0, x2), max(x3, x4)), y3)
    return QPoint(x, y)


def getImageData(filename):
    image_pil = PIL.Image.open(filename)
    with io.BytesIO() as f:
        ext = os.path.splitext(filename)[1].lower()
        format = 'JPEG' if ext in ['.jpg', '.jpeg'] else 'PNG'
        image_pil.save(f, format=format)
        f.seek(0)
        return f.read()


def restoreFromImageData(data):
    f = io.BytesIO()
    f.write(base64.b64decode(data))
    img_arr = np.array(PIL.Image.open(f))
    return img_arr


def saveJsonFile(filename, shapes, imagePath, imageData, imageHeight, imageWidth):
    # 转换为 base64 编码
    if imageData is not None:
        imageData = base64.b64encode(imageData).decode('utf-8')
    data = dict(
        shapes=shapes,
        imagePath=imagePath,
        imageData=imageData,
        imageHeight=imageHeight,
        imageWidth=imageWidth,
    )
    with open(filename, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def loadJsonFile(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
        assert data['imageData'] is not None
        shapes = (
            (
                s['label'],
                s['points'],
                s.get('shape_type', 'polygon'),
            )
            for s in data['shapes']
        )
        return shapes


def json_to_dataset(filename):
    success = fail = 0
    for f in filename:
        if _json_to_dataset(f):
            success += 1
        else:
            fail += 1
    return success, fail


def _json_to_dataset(filename):
    data = json.load(open(filename))
    img = restoreFromImageData(data['imageData'])

    label_name_to_value = {'_background_': 0}
    for shape in data['shapes']:
        label_name = shape['label']
        label_value = label_name_to_value.get(label_name, len(label_name_to_value))
        label_name_to_value[label_name] = label_value

    # label_values must be dense
    label_values, label_names = [], []
    for ln, lv in sorted(label_name_to_value.items(), key=lambda x: x[1]):
        label_values.append(lv)
        label_names.append(ln)
    assert label_values == list(range(len(label_values)))

    lbl = shapes_to_label(img.shape, data['shapes'], label_name_to_value)

    captions = ['{}: {}'.format(lv, ln)
                for ln, lv in label_name_to_value.items()]

    lbl_viz = draw_label(lbl, img, captions)

    out_dir = os.path.join(os.path.splitext(filename)[0] + '_dataset')
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    PIL.Image.fromarray(img).save(os.path.join(out_dir, 'img.png'))
    PIL.Image.fromarray(lbl).save(os.path.join(out_dir, 'label.png'))
    PIL.Image.fromarray(lbl_viz).save(os.path.join(out_dir, 'label_viz.png'))

    with open(os.path.join(out_dir, 'label_names.txt'), 'w') as f:
        for lbl_name in label_names:
            f.write(lbl_name + '\n')

        info = dict(label_names=label_names)
        with open(os.path.join(out_dir, 'info.yaml'), 'w') as f:
            yaml.safe_dump(info, f, default_flow_style=False)

        return True


def polygons_to_mask(img_shape, polygons, isCircleArea):
    mask = np.zeros(img_shape[:2], dtype=np.uint8)
    mask = PIL.Image.fromarray(mask)
    xy = list(map(tuple, polygons))
    if isCircleArea:
        # 对于圆形区域
        # 传入的参数为外接矩形的四个点坐标
        PIL.ImageDraw.Draw(mask).ellipse(xy=xy, outline=1, fill=1)
    else:
        PIL.ImageDraw.Draw(mask).polygon(xy=xy, outline=1, fill=1)  # 完成点的连接
    mask = np.array(mask, dtype=bool)
    return mask


def shapes_to_label(img_shape, shapes, label_name_to_value, type='class'):
    assert type in ['class', 'instance']

    cls = np.zeros(img_shape[:2], dtype=np.int32)
    if type == 'instance':
        ins = np.zeros(img_shape[:2], dtype=np.int32)
        instance_names = ['_background_']
    for shape in shapes:
        polygons = shape['points']

        # 增加对于矩形区域的适配
        if shape['shape_type'] == 'rectangle':
            pt1, pt2 = polygons[0], polygons[1]

            # 需要保证有序
            polygons.insert(1, [pt1[0], pt2[1]])
            polygons.append([pt2[0], pt1[1]])

        # 增加对于圆形区域的适配
        elif shape['shape_type'] == 'circle':
            center, p = polygons[0], polygons[1]
            r = abs(center[0] - p[0])
            x = center[0] - r if center[0] < p[0] else center[0] + r
            y = center[1] - r if center[1] < p[1] else center[1] + r
            polygons[0] = [x, y]

        label = shape['label']
        if type == 'class':
            cls_name = label
        elif type == 'instance':
            cls_name = label.split('-')[0]
            if label not in instance_names:
                instance_names.append(label)
            ins_id = len(instance_names) - 1
        cls_id = label_name_to_value[cls_name]

        if shape['shape_type'] == 'circle':
            mask = polygons_to_mask(img_shape[:2], polygons, True)
        else:
            mask = polygons_to_mask(img_shape[:2], polygons, False)
        cls[mask] = cls_id
        if type == 'instance':
            ins[mask] = ins_id

    if type == 'instance':
        return cls, ins
    return cls


def label_colormap(N=256):

    def bitget(byteval, idx):
        return ((byteval & (1 << idx)) != 0)

    cmap = np.zeros((N, 3))
    for i in range(0, N):
        id = i
        r, g, b = 0, 0, 0
        for j in range(0, 8):
            r = np.bitwise_or(r, (bitget(id, 0) << 7 - j))
            g = np.bitwise_or(g, (bitget(id, 1) << 7 - j))
            b = np.bitwise_or(b, (bitget(id, 2) << 7 - j))
            id = (id >> 3)
        cmap[i, 0] = r
        cmap[i, 1] = g
        cmap[i, 2] = b
    cmap = cmap.astype(np.float32) / 255
    return cmap

# similar function as skimage.color.label2rgb


def label2rgb(lbl, img=None, n_labels=None, alpha=0.3, thresh_suppress=0):
    if n_labels is None:
        n_labels = len(np.unique(lbl))

    cmap = label_colormap(n_labels)
    cmap = (cmap * 255).astype(np.uint8)

    lbl_viz = cmap[lbl]
    lbl_viz[lbl == -1] = (0, 0, 0)  # unlabeled

    if img is not None:
        img_gray = PIL.Image.fromarray(img).convert('LA')
        img_gray = np.asarray(img_gray.convert('RGB'))
        lbl_viz = alpha * lbl_viz + (1 - alpha) * img_gray
        lbl_viz = lbl_viz.astype(np.uint8)

    return lbl_viz


def draw_label(label, img, label_names, colormap=None):
    import matplotlib.pyplot as plt
    backend_org = plt.rcParams['backend']
    plt.switch_backend('agg')

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0,
                        wspace=0, hspace=0)
    plt.margins(0, 0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())

    if colormap is None:
        colormap = label_colormap(len(label_names))

    label_viz = label2rgb(label, img, n_labels=len(label_names))
    plt.imshow(label_viz)
    plt.axis('off')

    plt_handlers = []
    plt_titles = []
    for label_value, label_name in enumerate(label_names):
        if label_value not in label:
            continue
        if label_name.startswith('_'):
            continue
        fc = colormap[label_value]
        p = plt.Rectangle((0, 0), 1, 1, fc=fc)
        plt_handlers.append(p)
        plt_titles.append(label_name)
    plt.legend(plt_handlers, plt_titles, loc='lower right', framealpha=.5)

    f = io.BytesIO()
    plt.savefig(f, bbox_inches='tight', pad_inches=0)
    plt.cla()
    plt.close()

    plt.switch_backend(backend_org)

    out_size = (img.shape[1], img.shape[0])
    out = PIL.Image.open(f).resize(out_size, PIL.Image.BILINEAR).convert('RGB')
    out = np.asarray(out)
    return out

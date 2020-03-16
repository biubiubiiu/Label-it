from skimage import io
from matplotlib import pylab as plt

# input_file = r'D:\File\HUST\数字图像处理\Label-it\TestImage\IMG_2784(20191112-135306)_dataset\label.png'  # 文件路径
input_file = r'C:\Users\19471\Pictures\Saved Pictures\Saved Pictures\IMG_2110_dataset\label.png'  # 文件路径

img = io.imread(input_file)  # 使用 io 模块读取图片不会改变图片的数据格式
plt.imshow(img * 40)  # 简单的图像增强
plt.show()

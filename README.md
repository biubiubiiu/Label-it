# Label-it

2019年秋 数字图像处理大作业

简易图像标注软件

## 简介

该软件实现了基本的图像标注功能，支持标注多边形、矩形及圆形区域

参考了图像标注软件[Labelme](https://github.com/wkentaro/labelme)的做法，将标注结果保存为轻量级的json格式文件。同时，整合了转换json文件的功能：只使用json文件即可复原原图像，并导出标注区域的8位掩模，及相应的标注区域信息（支持批量转换）

## 开发环境

在Windows系统下，使用Python3进行开发

相关依赖库及版本
- PyQt5 = 5.13.0
- Pillow = 5.4.1
- matplotlib = 3.0.3
- PyYAML = 5.1

使用前需要确保安装了上述模块，推荐使用尽可能新的版本
```bash
pip install PyQT5
pip install Pillow
pip install matplotlib
pip install PyYAML
```
## 运行环境

- Python3
- PyQt5
- Windows / Linux

## 运行方法
```bash
cd Label-it/src
python app.py
```

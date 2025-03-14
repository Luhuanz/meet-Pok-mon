# -*- coding: utf-8 -*-
# @Author : senwang
'''
from ultralytics import YOLO
# 下载模型
# yolo11 : wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11{x|l|m|s|n}.pt  # float16版本
# yolov10: wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10{n/s/m/b/l/x}.pt # float16版本
           wget https://github.com/THU-MIG/yolov10/releases/download/v1.1/yolov10{n/s/m/b/l/x}.pt # float32版本
model = YOLO("yolo11x.pt")
results = model.predict("test3.png")
# Display the results
results[0].show()
# Export the model to ONNX format
path = model.export(format="onnx", half=True)  # gpu机器下跑model.export(format="onnx", half=True, device=0),onnx模型才会小于等于pt模型 return path to exported model
## 在cpu环境下导出不了half即float16的模型，因为float16在cpu下跑的比float32慢。在gpu环境下可以导出half的模型，但是用cpu运行比float32慢一倍（仅自己测试的结果）
## 有时候gpu机器上用不了gpu跑，可能同时存在cpu和gpu的onnxruntime版本。解决如下：pip uninstall onnxruntime, pip uninstall onnxruntime-gpu, pip install onnxruntime-gpu



float16 模型在显存占用更少、推理速度更快时表现较好，但仅在 GPU 环境 下效果明显。在 CPU 环境 下，float32 模型通常更高效。
 将 YOLO 模型导出为 ONNX 格式。如果设置 half=True，模型会以 float16 格式导出，但这只能在 GPU 环境 下进行。
  用half模型运行的时候，输入数据记得改成.astype(np.float16)  因此对于我们的检测需要
 请导出 onnx  fp32
'''


import cv2
import numpy as np
import onnxruntime as ort
import time
import os
# 类外定义类别映射关系，使用字典格式  修改类
CLASS_NAMES = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train',
               7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter',
               13: 'bench', 14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant',
               21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie',
               28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite',
               34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket',
               39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana',
               47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza',
               54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table',
               61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone',
               68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock',
               75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'}


class YOLO11:
    """YOLO11 目标检测模型类，用于处理推理和可视化。"""

    def __init__(self, onnx_model, confidence_thres, iou_thres):
        """
        初始化 YOLO11 类的实例。
        参数：
            onnx_model: ONNX 模型的路径。
            input_image: 输入图像的路径。
            confidence_thres: 用于过滤检测结果的置信度阈值。
            iou_thres: 非极大值抑制（NMS）的 IoU（交并比）阈值。
        """
        self.onnx_model = onnx_model
        self.confidence_thres = confidence_thres
        self.iou_thres = iou_thres

        # 加载类别名称
        self.classes = CLASS_NAMES

        # 为每个类别生成一个颜色调色板
        self.color_palette = np.random.uniform(0, 255, size=(len(self.classes), 3))  #

        # 使用 ONNX 模型创建推理会话，自动选择CPU或GPU
        self.session = ort.InferenceSession(
            self.onnx_model,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"] if ort.get_device() == "GPU" else [
                "CPUExecutionProvider"],
        )
        # 打印模型的输入尺寸
        print("YOLO11 🚀 目标检测 ONNXRuntime")
        print("模型名称：", self.onnx_model)

        # 获取模型的输入形状
        self.model_inputs = self.session.get_inputs()
        input_shape = self.model_inputs[0].shape
        self.input_width = input_shape[2]
        self.input_height = input_shape[3]
        print(f"模型输入尺寸：宽度 = {self.input_width}, 高度 = {self.input_height}")

    def preprocess(self, img_input):
        """
            对输入图像进行预处理，以便进行推理。
            参数：
                img_input (str | numpy.ndarray): 输入图像路径或图像数组。
            返回：
                image_data: 经过预处理的图像数据，准备进行推理。
            """
        # 判断输入是路径还是 NumPy 数组
        if isinstance(img_input, str) and os.path.isfile(img_input):
            # 如果是路径，加载图像
            self.img = cv2.imread(img_input)
            if self.img is None:
                raise ValueError(f"无法加载图像：{img_input}")

        elif isinstance(img_input, np.ndarray):
            self.img = img_input
        else:
            raise TypeError("img_input 必须是图像路径或 numpy.ndarray 类型")

        # 获取输入图像的高度和宽度
        self.img_height, self.img_width = self.img.shape[:2]

        # 将图像颜色空间从 BGR 转换为 RGB
        img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)

        # 保持宽高比，进行 letterbox 填充, 使用模型要求的输入尺寸
        img, ratio, (dw, dh) = self.letterbox(img, new_shape=(self.input_width, self.input_height))

        # 通过除以 255.0 来归一化图像数据
        image_data = np.array(img) / 255.0

        # 将图像的通道维度移到第一维
        image_data = np.transpose(image_data, (2, 0, 1))  # 通道优先

        # 扩展图像数据的维度，以匹配模型输入的形状
        image_data = np.expand_dims(image_data, axis=0).astype(np.float32)

        # 返回预处理后的图像数据
        return image_data, ratio, dw, dh

    def letterbox(self, img, new_shape=(640, 640), color=(114, 114, 114), auto=False, scaleFill=False, scaleup=True):
        """
        将图像进行 letterbox 填充，保持纵横比不变，并缩放到指定尺寸。
        """
        shape = img.shape[:2]  # 当前图像的宽高
        print(f"Original image shape: {shape}")

        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # 计算缩放比例
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])  # 选择宽高中最小的缩放比
        if not scaleup:  # 仅缩小，不放大
            r = min(r, 1.0)

        # 缩放后的未填充尺寸
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))

        # 计算需要的填充
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # 计算填充的尺寸
        dw_left = dw // 2  # padding 均分
        dh_top = dh // 2

        # 缩放图像
        if shape[::-1] != new_unpad:  # 如果当前图像尺寸不等于 new_unpad，则缩放
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)

        # 为图像添加边框以达到目标尺寸
        top, bottom = int(round(dh_top)), int(round(dh - dh_top))
        left, right = int(round(dw_left)), int(round(dw - dw_left))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        print(f"Final letterboxed image shape: {img.shape}")

        return img, (r, r), (dw_left, dh_top)

    def postprocess_yolo11x(self, input_image, output, ratio, dw, dh, draw_box=False, class_id=None):
        """
        对yolo11x模型输出进行后处理，以提取边界框、分数和类别 ID。
        参数：
            input_image (numpy.ndarray): 输入图像。
            output (numpy.ndarray): 模型的输出。
            class_id: 默认None将各个存在的类都输出，若指定特定的类别如class_id=0则只输出人的框，这种优点是不会因为nms被过滤掉
        返回：
            numpy.ndarray: 包含检测结果的输入图像。
        """
        # 转置并压缩输出，以匹配预期形状
        outputs = np.transpose(np.squeeze(output[0]))  #  nx84, 84为box占4，cls_score占80
        rows = outputs.shape[0]
        boxes, scores, class_ids = [], [], []

        # 计算缩放比例和填充
        # ratio = self.img_width / self.input_width, self.img_height / self.input_height
        # ratio = self.ratio
        # dw, dh = self.dw, self.dh
        confidence_thres = self.confidence_thres
        tic = time.time()

        # 对 scores 进行过滤
        classes_scores = outputs[:, 4:]  # 获取类别得分
        max_scores = np.amax(classes_scores, axis=1)  # 每一行的最大得分
        mask = max_scores >= confidence_thres  # 创建筛选掩码

        # 只保留符合信心的输出
        filtered_outputs = outputs[mask]
        scores = max_scores[mask]

        if filtered_outputs.size == 0:
            return class_ids, scores, boxes, input_image  # 如果没有合格的检测框，直接返回输入图像

        class_ids = np.argmax(filtered_outputs[:, 4:], axis=1)  # 筛选后计算类别ID
        boxes = filtered_outputs[:, :4]  # 获取框位置
        if class_id is not None:
            mask = class_ids == class_id
            scores = scores[mask]
            class_ids = class_ids[mask]
            boxes = boxes[mask]
        # 将框调整到原始图像尺寸，考虑缩放和填充
        boxes[:, 0] = (boxes[:, 0] - dw) / ratio[0]  # x
        boxes[:, 1] = (boxes[:, 1] - dh) / ratio[1]  # y
        boxes[:, 2] /= ratio[0]  # w
        boxes[:, 3] /= ratio[1]  # h

        # 计算左上角和尺寸
        left = (boxes[:, 0] - boxes[:, 2] / 2).astype(int)
        top = (boxes[:, 1] - boxes[:, 3] / 2).astype(int)
        width = boxes[:, 2].astype(int)
        height = boxes[:, 3].astype(int)

        # 将所有框放在一个结构中
        boxes = np.vstack((left, top, width, height)).T

        # NMS
        indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), confidence_thres, self.iou_thres)
        print('take time prenms:{}'.format(time.time()-tic))
        boxes = boxes[indices]
        scores = scores[indices]
        class_ids = class_ids[indices]
        if draw_box:
            for i in range(len(indices)):
                box = boxes[i]
                score = scores[i]
                class_id = class_ids[i]
                self.draw_detections(input_image, box, score, class_id)
        return class_ids, scores, boxes, input_image


    def draw_detections(self, img, box, score, class_id):
        """
        在输入图像上绘制检测到的边界框和标签。
        参数：
            img: 用于绘制检测结果的输入图像。
            box: 检测到的边界框。
            score: 对应的检测分数。
            class_id: 检测到的目标类别 ID。

        返回：
            None
        """
        # 提取边界框的坐标
        x1, y1, w, h = box

        # 获取类别对应的颜色
        color = self.color_palette[int(class_id)]

        # 在图像上绘制边界框
        cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color, 2)

        # 创建包含类别名和分数的标签文本
        label = f"{self.classes[class_id]}: {score:.2f}"

        # 计算标签文本的尺寸
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        # 计算标签文本的位置
        label_x = x1
        label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10

        # 绘制填充的矩形作为标签文本的背景
        cv2.rectangle(img, (label_x, label_y - label_height), (label_x + label_width, label_y + label_height), color,
                      cv2.FILLED)

        # 在图像上绘制标签文本
        cv2.putText(img, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    def predict(self, img_input, draw_box=False, class_id=None):
        # 预处理图像数据，确保使用模型要求的尺寸 (640x640)
        img_data, ratio, dw, dh = self.preprocess(img_input)

        # 使用预处理后的图像数据运行推理
        outputs = self.session.run(None, {self.model_inputs[0].name: img_data})

        # 对输出进行后处理以获取输出图像
        if '10' in self.onnx_model:
            res = self.postprocess_yolov10x(self.img, outputs, ratio, dw, dh, draw_box, class_id=class_id)  # 输出图像
        else:
            res = self.postprocess_yolo11x(self.img, outputs, ratio, dw, dh, draw_box, class_id=class_id)  # 输出图像
        return res
# 使用指定的参数创建 YOLO11 类的实例
cur_dir = os.path.dirname(__file__)
yolo_detection = YOLO11(onnx_model=os.path.join(cur_dir, "yolo11x_float32.onnx"),  confidence_thres=0.2, iou_thres=0.5)  #  "yolov10x.onnx", "yolo11x.onnx"
if __name__ == "__main__":
    img_input = cv2.imread('test.png')
    # 执行目标检测并获取输出图像
    tic = time.time()
    class_ids, scores, boxes, output_image = yolo_detection.predict(img_input, draw_box=True, class_id=0)
    print('take time:{}'.format(time.time()-tic))
    # 保存输出图像到文件
    cv2.imwrite("det_result_picture.jpg", output_image)

    print("图像已保存为 det_result_picture.jpg")
    print('class_names:{}, scores:{}'.format([CLASS_NAMES[t] for t in class_ids], scores))




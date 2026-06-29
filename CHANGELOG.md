# Changelog

所有重要变更均记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-06-28

### 新增
- **单张图片检测**：支持点击上传和拖拽上传，实时检测并显示结果
- **文件夹批量检测**：支持选择文件夹批量导入图片，每秒 2 张自动检测
- **实时摄像头检测**：通过浏览器 WebRTC 摄像头拍照检测
- **检测结果可视化**：在图片上标注缺陷位置、类别和置信度，标签自适应边界
- **批量结果导出**：支持将批量检测结果导出为 CSV 格式报告（UTF-8 BOM 编码）
- **样本图片快速测试**：页面底部提供数据集样本图片，一键快速测试
- **端口冲突自动处理**：启动时检测端口占用，自动释放或切换备用端口
- **模拟检测模式**：模型不存在时自动切换模拟模式，基于文件名生成演示结果
- **模型延迟加载**：模型在首次检测请求时加载，加快应用启动速度

### 模型
- YOLOv8 Nano 模型训练脚本 `model/train.py`，支持训练/验证/导出
- `runs/detect/runs/train_cpu/` 包含训练好的 NEU-DET 专用模型权重
- 支持导出为 ONNX / TFLite 格式

### 技术栈
- 后端：Flask 3.x + Werkzeug
- 检测引擎：YOLOv8 (Ultralytics)
- 图像处理：OpenCV 4.x + NumPy
- 前端：Vanilla JavaScript + CSS3 (Flexbox/Grid)

### 缺陷类型
- 6 类钢材表面缺陷检测：裂纹、夹杂物、斑点、麻面、轧入氧化皮、划痕

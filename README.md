# NEU-DET 钢材表面缺陷检测 Web 应用

基于 Flask + YOLOv8 的钢材表面缺陷实时检测系统。

**作者：孙国龙** | **创建时间：2026-06-28**

---

## 目录

- [功能特性](#功能特性)
- [缺陷类型说明](#缺陷类型说明)
- [项目结构](#项目结构)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [API 接口文档](#api-接口文档)
- [模型训练](#模型训练)
- [配置说明](#配置说明)
- [开发扩展指南](#开发扩展指南)
- [故障排除](#故障排除)
- [技术栈](#技术栈)
- [数据来源与引用](#数据来源与引用)

---

## 功能特性

### 核心功能
| 功能 | 描述 |
|------|------|
| **单张图片检测** | 支持点击上传或拖拽图片进行缺陷检测，实时返回检测结果 |
| **文件夹批量检测** | 支持选择文件夹批量导入图片，以每秒 2 张的速度自动检测 |
| **实时摄像头检测** | 支持通过浏览器摄像头拍照检测（需浏览器支持 WebRTC） |
| **结果可视化** | 在图片上标注缺陷位置、类别和置信度，标签自适应边界不越界 |
| **结果导出** | 批量检测结果支持导出为 CSV 报告（UTF-8 BOM 编码，兼容 Excel） |

### 工程特性
- **模拟检测模式**：当模型文件不存在时自动启用，基于文件名/标注文件生成演示结果
- **端口冲突自动处理**：启动时自动检测端口占用，支持自动释放或切换备用端口
- **延迟模型加载**：模型在首次检测时加载，加快应用启动速度
- **跨平台支持**：Windows / macOS / Linux 均可运行

---

## 缺陷类型说明

系统可检测 NEU-DET 数据集中的 6 类钢材表面缺陷：

| ID | 英文名称 | 中文名称 | 颜色 | 说明 |
|----|----------|----------|------|------|
| 0 | Crazing | 裂纹 | 红色 `#e74c3c` | 表面细微裂纹 |
| 1 | Inclusion | 夹杂物 | 绿色 `#27ae60` | 非金属夹杂物 |
| 2 | Patches | 斑点 | 蓝色 `#3498db` | 表面斑状缺陷 |
| 3 | Pitted Surface | 麻面 | 黄色 `#f1c40f` | 表面麻点/凹坑 |
| 4 | Rolled-in Scale | 轧入氧化皮 | 紫色 `#9b59b6` | 氧化皮压入 |
| 5 | Scratches | 划痕 | 青色 `#1abc9c` | 机械划痕 |

---

## 项目结构

```
neu-det-webapp/
├── app.py                      # Flask 主应用入口（路由、配置、启动）
├── requirements.txt            # Python 依赖清单
├── README.md                   # 项目文档（本文件）
├── CHANGELOG.md                # 版本变更记录
├── CONTRIBUTING.md             # 贡献指南
├── SECURITY.md                 # 安全策略
├── .gitignore                  # Git 忽略规则
│
├── model/                      # 模型模块
│   ├── __init__.py             # 模块入口，导出 DefectDetector/train/validate/export
│   ├── predict.py              # 检测推理：DefectDetector 类（含模拟模式）
│   └── train.py                # 模型训练：训练/验证/导出/更新数据配置
│
├── templates/
│   └── index.html              # Web 界面模板（Jinja2）
│
├── static/
│   ├── css/
│   │   └── style.css           # 全局样式（740 行，含响应式布局）
│   ├── js/
│   │   └── main.js             # 前端交互逻辑（834 行，含摄像头/批量检测）
│   ├── uploads/                # 用户上传图片（运行时自动创建）
│   └── results/                # 检测结果图片（运行时自动创建）
│
├── runs/                       # 模型训练输出
│   └── detect/
│       └── runs/
│           └── train_cpu/      # CPU 训练结果
│               ├── weights/
│               │   ├── best.pt # 最佳模型权重
│               │   └── last.pt # 最后一轮模型权重
│               ├── results.png # 训练曲线
│               ├── confusion_matrix.png
│               └── ...         # 其他训练产出
│
├── yolov8n.pt                  # YOLOv8 Nano 预训练权重（可选，用于迁移学习）
│
└── .venv/                      # Python 虚拟环境（请勿提交到 Git）
```

---

## 系统架构

### 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (前端)                         │
│  HTML (Jinja2)  │  CSS (响应式)  │  JS (异步交互)       │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / JSON / FormData / Base64
┌──────────────────────▼──────────────────────────────────┐
│              Flask Web Application (app.py)              │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐  │
│  │  路由     │  │ 请求处理   │  │ 端口管理/服务启动    │  │
│  │ /         │  │ /upload   │  │ kill_process_on_port │  │
│  │ /upload   │  │ /detect   │  │ find_available_port  │  │
│  │ /detect   │  │ _base64   │  │ ensure_port_avail    │  │
│  │ /model    │  │ /model_   │  │ able                  │  │
│  │ _status   │  │ _status   │  │                      │  │
│  └──────────┘  └─────┬─────┘  └──────────────────────┘  │
└──────────────────────┼──────────────────────────────────┘
                       │ DefectDetector
┌──────────────────────▼──────────────────────────────────┐
│                 Model Layer (model/)                     │
│  ┌─────────────────────┐  ┌──────────────────────────┐  │
│  │   predict.py        │  │   train.py               │  │
│  │   - DefectDetector  │  │   - train_neu_det()      │  │
│  │   - mock_predict()  │  │   - validate_model()     │  │
│  │   - draw_detections │  │   - export_model()       │  │
│  └─────────┬───────────┘  └──────────────────────────┘  │
└────────────┼───────────────────────────────────────────┘
             │ YOLOv8 / OpenCV
┌────────────▼──────────────────────────────────────────┐
│              YOLOv8 推理引擎 (ultralytics)             │
│  ┌──────────────────────────────────────────────────┐ │
│  │  best.pt (训练后的 NEU-DET 专用模型)              │ │
│  │  或 yolov8n.pt (通用预训练，启用模拟模式时的后备)   │ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

### 数据流

```
[用户上传图片] → [Flask 接收文件] → [保存到 uploads/]
                                    → [DefectDetector.predict()]
                                       → [YOLOv8 推理 / 模拟模式]
                                       → [draw_detections() 绘制标注]
                                    → [保存结果到 results/]
                                    → [返回 JSON（含图片 URL + 检测列表）]
                                    → [前端渲染原图 / 结果图 / 统计信息]
```

---

## 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器
- （可选）CUDA 支持的 GPU 用于模型训练

### 安装步骤

```bash
# 1. 进入项目目录
cd neu-det-webapp

# 2. （推荐）创建虚拟环境
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
# 或 .venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 Web 服务
python app.py
```

启动后访问 http://localhost:5001

### 快速验证

1. 打开浏览器访问 http://localhost:5001
2. 在页面底部点击任意"样本图片"快速测试
3. 或拖拽一张钢材表面图片到上传区域

---

## 使用指南

### 单张图片检测

1. 在左侧上传区域点击或拖拽图片
2. 系统自动上传并执行检测
3. 右侧显示原图与检测结果对比图
4. 下方列出每个缺陷的详细信息（类别、置信度、位置）

### 文件夹批量检测

1. 点击"选择文件夹批量检测"按钮
2. 选择包含图片的文件夹
3. 系统以每秒 2 张的速度自动检测
4. 检测过程中实时显示当前图片原图和检测结果
5. 检测完成后表格显示所有图片的结果清单
6. 点击"导出报告"下载 CSV 格式结果

### 实时摄像头检测

1. 点击"实时摄像头检测"按钮
2. 在弹出的摄像头窗口中点击"开启摄像头"
3. 对准钢材表面，点击"拍照检测"
4. 检测结果会显示在摄像头窗口下方

---

## API 接口文档

### 1. 上传图片检测

```
POST /upload
Content-Type: multipart/form-data

参数:
  - file: 图片文件（必填，支持 jpg/jpeg/png/bmp，最大 16MB）

响应 200:
{
  "success": true,
  "original_image": "/static/uploads/20260628_143012_a1b2c3d4_img.jpg",
  "result_image": "/static/results/result_20260628_143012_a1b2c3d4_img.jpg",
  "total_defects": 3,
  "defect_summary": {
    "裂纹 (Crazing)": 2,
    "划痕 (Scratches)": 1
  },
  "detections": [
    {
      "class_id": 0,
      "class_name": "crazing",
      "confidence": 0.85,
      "bbox": [120, 45, 200, 130]
    }
  ]
}

响应 400:
{ "error": "没有上传文件" }

响应 500:
{ "error": "检测失败: ..." }
```

### 2. Base64 图片检测（摄像头）

```
POST /detect_base64
Content-Type: application/json

参数:
{
  "image": "data:image/jpeg;base64,/9j/4AAQ..."  // Base64 编码图片
}

响应 200:
{
  "success": true,
  "result_image": "data:image/jpeg;base64,...",  // 结果图也是 Base64
  "total_defects": 2,
  "defect_summary": { ... },
  "detections": [ ... ]
}
```

### 3. 模型状态查询

```
GET /model_status

响应 200:
{
  "status": "trained",        // "trained" | "demo" | "error"
  "message": "模型已加载",
  "model_path": "runs/detect/runs/train_cpu/weights/best.pt"
}
```

### 4. 静态文件服务

```
GET /static/{path}
Flask 自动提供 static/ 目录下的文件。
```

### 错误码说明

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 检测成功 |
| 400 | 请求参数错误（无文件/类型不支持） |
| 500 | 检测过程中发生服务器错误 |

---

## 模型训练

### 训练新模型

```bash
python model/train.py \
    --data ../fa031-main/NEU-DET/NEU-DET/data.yaml \
    --model n \
    --epochs 100 \
    --batch 16 \
    --img-size 640 \
    --device 0 \
    --name train_cpu
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--data` | 必填 | 数据集配置文件路径 (data.yaml) |
| `--model` | `n` | YOLOv8 模型大小：`n`/`s`/`m`/`l`/`x` |
| `--epochs` | `100` | 训练轮数 |
| `--batch` | `16` | 批次大小 |
| `--img-size` | `640` | 输入图片尺寸 |
| `--device` | `0` | GPU 编号；设为 `cpu` 使用 CPU |
| `--project` | `runs` | 项目保存目录 |
| `--name` | `train` | 实验名称 |
| `--resume` | 无 | 从检查点恢复训练 |
| `--validate` | 无 | 仅验证模型（不训练） |
| `--export` | 无 | 导出模型格式，如 `onnx`/`tflite` |

### 验证模型

```bash
python model/train.py --validate --data data.yaml --name train_cpu
```

### 导出模型

```bash
# 导出为 ONNX 格式
python model/train.py --export onnx --name train_cpu

# 导出为 TFLite 格式
python model/train.py --export tflite --name train_cpu
```

### 更新数据配置路径

如果数据集位置发生变化，可以使用以下函数更新 data.yaml 中的路径：

```python
from model.train import update_data_yaml
update_data_yaml('原始data.yaml', '输出data.yaml', '数据集基础路径')
```

---

## 配置说明

### 关键配置项（app.py）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | `5001` | Web 服务端口 |
| `HOST` | `0.0.0.0` | 监听地址（允许局域网访问） |
| `UPLOAD_FOLDER` | `static/uploads/` | 上传图片存储目录 |
| `RESULT_FOLDER` | `static/results/` | 检测结果图片存储目录 |
| `MODEL_PATH` | `runs/.../best.pt` | 模型权重文件路径 |
| `MAX_CONTENT_LENGTH` | `16MB` | 上传文件大小上限 |
| `ALLOWED_EXTENSIONS` | `png/jpg/jpeg/bmp` | 允许的图片格式 |

### 端口管理机制

应用启动时自动执行以下端口管理逻辑：

1. 检查 `PORT`（默认 5001）是否被占用
2. 如果被占用，尝试 `SIGTERM` 终止占用进程
3. 如果无法终止，自动搜索 `5001~5100` 间的可用端口
4. 如果启动时仍失败，在 `PORT+1 ~ PORT+20` 间再次尝试

### 模型加载策略

- **训练模型优先**：优先加载 `runs/detect/runs/train_cpu/weights/best.pt`
- **文件不存在**：自动启用**模拟检测模式**（基于文件名生成模拟缺陷）
- **延迟加载**：模型在首次检测请求时初始化，加快应用启动速度

---

## 开发扩展指南

### 添加新的缺陷类别

**后端**（`app.py` 和 `model/predict.py`）：

```python
# 1. app.py 中添加显示名称
DEFECT_NAMES = {
    6: '新缺陷名称 (New Defect)'
}

# 2. model/predict.py 中添加类别定义
DEFECT_CLASSES = {
    6: 'new_defect'
}

COLORS = {
    6: (128, 128, 0)  # BGR 格式
}
```

**前端**（`static/js/main.js`）：

```javascript
const DEFECT_COLORS = {
    6: '#808000'  // 十六进制颜色
};
const DEFECT_NAMES = {
    6: '新缺陷'
};
```

### 更换检测模型

```python
# 在 app.py 中修改 MODEL_PATH
MODEL_PATH = os.path.join(BASE_DIR, 'path/to/your/custom_model.pt')
```

### 调整批量检测速度

```javascript
// 在 static/js/main.js 中找到 BATCH_INTERVAL_MS
const BATCH_INTERVAL_MS = 500;  // 当前为 500ms（每秒2张）
```

### 添加新的 API 接口

参考 `app.py` 中的 `/upload` 和 `/detect_base64` 路由模式，使用 Flask 的 `@app.route` 装饰器添加新端点。

---

## 故障排除

### 常见问题

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 启动报错 `Address already in use` | 端口 5001 被占用 | 程序会自动处理，或手动 `kill` 占用进程 |
| 摄像头无法打开 | 浏览器权限/未使用 HTTPS | 在 Chrome 设置中允许摄像头权限 |
| 检测结果不准确 | 模拟模式未加载真实模型 | 训练专用模型并确保 `best.pt` 在正确路径 |
| `ModuleNotFoundError: ultralytics` | 依赖未安装 | `pip install -r requirements.txt` |
| 批量检测结果为空 | 文件夹中无支持的图片格式 | 确保图片为 `jpg/jpeg/png/bmp` 格式 |
| 图片上传失败 | 超过 16MB 限制 | 压缩图片或修改 `MAX_CONTENT_LENGTH` |

### 调试模式

```python
# 在 app.py 启动时开启 debug 模式（不建议生产环境使用）
app.run(host=HOST, port=PORT, debug=True)
```

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **后端框架** | Flask 3.x | Web 路由与请求处理 |
| **目标检测** | YOLOv8 (Ultralytics) | 缺陷检测推理引擎 |
| **图像处理** | OpenCV 4.x / NumPy | 图片读写、绘制标注框 |
| **前端模板** | Jinja2 | 服务端模板渲染 |
| **前端样式** | CSS3（Flexbox/Grid） | 响应式布局 |
| **前端交互** | Vanilla JavaScript | 异步上传、摄像头、批量检测 |
| **序列化** | Werkzeug / Base64 | 文件上传、Base64 编解码 |

---

## 数据来源与引用

- **NEU-DET 数据集**：东北大学宋克臣团队制作，包含 1800 张钢材表面缺陷图片
  - 论文：Cheng, G., & Song, K. (2022). *NEU-DET: A Surface Defect Detection Dataset for Steel Strips*
  - 数据来源：https://github.com/fa0311/NEU-DET

### 许可证

本项目仅供学习交流使用，请勿用于商业用途。

---

## 作者信息

**孙国龙**

本项目为工业视觉课程实践作品，旨在展示基于 YOLOv8 的钢材表面缺陷检测完整解决方案。

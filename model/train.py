"""
NEU-DET 钢材表面缺陷检测模型训练脚本
使用 YOLOv8 训练自定义缺陷检测模型
"""

import os
import sys
import yaml
from datetime import datetime
from ultralytics import YOLO


def train_neu_det(
    data_yaml,
    model_size='n',
    epochs=100,
    batch_size=16,
    img_size=640,
    device='0',  # 使用GPU，改为 'cpu' 使用CPU
    project='runs',
    name='train',
    resume=False
):
    """
    训练NEU-DET缺陷检测模型
    
    Args:
        data_yaml: 数据配置文件路径 (data.yaml)
        model_size: YOLOv8模型大小 (n/s/m/l/x)
        epochs: 训练轮数
        batch_size: 批次大小
        img_size: 图片尺寸
        device: 设备 ('0' for GPU, 'cpu' for CPU)
        project: 项目保存目录
        name: 实验名称
        resume: 是否恢复训练
    
    Returns:
        训练结果
    """
    
    # 检查数据配置文件
    if not os.path.exists(data_yaml):
        raise FileNotFoundError(f"数据配置文件不存在: {data_yaml}")
    
    # 选择基础模型
    model_name = f'yolov8{model_size}.pt'
    
    print("=" * 60)
    print("NEU-DET 钢材表面缺陷检测模型训练")
    print("=" * 60)
    print(f"数据配置: {data_yaml}")
    print(f"基础模型: {model_name}")
    print(f"训练轮数: {epochs}")
    print(f"批次大小: {batch_size}")
    print(f"图片尺寸: {img_size}")
    print(f"设备: {device}")
    print(f"输出目录: {project}/{name}")
    print("=" * 60)
    
    # 加载模型
    if resume:
        # 恢复训练
        model_path = os.path.join(project, name, 'weights', 'last.pt')
        if not os.path.exists(model_path):
            print(f"警告: 找不到检查点文件 {model_path}, 从基础模型开始")
            model = YOLO(model_name)
        else:
            model = YOLO(model_path)
            print(f"从检查点恢复: {model_path}")
    else:
        # 新训练
        model = YOLO(model_name)
    
    # 开始训练
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project=project,
        name=name,
        patience=50,  # 早停耐心值
        save=True,
        save_period=10,  # 每10轮保存一次
        plots=True,  # 生成训练曲线图
        verbose=True
    )
    
    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)
    
    # 显示结果路径
    train_dir = os.path.join(project, name)
    print(f"模型保存位置:")
    print(f"  - 最佳模型: {os.path.join(train_dir, 'weights', 'best.pt')}")
    print(f"  - 最后模型: {os.path.join(train_dir, 'weights', 'last.pt')}")
    print(f"\n训练曲线图:")
    print(f"  - 结果曲线: {os.path.join(train_dir, 'results.png')}")
    print(f"  - 混淆矩阵: {os.path.join(train_dir, 'confusion_matrix.png')}")
    print(f"\n验证结果:")
    print(f"  - PR曲线: {os.path.join(train_dir, 'PR_curve.png')}")
    print(f"  - F1曲线: {os.path.join(train_dir, 'F1_curve.png')}")
    
    return results


def validate_model(model_path, data_yaml):
    """
    验证模型性能
    
    Args:
        model_path: 模型路径
        data_yaml: 数据配置文件
    
    Returns:
        验证结果
    """
    print("=" * 60)
    print("模型验证")
    print("=" * 60)
    
    model = YOLO(model_path)
    results = model.val(data=data_yaml)
    
    print(f"\n验证结果:")
    print(f"  mAP50: {results.box.map50:.4f}")
    print(f"  mAP50-95: {results.box.map:.4f}")
    print(f"  Precision: {results.box.mp:.4f}")
    print(f"  Recall: {results.box.mr:.4f}")
    
    return results


def export_model(model_path, format='onnx'):
    """
    导出模型为其他格式
    
    Args:
        model_path: 模型路径
        format: 导出格式 (onnx/tflite/torchscript/openvino)
    
    Returns:
        导出路径
    """
    print("=" * 60)
    print(f"导出模型为 {format} 格式")
    print("=" * 60)
    
    model = YOLO(model_path)
    export_path = model.export(format=format)
    
    print(f"导出完成: {export_path}")
    return export_path


def update_data_yaml(original_yaml, output_yaml, base_path):
    """
    更新数据配置文件中的路径
    
    Args:
        original_yaml: 原始配置文件
        output_yaml: 输出配置文件
        base_path: 数据集基础路径
    """
    with open(original_yaml, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # 更新路径
    data['train'] = os.path.join(base_path, 'train', 'images')
    data['val'] = os.path.join(base_path, 'valid', 'images')
    
    with open(output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    
    print(f"配置文件已更新: {output_yaml}")
    print(f"训练路径: {data['train']}")
    print(f"验证路径: {data['val']}")


# 命令行接口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='NEU-DET缺陷检测模型训练')
    
    parser.add_argument('--data', type=str, required=True,
                        help='数据配置文件路径 (data.yaml)')
    parser.add_argument('--model', type=str, default='n',
                        help='YOLOv8模型大小 (n/s/m/l/x)')
    parser.add_argument('--epochs', type=int, default=100,
                        help='训练轮数')
    parser.add_argument('--batch', type=int, default=16,
                        help='批次大小')
    parser.add_argument('--img-size', type=int, default=640,
                        help='图片尺寸')
    parser.add_argument('--device', type=str, default='0',
                        help='设备 (0 for GPU, cpu for CPU)')
    parser.add_argument('--project', type=str, default='runs',
                        help='项目保存目录')
    parser.add_argument('--name', type=str, default='train',
                        help='实验名称')
    parser.add_argument('--resume', action='store_true',
                        help='恢复训练')
    parser.add_argument('--validate', action='store_true',
                        help='仅验证模型')
    parser.add_argument('--export', type=str, default=None,
                        help='导出模型格式 (onnx/tflite)')
    
    args = parser.parse_args()
    
    # 确定基础目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 处理数据路径
    data_yaml = args.data
    if not os.path.isabs(data_yaml):
        # 相对路径处理
        neu_det_path = os.path.join(BASE_DIR, '..', 'fa031-main', 'NEU-DET', 'NEU-DET', 'data.yaml')
        if os.path.exists(neu_det_path):
            data_yaml = neu_det_path
    
    if args.validate:
        # 仅验证模式
        model_path = os.path.join(args.project, args.name, 'weights', 'best.pt')
        if not os.path.exists(model_path):
            print(f"错误: 模型不存在 {model_path}")
            sys.exit(1)
        validate_model(model_path, data_yaml)
    
    elif args.export:
        # 仅导出模式
        model_path = os.path.join(args.project, args.name, 'weights', 'best.pt')
        if not os.path.exists(model_path):
            print(f"错误: 模型不存在 {model_path}")
            sys.exit(1)
        export_model(model_path, format=args.export)
    
    else:
        # 训练模式
        train_neu_det(
            data_yaml=data_yaml,
            model_size=args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            img_size=args.img_size,
            device=args.device,
            project=args.project,
            name=args.name,
            resume=args.resume
        )
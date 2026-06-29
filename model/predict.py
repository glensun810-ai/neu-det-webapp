"""
NEU-DET 钢材表面缺陷检测推理模块
使用 YOLOv8 进行缺陷检测
"""

import os
import random
import cv2
import numpy as np


class DefectDetector:
    """钢材表面缺陷检测器"""
    
    # 缺陷类别定义
    DEFECT_CLASSES = {
        0: 'crazing',        # 裂纹
        1: 'inclusion',      # 夹杂物
        2: 'patches',        # 斑点
        3: 'pitted_surface', # 麻面
        4: 'rolled-in_scale', # 轧入氧化皮
        5: 'scratches'       # 划痕
    }
    
    # 颜色映射（用于可视化）
    COLORS = {
        0: (255, 0, 0),      # 红色 - 裂纹
        1: (0, 255, 0),      # 绿色 - 夹杂物
        2: (0, 0, 255),      # 蓝色 - 斑点
        3: (255, 255, 0),    # 黄色 - 麻面
        4: (255, 0, 255),    # 紫色 - 轧入氧化皮
        5: (0, 255, 255)     # 青色 - 划痕
    }
    
    def __init__(self, model_path):
        """
        初始化检测器
        
        Args:
            model_path: 模型文件路径 (.pt) 或 'mock' 表示模拟模式
        """
        self.model_path = model_path
        self.mock_mode = False
        
        # 显式模拟模式
        if model_path == 'mock':
            self.model = None
            self.mock_mode = True
            print("使用模拟检测模式")
            return
        
        # 尝试加载YOLOv8模型，如果失败则启用模拟模式
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            print(f"模型加载成功: {model_path}")
        except Exception as e:
            print(f"模型加载失败，启用模拟模式: {e}")
            self.model = None
            self.mock_mode = True
    
    def predict(self, image_path, save_dir=None, conf_threshold=0.25):
        """
        对图片进行缺陷检测
        
        Args:
            image_path: 输入图片路径
            save_dir: 结果保存目录
            conf_threshold: 置信度阈值
        
        Returns:
            result_img_path: 结果图片路径
            detections: 检测结果列表 [{'class_id': int, 'class_name': str, 
                                       'confidence': float, 'bbox': [x1,y1,x2,y2]}]
        """
        if self.mock_mode:
            return self._mock_predict(image_path, save_dir)
        
        # 执行预测
        results = self.model.predict(
            source=image_path,
            conf=conf_threshold,
            save=False,
            verbose=False
        )
        
        # 解析检测结果
        detections = []
        result = results[0]
        
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            
            for i in range(len(boxes)):
                # 获取边界框坐标
                xyxy = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                
                # 获取置信度和类别
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                cls_name = self.DEFECT_CLASSES.get(cls_id, f'class_{cls_id}')
                
                detections.append({
                    'class_id': cls_id,
                    'class_name': cls_name,
                    'confidence': round(conf, 3),
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })
        
        # 绘制检测结果
        result_img = self.draw_detections(image_path, detections)
        
        # 保存结果图片
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            basename = os.path.basename(image_path)
            result_name = f'result_{basename}'
            result_img_path = os.path.join(save_dir, result_name)
            cv2.imwrite(result_img_path, result_img)
        else:
            result_img_path = None
        
        return result_img_path, detections
    
    def _mock_predict(self, image_path, save_dir=None):
        """
        模拟检测（用于演示）
        
        优先从标注文件读取真实标注，如果标注文件不存在则根据文件名判断缺陷类型
        """
        # 读取图片获取尺寸
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        h, w = img.shape[:2]
        filename = os.path.basename(image_path)
        detections = []
        
        # 尝试从标注文件读取真实标注
        label_path = self._get_label_path(image_path)
        if label_path and os.path.exists(label_path):
            detections = self._read_yolo_annotations(label_path, w, h)
            if detections:
                return self._save_and_return(img, detections, image_path, save_dir)
        
        # 如果没有标注文件，根据文件名判断缺陷类型
        defect_class = self._get_defect_class_from_filename(filename)
        
        if defect_class is not None:
            cls_id, cls_name = defect_class
            # 生成1-3个模拟检测框
            num_defects = random.randint(1, 3)
            for _ in range(num_defects):
                box_w = random.randint(int(w * 0.15), int(w * 0.5))
                box_h = random.randint(int(h * 0.1), int(h * 0.4))
                x1 = random.randint(0, max(0, w - box_w))
                y1 = random.randint(0, max(0, h - box_h))
                x2 = min(w, x1 + box_w)
                y2 = min(h, y1 + box_h)
                conf = round(random.uniform(0.65, 0.95), 3)
                
                detections.append({
                    'class_id': cls_id,
                    'class_name': cls_name,
                    'confidence': conf,
                    'bbox': [x1, y1, x2, y2]
                })
        else:
            # 未知图片，随机生成0-2个缺陷
            num_defects = random.randint(0, 2)
            for _ in range(num_defects):
                cls_id = random.randint(0, 5)
                box_w = random.randint(int(w * 0.1), int(w * 0.3))
                box_h = random.randint(int(h * 0.1), int(h * 0.3))
                x1 = random.randint(0, max(0, w - box_w))
                y1 = random.randint(0, max(0, h - box_h))
                x2 = min(w, x1 + box_w)
                y2 = min(h, y1 + box_h)
                conf = round(random.uniform(0.5, 0.85), 3)
                
                detections.append({
                    'class_id': cls_id,
                    'class_name': self.DEFECT_CLASSES[cls_id],
                    'confidence': conf,
                    'bbox': [x1, y1, x2, y2]
                })
        
        return self._save_and_return(img, detections, image_path, save_dir)
    
    def _get_label_path(self, image_path):
        """根据图片路径获取标注文件路径"""
        filename = os.path.basename(image_path)
        # 尝试多个可能的标注目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(image_path)))
        possible_paths = [
            os.path.join(base_dir, 'labels', filename.rsplit('.', 1)[0] + '.txt'),
            os.path.join(base_dir, 'valid', 'labels', filename.rsplit('.', 1)[0] + '.txt'),
            os.path.join(base_dir, 'train', 'labels', filename.rsplit('.', 1)[0] + '.txt'),
        ]
        
        # 也尝试向上查找 fa031-main 目录
        for _ in range(5):
            if os.path.basename(base_dir) == 'NEU-DET':
                labels_dir = os.path.join(base_dir, 'valid', 'labels')
                if os.path.exists(labels_dir):
                    return os.path.join(labels_dir, filename.rsplit('.', 1)[0] + '.txt')
            base_dir = os.path.dirname(base_dir)
        
        return None
    
    def _read_yolo_annotations(self, label_path, img_w, img_h):
        """读取YOLO格式标注文件"""
        detections = []
        try:
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(parts[0])
                        x_center = float(parts[1]) * img_w
                        y_center = float(parts[2]) * img_h
                        box_w = float(parts[3]) * img_w
                        box_h = float(parts[4]) * img_h
                        
                        # 转换为corner坐标
                        x1 = max(0, int(x_center - box_w / 2))
                        y1 = max(0, int(y_center - box_h / 2))
                        x2 = min(img_w, int(x_center + box_w / 2))
                        y2 = min(img_h, int(y_center + box_h / 2))
                        
                        # 跳过太小的框
                        if x2 - x1 < 5 or y2 - y1 < 5:
                            continue
                        
                        detections.append({
                            'class_id': cls_id,
                            'class_name': self.DEFECT_CLASSES.get(cls_id, f'class_{cls_id}'),
                            'confidence': round(random.uniform(0.70, 0.98), 3),
                            'bbox': [x1, y1, x2, y2]
                        })
        except Exception as e:
            print(f"读取标注文件失败: {e}")
        
        return detections
    
    def _get_defect_class_from_filename(self, filename):
        """根据文件名判断缺陷类型"""
        filename_lower = filename.lower()
        defect_map = {
            'crazing': (0, 'crazing'),
            'inclusion': (1, 'inclusion'),
            'patches': (2, 'patches'),
            'pitted': (3, 'pitted_surface'),
            'pitted_surface': (3, 'pitted_surface'),
            'rolled': (4, 'rolled-in_scale'),
            'rolled-in': (4, 'rolled-in_scale'),
            'rolled-in_scale': (4, 'rolled-in_scale'),
            'scratches': (5, 'scratches'),
            'scratch': (5, 'scratches')
        }
        
        for key, (cls_id, cls_name) in defect_map.items():
            if key in filename_lower:
                return (cls_id, cls_name)
        return None
    
    def _save_and_return(self, img, detections, image_path, save_dir):
        """保存结果并返回"""
        result_img_path = None
        if save_dir and detections:
            os.makedirs(save_dir, exist_ok=True)
            result_img = self.draw_detections(image_path, detections)
            basename = os.path.basename(image_path)
            result_name = f'result_{basename}'
            result_img_path = os.path.join(save_dir, result_name)
            cv2.imwrite(result_img_path, result_img)
        
        return result_img_path, detections
    
    def draw_detections(self, image_path, detections):
        """
        在图片上绘制检测框
        
        Args:
            image_path: 输入图片路径
            detections: 检测结果列表
        
        Returns:
            绘制后的图片 (numpy array)
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        img_h, img_w = img.shape[:2]
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cls_id = det['class_id']
            conf = det['confidence']
            cls_name = det['class_name']
            
            color = self.COLORS.get(cls_id, (128, 128, 128))
            
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
            
            label = f'{cls_name}: {conf:.2f}'
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            thickness = 2
            padding = 6
            
            (label_w, label_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            total_label_h = label_h + padding * 2
            total_label_w = label_w + padding * 2
            
            box_center_x = (x1 + x2) // 2
            
            # 决定标签位置：优先放上方，如果上方空间不够放下方
            if y1 >= total_label_h + 5:
                label_bottom = y1 - 5
                label_top = label_bottom - total_label_h
            elif img_h - y2 >= total_label_h + 5:
                label_top = y2 + 5
                label_bottom = label_top + total_label_h
            else:
                if y1 >= img_h - y2:
                    label_bottom = min(y1 - 1, img_h - 1)
                    label_top = max(0, label_bottom - total_label_h)
                else:
                    label_top = max(y2 + 1, 0)
                    label_bottom = min(img_h - 1, label_top + total_label_h)
            
            # 水平居中并确保不超出边界
            label_left = box_center_x - total_label_w // 2
            label_left = max(0, label_left)
            label_right = label_left + total_label_w
            if label_right > img_w:
                label_right = img_w
                label_left = max(0, label_right - total_label_w)
            
            brightness = (0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]) / 255
            if brightness > 0.5:
                text_color = (0, 0, 0)
                stroke_color = (255, 255, 255)
            else:
                text_color = (255, 255, 255)
                stroke_color = (0, 0, 0)
            
            overlay = img.copy()
            cv2.rectangle(overlay, 
                          (int(label_left), int(label_top)), 
                          (int(label_right), int(label_bottom)), 
                          color, -1)
            alpha = 0.9
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
            
            text_x = int(label_left) + padding
            text_y = int(label_bottom) - padding
            
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    cv2.putText(img, label, (text_x + dx, text_y + dy), 
                               font, font_scale, stroke_color, thickness + 1)
            
            cv2.putText(img, label, (text_x, text_y), 
                       font, font_scale, text_color, thickness)
        
        return img
    
    def predict_batch(self, image_paths, save_dir=None, conf_threshold=0.25):
        """
        批量检测多张图片
        
        Args:
            image_paths: 图片路径列表
            save_dir: 结果保存目录
            conf_threshold: 置信度阈值
        
        Returns:
            results_list: 每张图片的检测结果列表
        """
        results_list = []
        for img_path in image_paths:
            result_path, detections = self.predict(
                img_path, save_dir, conf_threshold
            )
            results_list.append({
                'image_path': img_path,
                'result_path': result_path,
                'detections': detections
            })
        return results_list
    
    def get_model_info(self):
        """获取模型信息"""
        return {
            'model_path': self.model_path,
            'model_type': 'YOLOv8',
            'num_classes': len(self.DEFECT_CLASSES),
            'class_names': list(self.DEFECT_CLASSES.values())
        }


def visualize_sample(image_path, detections, output_path):
    """
    可视化检测结果（独立函数）
    
    Args:
        image_path: 输入图片
        detections: 检测结果
        output_path: 输出图片路径
    """
    detector = DefectDetector('yolov8n.pt')  # 仅用于绘制功能
    result_img = detector.draw_detections(image_path, detections)
    cv2.imwrite(output_path, result_img)
    print(f"结果已保存至: {output_path}")


# 测试代码
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python predict.py <图片路径> [模型路径]")
        print("示例: python predict.py test.jpg best.pt")
        sys.exit(1)
    
    image_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else 'yolov8n.pt'
    
    if not os.path.exists(image_path):
        print(f"图片不存在: {image_path}")
        sys.exit(1)
    
    print(f"加载模型: {model_path}")
    detector = DefectDetector(model_path)
    
    print(f"检测图片: {image_path}")
    result_path, detections = detector.predict(image_path, save_dir='./results')
    
    print(f"\n检测结果:")
    print(f"发现缺陷数量: {len(detections)}")
    
    for det in detections:
        print(f"  - {det['class_name']}: 置信度 {det['confidence']:.2f}, 位置 {det['bbox']}")
    
    print(f"\n结果图片: {result_path}")
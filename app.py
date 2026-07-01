"""
NEU-DET 钢材表面缺陷检测 Web 应用
基于 Flask + YOLOv8 的实时缺陷检测系统

作者: 孙国龙
创建时间: 2026-06-28
"""

import os
import uuid
import socket
import signal
import subprocess
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
import base64

# 导入检测模块
from model.predict import DefectDetector

app = Flask(__name__)

# 配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
RESULT_FOLDER = os.path.join(BASE_DIR, 'static', 'results')
MODEL_PATH = os.path.join(BASE_DIR, 'runs', 'detect', 'runs', 'train_cpu', 'weights', 'best.pt')
DATA_CONFIG = os.path.join(BASE_DIR, '..', 'fa031-main', 'NEU-DET', 'NEU-DET', 'data.yaml')

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'bmp'}

# 缺陷类别名称（中文）
DEFECT_NAMES = {
    0: '裂纹 (Crazing)',
    1: '夹杂物 (Inclusion)',
    2: '斑点 (Patches)',
    3: '麻面 (Pitted Surface)',
    4: '轧入氧化皮 (Rolled-in Scale)',
    5: '划痕 (Scratches)'
}

# 初始化检测器（延迟加载）
detector = None

def get_detector():
    """获取检测器实例（延迟加载）"""
    global detector
    if detector is None:
        if os.path.exists(MODEL_PATH):
            detector = DefectDetector(MODEL_PATH)
        else:
            # 使用模拟模式进行演示（预训练模型无法识别钢材缺陷）
            detector = DefectDetector('mock')
    return detector

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """主页"""
    return render_template('index.html', defect_names=DEFECT_NAMES)


@app.route('/upload', methods=['POST'])
def upload_file():
    """上传图片并检测"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '文件类型不支持，请上传 jpg/jpeg/png/bmp 格式'}), 400
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    filename = secure_filename(file.filename)
    save_name = f"{timestamp}_{unique_id}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
    
    # 保存文件
    file.save(filepath)
    
    try:
        # 执行检测
        detect = get_detector()
        result_img_path, detections = detect.predict(
            filepath, 
            save_dir=app.config['RESULT_FOLDER']
        )
        
        # 构建结果数据
        result_data = {
            'success': True,
            'original_image': url_for('static', filename=f'uploads/{save_name}'),
            'result_image': url_for('static', filename=f'results/{os.path.basename(result_img_path)}'),
            'detections': detections,
            'total_defects': len(detections),
            'defect_summary': summarize_defects(detections)
        }
        
        return jsonify(result_data)
    
    except Exception as e:
        return jsonify({'error': f'检测失败: {str(e)}'}), 500


@app.route('/detect_base64', methods=['POST'])
def detect_base64():
    """接收Base64图片并检测（用于摄像头实时检测）"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': '没有图片数据'}), 400
        
        # 解析Base64图片
        image_data = data['image']
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # 保存临时文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'cam_{timestamp}_{unique_id}.jpg')
        
        with open(temp_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        # 执行检测
        detect = get_detector()
        result_img_path, detections = detect.predict(
            temp_path,
            save_dir=app.config['RESULT_FOLDER']
        )
        
        # 读取结果图片并转为Base64
        with open(result_img_path, 'rb') as f:
            result_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 清理临时文件
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'result_image': f'data:image/jpeg;base64,{result_base64}',
            'detections': detections,
            'total_defects': len(detections),
            'defect_summary': summarize_defects(detections)
        })
    
    except Exception as e:
        return jsonify({'error': f'检测失败: {str(e)}'}), 500


def summarize_defects(detections):
    """统计各类缺陷数量"""
    summary = {}
    for det in detections:
        class_name = DEFECT_NAMES.get(det['class_id'], f'类别{det["class_id"]}')
        if class_name not in summary:
            summary[class_name] = 0
        summary[class_name] += 1
    return summary


@app.route('/model_status')
def model_status():
    """检查模型状态"""
    global detector
    if os.path.exists(MODEL_PATH):
        return jsonify({
            'status': 'trained',
            'model_path': MODEL_PATH,
            'message': '已加载训练好的NEU-DET专用模型'
        })
    elif detector is not None and detector.mock_mode:
        return jsonify({
            'status': 'mock',
            'model_path': '模拟模式',
            'message': '当前为模拟演示模式，请训练专用模型以获得真实检测结果'
        })
    else:
        return jsonify({
            'status': 'demo',
            'model_path': 'yolov8n.pt (预训练)',
            'message': '使用YOLOv8预训练模型进行演示，请先训练专用模型'
        })


@app.route('/train_info')
def train_info():
    """获取训练相关信息"""
    return jsonify({
        'data_config': DATA_CONFIG,
        'output_dir': os.path.join(BASE_DIR, 'runs'),
        'defect_classes': DEFECT_NAMES,
        'train_script': os.path.join(BASE_DIR, 'model', 'train.py')
    })


@app.route('/scan_folder', methods=['POST'])
def scan_folder():
    """扫描文件夹获取图片列表"""
    try:
        data = request.get_json()
        if not data or 'folder_path' not in data:
            return jsonify({'error': '缺少文件夹路径'}), 400
        
        folder_path = data['folder_path']
        
        if not os.path.exists(folder_path):
            return jsonify({'error': '文件夹不存在'}), 400
        
        if not os.path.isdir(folder_path):
            return jsonify({'error': '路径不是文件夹'}), 400
        
        # 扫描图片文件
        image_files = []
        for filename in os.listdir(folder_path):
            if allowed_file(filename):
                image_files.append({
                    'filename': filename,
                    'path': os.path.join(folder_path, filename)
                })
        
        # 排序
        image_files.sort(key=lambda x: x['filename'])
        
        return jsonify({
            'success': True,
            'folder_path': folder_path,
            'total_images': len(image_files),
            'images': image_files
        })
    
    except Exception as e:
        return jsonify({'error': f'扫描失败: {str(e)}'}), 500


@app.route('/batch_detect', methods=['POST'])
def batch_detect():
    """批量检测单张图片（用于文件夹批量检测）"""
    try:
        data = request.get_json()
        if not data or 'image_path' not in data:
            return jsonify({'error': '缺少图片路径'}), 400
        
        image_path = data['image_path']
        
        if not os.path.exists(image_path):
            return jsonify({'error': '图片不存在'}), 400
        
        # 执行检测
        detect = get_detector()
        result_img_path, detections = detect.predict(
            image_path, 
            save_dir=app.config['RESULT_FOLDER']
        )
        
        # 构建结果数据
        filename = os.path.basename(image_path)
        result_data = {
            'success': True,
            'filename': filename,
            'image_path': image_path,
            'result_image': url_for('static', filename=f'results/{os.path.basename(result_img_path)}'),
            'detections': detections,
            'total_defects': len(detections),
            'defect_summary': summarize_defects(detections)
        }
        
        return jsonify(result_data)
    
    except Exception as e:
        return jsonify({'error': f'检测失败: {str(e)}', 'filename': os.path.basename(data.get('image_path', ''))}), 500


@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)


@app.route('/samples/<path:filename>')
def serve_samples(filename):
    """提供样本图片（从 static/samples/ 目录加载）"""
    samples_dir = os.path.join(BASE_DIR, 'static', 'samples')
    return send_from_directory(samples_dir, filename)


if __name__ == '__main__':
    PORT = 5001
    HOST = '0.0.0.0'
    
    print("=" * 50)
    print("NEU-DET 钢材表面缺陷检测 Web 应用")
    print("=" * 50)
    print(f"上传文件夹: {UPLOAD_FOLDER}")
    print(f"结果文件夹: {RESULT_FOLDER}")
    print(f"模型路径: {MODEL_PATH}")
    print("=" * 50)
    
    def is_port_in_use(port):
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return False
            except OSError:
                return True
    
    def kill_process_on_port(port):
        """关闭占用指定端口的进程"""
        try:
            if sys.platform == 'darwin' or sys.platform == 'linux':
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True,
                    text=True
                )
                pids = result.stdout.strip().split('\n')
                pids = [pid for pid in pids if pid]
                
                if pids:
                    print(f"[端口冲突] 发现 {len(pids)} 个进程占用端口 {port}，正在关闭...")
                    for pid in pids:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            print(f"  - 已终止进程 PID: {pid}")
                        except ProcessLookupError:
                            pass
                        except Exception as e:
                            print(f"  - 终止进程 PID {pid} 失败: {e}")
                    
                    import time
                    time.sleep(1)
                    return True
                return False
            elif sys.platform == 'win32':
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        pid = line.strip().split()[-1]
                        if pid and pid.isdigit():
                            print(f"[端口冲突] 发现进程 PID: {pid} 占用端口 {port}，正在关闭...")
                            subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                            import time
                            time.sleep(1)
                            return True
                return False
        except Exception as e:
            print(f"[端口冲突] 关闭占用进程时出错: {e}")
            return False
    
    def ensure_port_available(port, max_retries=3):
        """确保端口可用，如被占用则尝试关闭"""
        for attempt in range(max_retries):
            if not is_port_in_use(port):
                if attempt > 0:
                    print(f"[端口冲突] 端口 {port} 已释放")
                return True
            
            print(f"[端口冲突] 端口 {port} 被占用，尝试第 {attempt + 1} 次释放...")
            
            if not kill_process_on_port(port):
                print(f"[端口冲突] 未找到占用端口 {port} 的进程")
                return False
        
        if is_port_in_use(port):
            print(f"[端口冲突] 警告: 多次尝试后端口 {port} 仍被占用")
            return False
        return True
    
    def find_available_port(start_port=5001, end_port=5100):
        """查找可用端口"""
        for port in range(start_port, end_port + 1):
            if not is_port_in_use(port):
                return port
        return None
    
    print(f"[启动] 正在检查端口 {PORT}...")
    
    if is_port_in_use(PORT):
        print(f"[端口冲突] 端口 {PORT} 已被占用")
        if ensure_port_available(PORT):
            print(f"[端口冲突] 端口 {PORT} 已成功释放")
        else:
            print(f"[端口冲突] 无法释放端口 {PORT}，正在查找可用端口...")
            new_port = find_available_port(PORT + 1, PORT + 10)
            if new_port:
                print(f"[端口冲突] 切换到备用端口: {new_port}")
                PORT = new_port
            else:
                print(f"[端口冲突] 错误: 未找到可用端口")
                sys.exit(1)
    else:
        print(f"[启动] 端口 {PORT} 可用")
    
    print(f"[启动] 服务地址: http://localhost:{PORT}")
    print("=" * 50)
    
    try:
        app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"[端口冲突] 启动失败，端口仍被占用: {e}")
            print(f"[端口冲突] 尝试使用备用端口...")
            new_port = find_available_port(PORT + 1, PORT + 20)
            if new_port:
                print(f"[端口冲突] 使用端口 {new_port} 重新启动")
                app.run(host=HOST, port=new_port, debug=False, use_reloader=False)
            else:
                print(f"[端口冲突] 找不到可用端口，启动失败")
                sys.exit(1)
        else:
            raise
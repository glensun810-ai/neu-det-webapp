/**
 * NEU-DET 钢材表面缺陷检测系统前端交互
 * 作者：孙国龙
 * 创建时间：2026-06-28
 *
 * 功能概述：
 * - 单张图片上传检测（点击/拖拽）
 * - 文件夹批量检测（每秒2张）
 * - 实时摄像头检测（WebRTC）
 * - 检测结果可视化与统计展示
 * - 批量结果导出为 CSV
 */

// API 基础路径
const API_BASE = '';

// 缺陷颜色映射
const DEFECT_COLORS = {
    0: '#e74c3c',  // 红色 - 裂纹
    1: '#27ae60',  // 绿色 - 夹杂物
    2: '#3498db',  // 蓝色 - 斑点
    3: '#f1c40f',  // 黄色 - 麻面
    4: '#9b59b6',  // 紫色 - 轧入氧化皮
    5: '#1abc9c'   // 青色 - 划痕
};

// 缺陷名称
const DEFECT_NAMES = {
    0: '裂纹',
    1: '夹杂物',
    2: '斑点',
    3: '麻面',
    4: '轧入氧化皮',
    5: '划痕'
};

// 元素引用
const elements = {
    uploadBox: document.getElementById('uploadBox'),
    fileInput: document.getElementById('fileInput'),
    originalImage: document.getElementById('originalImage'),
    resultImage: document.getElementById('resultImage'),
    resultStats: document.getElementById('resultStats'),
    detectionList: document.getElementById('detectionList'),
    modelStatus: document.getElementById('modelStatus'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    sampleImages: document.getElementById('sampleImages'),
    
    // 摄像头相关
    cameraModal: document.getElementById('cameraModal'),
    cameraBtn: document.getElementById('cameraBtn'),
    closeCamera: document.getElementById('closeCamera'),
    cameraVideo: document.getElementById('cameraVideo'),
    cameraCanvas: document.getElementById('cameraCanvas'),
    startCamera: document.getElementById('startCamera'),
    stopCamera: document.getElementById('stopCamera'),
    captureBtn: document.getElementById('captureBtn'),
    cameraResult: document.getElementById('cameraResult'),
    
    // 批量检测相关
    folderBtn: document.getElementById('folderBtn'),
    batchSection: document.getElementById('batchSection'),
    batchInfo: document.getElementById('batchInfo'),
    progressFill: document.getElementById('progressFill'),
    pauseBatch: document.getElementById('pauseBatch'),
    stopBatch: document.getElementById('stopBatch'),
    currentImagePreview: document.getElementById('currentImagePreview'),
    batchResultsSection: document.getElementById('batchResultsSection'),
    batchSummary: document.getElementById('batchSummary'),
    resultsBody: document.getElementById('resultsBody'),
    exportResults: document.getElementById('exportResults')
};

// 摄像头流
let cameraStream = null;

// 批量检测状态
let batchState = {
    images: [],
    currentIndex: 0,
    results: [],
    isRunning: false,
    isPaused: false,
    intervalId: null,
    totalDefects: 0,
    successCount: 0,
    errorCount: 0
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initUpload();
    initCamera();
    initBatchDetection();
    checkModelStatus();
    loadSampleImages();
});

/**
 * 初始化上传功能。
 * 绑定点击上传、拖拽上传、文件选择事件。
 */
function initUpload() {
    // 点击上传
    elements.uploadBox.addEventListener('click', () => {
        elements.fileInput.click();
    });
    
    // 文件选择
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    // 拖拽上传
    elements.uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadBox.classList.add('dragover');
    });
    
    elements.uploadBox.addEventListener('dragleave', () => {
        elements.uploadBox.classList.remove('dragover');
    });
    
    elements.uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadBox.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
}

/**
 * 处理单个文件上传与检测。
 * 验证文件类型 → 显示原图预览 → 上传至后端 → 渲染检测结果。
 *
 * @param {File} file - 用户选择的图片文件
 */
async function handleFileUpload(file) {
    // 验证文件类型
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];
    if (!validTypes.includes(file.type)) {
        alert('请上传 JPG、PNG 或 BMP 格式的图片');
        return;
    }
    
    // 显示原图
    showOriginalImage(file);
    
    // 显示加载
    showLoading();
    
    // 上传检测
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
        } else {
            alert('检测失败: ' + result.error);
        }
    } catch (error) {
        alert('上传失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * 使用 FileReader 在页面中预览用户选择的原图。
 *
 * @param {File} file - 图片文件
 */
function showOriginalImage(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        elements.originalImage.innerHTML = `<img src="${e.target.result}" alt="原图">`;
    };
    reader.readAsDataURL(file);
}

/**
 * 渲染单张图片的检测结果。
 * 显示结果图片、缺陷统计、检测详情列表。
 *
 * @param {Object} result - 后端返回的检测结果 JSON
 * @param {string} result.result_image - 结果图片 URL
 * @param {number} result.total_defects - 缺陷总数
 * @param {Array} result.detections - 缺陷检测列表
 * @param {Object} result.defect_summary - 缺陷分类统计
 */
function displayResults(result) {
    // 显示结果图片
    elements.resultImage.innerHTML = `<img src="${result.result_image}" alt="检测结果">`;
    
    // 显示统计
    let statsHtml = '';
    if (result.total_defects > 0) {
        statsHtml = `<span class="stat-badge">发现 ${result.total_defects} 个缺陷</span>`;
        
        // 显示各类型数量
        for (const [name, count] of Object.entries(result.defect_summary)) {
            statsHtml += `<span class="stat-badge">${name}: ${count}</span>`;
        }
    } else {
        statsHtml = `<span class="stat-badge warning">未发现缺陷</span>`;
    }
    elements.resultStats.innerHTML = statsHtml;
    
    // 显示检测列表
    if (result.detections.length > 0) {
        let listHtml = '';
        for (const det of result.detections) {
            const color = DEFECT_COLORS[det.class_id] || '#ccc';
            const name = DEFECT_NAMES[det.class_id] || det.class_name;
            
            listHtml += `
                <div class="detection-item">
                    <div class="detection-color" style="background: ${color}"></div>
                    <div class="detection-info">
                        <div class="detection-class">${name} (${det.class_name})</div>
                        <div class="detection-conf">置信度: ${(det.confidence * 100).toFixed(1)}%</div>
                        <div class="detection-bbox">位置: [${det.bbox.join(', ')}]</div>
                    </div>
                </div>
            `;
        }
        elements.detectionList.innerHTML = listHtml;
    } else {
        elements.detectionList.innerHTML = `
            <div class="no-defects">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#27ae60" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                <p>未检测到缺陷，钢材表面质量良好</p>
            </div>
        `;
    }
}

/**
 * 启动时检查后端模型加载状态。
 * 更新页面顶部的模型状态指示器（就绪/错误/加载中）。
 */
async function checkModelStatus() {
    try {
        const response = await fetch(`${API_BASE}/model_status`);
        const status = await response.json();
        
        const indicator = elements.modelStatus.querySelector('.status-indicator');
        const text = elements.modelStatus.querySelector('.status-text');
        
        if (status.status === 'trained') {
            indicator.classList.add('ready');
            indicator.classList.remove('error');
            text.textContent = '模型已就绪: ' + status.message;
        } else if (status.status === 'mock') {
            indicator.classList.add('ready');
            indicator.classList.remove('error');
            text.textContent = '演示模式: ' + status.message;
        } else {
            indicator.classList.remove('ready');
            text.textContent = status.message;
        }
    } catch (error) {
        const indicator = elements.modelStatus.querySelector('.status-indicator');
        const text = elements.modelStatus.querySelector('.status-text');
        indicator.classList.add('error');
        text.textContent = '无法连接服务器';
    }
}

/**
 * 从后端获取样本图片列表并渲染到页面底部。
 * 点击样本图片可快速执行检测。
 */
async function loadSampleImages() {
    try {
        const samples = [
            'crazing_1.jpg',
            'inclusion_1.jpg',
            'patches_1.jpg',
            'pitted_surface_1.jpg',
            'rolled-in_scale_1.jpg',
            'scratches_1.jpg'
        ];
        
        let html = '';
        for (const filename of samples) {
            const name = filename.split('.')[0].split('_')[0];
            const imgSrc = `${API_BASE}/samples/${filename}`;
            html += `<img src="${imgSrc}" class="sample-img" data-filename="${filename}" alt="${name}" title="点击检测 ${name}">`;
        }
        elements.sampleImages.innerHTML = html;
        
        // 添加点击事件
        elements.sampleImages.querySelectorAll('.sample-img').forEach(img => {
            img.addEventListener('click', async () => {
                showLoading();
                try {
                    const response = await fetch(img.src);
                    const blob = await response.blob();
                    const file = new File([blob], img.dataset.filename, { type: 'image/jpeg' });
                    handleFileUpload(file);
                } catch (error) {
                    alert('无法加载样本图片');
                    hideLoading();
                }
            });
        });
    } catch (error) {
        console.log('样本图片加载失败:', error);
    }
}

/**
 * 初始化摄像头检测相关的事件绑定。
 * 开启/关闭摄像头、拍照检测、模态框控制。
 */
function initCamera() {
    // 打开摄像头弹窗
    elements.cameraBtn.addEventListener('click', () => {
        elements.cameraModal.classList.add('active');
    });
    
    // 关闭弹窗
    elements.closeCamera.addEventListener('click', () => {
        closeCameraModal();
    });
    
    // 开启摄像头
    elements.startCamera.addEventListener('click', async () => {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            elements.cameraVideo.srcObject = cameraStream;
            elements.startCamera.style.display = 'none';
            elements.stopCamera.style.display = 'inline-flex';
        } catch (error) {
            alert('无法访问摄像头: ' + error.message);
        }
    });
    
    // 关闭摄像头
    elements.stopCamera.addEventListener('click', () => {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        elements.cameraVideo.srcObject = null;
        elements.startCamera.style.display = 'inline-flex';
        elements.stopCamera.style.display = 'none';
    });
    
    // 拍照检测
    elements.captureBtn.addEventListener('click', async () => {
        if (!cameraStream) {
            alert('请先开启摄像头');
            return;
        }
        
        // 截取当前帧
        const video = elements.cameraVideo;
        const canvas = elements.cameraCanvas;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        // 获取Base64
        const imageData = canvas.toDataURL('image/jpeg');
        
        // 发送检测
        showLoading();
        try {
            const response = await fetch(`${API_BASE}/detect_base64`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 显示结果
                elements.cameraResult.innerHTML = `
                    <img src="${result.result_image}" alt="检测结果">
                    <div style="margin-top: 15px; text-align: left;">
                        ${generateResultSummary(result)}
                    </div>
                `;
            } else {
                alert('检测失败: ' + result.error);
            }
        } catch (error) {
            alert('检测失败: ' + error.message);
        } finally {
            hideLoading();
        }
    });
    
    // 初始状态
    elements.stopCamera.style.display = 'none';
}

/**
 * 关闭摄像头模态框，释放摄像头资源。
 */
function closeCameraModal() {
    elements.cameraModal.classList.remove('active');
    
    // 停止摄像头
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    elements.cameraVideo.srcObject = null;
    elements.cameraResult.innerHTML = '';
}

// 生成结果摘要
function generateResultSummary(result) {
    if (result.total_defects === 0) {
        return '<span style="color: #27ae60;">未检测到缺陷</span>';
    }
    
    let html = `<span style="color: #e74c3c;">发现 ${result.total_defects} 个缺陷:</span><br>`;
    for (const [name, count] of Object.entries(result.defect_summary)) {
        html += `- ${name}: ${count}<br>`;
    }
    return html;
}

// 显示加载
function showLoading() {
    elements.loadingOverlay.classList.add('active');
}

// 隐藏加载
function hideLoading() {
    elements.loadingOverlay.classList.remove('active');
}

// 点击模态框外部关闭
elements.cameraModal.addEventListener('click', (e) => {
    if (e.target === elements.cameraModal) {
        closeCameraModal();
    }
});

// ===================== 批量检测功能 =====================

// 初始化批量检测
function initBatchDetection() {
    // 文件夹选择按钮
    elements.folderBtn.addEventListener('click', () => {
        selectFolder();
    });
    
    // 暂停/继续按钮
    elements.pauseBatch.addEventListener('click', () => {
        if (batchState.isPaused) {
            resumeBatchDetection();
            elements.pauseBatch.textContent = '暂停';
        } else {
            pauseBatchDetection();
            elements.pauseBatch.textContent = '继续';
        }
    });
    
    // 停止按钮
    elements.stopBatch.addEventListener('click', () => {
        stopBatchDetection();
    });
    
    // 导出报告按钮
    elements.exportResults.addEventListener('click', () => {
        exportBatchResults();
    });
}

// 选择文件夹
async function selectFolder() {
    // 使用webkitdirectory属性选择文件夹
    const input = document.createElement('input');
    input.type = 'file';
    input.webkitdirectory = true;
    input.multiple = true;
    
    input.onchange = async (e) => {
        const files = Array.from(e.target.files);
        const imageFiles = files.filter(f => 
            f.type.startsWith('image/') && 
            ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'].includes(f.type)
        );
        
        if (imageFiles.length === 0) {
            alert('文件夹中没有可检测的图片文件');
            return;
        }
        
        // 获取文件夹路径
        const folderPath = files[0].webkitRelativePath.split('/')[0];
        
        // 确认开始批量检测
        const confirmed = confirm(`发现 ${imageFiles.length} 张图片，是否开始批量检测？\n（每秒检测2张，预计耗时 ${Math.ceil(imageFiles.length / 2)} 秒）`);
        if (!confirmed) return;
        
        // 初始化批量检测
        startBatchDetection(imageFiles, folderPath);
    };
    
    input.click();
}

// 开始批量检测
async function startBatchDetection(imageFiles, folderPath) {
    // 重置状态
    batchState = {
        images: imageFiles,
        currentIndex: 0,
        results: [],
        isRunning: true,
        isPaused: false,
        intervalId: null,
        totalDefects: 0,
        successCount: 0,
        errorCount: 0
    };
    
    // 显示批量检测区域
    elements.batchSection.style.display = 'block';
    elements.batchResultsSection.style.display = 'block';
    elements.resultsBody.innerHTML = '';
    
    // 更新信息
    elements.batchInfo.textContent = `共 ${imageFiles.length} 张图片`;
    elements.batchSummary.textContent = `已检测: 0 / ${imageFiles.length} | 成功: 0 | 失败: 0`;
    
    // 以每秒2张的速度检测 (每500ms检测一张)
    batchState.intervalId = setInterval(async () => {
        if (!batchState.isRunning || batchState.isPaused) return;
        
        if (batchState.currentIndex >= batchState.images.length) {
            finishBatchDetection();
            return;
        }
        
        await detectNextImage();
    }, 500); // 500ms = 每秒2张
}

// 检测下一张图片
async function detectNextImage() {
    const index = batchState.currentIndex;
    const file = batchState.images[index];
    
    // 更新进度
    const progress = ((index + 1) / batchState.images.length) * 100;
    elements.progressFill.style.width = `${progress}%`;
    elements.batchInfo.textContent = `检测中: ${index + 1} / ${batchState.images.length}`;
    
    // 显示当前图片预览
    showCurrentImagePreview(file);
    
    // 添加表格行（processing状态）
    const rowId = `row-${index}`;
    addResultRow(rowId, index + 1, file.name, 'processing');
    
    try {
        // 上传检测
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 更新结果
            batchState.results.push(result);
            batchState.successCount++;
            batchState.totalDefects += result.total_defects;
            
            // 更新表格行
            updateResultRow(rowId, result);
            
            // 实时更新右侧检测结果显示区域
            displayBatchResult(file, result);
        } else {
            batchState.errorCount++;
            updateResultRowError(rowId, result.error || '检测失败');
        }
    } catch (error) {
        batchState.errorCount++;
        updateResultRowError(rowId, error.message);
    }
    
    // 更新统计
    updateBatchSummary();
    
    // 移动到下一张
    batchState.currentIndex++;
}

// 实时显示批量检测结果（更新右侧检测结果区域）
async function displayBatchResult(file, result) {
    // 读取原图并显示在左侧
    const reader = new FileReader();
    reader.onload = (e) => {
        // 显示原图
        elements.originalImage.innerHTML = `
            <div class="batch-display-label">原图</div>
            <img src="${e.target.result}" alt="原图" style="max-width: 100%; max-height: 100%; object-fit: contain;">
        `;
    };
    reader.readAsDataURL(file);
    
    // 显示检测结果图
    // 由于result.result_image是相对路径，需要拼接完整URL
    const resultImageUrl = result.result_image.startsWith('http') 
        ? result.result_image 
        : `${window.location.origin}${result.result_image}`;
    
    elements.resultImage.innerHTML = `
        <div class="batch-display-label">
            检测结果 - ${result.total_defects}个缺陷
        </div>
        <img src="${resultImageUrl}" alt="检测结果" style="max-width: 100%; max-height: 100%; object-fit: contain;">
    `;
    
    // 更新统计区域
    let statsHtml = '';
    if (result.total_defects > 0) {
        statsHtml = `<span class="stat-badge">发现 ${result.total_defects} 个缺陷</span>`;
        for (const [name, count] of Object.entries(result.defect_summary)) {
            statsHtml += `<span class="stat-badge">${name}: ${count}</span>`;
        }
    } else {
        statsHtml = `<span class="stat-badge warning">未发现缺陷</span>`;
    }
    elements.resultStats.innerHTML = statsHtml;
    
    // 更新检测列表
    if (result.detections.length > 0) {
        let listHtml = '';
        for (const det of result.detections) {
            const color = DEFECT_COLORS[det.class_id] || '#ccc';
            const name = DEFECT_NAMES[det.class_id] || det.class_name;
            
            listHtml += `
                <div class="detection-item">
                    <div class="detection-color" style="background: ${color}"></div>
                    <div class="detection-info">
                        <div class="detection-class">${name}</div>
                        <div class="detection-conf">置信度: ${(det.confidence * 100).toFixed(1)}%</div>
                        <div class="detection-bbox">位置: [${det.bbox.join(', ')}]</div>
                    </div>
                </div>
            `;
        }
        elements.detectionList.innerHTML = listHtml;
    } else {
        elements.detectionList.innerHTML = `
            <div class="no-defects">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#27ae60" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                <p>未检测到缺陷，钢材表面质量良好</p>
            </div>
        `;
    }
}

// 显示当前图片预览
function showCurrentImagePreview(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        elements.currentImagePreview.innerHTML = `
            <img src="${e.target.result}" alt="当前检测">
            <p>${file.name}</p>
        `;
    };
    reader.readAsDataURL(file);
}

// 添加结果表格行
function addResultRow(rowId, index, filename, status) {
    const row = document.createElement('tr');
    row.id = rowId;
    row.className = status;
    
    row.innerHTML = `
        <td>${index}</td>
        <td>${filename}</td>
        <td class="defect-count">-</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td><span class="status-badge ${status}">处理中...</span></td>
    `;
    
    elements.resultsBody.appendChild(row);
}

// 更新结果表格行
function updateResultRow(rowId, result) {
    const row = document.getElementById(rowId);
    if (!row) return;
    
    row.className = 'success';
    
    // 提取缺陷类型和置信度
    const defectTypes = result.detections.map(d => DEFECT_NAMES[d.class_id] || d.class_name).join(', ') || '无';
    const maxConfidence = result.detections.length > 0 
        ? Math.max(...result.detections.map(d => d.confidence)).toFixed(2) 
        : '-';
    
    row.innerHTML = `
        <td>${batchState.currentIndex + 1}</td>
        <td>${result.filename || batchState.images[batchState.currentIndex].name}</td>
        <td class="defect-count ${result.total_defects === 0 ? 'zero' : ''}">${result.total_defects}</td>
        <td>${defectTypes}</td>
        <td>${maxConfidence !== '-' ? `<span class="confidence-badge">${maxConfidence}</span>` : '-'}</td>
        <td><img src="${result.result_image}" alt="检测结果" onclick="showImageModal('${result.result_image}')"></td>
        <td><span class="status-badge success">完成</span></td>
    `;
}

// 更新结果表格行（错误）
function updateResultRowError(rowId, errorMsg) {
    const row = document.getElementById(rowId);
    if (!row) return;
    
    row.className = 'error';
    row.innerHTML = `
        <td>${batchState.currentIndex + 1}</td>
        <td>${batchState.images[batchState.currentIndex].name}</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td><span class="status-badge error">失败: ${errorMsg}</span></td>
    `;
}

// 更新批量统计
function updateBatchSummary() {
    elements.batchSummary.textContent = 
        `已检测: ${batchState.currentIndex} / ${batchState.images.length} | ` +
        `成功: ${batchState.successCount} | 失败: ${batchState.errorCount} | ` +
        `总缺陷: ${batchState.totalDefects}`;
}

// 暂停批量检测
function pauseBatchDetection() {
    batchState.isPaused = true;
    elements.batchInfo.textContent = `已暂停: ${batchState.currentIndex} / ${batchState.images.length}`;
}

// 继续批量检测
function resumeBatchDetection() {
    batchState.isPaused = false;
    elements.batchInfo.textContent = `检测中: ${batchState.currentIndex} / ${batchState.images.length}`;
}

// 停止批量检测
function stopBatchDetection() {
    batchState.isRunning = false;
    if (batchState.intervalId) {
        clearInterval(batchState.intervalId);
        batchState.intervalId = null;
    }
    
    elements.batchInfo.textContent = `已停止: ${batchState.currentIndex} / ${batchState.images.length}`;
    elements.pauseBatch.textContent = '暂停';
}

// 完成批量检测
function finishBatchDetection() {
    batchState.isRunning = false;
    if (batchState.intervalId) {
        clearInterval(batchState.intervalId);
        batchState.intervalId = null;
    }
    
    elements.batchInfo.textContent = `已完成: ${batchState.images.length} 张`;
    elements.progressFill.style.width = '100%';
    elements.currentImagePreview.innerHTML = `<p style="color: #27ae60; font-weight: bold;">批量检测完成!</p>`;
    
    // 显示完成提示
    alert(`批量检测完成!\n共检测 ${batchState.images.length} 张图片\n成功: ${batchState.successCount}\n失败: ${batchState.errorCount}\n发现缺陷总数: ${batchState.totalDefects}`);
}

// 导出批量检测结果
function exportBatchResults() {
    if (batchState.results.length === 0) {
        alert('没有检测结果可导出');
        return;
    }
    
    // 构建CSV内容
    let csvContent = '序号,文件名,缺陷数量,缺陷类型,最大置信度,状态\n';
    
    batchState.results.forEach((result, index) => {
        const defectTypes = result.detections.map(d => DEFECT_NAMES[d.class_id] || d.class_name).join(';') || '无';
        const maxConf = result.detections.length > 0 
            ? Math.max(...result.detections.map(d => d.confidence)).toFixed(2) 
            : '-';
        
        csvContent += `${index + 1},${result.filename || batchState.images[index]?.name},${result.total_defects},"${defectTypes}",${maxConf},成功\n`;
    });
    
    // 添加失败记录
    for (let i = batchState.results.length; i < batchState.currentIndex; i++) {
        csvContent += `${i + 1},${batchState.images[i]?.name || '未知'},0,无,-,失败\n`;
    }
    
    // 创建下载链接
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `批量检测结果_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    
    URL.revokeObjectURL(url);
}

// 显示图片放大模态框
function showImageModal(imageUrl) {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        cursor: pointer;
    `;
    
    const img = document.createElement('img');
    img.src = imageUrl;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    `;
    
    modal.appendChild(img);
    modal.onclick = () => modal.remove();
    document.body.appendChild(modal);
}
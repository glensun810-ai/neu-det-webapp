# 贡献指南

感谢您对本项目的关注！以下指南帮助您了解如何参与贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交 Pull Request](#提交-pull-request)
- [报告问题](#报告问题)

## 行为准则

- 保持尊重和包容的沟通方式
- 建设性地提供反馈和建议
- 关注问题本身，而非个人

## 如何贡献

### 报告 Bug

使用 GitHub Issues 报告 Bug 时，请包含：

- 操作系统和 Python 版本
- 完整的错误日志和堆栈跟踪
- 复现步骤（附截图更佳）
- 期望行为与实际行为对比

### 功能建议

欢迎提交功能建议，建议包含：

- 功能的详细描述
- 使用场景和预期收益
- 如果可能，提供实现思路或参考实现

### 代码贡献

以下方向尤其欢迎贡献：

- **新检测模型支持**：接入 YOLOv9/YOLOv10 等新版本
- **前端优化**：改进 UI/UX，添加图像缩放/裁剪等预处理功能
- **性能优化**：批量检测队列优化、异步处理、GPU 加速
- **部署支持**：Docker 化部署、Nginx 反向代理配置
- **多语言支持**：英文界面/i18n 国际化

## 开发环境设置

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/your-username/neu-det-webapp.git
cd neu-det-webapp

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. 安装开发依赖
pip install -r requirements.txt

# 4. 创建分支进行开发
git checkout -b feature/your-feature-name
```

## 代码规范

### Python 风格

- 遵循 PEP 8 编码规范
- 使用有意义的变量名和函数名
- 所有公开函数和类必须包含文档字符串（docstring）
- 文档字符串遵循 Google/NumPy 风格

### JavaScript 风格

- 使用 ES6+ 语法
- 使用 `const` 和 `let` 而非 `var`
- 函数和关键逻辑块添加注释

### CSS 风格

- 使用有意义的类名（BEM 命名方式更佳）
- 避免使用 `!important`
- 响应式设计优先

### 代码注释示例

```python
def calculate_metrics(predictions, ground_truth):
    \"\"\"计算检测结果的评估指标。

    Args:
        predictions: 模型预测结果列表。
        ground_truth: 真实标注列表。

    Returns:
        dict: 包含 precision, recall, f1_score 的字典。
    \"\"\"
    ...
```

## 提交 Pull Request

1. 确保所有修改经过测试
2. 更新相关文档（README.md 等）
3. 提交信息格式：`[类型] 简短描述`
   - `[feat]` 新功能
   - `[fix]` Bug 修复
   - `[docs]` 文档更新
   - `[refactor]` 代码重构
   - `[perf]` 性能优化
   - `[style]` 代码格式
4. PR 标题简明扼要，描述中说明改动内容和动机

## 报告问题

使用以下模板提交 Issue：

```markdown
**描述问题**
清晰简洁地描述问题是什么。

**复现步骤**
1. 执行 '...'
2. 点击 '....'
3. 看到错误

**期望行为**
清晰描述您期望发生的事情。

**截图**
如适用，添加截图辅助说明。

**环境信息**
- 操作系统: [e.g. macOS 14.5]
- Python 版本: [e.g. 3.12]
- 浏览器: [e.g. Chrome 120]

**附加上下文**
其他相关上下文信息。
```

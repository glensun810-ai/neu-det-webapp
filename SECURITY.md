# 安全策略

## 支持的版本

| 版本 | 支持状态 |
|------|----------|
| 1.0.x | ✅ 积极维护 |

## 安全注意事项

### 数据安全

- 本系统处理的图片数据存储在服务端 `static/uploads/` 和 `static/results/` 目录
- 上传的图片通过 UUID 和時間戳生成唯一文件名，避免文件名冲突和信息泄露
- 系统**不包含**用户认证/授权机制，请勿在公网直接暴露

### 部署安全建议

如果需要在生产环境部署，请遵循以下建议：

1. **添加认证层**：配置 Nginx Basic Auth 或集成 OAuth2 认证
2. **使用 HTTPS**：配置 SSL 证书，确保传输加密
3. **限制访问范围**：使用防火墙仅允许特定 IP 访问
4. **定期清理**：设置定时任务清理 `uploads/` 和 `results/` 目录的临时文件
5. **使用反向代理**：通过 Nginx 反向代理提供静态文件服务，避免 Flask 直接处理

### Nginx 反向代理配置示例

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 限制上传大小
    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/neu-det-webapp/static/;
        expires 7d;
    }
}
```

### 报告漏洞

如果发现安全漏洞，请通过以下方式报告：

- **请勿公开披露**，优先通过私密渠道报告
- 联系项目作者提交详细说明
- 我们将在收到报告后 48 小时内回复

### 已知安全限制

1. 无 CSRF 保护（适用于内部/教学场景）
2. 无上传文件类型深度校验（仅检查文件扩展名）
3. 无请求频率限制
4. 无用户会话管理

# WSS Plugin 快速入门指南

## 快速测试

### 1. 测试数据加扰模块

```bash
python3 obfuscator.py
```

应该看到类似输出：
```
Testing DataObfuscator...

Test 1: 13 bytes
Original: b'Hello, World!'
Obfuscated: 20 bytes (expansion: 7 bytes)
✓ Success: Data matches!
...
All tests completed!
```

### 2. 准备 SSL 证书

#### 选项 A: 使用自签名证书（测试用）

```bash
# 生成自签名证书
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout privkey.pem \
  -out fullchain.pem \
  -days 365 \
  -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"
```

#### 选项 B: 使用 Let's Encrypt 证书（生产环境）

```bash
# 安装 certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your_domain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/your_domain.com/fullchain.pem .
sudo cp /etc/letsencrypt/live/your_domain.com/privkey.pem .
sudo chown $USER:$USER fullchain.pem privkey.pem
```

### 3. 启动测试

#### 准备工作

首先需要一个运行的 Shadowsocks 服务器：

```bash
# 安装 shadowsocks-libev (Ubuntu/Debian)
sudo apt-get install shadowsocks-libev

# 或使用 shadowsocks-rust
# 从 https://github.com/shadowsocks/shadowsocks-rust/releases 下载
```

#### 测试场景 1: 本地环回测试

**终端 1: 启动 Shadowsocks 服务器**
```bash
# 创建简单配置
cat > ss_server.json << EOF
{
  "server": "127.0.0.1",
  "server_port": 8388,
  "password": "test_password",
  "method": "aes-256-gcm"
}
EOF

# 启动 Shadowsocks 服务器
ss-server -c ss_server.json
```

**终端 2: 启动 WSS Plugin 服务端**
```bash
./test_server.sh
```

**终端 3: 启动 WSS Plugin 客户端**
```bash
./test_client.sh
```

**终端 4: 测试连接**
```bash
# 通过 SOCKS5 代理测试
curl -x socks5h://127.0.0.1:1080 https://www.google.com

# 或使用 proxychains
proxychains4 curl https://www.google.com
```

#### 测试场景 2: 实际部署测试

**服务器端 (your_server_ip):**

1. 安装 Shadowsocks:
```bash
sudo apt-get install shadowsocks-libev
```

2. 准备配置文件 `/etc/shadowsocks/config.json`:
```json
{
  "server": "127.0.0.1",
  "server_port": 8388,
  "password": "your_strong_password",
  "method": "aes-256-gcm"
}
```

3. 启动 Shadowsocks:
```bash
ss-server -c /etc/shadowsocks/config.json &
```

4. 配置并启动 WSS Plugin:
```bash
export SS_REMOTE_HOST=127.0.0.1
export SS_REMOTE_PORT=8388
export SS_LOCAL_HOST=0.0.0.0
export SS_LOCAL_PORT=443
export SS_PLUGIN_OPTIONS="wss_path=/ws;cert=fullchain.pem;key=privkey.pem;obfs_key=MySecureKey2024"

python3 wss_plugin_server.py &
```

**客户端 (本地机器):**

1. 安装 Shadowsocks:
```bash
sudo apt-get install shadowsocks-libev
# 或 brew install shadowsocks-libev (macOS)
```

2. 配置客户端 (编辑 test_client.sh):
```bash
export SS_REMOTE_HOST=your_server_ip
export SS_REMOTE_PORT=443
export SS_LOCAL_HOST=127.0.0.1
export SS_LOCAL_PORT=1080
export SS_PLUGIN_OPTIONS="wss_host=your_server_ip;wss_port=443;wss_path=/ws;skip_cert_verify=false;obfs_key=MySecureKey2024"
```

3. 启动客户端:
```bash
./test_client.sh
```

4. 测试连接:
```bash
curl -x socks5h://127.0.0.1:1080 https://ipinfo.io
```

## 常见问题

### Q1: 客户端连接失败
**A:** 检查：
- 服务器防火墙是否开放端口 443
- SSL 证书是否正确加载
- `obfs_key` 是否一致

### Q2: 数据传输错误
**A:** 确认：
- 客户端和服务端的 `obfs_key` 完全一致
- WebSocket 路径 `wss_path` 一致
- 网络连接稳定

### Q3: SSL 证书验证失败
**A:** 
- 使用自签名证书时设置 `skip_cert_verify=true`
- 使用正式证书时确保证书链完整

### Q4: 性能问题
**A:** 
- 检查网络带宽
- 调整 WebSocket 缓冲区大小
- 考虑关闭调试日志 (修改 logging.INFO → logging.WARNING)

## 监控和日志

### 查看实时日志

客户端和服务端都会输出详细日志：

```
2024-01-14 10:00:00 - wss-plugin-server - INFO - Server initialized: listen=0.0.0.0:443, path=/ws, backend=127.0.0.1:8388
2024-01-14 10:00:01 - wss-plugin-server - INFO - WSS Plugin Server listening on wss://0.0.0.0:443/ws
2024-01-14 10:00:05 - wss-plugin-server - INFO - New WSS client connection from ('192.168.1.100', 54321)
2024-01-14 10:00:05 - wss-plugin-server - DEBUG - WSS->SS: 150 bytes (deobfuscated to 128 bytes)
```

### 调整日志级别

编辑源文件，修改：
```python
logging.basicConfig(level=logging.INFO)  # 或 DEBUG, WARNING, ERROR
```

## 性能调优

### 1. 系统参数优化

```bash
# 增加文件描述符限制
ulimit -n 65535

# 优化 TCP 参数
sudo sysctl -w net.core.rmem_max=16777216
sudo sysctl -w net.core.wmem_max=16777216
sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 16777216'
sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 16777216'
```

### 2. 代码优化选项

在源代码中可以调整：

```python
# wss_plugin_client.py 或 wss_plugin_server.py

# 调整读缓冲区大小
data = await reader.read(16384)  # 默认 8192，可增加到 16384

# 调整 WebSocket 参数
max_size=32 * 1024 * 1024,  # 增加最大消息大小
ping_interval=60,            # 增加心跳间隔
```

## 生产环境部署建议

1. **使用 systemd 服务**

创建 `/etc/systemd/system/wss-plugin.service`:
```ini
[Unit]
Description=WSS Plugin Server
After=network.target

[Service]
Type=simple
User=nobody
Environment="SS_REMOTE_HOST=127.0.0.1"
Environment="SS_REMOTE_PORT=8388"
Environment="SS_LOCAL_HOST=0.0.0.0"
Environment="SS_LOCAL_PORT=443"
Environment="SS_PLUGIN_OPTIONS=wss_path=/ws;cert=/etc/ssl/fullchain.pem;key=/etc/ssl/privkey.pem;obfs_key=YourSecureKey"
ExecStart=/usr/bin/python3 /opt/wss_plugin/wss_plugin_server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable wss-plugin
sudo systemctl start wss-plugin
```

2. **使用 Nginx 反向代理（可选）**

可以在 Nginx 后面运行插件，利用 Nginx 的负载均衡和缓存功能。

3. **监控告警**

建议配置监控系统监控：
- 进程存活状态
- 网络连接数
- CPU/内存使用率
- 日志错误数量

## 下一步

阅读完整文档 [README_wss_plugin.md](README_wss_plugin.md) 了解更多细节。

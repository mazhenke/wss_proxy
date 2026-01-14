# WSS Plugin 测试工具使用指南

## 5 个独立测试工具

测试包含 5 个独立的脚本，可以分别在不同终端运行：

1. **generate_cert.py** - 生成SSL证书
2. **start_echo_server.py** - 启动Echo服务器（模拟Shadowsocks后端）
3. **start_plugin_server.py** - 启动WSS插件服务端
4. **start_plugin_client.py** - 启动WSS插件客户端
5. **test_data_transfer.py** - 测试数据传输

## 快速开始

### 步骤 1: 生成证书

```bash
# 生成自签名证书（首次运行）
./generate_cert.py

# 或自定义参数
./generate_cert.py --cert mycert.pem --key mykey.pem --days 730
```

### 步骤 2: 启动 Echo 服务器

```bash
# 终端 1 - 启动 Echo 服务器（默认端口 8388）
./start_echo_server.py

# 或自定义端口
./start_echo_server.py --host 0.0.0.0 --port 9000
```

### 步骤 3: 启动 WSS 插件服务端

```bash
# 终端 2 - 启动插件服务端（默认监听 8443）
./start_plugin_server.py

# 或自定义参数
./start_plugin_server.py \
  --backend-host 127.0.0.1 \
  --backend-port 8388 \
  --listen-host 0.0.0.0 \
  --listen-port 443 \
  --cert fullchain.pem \
  --key privkey.pem
```

### 步骤 4: 启动 WSS 插件客户端

```bash
# 终端 3 - 启动插件客户端（默认监听 1080）
./start_plugin_client.py

# 或自定义参数
./start_plugin_client.py \
  --remote-host 127.0.0.1 \
  --remote-port 8443 \
  --local-host 127.0.0.1 \
  --local-port 1080
```

### 步骤 5: 测试数据传输

```bash
# 终端 4 - 运行所有测试
./test_data_transfer.py

# 显示详细信息
./test_data_transfer.py --verbose

# 测试自定义消息
./test_data_transfer.py --custom "Hello, World!"

# 测试十六进制数据
./test_data_transfer.py --hex "48656c6c6f"

# 测试远程服务器
./test_data_transfer.py --host server.example.com --port 1080
```

## 各工具详细说明

### 1. generate_cert.py

生成自签名SSL证书，用于测试。

**参数：**
- `--cert` - 证书文件名（默认: fullchain.pem）
- `--key` - 私钥文件名（默认: privkey.pem）
- `--days` - 有效期天数（默认: 365）

**示例：**
```bash
# 基本使用
./generate_cert.py

# 生成有效期2年的证书
./generate_cert.py --days 730

# 自定义文件名
./generate_cert.py --cert server.crt --key server.key
```

**输出示例：**
```
Generating self-signed SSL certificate...
  Certificate: fullchain.pem
  Private key: privkey.pem
  Valid for: 365 days
✓ Certificate generated successfully!
  Certificate: /path/to/fullchain.pem
  Private key: /path/to/privkey.pem

Certificate details:
  subject=CN = localhost
  notBefore=Jan 14 10:00:00 2024 GMT
  notAfter=Jan 13 10:00:00 2025 GMT
```

### 2. start_echo_server.py

启动一个简单的Echo服务器，将接收到的数据原样返回。

**参数：**
- `--host` - 监听地址（默认: 127.0.0.1）
- `--port` - 监听端口（默认: 8388）

**示例：**
```bash
# 本地测试
./start_echo_server.py

# 监听所有网卡
./start_echo_server.py --host 0.0.0.0 --port 8388

# 使用不同端口
./start_echo_server.py --port 9000
```

**输出示例：**
```
Starting Echo Server on 127.0.0.1:8388
Press Ctrl+C to stop
--------------------------------------------------
✓ Echo Server listening on 127.0.0.1:8388
--------------------------------------------------
[Client 1] Connected from ('127.0.0.1', 54321)
[Client 1] Received 13 bytes (total: 13)
[Client 1] Echoed 13 bytes
[Client 1] Disconnected (total bytes: 13)
```

### 3. start_plugin_server.py

启动WSS插件服务端，连接Echo服务器（或实际的Shadowsocks服务器）。

**参数：**
- `--backend-host` - Shadowsocks后端地址（默认: 127.0.0.1）
- `--backend-port` - Shadowsocks后端端口（默认: 8388）
- `--listen-host` - 监听地址（默认: 127.0.0.1）
- `--listen-port` - 监听端口（默认: 8443）
- `--cert` - SSL证书文件（默认: fullchain.pem）
- `--key` - SSL私钥文件（默认: privkey.pem）

**示例：**
```bash
# 基本使用
./start_plugin_server.py

# 完整配置
./start_plugin_server.py \
  --backend-host 127.0.0.1 \
  --backend-port 8388 \
  --listen-host 0.0.0.0 \
  --listen-port 443 \
  --cert /path/to/cert.pem \
  --key /path/to/key.pem
```

**输出示例：**
```
============================================================
WSS Plugin Server Configuration
============================================================
Backend (Shadowsocks):  127.0.0.1:8388
Listen (WSS):           127.0.0.1:8443
Certificate:            fullchain.pem
Private Key:            privkey.pem
============================================================

2024-01-14 10:00:00 - wss-plugin-server - INFO - Server initialized
2024-01-14 10:00:01 - wss-plugin-server - INFO - WSS Plugin Server listening on wss://127.0.0.1:8443/ws
```

### 4. start_plugin_client.py

启动WSS插件客户端，连接到WSS插件服务端。

**参数：**
- `--remote-host` - WSS服务器地址（默认: 127.0.0.1）
- `--remote-port` - WSS服务器端口（默认: 8443）
- `--local-host` - 本地监听地址（默认: 127.0.0.1）
- `--local-port` - 本地监听端口（默认: 1080）
- `--cert` - SSL证书文件（可选；当前客户端仍禁用验证，仅记录日志）

**示例：**
```bash
# 基本使用（客户端始终跳过证书验证）
./start_plugin_client.py

# 连接远程服务器
./start_plugin_client.py \
  --remote-host server.example.com \
  --remote-port 443 \
  --local-port 1080
```

**输出示例：**
```
============================================================
WSS Plugin Client Configuration
============================================================
Remote (WSS Server):    127.0.0.1:8443
Local (SOCKS):          127.0.0.1:1080
Certificate:            None
Cert Verification:      Disabled
============================================================

2024-01-14 10:00:00 - wss-plugin-client - INFO - Client initialized
2024-01-14 10:00:01 - wss-plugin-client - INFO - WSS Plugin Client listening on 127.0.0.1:1080
```

### 5. test_data_transfer.py

测试数据传输，发送各种测试数据并验证回显。

**参数：**
- `--host` - 目标地址（默认: 127.0.0.1）
- `--port` - 目标端口（默认: 1080）
- `--verbose, -v` - 显示详细信息
- `--custom, -c` - 发送自定义字符串
- `--hex` - 发送十六进制数据

**示例：**
```bash
# 运行所有测试
./test_data_transfer.py

# 详细模式
./test_data_transfer.py --verbose

# 测试自定义消息
./test_data_transfer.py --custom "你好世界"

# 测试十六进制数据
./test_data_transfer.py --hex "deadbeef"

# 测试远程服务器
./test_data_transfer.py --host 192.168.1.100 --port 1080
```

**输出示例：**
```
============================================================
WSS Plugin Data Transfer Test
Target: 127.0.0.1:1080
============================================================

Test 1/8: Small message
  Size: 13 bytes
  ✓ PASSED (time: 0.015s)

Test 2/8: Medium message
  Size: 16 bytes
  ✓ PASSED (time: 0.012s)

Test 3/8: Large data (1KB)
  Size: 1000 bytes
  ✓ PASSED (time: 0.018s)

...

============================================================
Test Results: 8 passed, 0 failed
============================================================
✓ ALL TESTS PASSED!
```

## 快速串行流程（无后台）

在单终端串行验证：

```bash
./generate_cert.py --domain localhost
./start_echo_server.py --host 127.0.0.1 --port 8388 &
./start_plugin_server.py --backend-host 127.0.0.1 --backend-port 8388 --listen-host 127.0.0.1 --listen-port 8443 --cert fullchain.pem --key privkey.pem &
./start_plugin_client.py --remote-host 127.0.0.1 --remote-port 8443 --local-port 1080 &
./test_data_transfer.py --verbose
pkill -f "start_echo_server.py|start_plugin_server.py|start_plugin_client.py"
```

## 故障排查

### 常见问题

1. **证书生成失败**
   ```bash
   # 检查 openssl 是否安装
   which openssl
   
   # Ubuntu/Debian
   sudo apt-get install openssl
   ```

2. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tuln | grep -E '(8388|8443|1080)'
   
   # 使用不同端口
   ./start_echo_server.py --port 9000
   ./start_plugin_server.py --backend-port 9000 --listen-port 9443
   ./start_plugin_client.py --remote-port 9443 --local-port 9080
   ./test_data_transfer.py --port 9080
   ```

3. **连接被拒绝**
   - 确保所有服务按顺序启动
   - 检查防火墙设置
   - 验证端口配置是否正确

4. **测试失败**
   ```bash
   # 检查各组件是否运行
   ps aux | grep -E '(echo_server|plugin_server|plugin_client)'
   
   # 查看详细日志
   ./test_data_transfer.py --verbose
   ```

## 生产环境部署

测试通过后，可以配合实际的 Shadowsocks 服务器使用：

```bash
# 服务端
./start_plugin_server.py \
  --backend-host 127.0.0.1 \
  --backend-port 8388 \
  --listen-host 0.0.0.0 \
  --listen-port 443 \
  --cert /etc/ssl/fullchain.pem \
  --key /etc/ssl/privkey.pem

# 客户端
./start_plugin_client.py \
  --remote-host your-server.com \
  --remote-port 443 \
  --local-host 127.0.0.1 \
  --local-port 1080 \
  --cert /path/to/server-cert.pem
```

## 更多信息

- 详细文档: `使用说明.md`
- 测试指南: `TEST_GUIDE.md`

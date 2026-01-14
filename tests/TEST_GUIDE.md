# WSS Plugin 测试指南

## 自动化测试

### 运行完整测试

```bash
python3 test_plugin.py
```

测试脚本会自动：
1. ✓ 生成自签名证书（如果不存在）
2. ✓ 启动 Echo 服务器（模拟 Shadowsocks）
3. ✓ 启动 WSS Plugin 服务端
4. ✓ 启动 WSS Plugin 客户端
5. ✓ 执行 4 个数据传输测试
6. ✓ 自动清理所有进程

### 测试内容

1. **小消息测试** - 13 字节 "Hello, World!"
2. **中等消息测试** - 16 字节测试消息
3. **大数据测试** - 1KB 连续数据
4. **特殊字节测试** - 所有 256 个字节值

## 手动测试

### 步骤 1: 生成证书

```bash
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout privkey.pem -out fullchain.pem -days 365 \
  -subj "/CN=localhost"
```

### 步骤 2: 启动测试 Echo 服务器

```bash
# 终端 1
python3 << 'EOF'
import asyncio

async def handle(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f'Client: {addr}')
    while True:
        data = await reader.read(8192)
        if not data:
            break
        print(f'Echo {len(data)} bytes')
        writer.write(data)
        await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle, '127.0.0.1', 8388)
    print('Echo server on 127.0.0.1:8388')
    async with server:
        await server.serve_forever()

asyncio.run(main())
EOF
```

### 步骤 3: 启动 WSS 服务端

```bash
# 终端 2
export SS_REMOTE_HOST=127.0.0.1
export SS_REMOTE_PORT=8388
export SS_LOCAL_HOST=127.0.0.1
export SS_LOCAL_PORT=8443
export SS_PLUGIN_OPTIONS="cert=fullchain.pem;key=privkey.pem"

python3 wss_plugin_server.py
```

### 步骤 4: 启动 WSS 客户端

```bash
# 终端 3
export SS_REMOTE_HOST=127.0.0.1
export SS_REMOTE_PORT=8443
export SS_LOCAL_HOST=127.0.0.1
export SS_LOCAL_PORT=1080
export SS_PLUGIN_OPTIONS=""

python3 wss_plugin_client.py
```

### 步骤 5: 测试连接

```bash
# 终端 4 - 发送测试数据
echo "Hello from client" | nc 127.0.0.1 1080
```

应该看到数据被 echo 回来。

## 使用 netcat 测试

### 简单测试

```bash
# 发送数据
echo "test message" | nc 127.0.0.1 1080

# 交互式
nc 127.0.0.1 1080
# 输入任何内容，按回车
# 应该立即收到回显
```

### 大数据测试

```bash
# 发送 1MB 数据
dd if=/dev/zero bs=1M count=1 | nc 127.0.0.1 1080 > /dev/null
```

### 持续测试

```bash
# 持续发送数据 10 秒
timeout 10 bash -c 'while true; do echo "test"; sleep 0.1; done | nc 127.0.0.1 1080'
```

## 查看日志

### 实时查看所有组件日志

服务端和客户端都会输出详细日志：

```
2024-01-14 10:00:00 - wss-plugin-server - INFO - Server initialized
2024-01-14 10:00:01 - wss-plugin-server - INFO - WSS Plugin Server listening
2024-01-14 10:00:05 - wss-plugin-server - INFO - New WSS client connection
2024-01-14 10:00:05 - wss-plugin-server - DEBUG - WSS->SS: 150 bytes
```

### 启用 DEBUG 日志

编辑源文件，修改日志级别：

```python
logging.basicConfig(level=logging.DEBUG)  # 更详细的日志
```

## 性能测试

### 使用 iperf3

```bash
# 启动 iperf3 服务器
iperf3 -s -p 5201

# 通过代理测试
# (需要配置 iperf3 使用 SOCKS5 代理或使用其他工具)
```

### 简单带宽测试

```bash
# 发送大量数据并测速
dd if=/dev/zero bs=1M count=100 | pv | nc 127.0.0.1 1080 > /dev/null
```

## 故障排查

### 测试失败常见原因

1. **端口被占用**
   - 检查: `netstat -tuln | grep -E '(8388|8443|1080)'`
   - 解决: 关闭占用端口的程序或更改端口

2. **证书问题**
   - 检查: 确保 `fullchain.pem` 和 `privkey.pem` 存在
   - 解决: 重新生成证书

3. **权限问题**
   - 检查: 确保脚本有执行权限
   - 解决: `chmod +x *.py *.sh`

4. **Python 版本**
   - 检查: `python3 --version` (需要 3.7+)
   - 解决: 升级 Python

### 查看进程状态

```bash
# 查看所有相关进程
ps aux | grep wss_plugin

# 查看端口监听
netstat -tuln | grep -E '(8388|8443|1080)'

# 查看连接状态
netstat -tan | grep -E '(8388|8443|1080)'
```

### 手动清理

```bash
# 杀掉所有测试进程
pkill -f wss_plugin
pkill -f test_plugin

# 等待端口释放
sleep 2

# 验证端口已释放
netstat -tuln | grep -E '(8388|8443|1080)'
```

## 预期测试结果

### 成功输出

```
============================================================
WSS Plugin Test Suite
============================================================

✓ SSL certificates found
ℹ Starting echo server...
✓ Echo server started on 127.0.0.1:8388
ℹ Starting WSS plugin server...
✓ WSS server started
ℹ Starting WSS plugin client...
✓ WSS client started
ℹ Testing data transfer...
✓ Connected to local port
✓ Test 1: Data echoed correctly
✓ Test 2: Data echoed correctly
✓ Test 3: Data echoed correctly
✓ Test 4: Data echoed correctly
✓ All data transfer tests passed!

============================================================
✓ ALL TESTS PASSED!
============================================================
```

### 失败的迹象

- `✗` 红色错误标记
- 超时错误
- 连接拒绝
- 数据不匹配

## 下一步

测试通过后，可以：

1. 集成到实际的 Shadowsocks 服务器
2. 部署到生产环境
3. 配置系统服务（systemd）
4. 添加监控和告警

查看 `使用说明.md` 了解生产环境部署方法。

# Shadowsocks WebSocket Plugin (SIP003)

基于 WebSocket (WSS) 的 Shadowsocks SIP003 插件实现，使用 Python 编写。

## 功能特性

- ✅ 完整的 SIP003 标准支持
- ✅ 基于 WebSocket over TLS (WSS) 传输
- ✅ 数据加扰混淆，增加流量识别难度
- ✅ 异步高性能实现
- ✅ 支持自定义加扰密钥
- ✅ 简单易用的配置方式

## 技术实现

### 数据加扰算法

本插件实现了多层数据加扰机制：

1. **随机填充**: 为每个数据包添加 1-15 字节随机填充，打破固定长度特征
2. **XOR 混淆**: 使用从密钥派生的 256 字节密钥流进行 XOR 操作
3. **字节重排**: 按 4 字节块进行内部反转，增加混淆程度

数据包格式：`[2字节长度][原始数据][随机填充]`

### 架构设计

```
客户端:                                服务端:
本地应用                               Shadowsocks服务器
    ↓                                       ↑
Shadowsocks客户端                     Shadowsocks服务端
    ↓                                       ↑
WSS Plugin Client  ←--[WSS加密通道]-->  WSS Plugin Server
```

## 文件说明

- `wss_plugin_client.py` - 客户端插件程序
- `wss_plugin_server.py` - 服务端插件程序
- `obfuscator.py` - 数据加扰模块
- `README_wss_plugin.md` - 本文档

## 安装依赖

本插件依赖 websockets 库（已包含在项目中）:

```bash
# 如果需要安装标准版本
pip3 install websockets
```

## 使用方法

### 1. 服务端配置

服务端需要准备 SSL 证书：

```bash
# 证书文件
fullchain.pem  # SSL证书
privkey.pem    # SSL私钥
```

#### 启动方式

**方式一：作为 Shadowsocks 插件启动**

在 Shadowsocks 服务端配置文件中添加：

```json
{
    "server": "0.0.0.0",
    "server_port": 8388,
    "password": "your_password",
    "method": "aes-256-gcm",
    "plugin": "/path/to/wss_plugin_server.py",
    "plugin_opts": "wss_port=443;wss_path=/ws;cert=fullchain.pem;key=privkey.pem;obfs_key=my_secret_key"
}
```

**方式二：手动启动（用于测试）**

```bash
# 设置环境变量
export SS_REMOTE_HOST=127.0.0.1
export SS_REMOTE_PORT=8388
export SS_LOCAL_HOST=0.0.0.0
export SS_LOCAL_PORT=443
export SS_PLUGIN_OPTIONS="wss_path=/ws;cert=fullchain.pem;key=privkey.pem;obfs_key=my_secret_key"

# 启动服务端
python3 wss_plugin_server.py
```

### 2. 客户端配置

#### 启动方式

**方式一：作为 Shadowsocks 插件启动**

在 Shadowsocks 客户端配置文件中添加：

```json
{
    "server": "your_server_ip",
    "server_port": 443,
    "local_address": "127.0.0.1",
    "local_port": 1080,
    "password": "your_password",
    "method": "aes-256-gcm",
    "plugin": "/path/to/wss_plugin_client.py",
    "plugin_opts": "wss_host=your_server_ip;wss_port=443;wss_path=/ws;skip_cert_verify=true;obfs_key=my_secret_key"
}
```

**方式二：手动启动（用于测试）**

```bash
# 设置环境变量
export SS_REMOTE_HOST=your_server_ip
export SS_REMOTE_PORT=443
export SS_LOCAL_HOST=127.0.0.1
export SS_LOCAL_PORT=1080
export SS_PLUGIN_OPTIONS="wss_host=your_server_ip;wss_port=443;wss_path=/ws;skip_cert_verify=true;obfs_key=my_secret_key"

# 启动客户端
python3 wss_plugin_client.py
```

## 插件选项说明

### 客户端选项 (plugin_opts)

| 选项 | 默认值 | 说明 |
|------|--------|------|
| wss_host | SS_REMOTE_HOST | WSS 服务器地址 |
| wss_port | SS_REMOTE_PORT | WSS 服务器端口 |
| wss_path | /ws | WebSocket 路径 |
| skip_cert_verify | true | 是否跳过证书验证 (true/false) |
| obfs_key | default_key_2024 | 数据加扰密钥（必须与服务端一致） |

### 服务端选项 (plugin_opts)

| 选项 | 默认值 | 说明 |
|------|--------|------|
| wss_host | SS_LOCAL_HOST | WSS 监听地址 |
| wss_port | SS_LOCAL_PORT | WSS 监听端口 |
| wss_path | /ws | WebSocket 路径 |
| cert | fullchain.pem | SSL 证书文件路径 |
| key | privkey.pem | SSL 私钥文件路径 |
| obfs_key | default_key_2024 | 数据加扰密钥（必须与客户端一致） |

## SIP003 标准环境变量

插件通过以下环境变量与 Shadowsocks 通信：

### 客户端环境变量

- `SS_REMOTE_HOST` - Shadowsocks 服务器地址
- `SS_REMOTE_PORT` - Shadowsocks 服务器端口
- `SS_LOCAL_HOST` - 本地监听地址
- `SS_LOCAL_PORT` - 本地监听端口
- `SS_PLUGIN_OPTIONS` - 插件选项字符串

### 服务端环境变量

- `SS_REMOTE_HOST` - Shadowsocks 后端地址
- `SS_REMOTE_PORT` - Shadowsocks 后端端口
- `SS_LOCAL_HOST` - 插件监听地址
- `SS_LOCAL_PORT` - 插件监听端口
- `SS_PLUGIN_OPTIONS` - 插件选项字符串

## 测试加扰模块

测试数据加扰和解扰功能：

```bash
python3 obfuscator.py
```

输出示例：
```
Testing DataObfuscator...

Test 1: 13 bytes
Original: b'Hello, World!'
Obfuscated: 20 bytes (expansion: 7 bytes)
Obfuscated data: 0d0048656c6c6f2c20576f726c6421...
Deobfuscated: 13 bytes
✓ Success: Data matches!
...
```

## 性能优化

- 使用异步 I/O (asyncio) 实现高并发
- WebSocket 帧最大 16MB，支持大数据传输
- 30 秒心跳保持连接活跃
- 8KB 读缓冲区，平衡内存和性能

## 安全建议

1. **使用强加扰密钥**: 建议使用长随机字符串作为 `obfs_key`
2. **启用证书验证**: 生产环境建议使用有效证书并设置 `skip_cert_verify=false`
3. **定期更换密钥**: 定期更换 `obfs_key` 增强安全性
4. **使用强密码**: Shadowsocks 密码应使用强随机密码

## 故障排除

### 客户端无法连接

1. 检查服务器地址和端口是否正确
2. 检查防火墙是否开放相应端口
3. 检查 SSL 证书是否有效
4. 查看日志输出定位问题

### 数据传输错误

1. 确认客户端和服务端 `obfs_key` 一致
2. 检查网络连接是否稳定
3. 查看日志中的错误信息

### 日志查看

插件会输出详细日志，包括：
- 连接状态
- 数据传输情况
- 错误信息

调整日志级别：
```python
# 在代码中修改
logging.basicConfig(level=logging.DEBUG)  # DEBUG 级别显示更详细信息
```

## 与 Cloak 的对比

本插件参考了 Cloak 的设计思路，但做了简化：

| 特性 | Cloak | 本插件 |
|------|-------|--------|
| 语言 | Go | Python |
| 传输 | TLS/WebSocket | WebSocket (WSS) |
| 加密 | AES-GCM + ECDH | XOR + 字节混淆 |
| 复杂度 | 高 | 中 |
| 性能 | 很高 | 高 |
| 易用性 | 中 | 高 |

## 开发计划

- [ ] 添加更多加扰算法选项
- [ ] 支持自定义 TLS 指纹
- [ ] 添加流量统计功能
- [ ] 支持多种证书验证模式
- [ ] 性能优化和压力测试

## 许可证

本项目基于现有的 Shadowsocks 和 Cloak 项目开发，遵循相应的开源许可证。

## 参考资料

- [Shadowsocks SIP003 Plugin](https://shadowsocks.org/en/wiki/Plugin.html)
- [Cloak](https://github.com/cbeuw/Cloak)
- [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)

---

**注意**: 本插件仅供学习和研究使用，请遵守当地法律法规。

# WSS Plugin 项目结构

## 目录布局

```
tls/
├── 核心程序
│   ├── wss_plugin_client.py      # 客户端插件
│   ├── wss_plugin_server.py      # 服务端插件
│   ├── obfuscator.py             # 数据加扰模块
│   └── ...
│
├── 测试工具 (tests/)
│   ├── README.md                 # 测试目录说明
│   ├── generate_cert.py          # 生成证书
│   ├── start_echo_server.py      # Echo 服务器
│   ├── start_plugin_server.py    # 启动插件服务端
│   ├── start_plugin_client.py    # 启动插件客户端
│   ├── test_data_transfer.py     # 数据传输测试
│   ├── TESTING_TOOLS.md          # 工具详细指南
│   └── TEST_GUIDE.md             # 测试指南
│
└── 文档
    ├── 使用说明.md               # 中文快速指南
    ├── README_wss_plugin.md      # 完整文档（英文）
    ├── QUICKSTART.md             # 快速入门（英文）
    └── PROJECT_SUMMARY.md        # 项目总结
```

## 快速开始

### 分步骤测试

```bash
cd tests

# 终端 1: 生成证书（首次）
./generate_cert.py

# 终端 1: 启动 Echo 服务器
./start_echo_server.py

# 终端 2: 启动 WSS 服务端
./start_plugin_server.py

# 终端 3: 启动 WSS 客户端
./start_plugin_client.py

# 终端 4: 测试数据传输
./test_data_transfer.py --verbose
```

## 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| wss_plugin_client.py | WSS Plugin 客户端实现 |
| wss_plugin_server.py | WSS Plugin 服务端实现 |
| obfuscator.py | 数据加扰模块，可独立测试 |

### 测试文件 (tests/ 目录)

| 文件 | 说明 |
|------|------|
| test_plugin.py | 完整自动化测试，一键运行 |
| generate_cert.py | 生成自签名 SSL 证书 |
| start_echo_server.py | Echo 服务器（模拟 Shadowsocks 后端） |
| start_plugin_server.py | 启动 WSS 插件服务端 |
| start_plugin_client.py | 启动 WSS 插件客户端 |
| test_data_transfer.py | 数据传输测试工具 |
| run_auto_test.sh | 一键运行自动化测试脚本 |

### 文档文件
generate_cert.py | 生成自签名 SSL 证书 |
| start_echo_server.py | Echo 服务器（模拟 Shadowsocks 后端） |
| start_plugin_server.py | 启动 WSS 插件服务端 |
| start_plugin_client.py | 启动 WSS 插件客户端 |
| test_data_transfer.py | 数据传输测试工具
| tests/TESTING_TOOLS.md | 测试工具详细说明 |
| tests/TEST_GUIDE.md | 测试步骤指南 |

## 环境准备

### 安装依赖

```bash
# Ubuntu/Debian
sudo apt-get install python3 openssl

# macOS
brew install python@3 openssl
```

### 检查环境

```bash
python3 --version    # 需要 3.7+
openssl version       # 检查 OpenSSL
```

## 使用场景

### 场景 1: 快速验证功能

```bash独立启动各组件

```bash
cd tests

# 启动各个组件
./generate_cert.py
./start_echo_server.py &     # 后台运行
./start_plugin_server.py &   # 后台运行
./start_plugin_client.py

# 在另一个终端测试
./test_data_transfer.py
```
# 使用实际 Shadowsocks 服务器
./tests/start_plugin_server.py \
  --backend-host <real-ss-server> \
  --backend-port 8388 \
  --listen-host 0.0.0.0 \
  --listen-port 443

# 客户端连接
./tests2start_plugin_client.py \
  --remote-host <your-server> \
  --remote-port 443
```

## 关键概念

### 数据流

```
客户端应用
    ↓
本地 SOCKS5 (1080)
    ↓
WSS Plugin Client ←--WSS加密通道→ WSS Plugin Server
    ↓
Shadowsocks 后端 (8388)
    ↓
目标服务器
```

### 加扰算法

1. 添加随机填充 (1-15 字节)
2. XOR 混淆
3. 字节重排

### SIP003 标准

插件通过环境变量与 Shadowsocks 通信：
- `SS_REMOTE_HOST/PORT` - 后端地址
- `SS_LOCAL_HOST/PORT` - 本地监听地址
- `SS_PLUGIN_OPTIONS` - 插件选项

## 常见命令

```bash
# 查看帮助
python3 generate_cert.py --help
python3 start_plugin_server.py --help
python3 start_plugin_client.py --help
python3 test_data_transfer.py --help

# 自定义参数
python3 start_plugin_server.py --listen-port 443 --backend-port 8388
python3 test_data_transfer.py --host 192.168.1.100 --port 1080

# 测试远程服务
python3 test_data_transfer.py --host your-server.com --port 1080 --custom "test"
```

## 故障排查

### 测试失败

```bash
# 1. 检查证书
ls -l tests/*.pem

# 2. 查看进程
ps aux | grep -E '(plugin|echo)'

# 3. 检查端口
netstat -tuln | grep -E '(8388|8443|1080)'

# 4. 查看详细日志
python3 test_data_transfer.py --verbose
```

### 清理环境

```bash
# 杀掉所有测试进程
pkill -f "wss_plugin|echo_server"

# 重新生成证书
rm tests/fullchain.pem tests/privkey.pem
python3 tests/generate_cert.py
```

## 更多信息

- 项目文档: [README_wss_plugin.md](README_wss_plugin.md)
- 使用指南: [使用说明.md](使用说明.md)
- 测试工具: [tests/TESTING_TOOLS.md](tests/TESTING_TOOLS.md)

---

**项目状态**: ✅ 完整可用
**最后更新**: 2024-01-14

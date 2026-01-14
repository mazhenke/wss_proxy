# Shadowsocks WebSocket Plugin (SIP003)

Python 实现的 Shadowsocks SIP003 插件，使用 WSS 搭桥并对载荷做轻量混淆。仓库包含客户端、服务端、加扰器以及本地测试脚本。

## 目前的真实特性

- SIP003 环境变量驱动：`SS_REMOTE_HOST/PORT`（远端或后端）、`SS_LOCAL_HOST/PORT`（本地监听）、`SS_PLUGIN_OPTIONS`（证书参数）。
- WebSocket 路径固定 `/ws`，不可配置。
- TLS 行为：
  - 服务端：从 `SS_PLUGIN_OPTIONS` 读取 `cert`、`key` 加载证书。
  - 客户端：始终禁用证书验证和主机名校验；即使传入 `cert` 也只记录日志，不会启用校验。
- 加扰：固定密钥 `wss_plugin_default_key`，流程为随机填充（1–15 字节）→ XOR → 4 字节块反转。
- 依赖：使用仓库自带 websockets/src，无需额外安装。

## 主要文件

- wss_plugin_client.py — SIP003 客户端，监听本地 SOCKS 端口并通过 WSS 转发。
- wss_plugin_server.py — SIP003 服务端，将 WSS 连接转发到后端 TCP（默认 127.0.0.1:8388）。
- obfuscator.py — 加扰实现，可直接运行做单测。
- build_executable.py — PyInstaller 打包脚本（client/server）。
- tests/ — 本地联调脚本与说明。

## 快速测试（本地环回）

在 `tests/` 内执行：

1) 生成证书：`./generate_cert.py --domain localhost`
2) 后端 Echo：`./start_echo_server.py --host 127.0.0.1 --port 8388`
3) WSS 服务端：`./start_plugin_server.py --backend-host 127.0.0.1 --backend-port 8388 --listen-host 127.0.0.1 --listen-port 8443 --cert fullchain.pem --key privkey.pem`
4) WSS 客户端：`./start_plugin_client.py --remote-host 127.0.0.1 --remote-port 8443 --local-port 1080`
5) 校验传输：`./test_data_transfer.py --verbose`

## 使用要点与限制

- 证书校验：客户端硬编码为 `CERT_NONE`，请勿在不可信网络依赖其验证。
- 路径/密钥：WSS 路径与加扰密钥均不可配置，如需自定义需修改代码。
- 性能/调试：`logging.basicConfig(level=logging.INFO)` 可改成 `DEBUG` 观察流量方向；读缓冲默认 8192，可按需调整。

## 数据加扰示意

```
[2 字节长度][原始数据][1-15 字节随机填充]
   ↓ XOR (256 字节密钥流，偏移 = len(original) % 256)
   ↓ 4 字节块反转
   → 发送数据
```

## 安全提示

- 加扰仅用于混淆，不等价于加密；机密性依赖 TLS。
- 客户端默认跳过证书验证，生产场景需先改代码再部署。

更多测试细节见 [QUICKSTART.md](QUICKSTART.md) 与 tests 下文档。

# WSS Plugin 快速入门

## 前置条件

- Python 3.7+，本仓库自带 websockets 源码，无需额外安装。
- OpenSSL（生成测试证书用）。

## 一次性准备

```bash
cd tests
./generate_cert.py --domain localhost
```

生成 `fullchain.pem` / `privkey.pem` 后续复用。

## 本地环回测试（4 个终端）

1. Echo 后端：`./start_echo_server.py --host 127.0.0.1 --port 8388`
2. WSS 服务端：`./start_plugin_server.py --backend-host 127.0.0.1 --backend-port 8388 --listen-host 127.0.0.1 --listen-port 8443 --cert fullchain.pem --key privkey.pem`
3. WSS 客户端：`./start_plugin_client.py --remote-host 127.0.0.1 --remote-port 8443 --local-port 1080`
4. 传输校验：`./test_data_transfer.py --verbose`（直连 1080，验证回显）

## 重要限制（务必知晓）

- 客户端 TLS 校验被硬编码关闭，即使传入 `cert` 也不会验证证书或主机名。
- WebSocket 路径固定为 `/ws`，无法配置。
- 数据加扰密钥固定为 `wss_plugin_default_key`，无法配置；用于混淆而非加密。

## 小贴士

- 先运行 `python3 obfuscator.py` 可单测加扰模块。
- 如端口被占用，可通过脚本参数调整 8388/8443/1080。
- 日志级别在主程序中由 `logging.basicConfig(level=logging.INFO)` 控制，必要时改为 `DEBUG`。

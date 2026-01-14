# WSS Shadowsocks Plugin - 项目总结

## 概述

使用 Python 编写的 Shadowsocks SIP003 插件，客户端与服务端通过 WSS 转发 TCP 流量，并在数据层做简单加扰（随机填充 + XOR + 4 字节块反转）。依赖 vendored websockets 库，无需额外安装。

## 真实能力与限制

- SIP003 配置：仅通过环境变量读取 `SS_REMOTE_HOST/PORT`、`SS_LOCAL_HOST/PORT`、`SS_PLUGIN_OPTIONS`。
- 可配置项：
  - 服务端：`SS_PLUGIN_OPTIONS` 仅支持 `cert`、`key`，用于 TLS 证书加载。
  - 客户端：可传入 `cert` 但**不会启用校验**，代码始终 `CERT_NONE`。
- WSS 路径固定为 `/ws`，无法自定义。
- 加扰密钥固定为 `wss_plugin_default_key`，无法通过配置变更。

## 现有文件

- wss_plugin_client.py — SIP003 客户端，禁用证书校验，固定 WSS 路径/加扰密钥。
- wss_plugin_server.py — SIP003 服务端，TLS 证书来自 `SS_PLUGIN_OPTIONS`（cert/key）。
- obfuscator.py — 加扰器实现，可直接运行做自测。
- build_executable.py — PyInstaller 打包脚本。
- tests/ — 本地联调脚本：
  - generate_cert.py / start_echo_server.py / start_plugin_server.py / start_plugin_client.py / test_data_transfer.py
  - 文档：README.md、TESTING_TOOLS.md、TEST_GUIDE.md

## 快速测试（本地回环）

1. 生成证书：`cd tests && ./generate_cert.py --domain localhost`
2. 终端 A：`./start_echo_server.py --host 127.0.0.1 --port 8388`
3. 终端 B：`./start_plugin_server.py --backend-host 127.0.0.1 --backend-port 8388 --listen-host 127.0.0.1 --listen-port 8443 --cert fullchain.pem --key privkey.pem`
4. 终端 C：`./start_plugin_client.py --remote-host 127.0.0.1 --remote-port 8443 --local-port 1080`
5. 终端 D：`./test_data_transfer.py --verbose`（直连 1080 做回显验证）

## 待改进方向

- 支持可配置的加扰密钥与 WSS 路径。
- 客户端可选启用证书校验与 Hostname 验证。
- 提供自动化一键测试脚本与示例配置文件。

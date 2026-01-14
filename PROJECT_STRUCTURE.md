# WSS Plugin 项目结构

## 顶层目录

- wss_plugin_client.py / wss_plugin_server.py — SIP003 WSS 客户端与服务端实现（依赖本地 websockets/src）
- obfuscator.py — 加扰器（固定密钥，随机填充 + XOR + 4 字节块反转）
- build_executable.py — 使用 PyInstaller 打包 client/server
- packet_sniffer.py — 简易抓包/调试脚本
- tests/ — 本地联调与验证脚本
- websockets/ — vendored upstream websockets 库（勿改）

## tests 目录

- generate_cert.py — 生成自签名证书
- start_echo_server.py — 简单回声服务，模拟后端
- start_plugin_server.py — 启动 WSS 服务端（设置 SIP003 环境变量后运行主程序）
- start_plugin_client.py — 启动 WSS 客户端
- test_data_transfer.py — 直连 SOCKS 端口做回显验证
- README.md / TESTING_TOOLS.md / TEST_GUIDE.md — 测试说明

## 运行路径小结

```
客户端应用
    ↓ (SOCKS5 1080 默认)
WSS Plugin Client (固定 /ws 路径，固定加扰密钥)
    ↓ WSS
WSS Plugin Server
    ↓ (TCP 转发)
Shadowsocks 后端 (默认 127.0.0.1:8388)
```

限制与约束：
- 客户端始终禁用证书校验；`SS_PLUGIN_OPTIONS` 中传入 `cert=...` 只被记录，不会启用验证。
- 加扰密钥硬编码为 `wss_plugin_default_key`，不可通过配置覆盖。
- WebSocket 路径固定 `/ws`，无路径配置项。

快速自测请参考 [QUICKSTART.md](QUICKSTART.md) 和 tests 下的脚本说明。

# WSS Plugin - Tests 目录

## 可用脚本

- generate_cert.py — 生成自签名证书（默认 fullchain.pem / privkey.pem）。
- start_echo_server.py — 简单 TCP Echo（默认 127.0.0.1:8388）。
- start_plugin_server.py — 设置 SIP003 环境变量后启动 WSS 服务端（默认监听 127.0.0.1:8443）。
- start_plugin_client.py — 启动 WSS 客户端并监听本地 SOCKS 端口（默认 127.0.0.1:1080）。
- test_data_transfer.py — 直连 SOCKS 端口做回显验证。

文档：TESTING_TOOLS.md（参数说明）、TEST_GUIDE.md（步骤示例）。

## 最短路径测试（4 终端）

1. `./generate_cert.py --domain localhost`
2. `./start_echo_server.py --host 127.0.0.1 --port 8388`
3. `./start_plugin_server.py --backend-host 127.0.0.1 --backend-port 8388 --listen-host 127.0.0.1 --listen-port 8443 --cert fullchain.pem --key privkey.pem`
4. `./start_plugin_client.py --remote-host 127.0.0.1 --remote-port 8443 --local-port 1080`
5. 另开终端：`./test_data_transfer.py --verbose`

说明：客户端证书校验被禁用；若端口冲突，可用脚本参数调整 8388/8443/1080。

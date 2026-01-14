# WSS Plugin 测试指南

聚焦于可用脚本的分步手动测试，已移除不存在的自动化脚本。

## 快速手动流程（推荐）

在 `tests/` 目录：

1. 证书（一次性）：`./generate_cert.py --domain localhost`
2. 终端 A：`./start_echo_server.py --host 127.0.0.1 --port 8388`
3. 终端 B：`./start_plugin_server.py --backend-host 127.0.0.1 --backend-port 8388 --listen-host 127.0.0.1 --listen-port 8443 --cert fullchain.pem --key privkey.pem`
4. 终端 C：`./start_plugin_client.py --remote-host 127.0.0.1 --remote-port 8443 --local-port 1080`
5. 终端 D：`./test_data_transfer.py --verbose`

客户端证书校验被禁用；如端口冲突，通过脚本参数调整 8388/8443/1080。

## 备用手动方式（纯命令版）

若想避免脚本，可直接运行主程序：

```bash
# Echo 后端（终端 A）
python3 - <<'PY'
import asyncio
async def handle(r, w):
    while True:
        data = await r.read(8192)
        if not data:
            break
        w.write(data)
        await w.drain()
    w.close(); await w.wait_closed()
asyncio.run(asyncio.start_server(handle, '127.0.0.1', 8388).serve_forever())
PY

# 服务端（终端 B）
export SS_REMOTE_HOST=127.0.0.1
export SS_REMOTE_PORT=8388
export SS_LOCAL_HOST=127.0.0.1
export SS_LOCAL_PORT=8443
export SS_PLUGIN_OPTIONS="cert=fullchain.pem;key=privkey.pem"
python3 ../wss_plugin_server.py

# 客户端（终端 C）
export SS_REMOTE_HOST=127.0.0.1
export SS_REMOTE_PORT=8443
export SS_LOCAL_HOST=127.0.0.1
export SS_LOCAL_PORT=1080
export SS_PLUGIN_OPTIONS=""
python3 ../wss_plugin_client.py
```

## 诊断与清理

- 端口检查：`netstat -tuln | grep -E '(8388|8443|1080)'`
- 进程检查：`ps aux | grep -E '(plugin|echo)'`
- 杀进程：`pkill -f wss_plugin && pkill -f echo_server`
- 日志等级：主程序中 `logging.basicConfig(level=logging.INFO)`，可改 `DEBUG`。

## 预期现象

- start_echo_server.py 输出连接与回显字节数。
- 服务端/客户端日志显示 WSS 建连与双向数据量（DEBUG 更详细）。
- test_data_transfer.py 显示 8 个用例全部 `PASSED`。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 WSS Plugin 服务端
用于测试
"""

import os
import sys

def start_server(backend_host='127.0.0.1', backend_port=8388,
                listen_host='0.0.0.0', listen_port=8443,
                cert_file=None, key_file=None,
                debug=False, log_file=None):
    """
    启动 WSS Plugin 服务端
    
    Args:
        backend_host: Shadowsocks 后端地址
        backend_port: Shadowsocks 后端端口
        listen_host: 监听地址
        listen_port: 监听端口
        cert_file: SSL 证书文件
        key_file: SSL 私钥文件
        debug: 启用调试日志
        log_file: 日志文件路径
    """
    if cert_file is not None:
        cert_file = os.path.abspath(cert_file)
    
    if key_file is not None:
        key_file = os.path.abspath(key_file)
    
    # 构建插件选项 - 只有在同时提供 cert 和 key 时才添加
    plugin_options_list = []
    if cert_file and key_file:
        plugin_options_list.append(f'cert={cert_file}')
        plugin_options_list.append(f'key={key_file}')
    
    if debug:
        plugin_options_list.append('debug=true')
    if log_file:
        plugin_options_list.append(f'log_file={os.path.abspath(log_file)}')
    
    plugin_options = ';'.join(plugin_options_list)
    
    # 设置环境变量
    os.environ['SS_REMOTE_HOST'] = backend_host
    os.environ['SS_REMOTE_PORT'] = str(backend_port)
    os.environ['SS_LOCAL_HOST'] = listen_host
    os.environ['SS_LOCAL_PORT'] = str(listen_port)
    os.environ['SS_PLUGIN_OPTIONS'] = plugin_options
    
    print('='*60)
    print('WSS Plugin Server Configuration')
    print('='*60)
    print(f'Backend (Shadowsocks):  {backend_host}:{backend_port}')
    print(f'Listen (WebSocket):     {listen_host}:{listen_port}')
    if cert_file and key_file:
        print(f'Certificate:            {cert_file}')
        print(f'Private Key:            {key_file}')
        print(f'SSL Mode:               Enabled (WSS)')
    else:
        print(f'SSL Mode:               Disabled (WS)')
    print('='*60)
    print()
    
    # 导入并启动服务器
    try:
        import asyncio
        # 添加父目录到路径中，以便导入 wss_plugin_server
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        
        # 动态导入服务端模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "wss_plugin_server",
            os.path.join(parent_dir, "wss_plugin_server.py")
        )
        server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server_module)
        
        # 运行服务器
        asyncio.run(server_module.main())
        
    except KeyboardInterrupt:
        print('\n\nWSS Plugin Server stopped by user')
        sys.exit(0)
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start WSS Plugin Server')
    parser.add_argument('--backend-host', default='127.0.0.1',
                       help='Shadowsocks backend host (default: 127.0.0.1)')
    parser.add_argument('--backend-port', type=int, default=8388,
                       help='Shadowsocks backend port (default: 8388)')
    parser.add_argument('--listen-host', default='0.0.0.0',
                       help='Listen host (default: 0.0.0.0)')
    parser.add_argument('--listen-port', type=int, default=8443,
                       help='Listen port (default: 8443)')
    parser.add_argument('--cert', default=None,
                       help='SSL certificate file (default: fullchain.pem)')
    parser.add_argument('--key', default=None,
                       help='SSL private key file (default: privkey.pem)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--log-file', default=None,
                       help='Log file path (optional)')
    
    args = parser.parse_args()
    
    start_server(
        args.backend_host,
        args.backend_port,
        args.listen_host,
        args.listen_port,
        args.cert,
        args.key,
        args.debug,
        args.log_file
    )


if __name__ == '__main__':
    main()

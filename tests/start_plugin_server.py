#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 WSS Plugin 服务端
用于测试
"""

import os
import sys

def start_server(backend_host='127.0.0.1', backend_port=8388,
                listen_host='127.0.0.1', listen_port=8443,
                cert_file='fullchain.pem', key_file='privkey.pem'):
    """
    启动 WSS Plugin 服务端
    
    Args:
        backend_host: Shadowsocks 后端地址
        backend_port: Shadowsocks 后端端口
        listen_host: 监听地址
        listen_port: 监听端口
        cert_file: SSL 证书文件
        key_file: SSL 私钥文件
    """
    cert_file = os.path.abspath(cert_file)
    key_file =  os.path.abspath(key_file)
    # 设置环境变量
    os.environ['SS_REMOTE_HOST'] = backend_host
    os.environ['SS_REMOTE_PORT'] = str(backend_port)
    os.environ['SS_LOCAL_HOST'] = listen_host
    os.environ['SS_LOCAL_PORT'] = str(listen_port)
    os.environ['SS_PLUGIN_OPTIONS'] = f'cert={cert_file};key={key_file}'
    
    print('='*60)
    print('WSS Plugin Server Configuration')
    print('='*60)
    print(f'Backend (Shadowsocks):  {backend_host}:{backend_port}')
    print(f'Listen (WSS):           {listen_host}:{listen_port}')
    print(f'Certificate:            {cert_file}')
    print(f'Private Key:            {key_file}')
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
    parser.add_argument('--listen-host', default='127.0.0.1',
                       help='Listen host (default: 127.0.0.1)')
    parser.add_argument('--listen-port', type=int, default=8443,
                       help='Listen port (default: 8443)')
    parser.add_argument('--cert', default='fullchain.pem',
                       help='SSL certificate file (default: fullchain.pem)')
    parser.add_argument('--key', default='privkey.pem',
                       help='SSL private key file (default: privkey.pem)')
    
    args = parser.parse_args()
    
    start_server(
        args.backend_host,
        args.backend_port,
        args.listen_host,
        args.listen_port,
        args.cert,
        args.key
    )


if __name__ == '__main__':
    main()

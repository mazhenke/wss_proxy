#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 WSS Plugin 客户端
用于测试
"""

import os
import sys

def start_client(remote_host='127.0.0.1', remote_port=8443,
                local_host='127.0.0.1', local_port=1080,
                cert_file=None, debug=False, log_file=None):
    """
    启动 WSS Plugin 客户端
    
    Args:
        remote_host: WSS 服务器地址
        remote_port: WSS 服务器端口
        local_host: 本地监听地址
        local_port: 本地监听端口
        cert_file: SSL 证书文件（可选，用于验证服务器证书）
        debug: 启用调试日志
        log_file: 日志文件路径
    """
    # 设置环境变量
    os.environ['SS_REMOTE_HOST'] = remote_host
    os.environ['SS_REMOTE_PORT'] = str(remote_port)
    os.environ['SS_LOCAL_HOST'] = local_host
    os.environ['SS_LOCAL_PORT'] = str(local_port)
    
    # 构建插件选项
    plugin_options = []
    if cert_file:
        plugin_options.append(f'cert={cert_file}')
    if debug:
        plugin_options.append('debug=true')
    if log_file:
        plugin_options.append(f'log_file={os.path.abspath(log_file)}')
    
    os.environ['SS_PLUGIN_OPTIONS'] = ';'.join(plugin_options)
    
    print('='*60)
    print('WSS Plugin Client Configuration')
    print('='*60)
    print(f'Remote (WSS Server):    {remote_host}:{remote_port}')
    print(f'Local (SOCKS):          {local_host}:{local_port}')
    if cert_file:
        cert_file = os.path.abspath(cert_file)
        print(f'Certificate:            {cert_file}')
        print(f'Cert Verification:      Enabled')
    else:
        print(f'Certificate:            None')
        print(f'Cert Verification:      Disabled')
    print('='*60)
    print()
    
    # 导入并启动客户端
    try:
        import asyncio
        # 添加父目录到路径中，以便导入 wss_plugin_client
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        
        # 动态导入客户端模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "wss_plugin_client",
            os.path.join(parent_dir, "wss_plugin_client.py")
        )
        client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(client_module)
        
        # 运行客户端
        asyncio.run(client_module.main())
        
    except KeyboardInterrupt:
        print('\n\nWSS Plugin Client stopped by user')
        sys.exit(0)
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start WSS Plugin Client')
    parser.add_argument('--remote-host', default='127.0.0.1',
                       help='WSS server host (default: 127.0.0.1)')
    parser.add_argument('--remote-port', type=int, default=8443,
                       help='WSS server port (default: 8443)')
    parser.add_argument('--local-host', default='127.0.0.1',
                       help='Local listen host (default: 127.0.0.1)')
    parser.add_argument('--local-port', type=int, default=1080,
                       help='Local listen port (default: 1080)')
    parser.add_argument('--cert', default=None,
                       help='SSL certificate file for verification (optional)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--log-file', default=None,
                       help='Log file path (optional)')
    
    args = parser.parse_args()
    
    start_client(
        args.remote_host,
        args.remote_port,
        args.local_host,
        args.local_port,
        args.cert,
        args.debug,
        args.log_file
    )


if __name__ == '__main__':
    main()

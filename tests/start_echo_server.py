#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动测试用的 Echo 服务器
模拟 Shadowsocks 后端服务
"""

import asyncio
import sys
import signal

class EchoServer:
    """Echo 服务器 - 将接收到的数据原样返回"""
    
    def __init__(self, host='127.0.0.1', port=8388):
        self.host = host
        self.port = port
        self.server = None
        self.client_count = 0
        
    async def handle_client(self, reader, writer):
        """处理客户端连接"""
        self.client_count += 1
        client_id = self.client_count
        addr = writer.get_extra_info('peername')
        
        print(f'[Client {client_id}] Connected from {addr}')
        
        try:
            total_bytes = 0
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                total_bytes += len(data)
                print(f'[Client {client_id}] Received {len(data)} bytes (total: {total_bytes})')
                
                # 回显数据
                writer.write(data)
                await writer.drain()
                print(f'[Client {client_id}] Echoed {len(data)} bytes')
                
        except asyncio.CancelledError:
            print(f'[Client {client_id}] Connection cancelled')
        except Exception as e:
            print(f'[Client {client_id}] Error: {e}')
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            print(f'[Client {client_id}] Disconnected (total bytes: {total_bytes})')
    
    async def start(self):
        """启动服务器"""
        print(f'Starting Echo Server on {self.host}:{self.port}')
        print('Press Ctrl+C to stop')
        print('-' * 50)
        
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
        print(f'✓ Echo Server listening on {addrs}')
        print('-' * 50)
        
        async with self.server:
            await self.server.serve_forever()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Echo Server for WSS Plugin')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8388, help='Port to listen (default: 8388)')
    
    args = parser.parse_args()
    
    server = EchoServer(args.host, args.port)
    
    # 处理 Ctrl+C
    def signal_handler(sig, frame):
        print('\n\nShutting down Echo Server...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print('\nEcho Server stopped by user')
    except Exception as e:
        print(f'✗ Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

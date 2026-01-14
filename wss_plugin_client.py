#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowsocks SIP003 Plugin - WebSocket Client
基于WSS的Shadowsocks插件客户端
"""

import asyncio
import os
import sys
import ssl
import logging
import struct
import pathlib
from typing import Optional

# 导入websockets库
PATH_WEBSOCKETS = pathlib.Path(__file__).parent / "websockets" / "src"
sys.path.insert(0, str(PATH_WEBSOCKETS))

from websockets.asyncio.client import connect as ws_connect

# 导入加扰模块
from obfuscator import DataObfuscator

def setup_logging(debug=False, log_file=None):
    """配置日志系统"""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # 文件输出（如果指定）
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # 配置根日志
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers,
        force=True
    )
    
    # 配置 SSL、websockets 和插件日志
    if debug:
        logging.getLogger('ssl').setLevel(logging.DEBUG)
        logging.getLogger('websockets').setLevel(logging.DEBUG)
        logging.getLogger('wss-plugin-server').setLevel(logging.DEBUG)
        logging.getLogger('wss-plugin-client').setLevel(logging.DEBUG)
    else:
        logging.getLogger('ssl').setLevel(logging.INFO)
        logging.getLogger('websockets').setLevel(logging.INFO)
        logging.getLogger('wss-plugin-server').setLevel(logging.INFO)
        logging.getLogger('wss-plugin-client').setLevel(logging.INFO)


logger = logging.getLogger('wss-plugin-client')


class WSSPluginClient:
    """WSS Plugin 客户端实现"""
    
    def __init__(self):
        """初始化客户端，从环境变量读取配置"""
        # SIP003 标准环境变量
        self.ss_remote_host = os.environ.get('SS_REMOTE_HOST', '127.0.0.1')
        self.ss_remote_port = int(os.environ.get('SS_REMOTE_PORT', '8388'))
        self.ss_local_host = os.environ.get('SS_LOCAL_HOST', '127.0.0.1')
        self.ss_local_port = int(os.environ.get('SS_LOCAL_PORT', '1080'))
        
        # 插件选项
        self.plugin_opts = self._parse_plugin_opts(os.environ.get('SS_PLUGIN_OPTIONS', ''))
        
        # 配置日志（从插件选项读取）
        debug = self.plugin_opts.get('debug', 'false').lower() in ('true', '1', 'yes')
        log_file = self.plugin_opts.get('log_file', None)
        setup_logging(debug=debug, log_file=log_file)
        
        # 证书配置（可选）
        self.cert_file = self.plugin_opts.get('cert', None)
        
        # 判断是否使用SSL - 根据是否提供了证书
        self.use_ssl = self.cert_file is not None
        
        # WSS配置 - 直接使用 SS 环境变量
        self.wss_host = self.ss_remote_host
        self.wss_port = self.ss_remote_port
        self.wss_path = '/ws'
        
        # 数据加扰器 - 使用固定密钥
        self.obfuscator = DataObfuscator('wss_plugin_default_key')
        
        protocol = 'wss' if self.use_ssl else 'ws'
        logger.info(f'Client initialized: local={self.ss_local_host}:{self.ss_local_port}, '
                   f'remote={protocol}://{self.wss_host}:{self.wss_port}')
    
    def _parse_plugin_opts(self, opts_str: str) -> dict:
        """解析插件选项字符串"""
        opts = {}
        if not opts_str:
            return opts
        
        for pair in opts_str.split(';'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                opts[key.strip()] = value.strip()
        
        return opts
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """创建SSL上下文"""
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        # 跳过所有证书验证（允许自签名和任何证书）
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        if self.cert_file:
            logger.info(f'SSL certificate specified (verification disabled for self-signed): {self.cert_file}')
        else:
            logger.info('SSL certificate verification disabled (no cert specified)')
        
        return ssl_context
    
    async def connect_websocket(self):
        """连接到WSS/WS服务器，返回websocket连接"""
        protocol = 'wss' if self.use_ssl else 'ws'
        uri = f"{protocol}://{self.wss_host}:{self.wss_port}{self.wss_path}"
        ssl_context = self._create_ssl_context() if self.use_ssl else None
        
        # 浏览器 User-Agent
        additional_headers = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        ]
        
        try:
            logger.info(f'Connecting to {uri}...')
            websocket = await ws_connect(
                uri,
                ssl=ssl_context,
                additional_headers=additional_headers,
                max_size=16 * 1024 * 1024,  # 16MB max message size
                ping_interval=30,
                ping_timeout=10
            )
            logger.info('WebSocket connected successfully')
            return websocket
        except Exception as e:
            logger.error(f'Failed to connect to WebSocket: {e}')
            return None
    
    async def handle_local_to_remote(self, websocket, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, running: dict):
        """处理从本地到远程的数据流"""
        try:
            while running['active']:
                # 从本地Shadowsocks读取数据
                data = await reader.read(8192)
                if not data:
                    logger.debug('Local connection closed')
                    break
                
                # 数据加扰
                obfuscated_data = self.obfuscator.obfuscate(data)
                
                # 发送到WSS服务器
                await websocket.send(obfuscated_data)
                logger.debug(f'Sent {len(data)} bytes (obfuscated to {len(obfuscated_data)} bytes)')
                
        except Exception as e:
            logger.error(f'Error in local_to_remote: {e}')
        finally:
            running['active'] = False
            writer.close()
            await writer.wait_closed()
    
    async def handle_remote_to_local(self, websocket, writer: asyncio.StreamWriter, running: dict):
        """处理从远程到本地的数据流"""
        try:
            while running['active']:
                # 从WSS服务器接收数据
                obfuscated_data = await websocket.recv()
                
                # 数据去加扰
                data = self.obfuscator.deobfuscate(obfuscated_data)
                
                # 写入本地Shadowsocks
                writer.write(data)
                await writer.drain()
                logger.debug(f'Received {len(obfuscated_data)} bytes (deobfuscated to {len(data)} bytes)')
                
        except Exception as e:
            logger.error(f'Error in remote_to_local: {e}')
        finally:
            running['active'] = False
            writer.close()
            await writer.wait_closed()
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """处理单个客户端连接"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f'New client connection from {client_addr}')
        
        websocket = None
        try:
            # 连接到WSS服务器（每个客户端独立连接）
            websocket = await self.connect_websocket()
            if not websocket:
                logger.error('Failed to establish WebSocket connection')
                writer.close()
                await writer.wait_closed()
                return
            
            # 双向转发数据（使用独立的running状态）
            running = {'active': True}
            
            local_to_remote = asyncio.create_task(self.handle_local_to_remote(websocket, reader, writer, running))
            remote_to_local = asyncio.create_task(self.handle_remote_to_local(websocket, writer, running))
            
            # 等待任一方向关闭
            done, pending = await asyncio.wait(
                [local_to_remote, remote_to_local],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 取消未完成的任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            logger.error(f'Error handling client: {e}')
        finally:
            if websocket:
                await websocket.close()
            logger.info(f'Client connection closed {client_addr}')
    
    async def start(self):
        """启动客户端服务"""
        logger.info(f'Starting WSS Plugin Client on {self.ss_local_host}:{self.ss_local_port}')
        
        server = await asyncio.start_server(
            self.handle_client,
            self.ss_local_host,
            self.ss_local_port
        )
        
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logger.info(f'WSS Plugin Client listening on {addrs}')
        
        async with server:
            await server.serve_forever()


async def main():
    """主函数"""
    try:
        client = WSSPluginClient()
        await client.start()
    except KeyboardInterrupt:
        logger.info('Received interrupt signal, shutting down...')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

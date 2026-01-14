#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowsocks SIP003 Plugin - WebSocket Server
基于WSS的Shadowsocks插件服务端
"""

import asyncio
import os
import sys
import ssl
import logging
import pathlib
from typing import Optional

# 导入websockets库
PATH_WEBSOCKETS = pathlib.Path(__file__).parent / "websockets" / "src"
sys.path.insert(0, str(PATH_WEBSOCKETS))

from websockets.asyncio.server import serve

# 导入加扰模块
from obfuscator import DataObfuscator


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wss-plugin-server')


# Get loggers for SSL and websockets
ssl_logger = logging.getLogger('ssl')
ssl_logger.setLevel(logging.DEBUG)

websockets_logger = logging.getLogger('websockets')
websockets_logger.setLevel(logging.DEBUG)

class WSSPluginServer:
    """WSS Plugin 服务端实现"""
    
    def __init__(self):
        """初始化服务端，从环境变量读取配置"""
        # SIP003 标准环境变量
        self.ss_remote_host = os.environ.get('SS_REMOTE_HOST', '127.0.0.1')
        self.ss_remote_port = int(os.environ.get('SS_REMOTE_PORT', '8388'))
        self.ss_local_host = os.environ.get('SS_LOCAL_HOST', '0.0.0.0')
        self.ss_local_port = int(os.environ.get('SS_LOCAL_PORT', '443'))
        
        # 插件选项 - 仅支持证书和密钥配置
        self.plugin_opts = self._parse_plugin_opts(os.environ.get('SS_PLUGIN_OPTIONS', ''))
        
        # 证书配置
        self.cert_file = self.plugin_opts.get('cert', 'fullchain.pem')
        self.key_file = self.plugin_opts.get('key', 'privkey.pem')
        
        # WSS配置 - 直接使用 SS 环境变量
        self.wss_host = self.ss_local_host
        self.wss_port = self.ss_local_port
        self.wss_path = '/ws'
        
        # 数据加扰器 - 使用固定密钥
        self.obfuscator = DataObfuscator('wss_plugin_default_key')
        
        logger.info(f'Server initialized: listen={self.wss_host}:{self.wss_port}, '
                   f'backend={self.ss_remote_host}:{self.ss_remote_port}')
    
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
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        try:
            # 加载证书和私钥
            cert_path = pathlib.Path(self.cert_file)
            if not cert_path.is_absolute():
                cert_path = pathlib.Path(__file__).parent / self.cert_file
            
            key_path = pathlib.Path(self.key_file)
            if not key_path.is_absolute():
                key_path = pathlib.Path(__file__).parent / self.key_file
            
            ssl_context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
            logger.info(f'Loaded certificate from {cert_path} and key from {key_path}')
        except Exception as e:
            logger.error(f'Failed to load certificate/key: {e}')
            raise
        
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        return ssl_context
    
    async def connect_to_shadowsocks(self) -> tuple:
        """连接到后端Shadowsocks服务器"""
        try:
            reader, writer = await asyncio.open_connection(
                self.ss_remote_host,
                self.ss_remote_port
            )
            logger.debug(f'Connected to Shadowsocks backend at {self.ss_remote_host}:{self.ss_remote_port}')
            return reader, writer
        except Exception as e:
            logger.error(f'Failed to connect to Shadowsocks backend: {e}')
            raise
    
    async def handle_wss_to_ss(self, websocket, writer: asyncio.StreamWriter, running: dict):
        """处理从WSS客户端到Shadowsocks的数据流"""
        try:
            while running['active']:
                # 从WSS客户端接收数据
                obfuscated_data = await websocket.recv()
                
                # 数据去加扰
                data = self.obfuscator.deobfuscate(obfuscated_data)
                
                # 写入Shadowsocks
                writer.write(data)
                await writer.drain()
                logger.debug(f'WSS->SS: {len(obfuscated_data)} bytes (deobfuscated to {len(data)} bytes)')
                
        except Exception as e:
            logger.debug(f'WSS->SS error: {e}')
        finally:
            running['active'] = False
            writer.close()
            await writer.wait_closed()
    
    async def handle_ss_to_wss(self, websocket, reader: asyncio.StreamReader, running: dict):
        """处理从Shadowsocks到WSS客户端的数据流"""
        try:
            while running['active']:
                # 从Shadowsocks读取数据
                data = await reader.read(8192)
                if not data:
                    logger.debug('Shadowsocks connection closed')
                    break
                
                # 数据加扰
                obfuscated_data = self.obfuscator.obfuscate(data)
                
                # 发送到WSS客户端
                await websocket.send(obfuscated_data)
                logger.debug(f'SS->WSS: {len(data)} bytes (obfuscated to {len(obfuscated_data)} bytes)')
                
        except Exception as e:
            logger.debug(f'SS->WSS error: {e}')
        finally:
            running['active'] = False
    
    async def handle_client(self, websocket):
        """处理单个WSS客户端连接"""
        client_addr = websocket.remote_address
        logger.info(f'New WSS client connection from {client_addr}')
        
        ss_reader = None
        ss_writer = None
        
        try:
            # 连接到后端Shadowsocks服务器
            ss_reader, ss_writer = await self.connect_to_shadowsocks()
            
            # 双向转发数据
            running = {'active': True}
            
            wss_to_ss = asyncio.create_task(self.handle_wss_to_ss(websocket, ss_writer, running))
            ss_to_wss = asyncio.create_task(self.handle_ss_to_wss(websocket, ss_reader, running))
            
            # 等待任一方向关闭
            done, pending = await asyncio.wait(
                [wss_to_ss, ss_to_wss],
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
            logger.error(f'Error handling WSS client: {e}')
        finally:
            if ss_writer:
                ss_writer.close()
                await ss_writer.wait_closed()
            await websocket.close()
            logger.info(f'WSS client connection closed {client_addr}')
    
    async def start(self):
        """启动服务端"""
        logger.info(f'Starting WSS Plugin Server on {self.wss_host}:{self.wss_port}{self.wss_path}')
        
        ssl_context = self._create_ssl_context()
        
        async with serve(
            self.handle_client,
            self.wss_host,
            self.wss_port,
            ssl=ssl_context,
            max_size=16 * 1024 * 1024,  # 16MB max message size
            ping_interval=30,
            ping_timeout=10
        ) as server:
            logger.info(f'WSS Plugin Server listening on wss://{self.wss_host}:{self.wss_port}{self.wss_path}')
            await asyncio.Future()  # run forever


async def main():
    """主函数"""
    try:
        server = WSSPluginServer()
        await server.start()
    except KeyboardInterrupt:
        logger.info('Received interrupt signal, shutting down...')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

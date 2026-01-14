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

# 配置常量
CFG_MAX_MESSAGE_SIZE = 16 * 1024 * 1024  # 16MB
CFG_PING_INTERVAL = 30 # ping every 30 seconds
CFG_PING_TIMEOUT = 10 # timeout if no pong within 10 seconds
CFG_READ_BUF_SIZE = 8192  # 8KB
CFG_PRE_CONNECTION = True  # True: per-connection mode (for ss-libev), False: daemon mode (standalone)

# 导入websockets库
PATH_WEBSOCKETS = pathlib.Path(__file__).parent / "websockets" / "src"
sys.path.insert(0, str(PATH_WEBSOCKETS))

from websockets.asyncio.server import serve

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


logger = logging.getLogger('wss-plugin-server')

class WSSPluginServer:
    """WSS Plugin 服务端实现"""
    
    def __init__(self):
        """初始化服务端，从环境变量读取配置"""
        # SIP003 标准环境变量
        self.ss_remote_host = os.environ.get('SS_REMOTE_HOST', '127.0.0.1')
        self.ss_remote_port = int(os.environ.get('SS_REMOTE_PORT', '8388'))
        self.ss_local_host = os.environ.get('SS_LOCAL_HOST', '0.0.0.0')
        self.ss_local_port = int(os.environ.get('SS_LOCAL_PORT', '443'))
        
        # 插件选项
        self.plugin_opts = self._parse_plugin_opts(os.environ.get('SS_PLUGIN_OPTIONS', ''))
        
        # 配置日志（从插件选项读取）
        debug = self.plugin_opts.get('debug', 'false').lower() in ('true', '1', 'yes')
        log_file = self.plugin_opts.get('log_file', None)
        setup_logging(debug=debug, log_file=log_file)
        
        # 证书配置
        self.cert_file = self.plugin_opts.get('cert', None)
        self.key_file = self.plugin_opts.get('key', None)
        
        # 判断是否使用SSL（只有在同时提供cert和key时才使用SSL）
        self.use_ssl = self.cert_file is not None and self.key_file is not None
        
        # WSS配置 - 在服务端模式下，LOCAL 是 ss-server 监听的内部地址，REMOTE 是插件对外暴露的地址
        # 所以插件应该监听 REMOTE，连接到 LOCAL
        self.wss_host = self.ss_remote_host  # 插件对外监听地址
        self.wss_port = self.ss_remote_port  # 插件对外监听端口
        self.wss_path = '/ws'
        
        # Shadowsocks 后端地址（插件连接的目标）
        self.backend_host = self.ss_local_host  # SS 内部监听地址
        self.backend_port = self.ss_local_port  # SS 内部监听端口
        
        # 数据加扰器 - 使用固定密钥
        self.obfuscator = DataObfuscator('wss_plugin_default_key')
        
        logger.info(f'Server initialized: listen={self.wss_host}:{self.wss_port}, '
                   f'backend={self.backend_host}:{self.backend_port}')
    
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
                self.backend_host,
                self.backend_port
            )
            logger.debug(f'Connected to Shadowsocks backend at {self.backend_host}:{self.backend_port}')
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
                data = await reader.read(CFG_READ_BUF_SIZE)
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
        ssl_context = None
        protocol = 'wss'
        
        if self.use_ssl:
            logger.info(f'Starting WSS Plugin Server on {self.wss_host}:{self.wss_port}{self.wss_path} (SSL enabled)')
            ssl_context = self._create_ssl_context()
        else:
            logger.info(f'Starting WebSocket Plugin Server on {self.wss_host}:{self.wss_port}{self.wss_path} (SSL disabled)')
            protocol = 'ws'
        
        async with serve(
            self.handle_client,
            self.wss_host,
            self.wss_port,
            ssl=ssl_context,
            max_size=CFG_MAX_MESSAGE_SIZE,
            ping_interval=CFG_PING_INTERVAL,
            ping_timeout=CFG_PING_TIMEOUT
        ) as server:
            logger.info(f'Plugin Server listening on {protocol}://{self.wss_host}:{self.wss_port}{self.wss_path}')
            await asyncio.Future()  # run forever


async def main():
    """主函数 - 支持 per-connection 和 daemon 两种模式"""
    try:
        server = WSSPluginServer()
        
        if CFG_PRE_CONNECTION:
            # Per-connection mode：处理单个客户端连接后退出
            logger.info('Running in per-connection mode')
            await main_per_connection(server)
        else:
            # Daemon mode：持续监听多个客户端连接
            logger.info('Running in daemon mode')
            await server.start()
            
    except KeyboardInterrupt:
        logger.info('Received interrupt signal, shutting down...')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        sys.exit(1)


async def main_per_connection(server):
    """Per-connection mode - 处理单个 WebSocket 客户端连接，通常由 ss-libev 为每个用户连接调用一次"""
    try:
        # 在 per-connection mode 下，ss-libev 创建一个 WebSocket 连接并传给我们
        # 我们需要接受 WebSocket 连接并转发数据
        
        ssl_context = None
        protocol = 'wss'
        
        if server.use_ssl:
            logger.info(f'Per-connection WSS mode (SSL enabled)')
            ssl_context = server._create_ssl_context()
        else:
            logger.info(f'Per-connection WebSocket mode (SSL disabled)')
            protocol = 'ws'
        
        # 监听一个连接（使用 serve 但立即接受一个连接后就处理）
        async def handle_one_connection(websocket):
            logger.info(f'Per-connection: Handling WebSocket client from {websocket.remote_address}')
            await server.handle_client(websocket)
        
        # 创建服务器以接受单个连接
        async with serve(
            handle_one_connection,
            server.wss_host,
            server.wss_port,
            ssl=ssl_context,
            max_size=CFG_MAX_MESSAGE_SIZE,
            ping_interval=CFG_PING_INTERVAL,
            ping_timeout=CFG_PING_TIMEOUT
        ) as ws_server:
            logger.info(f'Per-connection server listening on {protocol}://{server.wss_host}:{server.wss_port}{server.wss_path}')
            
            # 在 per-connection mode 下，我们通常只处理一个连接
            # 但保持服务器运行，让 ss-libev 控制生命周期
            await asyncio.Future()  # run forever
            
    except Exception as e:
        logger.error(f'Error in per-connection mode: {e}', exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())

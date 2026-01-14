#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 WSS Plugin 转换为可执行文件（ELF 或 EXE）
使用 PyInstaller 打包 Python 代码

Requirements:
  pip install pyinstaller
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path


class ExecutableBuilder:
    """可执行文件构建器"""
    
    def __init__(self, output_dir='dist'):
        """
        初始化构建器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.system = platform.system()
        self.script_dir = Path(__file__).parent
    
    def build_client(self, onefile=False, console=True):
        """
        构建客户端可执行文件
        
        Args:
            onefile: 是否生成单一文件（True: 单文件，False: 文件夹）
            console: 是否显示控制台
        """
        return self._build(
            'wss_plugin_client.py',
            'wss-plugin-client',
            onefile=onefile,
            console=console
        )
    
    def build_server(self, onefile=False, console=True):
        """
        构建服务端可执行文件
        
        Args:
            onefile: 是否生成单一文件
            console: 是否显示控制台
        """
        return self._build(
            'wss_plugin_server.py',
            'wss-plugin-server',
            onefile=onefile,
            console=console
        )
    
    def _build(self, script_file, output_name, onefile=False, console=True):
        """
        通用构建函数
        
        Args:
            script_file: Python 脚本文件名
            output_name: 输出可执行文件名（不含扩展名）
            onefile: 是否生成单一文件
            console: 是否显示控制台
        
        Returns:
            bool: 成功返回 True
        """
        script_path = self.script_dir / script_file
        
        if not script_path.exists():
            print(f'✗ Error: {script_file} not found')
            return False
        
        print(f'\n{"="*60}')
        print(f'Building {script_file} -> {output_name}')
        print(f'Platform: {self.system}')
        print(f'Output directory: {self.output_dir.absolute()}')
        print(f'{"="*60}\n')
        
        # 构建 PyInstaller 命令
        cmd = [
            'pyinstaller',
            '--distpath', str(self.output_dir),
            '--workpath', str(self.output_dir / 'build'),
            '--specpath', str(self.output_dir / 'build'),
            '--name', output_name,
        ]
        
        # 单文件选项
        if onefile:
            cmd.append('--onefile')
        
        # 平台相关选项
        if self.system == 'Windows':
            if not console:
                cmd.append('--windowed')
        elif self.system == 'Darwin':  # macOS
            if not console:
                cmd.append('--windowed')
        
        # 添加数据文件（websockets 库）；优先打包本地 websockets/src，如果不存在则依赖已安装包
        websockets_src = self.script_dir / 'websockets' / 'src'
        if websockets_src.exists():
            cmd.append(f'--add-data={websockets_src}:websockets')
            cmd.extend(['--paths', str(websockets_src)])

        # 强制包含 websockets 核心模块（其余交由 hook-websockets 处理）
        cmd.append('--hidden-import=websockets')
        
        # 添加脚本
        cmd.append(str(script_path))
        
        print(f'Executing: {" ".join(cmd)}\n')
        
        try:
            result = subprocess.run(cmd, check=True)
            print(f'\n✓ Build successful!')
            
            # 显示输出文件路径
            if self.system == 'Windows':
                exe_file = self.output_dir / output_name / f'{output_name}.exe'
                print(f'Output: {exe_file.absolute()}')
            else:
                elf_file = self.output_dir / output_name / output_name
                print(f'Output: {elf_file.absolute()}')
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f'\n✗ Build failed with error code {e.returncode}')
            return False
        except FileNotFoundError:
            print(f'\n✗ Error: pyinstaller not found')
            print(f'Please install: pip install pyinstaller')
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Build WSS Plugin executables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Build client (default: folder mode)
  python3 build_executable.py --client
  
  # Build server (single file)
  python3 build_executable.py --server --onefile
  
  # Build both
  python3 build_executable.py --all --onefile
  
  # Custom output directory
  python3 build_executable.py --client --output build/bin
  
Requirements:
  pip install pyinstaller
        '''
    )
    
    parser.add_argument('--client', action='store_true', help='Build client')
    parser.add_argument('--server', action='store_true', help='Build server')
    parser.add_argument('--all', action='store_true', help='Build both client and server')
    parser.add_argument('--onefile', action='store_true', help='Generate single-file executable')
    parser.add_argument('--output', default='dist', help='Output directory (default: dist)')
    parser.add_argument('--windowed', action='store_true', help='Hide console window (Windows)')
    
    args = parser.parse_args()
    
    # 默认构建客户端
    if not (args.client or args.server or args.all):
        args.client = True
        args.server = True
    
    builder = ExecutableBuilder(output_dir=args.output)
    
    success = True
    
    if args.client or args.all:
        if not builder.build_client(onefile=args.onefile, console=not args.windowed):
            success = False
    
    if args.server or args.all:
        if not builder.build_server(onefile=args.onefile, console=not args.windowed):
            success = False
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成自签名SSL证书
用于测试 WSS Plugin
"""

import os
import sys
import subprocess
from pathlib import Path

def generate_certificate(cert_file='fullchain.pem', key_file='privkey.pem', days=365, domain='localhost'):
    """
    生成自签名SSL证书
    
    Args:
        cert_file: 证书文件名
        key_file: 私钥文件名
        days: 有效期天数
        domain: 证书CN/域名
    
    Returns:
        bool: 成功返回 True，失败返回 False
    """
    cert_path = Path(cert_file)
    key_path = Path(key_file)
    
    # 检查证书是否已存在
    if cert_path.exists() and key_path.exists():
        print(f'✓ Certificates already exist:')
        print(f'  - {cert_path.absolute()}')
        print(f'  - {key_path.absolute()}')
        
        response = input('Overwrite existing certificates? [y/N]: ')
        if response.lower() != 'y':
            print('Keeping existing certificates.')
            return True
    
    print(f'Generating self-signed SSL certificate...')
    print(f'  Certificate: {cert_file}')
    print(f'  Private key: {key_file}')
    print(f'  Valid for: {days} days')
    
    # 生成证书命令
    cmd = [
        'openssl', 'req', '-x509',
        '-newkey', 'rsa:2048',
        '-nodes',
        '-keyout', key_file,
        '-out', cert_file,
        '-days', str(days),
        '-subj', f'/CN={domain}'
    ]
    
    try:
        # 执行命令，隐藏输出
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # 验证文件已创建
        if cert_path.exists() and key_path.exists():
            print(f'✓ Certificate generated successfully!')
            print(f'  Certificate: {cert_path.absolute()}')
            print(f'  Private key: {key_path.absolute()}')
            
            # 显示证书信息
            print('\nCertificate details:')
            cert_info = subprocess.run(
                ['openssl', 'x509', '-in', cert_file, '-noout', '-subject', '-dates'],
                capture_output=True,
                text=True
            )
            for line in cert_info.stdout.strip().split('\n'):
                print(f'  {line}')
            
            return True
        else:
            print('✗ Certificate files not found after generation')
            return False
            
    except subprocess.CalledProcessError as e:
        print(f'✗ Failed to generate certificate: {e}')
        if e.stderr:
            print(f'Error: {e.stderr}')
        return False
    except FileNotFoundError:
        print('✗ openssl command not found')
        print('Please install OpenSSL:')
        print('  Ubuntu/Debian: sudo apt-get install openssl')
        print('  macOS: brew install openssl')
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate self-signed SSL certificate')
    parser.add_argument('--cert', default='fullchain.pem', help='Certificate file name (default: fullchain.pem)')
    parser.add_argument('--key', default='privkey.pem', help='Private key file name (default: privkey.pem)')
    parser.add_argument('--days', type=int, default=365, help='Certificate validity in days (default: 365)')
    parser.add_argument('--domain', default='localhost', help='Common Name / domain for certificate (default: localhost)')
    
    args = parser.parse_args()
    
    success = generate_certificate(args.cert, args.key, args.days, args.domain)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

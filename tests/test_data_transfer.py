#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据传输
发送数据并验证接收到的数据是否正确
"""

import asyncio
import sys
import time

class DataTester:
    """数据传输测试器"""
    
    def __init__(self, host='127.0.0.1', port=1080):
        self.host = host
        self.port = port
        
    async def test_single_message(self, message, timeout=5.0):
        """
        测试单条消息
        
        Args:
            message: 要发送的消息（bytes）
            timeout: 超时时间（秒）
        
        Returns:
            tuple: (success, received_data)
        """
        try:
            # 连接到本地端口
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=timeout
            )
            
            # 发送数据
            writer.write(message)
            await writer.drain()
            
            # 接收数据
            received = await asyncio.wait_for(
                reader.read(len(message)),
                timeout=timeout
            )
            
            # 关闭连接
            writer.close()
            await writer.wait_closed()
            
            return (received == message, received)
            
        except asyncio.TimeoutError:
            return (False, b'TIMEOUT')
        except Exception as e:
            return (False, f'ERROR: {e}'.encode())
    
    async def run_tests(self, verbose=False):
        """
        运行所有测试
        
        Args:
            verbose: 是否显示详细信息
        
        Returns:
            int: 通过的测试数量
        """
        # 测试用例
        test_cases = [
            ('Small message', b'Hello, World!'),
            ('Medium message', b'Test message 123'),
            ('Large data (1KB)', b'A' * 1000),
            ('All byte values', bytes(range(256))),
            ('Empty message', b''),
            ('Binary data', b'\x00\x01\x02\x03\xff\xfe\xfd\xfc'),
            ('UTF-8 text', '你好世界 Hello World 🌍'.encode('utf-8')),
            ('Repeated pattern', b'0123456789' * 100),
        ]
        
        print('='*60)
        print(f'WSS Plugin Data Transfer Test')
        print(f'Target: {self.host}:{self.port}')
        print('='*60)
        print()
        
        passed = 0
        failed = 0
        
        for i, (name, message) in enumerate(test_cases, 1):
            print(f'Test {i}/{len(test_cases)}: {name}')
            print(f'  Size: {len(message)} bytes')
            
            if verbose and len(message) <= 50:
                print(f'  Data: {message!r}')
            
            # 运行测试
            start_time = time.time()
            success, received = await self.test_single_message(message)
            elapsed = time.time() - start_time
            
            if success:
                print(f'  ✓ PASSED (time: {elapsed:.3f}s)')
                passed += 1
            else:
                print(f'  ✗ FAILED (time: {elapsed:.3f}s)')
                print(f'  Expected: {len(message)} bytes')
                if isinstance(received, bytes):
                    print(f'  Received: {len(received)} bytes')
                    if verbose and len(received) <= 50:
                        print(f'  Data: {received!r}')
                else:
                    print(f'  Received: {received}')
                failed += 1
            
            print()
        
        # 总结
        print('='*60)
        print(f'Test Results: {passed} passed, {failed} failed')
        print('='*60)
        
        if failed == 0:
            print('✓ ALL TESTS PASSED!')
        else:
            print(f'✗ {failed} TEST(S) FAILED!')
        
        return passed


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test data transfer through WSS Plugin')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Target host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=1080,
                       help='Target port (default: 1080)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show verbose output')
    parser.add_argument('--custom', '-c', type=str,
                       help='Send custom message (string)')
    parser.add_argument('--hex', type=str,
                       help='Send custom message (hex string)')
    
    args = parser.parse_args()
    
    tester = DataTester(args.host, args.port)
    
    try:
        if args.custom:
            # 发送自定义字符串
            message = args.custom.encode('utf-8')
            print(f'Sending custom message: {args.custom}')
            print(f'Size: {len(message)} bytes')
            
            success, received = await tester.test_single_message(message)
            
            if success:
                print('✓ Message echoed correctly')
                print(f'Received: {received.decode("utf-8", errors="replace")}')
                sys.exit(0)
            else:
                print('✗ Message not echoed correctly')
                sys.exit(1)
                
        elif args.hex:
            # 发送自定义十六进制数据
            try:
                message = bytes.fromhex(args.hex.replace(' ', ''))
            except ValueError as e:
                print(f'✗ Invalid hex string: {e}')
                sys.exit(1)
            
            print(f'Sending hex data: {args.hex}')
            print(f'Size: {len(message)} bytes')
            
            success, received = await tester.test_single_message(message)
            
            if success:
                print('✓ Data echoed correctly')
                print(f'Received: {received.hex(" ")}')
                sys.exit(0)
            else:
                print('✗ Data not echoed correctly')
                sys.exit(1)
        else:
            # 运行所有测试
            passed = await tester.run_tests(args.verbose)
            sys.exit(0 if passed == 8 else 1)
            
    except ConnectionRefusedError:
        print(f'\n✗ Connection refused to {args.host}:{args.port}')
        print('Make sure the WSS Plugin Client is running.')
        sys.exit(1)
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

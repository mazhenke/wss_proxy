#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加扰模块
对传输的数据进行简单的混淆加扰，增加流量特征识别难度
"""

import hashlib
import struct
from typing import Union


class DataObfuscator:
    """数据加扰器，使用简单的XOR和字节位移混淆"""
    
    def __init__(self, key: str):
        """
        初始化加扰器
        
        Args:
            key: 加扰密钥字符串
        """
        self.key = key.encode('utf-8') if isinstance(key, str) else key
        # 生成256字节的密钥流
        self.key_stream = self._generate_key_stream(self.key)
    
    def _generate_key_stream(self, key: bytes) -> bytes:
        """
        从密钥生成密钥流
        
        Args:
            key: 原始密钥
            
        Returns:
            256字节的密钥流
        """
        # 使用SHA256派生密钥
        hash_result = hashlib.sha256(key).digest()
        
        # 扩展到256字节
        key_stream = bytearray()
        for i in range(8):
            hash_result = hashlib.sha256(hash_result + struct.pack('B', i)).digest()
            key_stream.extend(hash_result)
        
        return bytes(key_stream)
    
    def _xor_bytes(self, data: bytes, offset: int = 0) -> bytes:
        """
        使用密钥流对数据进行XOR操作
        
        Args:
            data: 要处理的数据
            offset: 密钥流偏移量
            
        Returns:
            XOR后的数据
        """
        result = bytearray()
        key_len = len(self.key_stream)
        
        for i, byte in enumerate(data):
            key_byte = self.key_stream[(offset + i) % key_len]
            result.append(byte ^ key_byte)
        
        return bytes(result)
    
    def _add_random_padding(self, data: bytes) -> bytes:
        """
        添加随机填充
        
        格式: [2字节长度][原始数据][填充数据]
        填充长度为1-15字节随机
        
        Args:
            data: 原始数据
            
        Returns:
            填充后的数据
        """
        import random
        
        # 生成1-15字节的随机填充
        padding_len = random.randint(1, 15)
        padding = bytes(random.randint(0, 255) for _ in range(padding_len))
        
        # 构造数据包: [2字节数据长度][数据][填充]
        data_len = len(data)
        packet = struct.pack('!H', data_len) + data + padding
        
        return packet
    
    def _remove_padding(self, packet: bytes) -> bytes:
        """
        移除填充
        
        Args:
            packet: 填充后的数据包
            
        Returns:
            原始数据
        """
        if len(packet) < 2:
            raise ValueError("Invalid packet: too short")
        
        # 读取数据长度
        data_len = struct.unpack('!H', packet[:2])[0]
        
        if len(packet) < 2 + data_len:
            raise ValueError(f"Invalid packet: expected at least {2 + data_len} bytes, got {len(packet)}")
        
        # 提取原始数据
        data = packet[2:2 + data_len]
        
        return data
    
    def obfuscate(self, data: Union[bytes, bytearray]) -> bytes:
        """
        对数据进行加扰
        
        加扰步骤:
        1. 添加随机填充
        2. XOR混淆
        3. 字节反转（简单的混淆）
        
        Args:
            data: 原始数据
            
        Returns:
            加扰后的数据
        """
        if isinstance(data, bytearray):
            data = bytes(data)
        
        # 1. 添加随机填充
        padded = self._add_random_padding(data)
        
        # 2. XOR混淆（使用数据长度作为偏移量的一部分）
        offset = len(data) % 256
        xored = self._xor_bytes(padded, offset)
        
        # 3. 简单的字节反转混淆
        # 将数据分成4字节块，每块内部反转
        result = bytearray()
        chunk_size = 4
        for i in range(0, len(xored), chunk_size):
            chunk = xored[i:i + chunk_size]
            result.extend(reversed(chunk))
        
        return bytes(result)
    
    def deobfuscate(self, data: Union[bytes, bytearray]) -> bytes:
        """
        对数据进行去加扰
        
        去加扰步骤（加扰的逆过程）:
        1. 字节反转恢复
        2. XOR恢复
        3. 移除填充
        
        Args:
            data: 加扰后的数据
            
        Returns:
            原始数据
        """
        if isinstance(data, bytearray):
            data = bytes(data)
        
        # 1. 恢复字节反转
        result = bytearray()
        chunk_size = 4
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            result.extend(reversed(chunk))
        
        unreversed = bytes(result)
        
        # 2. XOR恢复需要先解密得到原始长度
        # 但由于我们不知道原始长度，所以需要尝试不同的偏移量
        # 或者改进算法：使用固定偏移或从数据本身派生
        # 这里我们简化：在加扰的数据前添加原始长度信息
        
        # 由于加扰时使用的offset基于原始数据长度，这里需要反向推导
        # 我们尝试所有可能的偏移量（0-255）并选择能成功解密的那个
        for offset in range(256):
            try:
                unxored = self._xor_bytes(unreversed, offset)
                if len(unxored) < 2:
                    continue
                    
                data_len = struct.unpack('!H', unxored[:2])[0]
                
                # 验证数据长度是否合理
                if data_len > 65535 or data_len < 0:
                    continue
                
                # 验证数据包大小是否合理（至少要有长度字段+数据+至少1字节填充）
                if len(unxored) < 2 + data_len + 1:
                    continue
                
                # 尝试移除填充
                original = self._remove_padding(unxored)
                
                # 验证：重新加扰看是否能得到相同结果
                # 注意：由于随机填充的原因，无法精确验证
                # 但我们可以验证长度是否匹配
                if len(original) == data_len and len(original) % 256 == offset:
                    return original
                    
            except (ValueError, struct.error):
                continue
        
        # 如果所有偏移量都失败，抛出错误
        raise ValueError("Failed to deobfuscate data: unable to find valid offset")


# 测试代码
if __name__ == '__main__':
    # 测试加扰和解扰
    obfs = DataObfuscator('test_key_123')
    
    test_data = [
        b'Hello, World!',
        b'A' * 100,
        b'Short',
        b'This is a longer message with more content to test the obfuscation algorithm.',
        bytes(range(256)),  # 所有字节值
    ]
    
    print("Testing DataObfuscator...")
    for i, data in enumerate(test_data):
        print(f"\nTest {i + 1}: {len(data)} bytes")
        print(f"Original: {data[:50]}{'...' if len(data) > 50 else ''}")
        
        # 加扰
        obfuscated = obfs.obfuscate(data)
        print(f"Obfuscated: {len(obfuscated)} bytes (expansion: {len(obfuscated) - len(data)} bytes)")
        print(f"Obfuscated data: {obfuscated[:50].hex()}{'...' if len(obfuscated) > 50 else ''}")
        
        # 去加扰
        deobfuscated = obfs.deobfuscate(obfuscated)
        print(f"Deobfuscated: {len(deobfuscated)} bytes")
        
        # 验证
        if data == deobfuscated:
            print("✓ Success: Data matches!")
        else:
            print("✗ Error: Data mismatch!")
            print(f"Expected: {data[:50]}")
            print(f"Got: {deobfuscated[:50]}")
    
    print("\n" + "="*50)
    print("All tests completed!")

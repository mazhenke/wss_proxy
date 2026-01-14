#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络数据包监听工具 - 类似Wireshark功能
被动抓包（不占用端口），按TCP/UDP和端口过滤并dump
"""

import socket
import struct
import sys
import argparse
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('packet-sniffer')


class PacketSniffer:
    """网络数据包监听器"""
    
    def __init__(self, listen_port=None, listen_host='0.0.0.0', protocol='both', verbose=False, out_file=None, dump_full_frame=False):
        """
        初始化监听器
        
        Args:
            listen_port: 监听的端口（None表示监听所有）
            listen_host: 监听的地址
            protocol: 'tcp', 'udp', 或 'both'
            verbose: 是否详细输出
            out_file: 将输出附加保存到文件
            dump_full_frame: verbose时是否dump整帧（默认仅payload）
        """
        self.listen_port = listen_port
        self.listen_host = listen_host
        self.protocol = protocol.lower()
        self.verbose = verbose
        self.packet_count = 0
        self.out_file = out_file
        self.out_fp = None
        self.dump_full_frame = dump_full_frame
        
        if self.protocol not in ('tcp', 'udp', 'both'):
            raise ValueError("protocol must be 'tcp', 'udp', or 'both'")
        
        if self.out_file:
            try:
                self.out_fp = open(self.out_file, 'a', encoding='utf-8')
                logger.info(f'Logging to file: {self.out_file}')
            except Exception as e:
                logger.error(f'Failed to open output file {self.out_file}: {e}')
                sys.exit(1)
    
    def format_bytes(self, data, length=16, prefix=''):
        """格式化字节数据为16进制和ASCII，可添加前缀"""
        result = []
        result.append('\n')
        for i in range(0, len(data), length):
            chunk = data[i:i+length]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(
                chr(b) if 32 <= b < 127 else '.' 
                for b in chunk
            )
            result.append(f'{prefix}{i:08x}  {hex_part:<{length*3-1}}  {ascii_part}')
        
        return '\n'.join(result)
    
    def format_data_compact(self, data, max_len=256):
        """紧凑格式显示数据"""
        if len(data) <= max_len:
            try:
                return repr(data.decode('utf-8', errors='ignore'))
            except:
                return data.hex()
        else:
            try:
                preview = data[:max_len].decode('utf-8', errors='ignore')
                return f'{repr(preview)}... ({len(data)} bytes total)'
            except:
                return f'{data[:max_len].hex()}... ({len(data)} bytes total)'
    
    def _write_file(self, text: str):
        """写入文件（如果指定输出文件）"""
        if self.out_fp:
            self.out_fp.write(text)
            self.out_fp.flush()

    def sniff_passive(self):
        """被动抓包，不占用端口（需要root权限）"""
        logger.info(f'Starting passive sniffer on interface 0.0.0.0, filter port={self.listen_port or "any"}, protocol={self.protocol}')
        logger.warning('Passive sniffing requires root/administrator privileges')
        try:
            if sys.platform == 'win32':
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                sock.bind((self.listen_host, 0))
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            else:
                sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))

            logger.info('Capturing packets... (Press Ctrl+C to stop)')
            while True:
                try:
                    raw_data, addr = sock.recvfrom(65535)
                    self.process_raw_packet(raw_data, addr)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.debug(f'Error processing packet: {e}')

            if sys.platform == 'win32':
                sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            sock.close()

            if self.out_fp:
                self.out_fp.close()

        except PermissionError:
            logger.error('ERROR: This tool requires root/administrator privileges')
            logger.info('Run with: sudo python3 packet_sniffer.py --raw')
            sys.exit(1)
        except Exception as e:
            logger.error(f'Error: {e}')
            sys.exit(1)
    
    def process_raw_packet(self, data, addr):
        """处理原始以太网帧，解析IP/TCP/UDP并按端口过滤"""
        if len(data) < 34:  # 14字节以太网 + 20字节最小IP头
            return

        eth_proto = struct.unpack('!H', data[12:14])[0]
        if eth_proto != 0x0800:  # 仅处理IPv4
            return

        ip_header = data[14:34]
        ver_ihl = ip_header[0]
        version = ver_ihl >> 4
        ihl = (ver_ihl & 0x0F) * 4
        if version != 4 or len(data) < 14 + ihl:
            return

        total_length = struct.unpack('!H', ip_header[2:4])[0]
        proto = ip_header[9]
        src_ip = socket.inet_ntoa(ip_header[12:16])
        dst_ip = socket.inet_ntoa(ip_header[16:20])

        # 仅关心TCP/UDP
        if proto == 6:
            proto_name = 'TCP'
        elif proto == 17:
            proto_name = 'UDP'
        else:
            return

        # 协议过滤
        if self.protocol == 'tcp' and proto != 6:
            return
        if self.protocol == 'udp' and proto != 17:
            return

        # 端口过滤
        transport_offset = 14 + ihl
        if len(data) < transport_offset + 4:
            return
        src_port, dst_port = struct.unpack('!HH', data[transport_offset:transport_offset+4])
        if self.listen_port and (src_port != self.listen_port and dst_port != self.listen_port):
            return

        # 计算载荷
        if proto == 6:  # TCP
            if len(data) < transport_offset + 20:
                return
            offset_reserved = data[transport_offset + 12]
            tcp_header_len = (offset_reserved >> 4) * 4
            payload_offset = transport_offset + tcp_header_len
        else:  # UDP
            payload_offset = transport_offset + 8

        frame_len = 14 + total_length
        if frame_len > len(data):
            frame_len = len(data)
        payload = data[payload_offset:frame_len]
        frame_bytes = data[:frame_len]
        self.packet_count += 1

        header_line = f'[{proto_name} Packet #{self.packet_count}] {src_ip}:{src_port} -> {dst_ip}:{dst_port}  len={len(payload)} bytes'
        time_line = f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'

        if self.verbose:
            if self.dump_full_frame:
                body = '\nHex Dump (frame):' + self.format_bytes(frame_bytes, prefix='FRAME   ')
            else:
                body = '\nHex Dump (payload):' + self.format_bytes(payload, prefix='PAYLOAD ')
        else:
            body = self.format_data_compact(payload)

        separator = '-' * 80

        logger.info(f'\n{header_line}')
        logger.info(time_line)
        logger.info(body)
        logger.info(separator)

        log_block = f'\n{header_line}\n{time_line}\n{body}\n{separator}\n'
        self._write_file(log_block)
    
    def run(self):
        """启动被动抓包"""
        self.sniff_passive()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Passive Network Packet Sniffer (raw socket, no port bind)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
    Examples (needs sudo/root):
      # Capture TCP only on port 8080
      sudo python3 packet_sniffer.py --port 8080 --protocol tcp

      # Capture UDP 53 (DNS) with hex dump
      sudo python3 packet_sniffer.py --port 53 --protocol udp --verbose

      # Capture both TCP/UDP port 1080
      sudo python3 packet_sniffer.py --port 1080 --protocol both

      # Capture all traffic (no port filter)
      sudo python3 packet_sniffer.py
        '''
    )
    
    parser.add_argument('--port', type=int, default=None,
                help='Filter by port (src or dst). If omitted, capture all ports.')
    parser.add_argument('--protocol', choices=['tcp', 'udp', 'both'], default='both',
                        help='Protocol filter (default: both)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed hex dump (payload by default)')
    parser.add_argument('--dump-full-frame', action='store_true',
                        help='When verbose, dump entire frame instead of payload only')
    parser.add_argument('--out', default=None,
                        help='Append packet logs to file')
    
    args = parser.parse_args()
    
    try:
        sniffer = PacketSniffer(
            listen_port=args.port,
            listen_host='0.0.0.0',
            protocol=args.protocol,
            verbose=args.verbose,
            out_file=args.out,
            dump_full_frame=args.dump_full_frame
        )
        sniffer.run()
    
    except KeyboardInterrupt:
        logger.info('Exiting...')
    except Exception as e:
        logger.error(f'Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()

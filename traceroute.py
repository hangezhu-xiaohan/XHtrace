#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct
import random
import time
import platform
import subprocess
import re
import statistics
import sys
import select
import ipaddress
import threading
from typing import Generator, Tuple, Dict, Optional, List, Union

"""
Enhanced Traceroute Implementation

This module provides a robust implementation of the traceroute utility with support
for both IPv4 and IPv6 protocols, multiple packet types (ICMP, UDP), and cross-platform
compatibility. It includes comprehensive error handling and detailed reporting.
"""

# Constants
DEFAULT_MAX_HOPS = 30
DEFAULT_TIMEOUT = 3.0
DEFAULT_PACKET_SIZE = 64
DEFAULT_PORT = 33434
DEFAULT_MAX_RETRIES = 3

# Error messages
ERROR_UNSUPPORTED_PROTOCOL = "Unsupported protocol: {}"
ERROR_INVALID_HOPS = "Hops must be between 1 and 255: {}"
ERROR_INVALID_TIMEOUT = "Timeout must be positive: {}"
ERROR_ADDRESS_RESOLUTION = "Could not resolve target: {}"
ERROR_TRACEROUTE_FAILED = "Traceroute failed: {}"
ERROR_PERMISSION_DENIED = "Permission denied. Try running with administrative privileges."
ERROR_NETWORK_UNAVAILABLE = "Network unavailable or unreachable."

class TracerouteError(Exception):
    """Base exception class for traceroute operations"""
    pass

def calculate_checksum(data):
    """
    计算校验和
    """
    if len(data) % 2 != 0:
        data += b'\x00'
    
    checksum = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + data[i+1]
        checksum += w
    
    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum = ~checksum & 0xffff
    return checksum

def create_icmp_packet(packet_id, sequence, packet_size=64):
    """
    Create an ICMP echo request packet (Type 8, Code 0).
    
    Args:
        packet_id: Unique packet identifier
        sequence: Packet sequence number
        packet_size: Size of data portion in bytes
        
    Returns:
        Complete ICMP packet as bytes
    """
    # ICMP header: type(8), code(0), checksum(0), identifier(2 bytes), sequence(2 bytes)
    header = struct.pack('!BBHHH', 8, 0, 0, packet_id, sequence)
    
    # Data portion - fill with timestamp and padding to reach requested size
    timestamp = struct.pack('!d', time.time())
    padding_size = max(0, packet_size - len(header) - len(timestamp))
    padding = bytes([random.randint(0, 255) for _ in range(padding_size)])
    data = timestamp + padding
    
    # Calculate checksum
    checksum = calculate_checksum(header + data)
    header = struct.pack('!BBHHH', 8, 0, checksum, packet_id, sequence)
    
    return header + data

def create_icmpv6_packet(packet_id, sequence, packet_size=64):
    """
    Create an ICMPv6 echo request packet (Type 128, Code 0).
    
    Args:
        packet_id: Unique packet identifier
        sequence: Packet sequence number
        packet_size: Size of data portion in bytes
        
    Returns:
        Complete ICMPv6 packet as bytes
    """
    # ICMPv6 header: type(128), code(0), checksum(0), sequence(2 bytes)
    checksum = 0
    header = struct.pack('!BBHH', 128, 0, checksum, sequence)
    
    # Data portion - fill with timestamp and padding to reach requested size
    timestamp = struct.pack('!d', time.time())
    padding_size = max(0, packet_size - len(header) - len(timestamp))
    padding = bytes([random.randint(0, 255) for _ in range(padding_size)])
    data = timestamp + padding
    
    # Note: For ICMPv6, the checksum calculation requires the IPv6 pseudo-header
    # In practice, the socket will automatically compute and set the correct checksum
    header = struct.pack('!BBHH', 128, 0, 0, sequence)
    
    return header + data

def create_udp_packet(packet_id, port, packet_size=64):
    """
    Create a UDP packet for traceroute.
    
    Args:
        packet_id: Unique packet identifier (used in payload)
        port: Destination port
        packet_size: Size of data portion in bytes
        
    Returns:
        UDP payload as bytes
    """
    # Create payload with packet_id, timestamp, and random padding
    packet_id_bytes = struct.pack('!I', packet_id)
    timestamp = struct.pack('!d', time.time())
    
    # Calculate data size (excluding UDP header)
    data_size = packet_size - 8  # 8 bytes for UDP header
    padding_size = max(0, data_size - len(packet_id_bytes) - len(timestamp))
    padding = bytes([random.randint(0, 255) for _ in range(padding_size)])
    
    # Create data portion
    data = packet_id_bytes + timestamp + padding
    
    # UDP header
    udp_header = struct.pack('!HHHH', packet_id, port, len(data) + 8, 0)
    
    return udp_header + data

def _windows_tracert(
    target_ip: str,
    max_hops: int,
    timeout: float,
    resolve_dns: bool,
    debug_mode: bool,
    ip_version: int = None
) -> Generator[Tuple[Dict, float, bool], None, None]:
    """
    Windows tracert command integration with enhanced parsing and error handling.
    
    This implementation fully emulates Windows tracert command behavior and
    supports both IPv4 and IPv6 protocols with robust parsing of various output formats.
    
    Args:
        target_ip: Target IP address
        max_hops: Maximum number of hops to trace
        timeout: Timeout in seconds
        resolve_dns: Whether to resolve DNS hostnames
        debug_mode: Enable debug output
        ip_version: IP version (4 or 6), or None for auto-detection
        
    Yields:
        Tuple of (hop_info, progress, is_destination) where hop_info contains:
            - hop: Hop number
            - ip: IP address of the hop
            - hostname: Hostname if DNS resolution is enabled
            - delay: Average delay in milliseconds
            - ttl: Time-to-live value
            - raw_data: Raw tracert output line
    """
    try:
        # Build tracert command parameters - emulating standard Windows tracert behavior
        cmd = [
            'tracert',
            '-h', str(max_hops),  # -h: Set maximum hops
            '-w', str(int(timeout * 1000)),  # -w: Set timeout in milliseconds
        ]
        
        # Detect IPv6 address and add -6 parameter if needed
        if ip_version == 6 or ':' in target_ip:
            cmd.append('-6')
            if debug_mode:
                print(f"[DEBUG] Detected IPv6 address, adding -6 parameter")
        
        # -d option disables DNS resolution
        if not resolve_dns:
            cmd.append('-d')
        
        cmd.append(target_ip)
        
        if debug_mode:
            print(f"[DEBUG] Executing command: {' '.join(cmd)}")
        
        # Execute command - use Popen to get real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
        
        # Improved regular expressions for parsing tracert output - compatible with
        # both Chinese and English output and both IPv4/IPv6 addresses
        ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\b'
        
        # Parse output
        current_hop = 0
        destination_reached = False
        
        # Track visited IPs to detect routing loops
        visited_ips = set()

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
                
            if debug_mode:
                print(f"[DEBUG] tracert output line: {line}")
            
            # Skip summary and header lines
            if 'Tracing route' in line or 'Trace complete' in line or 'over a maximum of' in line or '通过最多' in line:
                continue
            
            # Initialize variables to avoid undefined errors
            rtt_values = []
            hostname = None
            ip = None
            hop_num = None
            
            # Check if line starts with a digit (possibly with leading spaces)
            parts = line.strip().split()
            if parts and parts[0].isdigit():
                current_hop += 1
                hop_num = parts[0]
                
                # 1. Extract RTT values with improved parsing logic
                for i in range(1, min(4, len(parts))):  # Check positions 1,2,3 for RTT values
                    rtt_str = parts[i]
                    if rtt_str == '*':
                        continue  # Skip timeouts
                    
                    try:
                        # Handle <1ms special case
                        if '<1' in rtt_str:
                            rtt_values.append(0.5)
                            if debug_mode:
                                print(f"[DEBUG] Parsing <1ms: {rtt_str} -> 0.5ms")
                            continue
                        
                        # Extract numeric value
                        num_str = ''.join(c for c in rtt_str if c.isdigit() or c == '.')
                        if num_str:
                            delay_value = float(num_str)
                            rtt_values.append(delay_value)
                            if debug_mode:
                                print(f"[DEBUG] Parsed RTT value: {rtt_str} -> {delay_value}ms")
                    except ValueError as e:
                        if debug_mode:
                            print(f"[DEBUG] Failed to parse RTT value: {rtt_str}, error: {str(e)}")
                        pass  # Skip if parsing fails
                
                # 2. Extract IP address and hostname with improved extraction logic
                # First check if it's a timeout line
                timeout_keywords = ['请求超时', 'timed out', '*']
                if any(keyword in ' '.join(parts) for keyword in timeout_keywords):
                    ip = '*'
                else:
                    # Look from RTT values onward
                    after_rtt_start = 4  # RTT values are usually in positions 1-3
                    found_ip = False
                    
                    # Check [IP] format
                    for i in range(after_rtt_start, len(parts)):
                        part = parts[i]
                        if '[' in part and ']' in part:
                            # Extract IP address
                            ip_candidate = part[part.find('[')+1:part.find(']')]
                            if '.' in ip_candidate or ':' in ip_candidate:
                                ip = ip_candidate
                                # Hostname might be part before [IP]
                                hostname_part = part[:part.find('[')].strip()
                                # Or the previous part
                                if not hostname_part and i > after_rtt_start:
                                    prev_part = parts[i-1]
                                    if not ('ms' in prev_part.lower() or '毫秒' in prev_part or prev_part == '*'):
                                        hostname = prev_part
                                else:
                                    hostname = hostname_part if hostname_part else None
                                found_ip = True
                                break
                    
                    # Check direct IP format with regex validation
                    if not found_ip:
                        for i in range(after_rtt_start, len(parts)):
                            part = parts[i].strip('[](),')
                            # Check IPv4 with regex
                            if '.' in part and re.match(ipv4_pattern, part):
                                ip = part
                                # Try to get hostname (previous non-RTT part)
                                if i > after_rtt_start:
                                    prev_part = parts[i-1]
                                    if not ('ms' in prev_part.lower() or '毫秒' in prev_part or prev_part == '*'):
                                        hostname = prev_part
                                found_ip = True
                                break
                            # Check IPv6 with regex
                            elif ':' in part and part != '*' and re.match(ipv6_pattern, part):
                                ip = part
                                # Try to get hostname
                                if i > after_rtt_start:
                                    prev_part = parts[i-1]
                                    if not ('ms' in prev_part.lower() or '毫秒' in prev_part or prev_part == '*'):
                                        hostname = prev_part
                                found_ip = True
                                break
                    
                    # Check if all RTTs are * (timeout case)
                    if not found_ip and len(parts) > 3:
                        rtt_fields = parts[1:4]
                        if all(field.strip() == '*' for field in rtt_fields):
                            ip = '*'
                    
                    # Final fallback: extract from last part
                    if not found_ip and parts:
                        last_part = parts[-1].strip('[](),')
                        if '.' in last_part and re.match(ipv4_pattern, last_part):
                            ip = last_part
                            # Try to get hostname
                            if len(parts) > 1:
                                second_last = parts[-2].strip()
                                if not ('ms' in second_last.lower() or '毫秒' in second_last or second_last == '*'):
                                    hostname = second_last
                
                # Ensure hop_num is valid
                if hop_num is None:
                    continue
                
                try:
                    hop_num_int = int(hop_num)
                except (ValueError, TypeError):
                    continue
                
                # 3. Calculate average delay
                if debug_mode:
                    print(f"[DEBUG] All RTT values for hop {hop_num}: {rtt_values}")
                
                if ip == '*':
                    avg_rtt = 'Timeout'
                elif rtt_values:
                    # Calculate precise average delay and format output
                    avg_delay = statistics.mean(rtt_values)
                    avg_rtt = f"{avg_delay:.1f} ms"
                    if debug_mode:
                        print(f"[DEBUG] Calculated average delay: {avg_delay:.3f}ms -> {avg_rtt}")
                else:
                    avg_rtt = 'Timeout'
                
                # 4. Build hop information with additional fields
                hop_info = {
                    'hop': hop_num_int,
                    'ip': ip,
                    'hostname': hostname or '',
                    'delay': avg_rtt,
                    'ttl': hop_num_int,
                    'raw_data': line
                }
                
                # Detect routing loops
                if ip != '*' and ip in visited_ips:
                    hop_info['warning'] = 'Routing loop detected'
                    if debug_mode:
                        print(f"[DEBUG] Routing loop detected at hop {hop_num_int}: {ip}")
                elif ip != '*':
                    visited_ips.add(ip)
                
                # Calculate progress
                progress = min(1.0, current_hop / max_hops)
                
                # Check if destination is reached
                is_destination = ip == target_ip
                if is_destination:
                    destination_reached = True
                    progress = 1.0
                
                yield hop_info, progress, is_destination
                
                if destination_reached:
                    break
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Check for error output and return code
        stderr = process.stderr.read()
        if stderr or return_code != 0:
            error_msg = f"Windows tracert error (code {return_code}): {stderr.strip()}"
            if debug_mode:
                print(f"[DEBUG] {error_msg}")
            # Only yield error if we haven't yielded any hops
            if current_hop == 0:
                yield {'error': error_msg}, 0, False
            
    except subprocess.SubprocessError as e:
        error_msg = f"tracert command execution failed: {str(e)}"
        if debug_mode:
            print(f"[DEBUG] {error_msg}")
        yield {'error': error_msg}, 0, False
    except FileNotFoundError:
        error_msg = "tracert command not found, please ensure system path is correct"
        if debug_mode:
            print(f"[DEBUG] {error_msg}")
        yield {'error': error_msg}, 0, False
    except TracerouteError:
        # Propagate TracerouteError exceptions
        raise
    except Exception as e:
        error_msg = f"Unexpected error in Windows tracert: {str(e)}"
        if debug_mode:
            print(f"[DEBUG] {error_msg}")
        yield {'error': error_msg}, 0, False

def send_receive_packet(sock, dest_ip, packet, timeout=3.0, ttl=1, ip_version=4) -> Tuple[Optional[str], Optional[float], Optional[int]]:
    """
    Send packet and receive response with proper error handling and timeout management.
    
    Args:
        sock: Socket object
        dest_ip: Destination IP address
        packet: Packet data to send
        timeout: Timeout in seconds
        ttl: Time-to-live value
        ip_version: IP version (4 or 6)
        
    Returns:
        Tuple of (hop_ip, delay_ms, icmp_type), all None if no response
    """
    # Set hop limit (TTL or Hop Limit) with platform-specific handling
    try:
        if ip_version == 4:
            # IPv4 TTL setting with Windows special case
            if platform.system() == 'Windows':
                # Windows TTL setting
                try:
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
                except (socket.error, AttributeError):
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_TTL, ttl)
                    except Exception:
                        pass
            else:
                # Linux/macOS TTL setting
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        else:  # IPv6
            # IPv6 hop limit setting
            try:
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, ttl)
            except Exception:
                # Windows may have different socket option handling
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_IPV6_UNICAST_HOPS, ttl)
                except Exception:
                    pass
    except Exception:
        pass
    
    # Record send time
    send_time = time.time()
    
    # Send packet
    try:
        # For ICMP, port is usually 0 or arbitrary
        port = 0
        if ip_version == 4:
            sock.sendto(packet, (dest_ip, port))
        else:  # IPv6
            sock.sendto(packet, (dest_ip, port, 0, 0))
    except socket.error as e:
        # Handle permission denied and other socket errors
        if e.errno == 1:  # EPERM - Operation not permitted
            raise TracerouteError(ERROR_PERMISSION_DENIED)
        return None, None, None
    except Exception:
        return None, None, None
    
    # Use select to wait for response
    try:
        ready = select.select([sock], [], [], timeout)
        
        if not ready[0]:
            # Timeout
            return None, None, None
        
        # Receive response
        data, addr = sock.recvfrom(1024)
        receive_time = time.time()
        
        # Calculate delay in milliseconds
        delay = (receive_time - send_time) * 1000  # Convert to milliseconds
        
        # Extract ICMP header (handled differently based on IP version)
        icmp_type = None
        if ip_version == 4:
            # For IPv4: IP header (20 bytes) + ICMP header (8 bytes)
            if len(data) >= 28:
                icmp_type = data[20]
        else:  # IPv6
            # For IPv6: ICMPv6 header starts at data position
            if len(data) >= 8:
                icmp_type = data[0]
        
        return addr[0], delay, icmp_type
    except socket.timeout:
        return None, None, None
    except socket.error as e:
        # Handle socket specific errors
        if e.errno == 1:  # EPERM - Operation not permitted
            raise TracerouteError(ERROR_PERMISSION_DENIED)
        return None, None, None
    except Exception:
        return None, None, None

def _icmp_traceroute(target_ip, max_hops, timeout, packet_size, resolve_dns, port, max_retries, debug_mode):
    """
    ICMP协议的路由跟踪实现
    """
    try:
        # 创建ICMP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.settimeout(timeout)
        
        # 生成随机ID
        packet_id = random.randint(0, 65535)
        
        # 已访问的IP集合，用于检测循环路由
        visited_ips = set()
        
        # 主追踪循环
        for ttl in range(1, max_hops + 1):
            # 初始化当前跳数的最佳结果
            best_response = None
            best_delay = float('inf')
            
            # 重试逻辑
            for attempt in range(max_retries):
                current_timeout = timeout + (attempt * 0.5)
                
                # 创建ICMP数据包
                packet = create_icmp_packet(packet_id, ttl, packet_size)
                
                # 发送数据包并接收响应
                addr, delay, icmp_type = send_receive_packet(sock, target_ip, packet, current_timeout, ttl)
                
                # 检查是否收到响应
                if addr:
                    best_response = addr
                    best_delay = delay
                    break
            
            # 获取响应的IP地址
            if best_response:
                hop_ip = best_response
                hop_info = {
                    'hop': ttl,
                    'ip': hop_ip,
                    'hostname': hop_ip,
                    'delay': f'{best_delay:.2f}ms'
                }
                
                # 解析主机名（如果需要）
                if resolve_dns:
                    try:
                        hop_info['hostname'] = socket.gethostbyaddr(hop_ip)[0]
                    except Exception:
                        hop_info['hostname'] = hop_ip
                
                # 检测循环路由
                if hop_ip in visited_ips:
                    hop_info['warning'] = '检测到循环路由'
                    yield hop_info, int((ttl / max_hops) * 100), False
                    break
                
                # 添加到已见IP集合
                visited_ips.add(hop_ip)
                
                # 检查是否到达目标
                is_destination = hop_ip == target_ip
                
                # 计算进度
                progress = min(1.0, ttl / max_hops)
                if is_destination:
                    progress = 1.0
                
                yield hop_info, progress, is_destination
                
                # 如果到达目标，结束追踪
                if is_destination:
                    break
            else:
                # 没有收到响应
                hop_info = {
                    'hop': ttl,
                    'ip': '*',
                    'hostname': '',
                    'delay': '超时'
                }
                
                # 计算进度
                progress = min(1.0, ttl / max_hops)
                
                yield hop_info, progress, False
        
        # 关闭套接字
        sock.close()
        
    except Exception as e:
        yield {'error': f'ICMP追踪失败: {str(e)}'}, 0, False

def _icmpv6_traceroute(target_ip, max_hops, timeout, packet_size, resolve_dns, port, max_retries, debug_mode):
    """
    ICMPv6协议的路由跟踪实现
    """
    try:
        # 创建ICMPv6套接字
        sock = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
        sock.settimeout(timeout)
        
        # 生成随机ID
        packet_id = random.randint(0, 65535)
        
        # 已访问的IP集合，用于检测循环路由
        visited_ips = set()
        
        # 主追踪循环
        for ttl in range(1, max_hops + 1):
            # 初始化当前跳数的最佳结果
            best_response = None
            best_delay = float('inf')
            
            # 设置IPv6跳数限制
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, ttl)
            
            # 重试逻辑
            for attempt in range(max_retries):
                current_timeout = timeout + (attempt * 0.5)
                
                # 创建ICMPv6数据包
                packet = create_icmpv6_packet(packet_id, ttl, packet_size)
                
                # 发送数据包并接收响应
                addr, delay, icmp_type = send_receive_packet(sock, target_ip, packet, current_timeout, ttl)
                
                # 检查是否收到响应
                if addr:
                    best_response = addr
                    best_delay = delay
                    break
            
            # 获取响应的IP地址
            if best_response:
                hop_ip = best_response
                hop_info = {
                    'hop': ttl,
                    'ip': hop_ip,
                    'hostname': hop_ip,
                    'delay': f'{best_delay:.2f}ms'
                }
                
                # 解析主机名（如果需要）
                if resolve_dns:
                    try:
                        hop_info['hostname'] = socket.getnameinfo((hop_ip, 0), 0)[0]
                    except Exception:
                        hop_info['hostname'] = hop_ip
                
                # 检测循环路由
                if hop_ip in visited_ips:
                    hop_info['warning'] = '检测到循环路由'
                    yield hop_info, int((ttl / max_hops) * 100), False
                    break
                
                # 添加到已见IP集合
                visited_ips.add(hop_ip)
                
                # 检查是否到达目标
                is_destination = hop_ip == target_ip
                
                # 计算进度
                progress = min(1.0, ttl / max_hops)
                if is_destination:
                    progress = 1.0
                
                yield hop_info, progress, is_destination
                
                # 如果到达目标，结束追踪
                if is_destination:
                    break
            else:
                # 没有收到响应
                hop_info = {
                    'hop': ttl,
                    'ip': '*',
                    'hostname': '',
                    'delay': '超时'
                }
                
                # 计算进度
                progress = min(1.0, ttl / max_hops)
                
                yield hop_info, progress, False
        
        # 关闭套接字
        sock.close()
        
    except Exception as e:
        yield {'error': f'ICMPv6追踪失败: {str(e)}'}, 0, False

def _udp_traceroute(target_ip, max_hops, timeout, packet_size, resolve_dns, port, max_retries, debug_mode):
    """
    UDP协议的路由跟踪实现
    """
    try:
        # 创建UDP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(timeout)
        
        # 生成随机ID
        packet_id = random.randint(0, 65535)
        
        # 已访问的IP集合，用于检测循环路由
        visited_ips = set()
        
        # 主追踪循环
        for ttl in range(1, max_hops + 1):
            # 初始化当前跳数的最佳结果
            best_response = None
            best_delay = float('inf')
            
            # 重试逻辑
            for attempt in range(max_retries):
                current_timeout = timeout + (attempt * 0.5)
                
                # 使用随机高端口
                target_port = port + ttl
                
                # 创建UDP数据包
                packet = create_udp_packet(packet_id, target_port, packet_size)
                
                # 发送数据包并接收响应
                addr, delay, icmp_type = send_receive_packet(sock, target_ip, packet, current_timeout, ttl)
                
                # 检查是否收到响应
                if addr:
                    best_response = addr
                    best_delay = delay
                    break
            
            # 获取响应的IP地址
            if best_response:
                hop_ip = best_response
                hop_info = {
                    'hop': ttl,
                    'ip': hop_ip,
                    'hostname': hop_ip,
                    'delay': f'{best_delay:.2f}ms'
                }
                
                # 解析主机名（如果需要）
                if resolve_dns:
                    try:
                        hop_info['hostname'] = socket.gethostbyaddr(hop_ip)[0]
                    except Exception:
                        hop_info['hostname'] = hop_ip
                
                # 检测循环路由
                if hop_ip in visited_ips:
                    hop_info['warning'] = '检测到循环路由'
                    yield hop_info, int((ttl / max_hops) * 100), False
                    break
                
                # 添加到已见IP集合
                visited_ips.add(hop_ip)
                
                # 检查是否到达目标
                is_destination = hop_ip == target_ip
                
                # 计算进度
                progress = min(1.0, ttl / max_hops)
                if is_destination:
                    progress = 1.0
                
                yield hop_info, progress, is_destination
                
                # 如果到达目标，结束追踪
                if is_destination:
                    break
            else:
                # 没有收到响应
                hop_info = {
                    'hop': ttl,
                    'ip': '*',
                    'hostname': '',
                    'delay': '超时'
                }
                
                # 计算进度
                progress = min(1.0, ttl / max_hops)
                
                yield hop_info, progress, False
        
        # 关闭套接字
        sock.close()
        
    except Exception as e:
        yield {'error': f'UDP追踪失败: {str(e)}'}, 0, False

def traceroute(
    target: str,
    max_hops: int = DEFAULT_MAX_HOPS,
    timeout: float = DEFAULT_TIMEOUT,
    packet_size: int = DEFAULT_PACKET_SIZE,
    resolve_dns: bool = True,
    protocol: str = 'icmp',  # 默认使用ICMP协议
    port: int = DEFAULT_PORT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    debug_mode: bool = False,
    ipv6: bool = False  # 是否优先使用IPv6
) -> Generator[Tuple[Dict, float, bool], None, None]:
    """
    Main traceroute function that works across platforms with support for both IPv4 and IPv6.
    
    This implementation automatically selects the appropriate underlying method based on the
    operating system and protocol requirements, providing consistent results across different
    environments.
    
    Args:
        target: Target hostname or IP address
        max_hops: Maximum number of hops (1-255, default: 30)
        timeout: Timeout in seconds per probe (default: 3.0)
        packet_size: Packet size in bytes (default: 64)
        resolve_dns: Whether to resolve hostnames (default: True)
        protocol: Protocol to use ('udp', 'icmp', or 'tcp', default: 'icmp')
        port: Destination port for UDP probes (default: 33434)
        max_retries: Maximum number of retries per hop (default: 3)
        debug_mode: Enable debug output (default: False)
        ipv6: Whether to prefer IPv6 over IPv4 (default: False)
        
    Yields:
        Tuple of (hop_info, progress, is_destination) for each hop
        hop_info contains details about the intermediate router
        progress is a float between 0 and 1
        is_destination is True when the target is reached
    
    Raises:
        TracerouteError: For traceroute-specific errors
        ValueError: For invalid parameter values
    """
    
    # Validate parameters
    if protocol not in ['udp', 'icmp', 'tcp']:
        raise ValueError(ERROR_UNSUPPORTED_PROTOCOL.format(protocol))
    
    if max_hops < 1 or max_hops > 255:
        raise ValueError(ERROR_INVALID_HOPS.format(max_hops))
    
    if timeout <= 0:
        raise ValueError(ERROR_INVALID_TIMEOUT.format(timeout))
    
    # Resolve target address with IP version selection
    try:
        # Configure socket family based on ipv6 preference
        family = socket.AF_UNSPEC  # Default: try both IPv4 and IPv6
        target_ip = None
        ip_version = None
        
        # Try to resolve address
        for res in socket.getaddrinfo(target, None, family, socket.SOCK_RAW):
            af, socktype, proto, canonname, sa = res
            # Select IP version based on preference
            if ipv6:
                # Prefer IPv6
                if af == socket.AF_INET6:
                    target_ip = sa[0]
                    ip_version = 6
                    break
                elif af == socket.AF_INET and ip_version is None:
                    target_ip = sa[0]
                    ip_version = 4
            else:
                # Prefer IPv4
                if af == socket.AF_INET:
                    target_ip = sa[0]
                    ip_version = 4
                    break
                elif af == socket.AF_INET6 and ip_version is None:
                    target_ip = sa[0]
                    ip_version = 6
                
        # If no IP address found, raise exception
        if target_ip is None:
            raise socket.gaierror("无法解析目标地址")
            
        if debug_mode:
            print(f"[DEBUG] Target resolved to: {target_ip} (IPv{ip_version})")
            
    except socket.gaierror as e:
        yield {'error': ERROR_ADDRESS_RESOLUTION.format(e)}, 0, False
        return
    except Exception as e:
        yield {'error': str(e)}, 0, False
        return
    
    # Windows implementation using tracert command - ensure we always use this on Windows
    if platform.system() == 'Windows':
        if debug_mode:
            print(f"[DEBUG] Using Windows tracert command implementation to avoid raw socket permission issues")
        
        # On Windows, disable DNS resolution by default to speed up tracert with -d parameter
        windows_resolve_dns = False
        if debug_mode:
            print(f"[DEBUG] Windows platform: Using -d parameter to disable DNS resolution for faster traceroute")
        
        yield from _windows_tracert(
            target_ip, max_hops, timeout, windows_resolve_dns, debug_mode, ip_version
        )
    else:
        # Unified implementation using Python's socket library for non-Windows platforms
        if debug_mode:
            print(f"[DEBUG] Using Python socket implementation for traceroute")
        
        # Select appropriate traceroute implementation based on IP version
        try:
            if protocol == 'icmp':
                if ip_version == 6:
                    if debug_mode:
                        print(f"[DEBUG] Using ICMPv6 protocol for traceroute")
                    for hop_info, progress, is_destination in _icmpv6_traceroute(
                        target_ip,
                        max_hops,
                        timeout,
                        packet_size,
                        resolve_dns,
                        port,
                        max_retries,
                        debug_mode
                    ):
                        # Handle potential error responses
                        if isinstance(hop_info, dict) and 'error' in hop_info:
                            raise TracerouteError(hop_info['error'])
                            
                        yield hop_info, progress, is_destination
                        if is_destination:
                            break
                else:
                    if debug_mode:
                        print(f"[DEBUG] Using ICMPv4 protocol for traceroute")
                    for hop_info, progress, is_destination in _icmp_traceroute(
                        target_ip,
                        max_hops,
                        timeout,
                        packet_size,
                        resolve_dns,
                        port,
                        max_retries,
                        debug_mode
                    ):
                        # Handle potential error responses
                        if isinstance(hop_info, dict) and 'error' in hop_info:
                            raise TracerouteError(hop_info['error'])
                            
                        yield hop_info, progress, is_destination
                        if is_destination:
                            break
            elif protocol == 'udp':
                if ip_version == 6:
                    # For IPv6, UDP traceroute is similar to ICMPv6
                    # Temporarily reuse ICMPv6 implementation
                    if debug_mode:
                        print(f"[DEBUG] Using UDP protocol for IPv6 traceroute")
                    for hop_info, progress, is_destination in _icmpv6_traceroute(
                        target_ip,
                        max_hops,
                        timeout,
                        packet_size,
                        resolve_dns,
                        port,
                        max_retries,
                        debug_mode
                    ):
                        # Handle potential error responses
                        if isinstance(hop_info, dict) and 'error' in hop_info:
                            raise TracerouteError(hop_info['error'])
                            
                        yield hop_info, progress, is_destination
                        if is_destination:
                            break
                else:
                    if debug_mode:
                        print(f"[DEBUG] Using UDP protocol for traceroute")
                    for hop_info, progress, is_destination in _udp_traceroute(
                        target_ip,
                        max_hops,
                        timeout,
                        packet_size,
                        resolve_dns,
                        port,
                        max_retries,
                        debug_mode
                    ):
                        # Handle potential error responses
                        if isinstance(hop_info, dict) and 'error' in hop_info:
                            raise TracerouteError(hop_info['error'])
                            
                        yield hop_info, progress, is_destination
                        if is_destination:
                            break
            else:  # tcp (not implemented)
                yield {'error': ERROR_UNSUPPORTED_PROTOCOL.format(protocol)}, 0, False
        except socket.error as e:
            # Handle socket-specific errors
            if e.errno == 1:  # EPERM - Operation not permitted
                raise TracerouteError(ERROR_PERMISSION_DENIED)
            else:
                raise TracerouteError(ERROR_TRACEROUTE_FAILED.format(str(e)))
        except PermissionError:
            raise TracerouteError(ERROR_PERMISSION_DENIED)

def mtr(
    target: str,
    count: int = 10,
    max_hops: int = DEFAULT_MAX_HOPS,
    timeout: float = DEFAULT_TIMEOUT,
    packet_size: int = DEFAULT_PACKET_SIZE,
    resolve_dns: bool = True,
    protocol: str = 'icmp',
    port: int = DEFAULT_PORT,
    debug_mode: bool = False,
    ipv6: bool = False
) -> Generator[Tuple[Dict, float, List[Dict]], None, None]:
    """
    MTR (My Traceroute) implementation that combines traceroute and ping functionality.
    
    Args:
        target: Target hostname or IP address
        count: Number of traceroute cycles to perform
        max_hops: Maximum number of hops to trace
        timeout: Timeout in seconds
        packet_size: Size of the packet in bytes
        resolve_dns: Whether to resolve DNS hostnames
        protocol: Protocol to use ('icmp', 'tcp', 'udp')
        port: Port number to use for TCP/UDP
        debug_mode: Enable debug output
        ipv6: Force IPv6 mode
        
    Yields:
        Tuple of (summary, progress, all_hops_data) where:
            - summary: Summary of MTR results
            - progress: Current progress (0.0-1.0)
            - all_hops_data: List of detailed hop information
    """
    # Validate protocol
    protocol = protocol.lower()
    if protocol not in ['icmp', 'tcp', 'udp']:
        raise TracerouteError(f"Unsupported protocol: {protocol}")
    
    # Resolve target to IP address for consistency
    try:
        if ipv6:
            # Force IPv6 resolution
            ip_version = 6
            target_info = socket.getaddrinfo(target, None, socket.AF_INET6)[0]
            dest_ip = target_info[4][0]
        else:
            # Auto-detect IP version
            try:
                # Try IPv4 first
                target_info = socket.getaddrinfo(target, None, socket.AF_INET)[0]
                ip_version = 4
            except socket.gaierror:
                # Try IPv6 if IPv4 fails
                try:
                    target_info = socket.getaddrinfo(target, None, socket.AF_INET6)[0]
                    ip_version = 6
                except socket.gaierror as e:
                    raise TracerouteError(f"Failed to resolve target '{target}': {str(e)}")
            dest_ip = target_info[4][0]
    except Exception as e:
        raise TracerouteError(f"Failed to resolve target '{target}': {str(e)}")
    
    if debug_mode:
        print(f"[DEBUG] MTR target resolved to {dest_ip} (IPv{ip_version})")
    
    # Initialize dictionaries to store hop data
    hop_data = {}
    all_hops_data = []
    
    # Run multiple traceroute cycles
    for cycle in range(count):
        cycle_progress = (cycle + 1) / count
        
        if debug_mode:
            print(f"[DEBUG] MTR cycle {cycle + 1}/{count}")
        
        # Run traceroute for this cycle
        try:
            # Call the unified traceroute function that handles platform differences
            # For Windows, this will automatically use tracert command to avoid raw socket permission issues
            for hop_info, _, is_destination in traceroute(
                target=dest_ip,
                max_hops=max_hops,
                timeout=timeout,
                packet_size=packet_size,
                resolve_dns=resolve_dns,
                protocol=protocol,
                port=port,
                debug_mode=debug_mode,
                ipv6=(ip_version == 6)
            ):
                # Process hop data
                hop_num = hop_info.get('hop', -1)
                hop_ip = hop_info.get('ip', '*')
                
                # Initialize hop data structure if not exists
                if hop_num not in hop_data:
                    hop_data[hop_num] = {
                        'hop': hop_num,
                        'ip': hop_ip,
                        'hostname': hop_info.get('hostname', ''),
                        'delays': [],
                        'loss_percent': 0,
                        'min_delay': float('inf'),
                        'max_delay': 0,
                        'avg_delay': 0,
                        'std_dev': 0
                    }
                
                # Update hostname if available
                if hop_info.get('hostname', '') and not hop_data[hop_num]['hostname']:
                    hop_data[hop_num]['hostname'] = hop_info.get('hostname', '')
                
                # Process delay - handle both string (from Windows) and numeric formats
                delay = hop_info.get('delay', 'Timeout')
                if delay != 'Timeout':
                    if isinstance(delay, str) and 'ms' in delay:
                        try:
                            delay_value = float(delay.split('ms')[0].strip())
                            hop_data[hop_num]['delays'].append(delay_value)
                            
                            # Update statistics
                            hop_data[hop_num]['min_delay'] = min(hop_data[hop_num]['min_delay'], delay_value)
                            hop_data[hop_num]['max_delay'] = max(hop_data[hop_num]['max_delay'], delay_value)
                        except (ValueError, IndexError):
                            # If parsing fails, count as lost packet
                            pass
                    elif isinstance(delay, (int, float)):
                        # Handle numeric delay values from non-Windows platforms
                        hop_data[hop_num]['delays'].append(float(delay))
                        
                        # Update statistics
                        hop_data[hop_num]['min_delay'] = min(hop_data[hop_num]['min_delay'], float(delay))
                        hop_data[hop_num]['max_delay'] = max(hop_data[hop_num]['max_delay'], float(delay))
                
                # If we've reached the destination, we can break early
                if is_destination:
                    break
        except TracerouteError as e:
            if debug_mode:
                print(f"[DEBUG] MTR cycle {cycle + 1} failed: {str(e)}")
            # Continue to next cycle
            continue
        
        # Calculate progress
        overall_progress = cycle_progress
        
        # After each cycle, update statistics
        all_hops_data = []
        for hop_num in sorted(hop_data.keys()):
            hop = hop_data[hop_num]
            
            # Calculate packet loss
            if cycle >= 0:
                total_packets = cycle + 1
                received_packets = len(hop['delays'])
                hop['loss_percent'] = ((total_packets - received_packets) / total_packets) * 100
            
            # Calculate average delay and standard deviation
            if hop['delays']:
                hop['avg_delay'] = statistics.mean(hop['delays'])
                if len(hop['delays']) > 1:
                    hop['std_dev'] = statistics.stdev(hop['delays'])
                else:
                    hop['std_dev'] = 0
            else:
                hop['avg_delay'] = 0
                hop['std_dev'] = 0
            
            # Handle infinity values
            if hop['min_delay'] == float('inf'):
                hop['min_delay'] = 0
            
            all_hops_data.append(hop.copy())
        
        # Create summary
        summary = {
            'target': target,
            'target_ip': dest_ip,
            'ip_version': ip_version,
            'protocol': protocol,
            'cycles_complete': cycle + 1,
            'total_cycles': count,
            'total_hops': len(all_hops_data),
            'summary_text': f"MTR to {target} ({dest_ip}), {cycle + 1}/{count} cycles complete"
        }
        
        yield summary, overall_progress, all_hops_data
    
    # Final calculation for all statistics
    for hop_num in sorted(hop_data.keys()):
        hop = hop_data[hop_num]
        
        # Calculate final packet loss
        total_packets = count
        received_packets = len(hop['delays'])
        hop['loss_percent'] = ((total_packets - received_packets) / total_packets) * 100
        
        # Calculate final average delay and standard deviation
        if hop['delays']:
            hop['avg_delay'] = statistics.mean(hop['delays'])
            if len(hop['delays']) > 1:
                hop['std_dev'] = statistics.stdev(hop['delays'])
            else:
                hop['std_dev'] = 0
        else:
            hop['avg_delay'] = 0
            hop['std_dev'] = 0
        
        # Handle infinity values
        if hop['min_delay'] == float('inf'):
            hop['min_delay'] = 0
    
    # Create final summary
    final_summary = {
        'target': target,
        'target_ip': dest_ip,
        'ip_version': ip_version,
        'protocol': protocol,
        'cycles_complete': count,
        'total_cycles': count,
        'total_hops': len(hop_data),
        'summary_text': f"MTR to {target} ({dest_ip}) complete, {count} cycles performed"
    }
    
    # Final yield with all data
    final_all_hops = [hop_data[hop_num].copy() for hop_num in sorted(hop_data.keys())]
    yield final_summary, 1.0, final_all_hops

if __name__ == "__main__":
    # 示例用法
    print("执行Traceroute到 8.8.8.8")
    for hop_info, progress, is_destination in traceroute("8.8.8.8", max_hops=20, timeout=1.0, debug_mode=True):
        if "error" in hop_info:
            print(hop_info["error"])
            break
        
        print(f"{hop_info['hop']}. {hop_info['ip']} {hop_info.get('hostname', '')} {hop_info['delay']}")
        
        if is_destination:
            print("已达到目标")
            break
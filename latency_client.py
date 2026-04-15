#!/usr/bin/env python3
"""
网络延迟测试客户端 - 统一版本
测试顺序: ICMP → UDP → TCP (支持 IPv4/IPv6)
"""

import socket
import time
import sys
import statistics
import argparse
import subprocess
import platform
import os

def detect_ip_version(ip_address):
    """自动检测 IP 地址版本"""
    try:
        socket.inet_pton(socket.AF_INET6, ip_address)
        return 6
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET, ip_address)
            return 4
        except socket.error:
            return None

def icmp_ping_test(server_ip, count=10):
    """
    ICMP Ping 测试
    """
    print("\n" + "=" * 60)
    print("第 1 步: ICMP Ping 测试")
    print("=" * 60)
    
    # 检测操作系统
    is_windows = platform.system().lower() == 'windows'
    
    # 构建 ping 命令
    if is_windows:
        # Windows: ping -n count ip
        ping_cmd = ['ping', '-n', str(count), server_ip]
    else:
        # Linux/Mac: ping -c count ip (IPv4) 或 ping6 -c count ip (IPv6)
        ip_version = detect_ip_version(server_ip)
        if ip_version == 6:
            # 尝试使用 ping6 或 ping -6
            if os.system('which ping6 > /dev/null 2>&1') == 0:
                ping_cmd = ['ping6', '-c', str(count), server_ip]
            else:
                ping_cmd = ['ping', '-6', '-c', str(count), server_ip]
        else:
            ping_cmd = ['ping', '-c', str(count), server_ip]
    
    try:
        print(f"执行命令: {' '.join(ping_cmd)}")
        print("-" * 60)
        
        # 执行 ping 命令
        result = subprocess.run(
            ping_cmd,
            capture_output=True,
            text=True,
            timeout=count * 2 + 5
        )
        
        # 显示输出
        output = result.stdout
        print(output)
        
        # 解析结果
        latencies = []
        lines = output.split('\n')
        
        for line in lines:
            # Windows: 时间=XXms 或 time=XXms
            # Linux: time=XX.X ms
            if 'time=' in line.lower() or '时间=' in line:
                try:
                    if is_windows:
                        if '时间=' in line:
                            time_str = line.split('时间=')[1].split('ms')[0].strip()
                        else:
                            time_str = line.split('time=')[1].split('ms')[0].strip()
                    else:
                        time_str = line.split('time=')[1].split('ms')[0].strip()
                    
                    latency = float(time_str)
                    latencies.append(latency)
                except:
                    continue
        
        # 统计结果
        if latencies:
            print("\n" + "-" * 60)
            print("ICMP 测试统计:")
            print("-" * 60)
            print(f"发送数据包: {count}")
            print(f"接收数据包: {len(latencies)}")
            print(f"丢包数: {count - len(latencies)}")
            print(f"丢包率: {((count - len(latencies))/count)*100:.2f}%")
            print(f"\n延迟统计:")
            print(f"  最小延迟: {min(latencies):.2f} ms")
            print(f"  最大延迟: {max(latencies):.2f} ms")
            print(f"  平均延迟: {statistics.mean(latencies):.2f} ms")
            if len(latencies) > 1:
                print(f"  标准差: {statistics.stdev(latencies):.2f} ms")
            return True, latencies
        else:
            print("\n✗ ICMP Ping 失败或无响应")
            return False, []
            
    except subprocess.TimeoutExpired:
        print("\n✗ ICMP Ping 超时")
        return False, []
    except FileNotFoundError:
        print("\n✗ 找不到 ping 命令")
        return False, []
    except Exception as e:
        print(f"\n✗ ICMP Ping 错误: {e}")
        return False, []

def udp_latency_test(server_ip, server_port, count, packet_size, ip_version):
    """UDP 延迟测试"""
    print("\n" + "=" * 60)
    print("第 2 步: UDP 延迟测试")
    print("=" * 60)
    
    # 创建 UDP socket
    if ip_version == 6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        protocol = "IPv6"
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        protocol = "IPv4"
    
    sock.settimeout(2.0)
    message = b'A' * packet_size
    
    addr_display = f"[{server_ip}]:{server_port}" if ip_version == 6 else f"{server_ip}:{server_port}"
    print(f"目标服务器: {addr_display}")
    print(f"协议: UDP/{protocol}")
    print(f"数据包大小: {packet_size} 字节")
    print(f"测试次数: {count}")
    print("-" * 60)
    
    latencies = []
    lost_packets = 0
    
    for i in range(count):
        try:
            start_time = time.time()
            sock.sendto(message, (server_ip, server_port))
            data, addr = sock.recvfrom(1024)
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            latencies.append(latency)
            print(f"#{i+1}: 延迟 {latency:.2f} ms")
            time.sleep(0.01)
        except socket.timeout:
            print(f"#{i+1}: 超时")
            lost_packets += 1
        except Exception as e:
            print(f"#{i+1}: 错误 - {e}")
            lost_packets += 1
    
    sock.close()
    
    # 统计结果
    print("\n" + "-" * 60)
    print("UDP 测试统计:")
    print("-" * 60)
    
    if latencies:
        print(f"发送数据包: {count}")
        print(f"接收数据包: {len(latencies)}")
        print(f"丢包数: {lost_packets}")
        print(f"丢包率: {(lost_packets/count)*100:.2f}%")
        print(f"\n延迟统计:")
        print(f"  最小延迟: {min(latencies):.2f} ms")
        print(f"  最大延迟: {max(latencies):.2f} ms")
        print(f"  平均延迟: {statistics.mean(latencies):.2f} ms")
        print(f"  中位数: {statistics.median(latencies):.2f} ms")
        if len(latencies) > 1:
            print(f"  标准差: {statistics.stdev(latencies):.2f} ms")
        return True, latencies
    else:
        print("✗ 所有 UDP 测试都失败了!")
        return False, []

def tcp_latency_test(server_ip, server_port, count, packet_size, ip_version):
    """TCP 延迟测试"""
    print("\n" + "=" * 60)
    print("第 3 步: TCP 延迟测试")
    print("=" * 60)
    
    # 创建 TCP socket
    if ip_version == 6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        protocol = "IPv6"
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        protocol = "IPv4"
    
    sock.settimeout(5.0)
    
    addr_display = f"[{server_ip}]:{server_port}" if ip_version == 6 else f"{server_ip}:{server_port}"
    print(f"目标服务器: {addr_display}")
    print(f"协议: TCP/{protocol}")
    print(f"数据包大小: {packet_size} 字节")
    print(f"测试次数: {count}")
    print("-" * 60)
    
    # 连接服务器
    try:
        print("正在建立 TCP 连接...")
        connect_start = time.time()
        sock.connect((server_ip, server_port))
        connect_time = (time.time() - connect_start) * 1000
        print(f"✓ TCP 连接成功! 耗时: {connect_time:.2f} ms\n")
    except Exception as e:
        print(f"✗ TCP 连接失败: {e}")
        sock.close()
        return False, []
    
    message = b'A' * packet_size
    latencies = []
    failed_count = 0
    
    for i in range(count):
        try:
            start_time = time.time()
            sock.sendall(message)
            
            received = 0
            while received < packet_size:
                data = sock.recv(packet_size - received)
                if not data:
                    raise Exception("连接已关闭")
                received += len(data)
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            latencies.append(latency)
            print(f"#{i+1}: 延迟 {latency:.2f} ms")
            time.sleep(0.01)
        except Exception as e:
            print(f"#{i+1}: 错误 - {e}")
            failed_count += 1
            break
    
    sock.close()
    
    # 统计结果
    print("\n" + "-" * 60)
    print("TCP 测试统计:")
    print("-" * 60)
    print(f"连接建立时间: {connect_time:.2f} ms")
    
    if latencies:
        print(f"发送数据包: {count}")
        print(f"成功接收: {len(latencies)}")
        print(f"失败次数: {failed_count}")
        print(f"成功率: {(len(latencies)/count)*100:.2f}%")
        print(f"\n延迟统计:")
        print(f"  最小延迟: {min(latencies):.2f} ms")
        print(f"  最大延迟: {max(latencies):.2f} ms")
        print(f"  平均延迟: {statistics.mean(latencies):.2f} ms")
        print(f"  中位数: {statistics.median(latencies):.2f} ms")
        if len(latencies) > 1:
            print(f"  标准差: {statistics.stdev(latencies):.2f} ms")
        return True, latencies
    else:
        print("✗ 所有 TCP 测试都失败了!")
        return False, []

def print_summary(icmp_result, udp_result, tcp_result):
    """打印总结报告"""
    print("\n" + "=" * 60)
    print("测试总结报告")
    print("=" * 60)
    
    icmp_success, icmp_latencies = icmp_result
    udp_success, udp_latencies = udp_result
    tcp_success, tcp_latencies = tcp_result
    
    # 对比表格
    print(f"\n{'协议':<10} {'状态':<10} {'平均延迟':<15} {'最小延迟':<15} {'最大延迟':<15}")
    print("-" * 60)
    
    if icmp_success and icmp_latencies:
        print(f"{'ICMP':<10} {'✓ 成功':<10} {statistics.mean(icmp_latencies):>10.2f} ms   "
              f"{min(icmp_latencies):>10.2f} ms   {max(icmp_latencies):>10.2f} ms")
    else:
        print(f"{'ICMP':<10} {'✗ 失败':<10} {'N/A':<15} {'N/A':<15} {'N/A':<15}")
    
    if udp_success and udp_latencies:
        print(f"{'UDP':<10} {'✓ 成功':<10} {statistics.mean(udp_latencies):>10.2f} ms   "
              f"{min(udp_latencies):>10.2f} ms   {max(udp_latencies):>10.2f} ms")
    else:
        print(f"{'UDP':<10} {'✗ 失败':<10} {'N/A':<15} {'N/A':<15} {'N/A':<15}")
    
    if tcp_success and tcp_latencies:
        print(f"{'TCP':<10} {'✓ 成功':<10} {statistics.mean(tcp_latencies):>10.2f} ms   "
              f"{min(tcp_latencies):>10.2f} ms   {max(tcp_latencies):>10.2f} ms")
    else:
        print(f"{'TCP':<10} {'✗ 失败':<10} {'N/A':<15} {'N/A':<15} {'N/A':<15}")
    
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(
        description='网络延迟测试客户端 (ICMP + UDP + TCP)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
测试顺序:
  1. ICMP Ping 测试 (基础网络连通性)
  2. UDP 延迟测试 (无连接协议)
  3. TCP 延迟测试 (面向连接协议)

示例:
  IPv4 测试: python3 %(prog)s 192.168.1.100
  IPv6 测试: python3 %(prog)s 2001:db8::1
  自定义参数: python3 %(prog)s 192.168.1.100 -p 8888 -c 50 -s 128
  跳过 ICMP: python3 %(prog)s 192.168.1.100 --skip-icmp
        """
    )
    
    parser.add_argument('server_ip', help='服务器 IP 地址 (IPv4 或 IPv6)')
    parser.add_argument('-p', '--port', type=int, default=9999, 
                       help='服务器端口 (默认: 9999, 用于 UDP/TCP)')
    parser.add_argument('-c', '--count', type=int, default=100, 
                       help='UDP/TCP 测试次数 (默认: 100)')
    parser.add_argument('--icmp-count', type=int, default=10, 
                       help='ICMP 测试次数 (默认: 10)')
    parser.add_argument('-s', '--size', type=int, default=64, 
                       help='数据包大小/字节 (默认: 64, 用于 UDP/TCP)')
    parser.add_argument('-6', '--ipv6', action='store_true', 
                       help='强制使用 IPv6')
    parser.add_argument('--skip-icmp', action='store_true', 
                       help='跳过 ICMP 测试')
    parser.add_argument('--skip-udp', action='store_true', 
                       help='跳过 UDP 测试')
    parser.add_argument('--skip-tcp', action='store_true', 
                       help='跳过 TCP 测试')
    
    args = parser.parse_args()
    
    # 检测 IP 版本
    ip_version = detect_ip_version(args.server_ip)
    if ip_version is None:
        print(f"错误: 无效的 IP 地址 '{args.server_ip}'")
        sys.exit(1)
    
    if args.ipv6:
        ip_version = 6
    
    protocol_name = "IPv6" if ip_version == 6 else "IPv4"
    
    print("=" * 60)
    print(f"网络延迟综合测试 ({protocol_name})")
    print("=" * 60)
    print(f"目标服务器: {args.server_ip}")
    print(f"UDP/TCP 端口: {args.port}")
    print(f"测试顺序: ", end="")
    
    tests = []
    if not args.skip_icmp:
        tests.append("ICMP")
    if not args.skip_udp:
        tests.append("UDP")
    if not args.skip_tcp:
        tests.append("TCP")
    
    print(" → ".join(tests))
    print("=" * 60)
    
    # 执行测试
    icmp_result = (False, [])
    udp_result = (False, [])
    tcp_result = (False, [])
    
    # 1. ICMP 测试
    if not args.skip_icmp:
        icmp_result = icmp_ping_test(args.server_ip, args.icmp_count)
        time.sleep(1)
    
    # 2. UDP 测试
    if not args.skip_udp:
        udp_result = udp_latency_test(
            args.server_ip, args.port, args.count, args.size, ip_version
        )
        time.sleep(1)
    
    # 3. TCP 测试
    if not args.skip_tcp:
        tcp_result = tcp_latency_test(
            args.server_ip, args.port, args.count, args.size, ip_version
        )
    
    # 打印总结
    if not args.skip_icmp or not args.skip_udp or not args.skip_tcp:
        print_summary(icmp_result, udp_result, tcp_result)

if __name__ == '__main__':
    main()
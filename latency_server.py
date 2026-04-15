#!/usr/bin/env python3
"""
网络延迟测试服务端 - 统一版本
同时启动 TCP 和 UDP 服务 (支持 IPv4/IPv6)
"""

import socket
import threading
import sys
import argparse

class LatencyServer:
    def __init__(self, host='0.0.0.0', port=9999, ipv6=False):
        self.host = host
        self.port = port
        self.ipv6 = ipv6
        self.protocol = "IPv6" if ipv6 else "IPv4"
        self.running = True
        
    def udp_server(self):
        """UDP 服务"""
        try:
            # 创建 UDP socket
            if self.ipv6:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                try:
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                except:
                    pass
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            
            print(f"✓ UDP 服务已启动 ({self.protocol}) - 端口 {self.port}")
            
            while self.running:
                try:
                    sock.settimeout(1.0)
                    data, addr = sock.recvfrom(1024)
                    sock.sendto(data, addr)
                    
                    if self.ipv6 and len(addr) >= 2:
                        addr_str = f"[{addr[0]}]:{addr[1]}"
                    else:
                        addr_str = f"{addr[0]}:{addr[1]}"
                    
                    print(f"  UDP: 收到来自 {addr_str} 的数据 ({len(data)} 字节)")
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"  UDP 错误: {e}")
                    
        except Exception as e:
            print(f"✗ UDP 服务启动失败: {e}")
        finally:
            sock.close()
            print("✓ UDP 服务已停止")
    
    def handle_tcp_client(self, client_socket, client_address):
        """处理 TCP 客户端"""
        if self.ipv6 and len(client_address) >= 2:
            addr_str = f"[{client_address[0]}]:{client_address[1]}"
        else:
            addr_str = f"{client_address[0]}:{client_address[1]}"
        
        print(f"  TCP: 客户端连接 {addr_str}")
        
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                client_socket.sendall(data)
                print(f"  TCP: 收到来自 {addr_str} 的数据 ({len(data)} 字节)")
        except Exception as e:
            if self.running:
                print(f"  TCP 客户端 {addr_str} 错误: {e}")
        finally:
            client_socket.close()
            print(f"  TCP: 客户端断开 {addr_str}")
    
    def tcp_server(self):
        """TCP 服务"""
        try:
            # 创建 TCP socket
            if self.ipv6:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                try:
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                except:
                    pass
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen(5)
            
            print(f"✓ TCP 服务已启动 ({self.protocol}) - 端口 {self.port}")
            
            sock.settimeout(1.0)
            
            while self.running:
                try:
                    client_socket, client_address = sock.accept()
                    client_thread = threading.Thread(
                        target=self.handle_tcp_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"  TCP 错误: {e}")
                    
        except Exception as e:
            print(f"✗ TCP 服务启动失败: {e}")
        finally:
            sock.close()
            print("✓ TCP 服务已停止")
    
    def start(self):
        """启动所有服务"""
        print("=" * 60)
        print(f"网络延迟测试服务端 ({self.protocol})")
        print("=" * 60)
        
        addr_display = f"[{self.host}]:{self.port}" if self.ipv6 else f"{self.host}:{self.port}"
        print(f"监听地址: {addr_display}")
        print(f"协议版本: {self.protocol}")
        print("-" * 60)
        
        # 启动 UDP 服务线程
        udp_thread = threading.Thread(target=self.udp_server)
        udp_thread.daemon = True
        udp_thread.start()
        
        # 启动 TCP 服务线程
        tcp_thread = threading.Thread(target=self.tcp_server)
        tcp_thread.daemon = True
        tcp_thread.start()
        
        # 等待线程启动
        import time
        time.sleep(0.5)
        
        print("-" * 60)
        print("服务端就绪，按 Ctrl+C 停止")
        print("=" * 60)
        print()
        
        try:
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n" + "=" * 60)
            print("正在关闭服务...")
            self.running = False
            time.sleep(2)
            print("服务端已关闭")
            print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='网络延迟测试服务端 (TCP + UDP)')
    parser.add_argument('-p', '--port', type=int, default=9999, 
                       help='监听端口 (默认: 9999)')
    parser.add_argument('-6', '--ipv6', action='store_true', 
                       help='使用 IPv6')
    parser.add_argument('-4', '--ipv4', action='store_true', 
                       help='使用 IPv4 (默认)')
    
    args = parser.parse_args()
    
    # 确定使用的协议
    use_ipv6 = args.ipv6 or not args.ipv4
    if args.ipv6:
        use_ipv6 = True
    else:
        use_ipv6 = False
    
    host = '::' if use_ipv6 else '0.0.0.0'
    
    server = LatencyServer(host=host, port=args.port, ipv6=use_ipv6)
    server.start()

if __name__ == '__main__':
    main()
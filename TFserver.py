#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TFserver - 新版无UI控制台服务端
基于server_ui.py的功能实现，采用chat.py的命令行形式
完全适配client_gui.py和client_lite.py客户端
"""

import socket
import threading
import json
import os
import sys
import datetime
import time

class TFServer:
    def __init__(self, ip, port, max_connections):
        self.ip = ip
        self.port = port
        self.max_connections = max_connections
        
        self.socket = None
        self.conn = []
        self.address = []
        self.usernames = []
        self.banned_ips = []
        self.banned_ports = {}  # 存储被封禁的IP和端口 {ip: [ports]}
        self.server_running = False
        self.start_time = time.time()  # 记录服务器启动时间
        
        # 尝试加载已封禁的IP和端口
        self.load_banned_data()
        
    def start(self):
        """启动服务器"""
        try:
            self.socket = socket.socket()
            self.socket.bind((self.ip, self.port))
            self.socket.listen(self.max_connections)
            self.socket.setblocking(0)
            
            self.server_running = True
            
            print(f"\nTouchFish服务器已启动！")
            print(f"监听地址: {self.ip}:{self.port}")
            print(f"最大连接数: {self.max_connections}")
            print("\n输入 'help' 查看所有可用命令")
            print("按 Ctrl+C 或输入 'exit' 停止服务器\n")
            
            # 启动线程
            t1 = threading.Thread(target=self.accept_connections)
            t2 = threading.Thread(target=self.receive_messages)
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()
            
            # 启动命令处理线程（非daemon，确保能正常处理命令）
            t3 = threading.Thread(target=self.handle_commands)
            t3.start()
            
            # 保持主线程运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 正在停止服务器...")
                self.stop()
                
        except Exception as e:
            print(f"❌ 启动服务器失败: {e}")
            
    def stop(self):
        """停止服务器"""
        self.server_running = False
        
        # 关闭所有连接
        for conn in self.conn:
            try:
                conn.close()
            except:
                pass
                
        self.conn.clear()
        self.address.clear()
        self.usernames.clear()
        
        try:
            self.socket.close()
        except:
            pass
            
        print("✅ 服务器已停止")
        
    def accept_connections(self):
        """接受客户端连接"""
        while self.server_running:
            try:
                conn, addr = self.socket.accept()
                
                # 检查IP是否被封禁
                if addr[0] in self.banned_ips:
                    conn.send("您已被服务器封禁".encode("utf-8"))
                    conn.close()
                    continue
                
                # 检查IP和端口是否被封禁
                if addr[0] in self.banned_ports and addr[1] in self.banned_ports[addr[0]]:
                    conn.send("您已被服务器封禁".encode("utf-8"))
                    conn.close()
                    continue
                
                conn.setblocking(0)
                self.conn.append(conn)
                self.address.append(addr)
                self.usernames.append("")
                
                print(f"[{self.get_timestamp()}] 🔗 新连接: {addr}")
            except BlockingIOError:
                # 正常的非阻塞socket行为，继续等待
                continue
            except Exception as e:
                print(f"❌ [ERROR] accept_connections: {e}")
                time.sleep(0.1)
                continue
                
    def receive_messages(self):
        """接收客户端消息"""
        while self.server_running:
            for i in range(len(self.conn)):
                try:
                    data = self.conn[i].recv(1024).decode('UTF-8')
                    if not data:
                        continue

                except BlockingIOError:
                    # 正常的非阻塞socket行为，继续等待
                    continue
                except Exception as e:
                    print(f"❌ [ERROR] receive_messages (recv): {e}")
                    # 移除断开的连接
                    try:
                        self.conn[i].close()
                    except:
                        pass
                    if i < len(self.conn):
                        self.conn.pop(i)
                        self.address.pop(i)
                        self.usernames.pop(i)
                    continue
                    

                        
                # 检查是否是用户名注册（客户端连接时发送用户名）
                if i < len(self.usernames) and not self.usernames[i] and data.strip() and ":" not in data:
                    # 这是用户名注册
                    username = data.strip()
                    if username.lower() == "server":
                        self.conn[i].send("用户名'server'被保留，请使用其他用户名".encode("utf-8"))
                    else:
                        self.usernames[i] = username
                        print(f"[{self.get_timestamp()}] 👤 用户 {username} 已连接")
                        # 发送确认消息
                        confirmation = f"USERNAME_OK:{username}"
                        self.conn[i].send(confirmation.encode("utf-8"))
                    continue
                        
                # 解析用户名和消息
                if ":" in data:
                    parts = data.split(":", 1)  # 只分割第一个冒号
                    username = parts[0]
                    message_content = parts[1] if len(parts) > 1 else ""
                    
                    # 检查用户名是否为server
                    if username.lower() == "server":
                        self.conn[i].send("用户名'server'被保留，请使用其他用户名".encode("utf-8"))
                        continue
                    
                    # 更新用户名
                    if i < len(self.usernames):
                        self.usernames[i] = username
                    
                    # 显示消息
                    print(f"[{self.get_timestamp()}] 💬 消息: {data.strip()}")
                    
                    # 转发给其他客户端
                    for j in range(len(self.conn)):
                        if i != j:  # 不转发给自己
                            try:
                                self.conn[j].send(data.encode("utf-8"))
                            except:
                                pass
                else:
                    # 显示消息
                    print(f"[{self.get_timestamp()}] 💬 消息: {data.strip()}")
                    
                    # 转发给其他客户端
                    for j in range(len(self.conn)):
                        if i != j:  # 不转发给自己
                            try:
                                self.conn[j].send(data.encode("utf-8"))
                            except:
                                    pass
                    
    def handle_commands(self):
        """处理控制台命令"""
        while self.server_running:
            try:
                cmd = input().strip().lower()
                
                if cmd == "help":
                    self.show_help()
                elif cmd == "list":
                    self.list_connections()

                elif cmd.startswith("ban "):
                    args = cmd[4:].strip()
                    if " " in args:
                        # ban ip port 格式
                        ip, port = args.split(" ", 1)
                        try:
                            port = int(port)
                            self.ban_port(ip, port)
                        except ValueError:
                            print("❌ 错误: 端口必须是整数")
                    else:
                        # ban ip 格式
                        self.ban_user(args)
                elif cmd.startswith("unban "):
                    args = cmd[6:].strip()
                    if " " in args:
                        # unban ip port 格式
                        ip, port = args.split(" ", 1)
                        try:
                            port = int(port)
                            self.unban_port(ip, port)
                        except ValueError:
                            print("❌ 错误: 端口必须是整数")
                    else:
                        # unban ip 格式
                        self.unban_user(args)
                elif cmd == "banned":
                    self.list_banned_ips()
                elif cmd.startswith("msg "):
                    message = cmd[4:]
                    self.send_server_message(message)
                elif cmd == "clear":
                    self.clear_banned()
                elif cmd == "status":
                    self.show_status()
                elif cmd == "exit" or cmd == "quit":
                    print("🛑 正在停止服务器...")
                    self.stop()
                    break
                elif cmd == "":
                    continue
                else:
                    print(f"❌ 未知命令: {cmd}. 输入 'help' 查看可用命令")
                    
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 命令处理错误: {e}")
                
    def show_help(self):
        """显示帮助信息"""
        print("\n=== TouchFish服务器命令帮助 ===")
        print("\n基本命令:")
        print("  help     - 显示此帮助信息")
        print("  list     - 显示所有连接")
        print("  status   - 显示服务器状态")
        print("  exit/quit - 停止服务器")
        print("\n消息命令:")
        print("  msg <text> - 发送服务器消息给所有客户端")
        print("\n封禁管理:")
        print("  ban <ip>         - 封禁指定IP的所有连接")
        print("  ban <ip> <port>  - 封禁指定IP的指定端口")
        print("  unban <ip>       - 解封指定IP")
        print("  unban <ip> <port> - 解封指定IP的指定端口")
        print("  banned           - 显示被封禁的IP和端口列表")
        print("  clear            - 清除所有封禁记录")
        print("\n示例:")
        print("  ban 192.168.1.100")
        print("  ban 192.168.1.100 8080")
        print("  msg 欢迎使用TouchFish聊天室！")
        print("\n=================================\n")
        
    def list_connections(self):
        """显示所有连接"""
        print("\n=== 当前连接列表 ===")
        if not self.address:
            print("当前没有活跃连接")
        else:
            print(f"总连接数: {len(self.address)}")
            for i, addr in enumerate(self.address):
                username = self.usernames[i] if i < len(self.usernames) else "未注册"
                print(f"  {i+1}. {addr[0]}:{addr[1]} - 用户: {username}")
        print("===================\n")
        

        
    def ban_user(self, ip):
        """封禁用户IP"""
        if not ip:
            print("❌ 错误: 请指定要封禁的IP地址")
            return
            
        if ip not in self.banned_ips:
            self.banned_ips.append(ip)
            self.save_banned_ips()
            print(f"✅ 已成功封禁IP: {ip}")
            
            # 断开该IP的所有连接
            disconnected_count = 0
            for i, addr in enumerate(self.address):
                if addr[0] == ip:
                    try:
                        self.conn[i].send("您已被服务器封禁".encode("utf-8"))
                        self.conn[i].close()
                        disconnected_count += 1
                    except:
                        pass
            
            if disconnected_count > 0:
                print(f"🔌 已断开 {disconnected_count} 个来自该IP的连接")
        else:
            print(f"ℹ️  IP {ip} 已被封禁")
            
    def unban_user(self, ip):
        """解封用户IP"""
        if not ip:
            print("❌ 错误: 请指定要解封的IP地址")
            return
            
        if ip in self.banned_ips:
            self.banned_ips.remove(ip)
            self.save_banned_ips()
            print(f"✅ 已成功解封IP: {ip}")
        else:
            print(f"ℹ️  IP {ip} 未被封禁")
            
    def list_banned_ips(self):
        """列出所有被封禁的IP和端口"""
        print("\n=== 封禁列表 ===")
        if self.banned_ips or self.banned_ports:
            if self.banned_ips:
                print(f"\n完全封禁的IP ({len(self.banned_ips)}个):")
                for ip in self.banned_ips:
                    print(f"  🚫 {ip} (所有端口)")
            
            if self.banned_ports:
                total_port_bans = sum(len(ports) for ports in self.banned_ports.values())
                print(f"\n端口封禁 ({total_port_bans}个):")
                for ip, ports in self.banned_ports.items():
                    for port in ports:
                        print(f"  🚫 {ip}:{port}")
        else:
            print("\n✅ 当前没有被封禁的IP或端口")
        print("\n==================\n")
        
    def clear_banned(self):
        """清除所有历史封禁"""
        if self.banned_ips or self.banned_ports:
            total_bans = len(self.banned_ips) + sum(len(ports) for ports in self.banned_ports.values())
            self.banned_ips.clear()
            self.banned_ports.clear()
            self.save_banned_data()
            print(f"✅ 已成功清除 {total_bans} 条封禁记录")
        else:
            print("ℹ️  当前没有需要清除的封禁记录")
            
    def send_server_message(self, message):
        """发送服务器消息"""
        if not message:
            print("❌ 错误: 消息内容不能为空")
            return
            
        full_msg = f"server: {message}\n"
        
        # 显示在控制台
        print(f"[{self.get_timestamp()}] 📢 服务器广播: {message}")
        
        # 发送给所有客户端
        sent_count = 0
        for conn in self.conn:
            try:
                conn.send(full_msg.encode("utf-8"))
                sent_count += 1
            except:
                pass
        
        if sent_count > 0:
            print(f"✅ 消息已发送给 {sent_count} 个客户端")
        else:
            print("ℹ️  当前没有连接的客户端")
                
    def show_status(self):
        """显示服务器状态"""
        print("\n=== TouchFish服务器状态 ===")
        print(f"\n服务器状态: {'🟢 运行中' if self.server_running else '🔴 已停止'}")
        print(f"监听地址: {self.ip}:{self.port}")
        print(f"最大连接数: {self.max_connections}")
        print(f"当前连接数: {len(self.conn)}")
        print(f"已注册用户: {len([name for name in self.usernames if name])}")
        print(f"完全封禁IP: {len(self.banned_ips)}")
        print(f"端口封禁数: {sum(len(ports) for ports in self.banned_ports.values())}")
        print("\n服务器运行时间: {self.get_uptime()}")
        print("==========================\n")
        
    def get_uptime(self):
        """获取服务器运行时间"""
        if hasattr(self, 'start_time'):
            uptime = time.time() - self.start_time
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return "00:00:00"
        
    def load_banned_data(self):
        """加载封禁的IP和端口数据"""
        try:
            if os.path.exists("banned_data.json"):
                with open("banned_data.json", "r") as f:
                    data = json.load(f)
                    self.banned_ips = data.get("banned_ips", [])
                    self.banned_ports = data.get("banned_ports", {})
        except:
            self.banned_ips = []
            self.banned_ports = {}
            
    def save_banned_data(self):
        """保存封禁的IP和端口数据"""
        try:
            data = {
                "banned_ips": self.banned_ips,
                "banned_ports": self.banned_ports
            }
            with open("banned_data.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"❌ 保存封禁数据失败: {e}")
            
    def ban_port(self, ip, port):
        """封禁指定ip的指定端口"""
        if not ip:
            print("❌ 错误: 请指定要封禁的ip地址")
            return
            
        if ip not in self.banned_ports:
            self.banned_ports[ip] = []
            
        if port not in self.banned_ports[ip]:
            self.banned_ports[ip].append(port)
            self.save_banned_data()
            print(f"✅ 已成功封禁 {ip}:{port}")
            
            # 断开该ip和端口的所有连接
            disconnected_count = 0
            for i, addr in enumerate(self.address):
                if addr[0] == ip and addr[1] == port:
                    try:
                        self.conn[i].send("您已被服务器封禁".encode("utf-8"))
                        self.conn[i].close()
                        disconnected_count += 1
                    except:
                        pass
            
            if disconnected_count > 0:
                print(f"🔌 已断开 {disconnected_count} 个来自该IP:端口的连接")
        else:
            print(f"ℹ️  {ip}:{port} 已被封禁")
            
    def unban_port(self, ip, port):
        """解封指定ip的指定端口"""
        if not ip:
            print("❌ 错误: 请指定要解封的ip地址")
            return
            
        if ip in self.banned_ports and port in self.banned_ports[ip]:
            self.banned_ports[ip].remove(port)
            # 如果该ip没有被封禁的端口了，删除该ip条目
            if not self.banned_ports[ip]:
                del self.banned_ports[ip]
            self.save_banned_data()
            print(f"✅ 已成功解封 {ip}:{port}")
        else:
            print(f"ℹ️  {ip}:{port} 未被封禁")
            
    def get_timestamp(self):
        """获取当前时间戳"""
        return datetime.datetime.now().strftime("%H:%M:%S")


def print_usage():
    """显示使用说明"""
    print("TouchFish服务器 - TFserver")
    print("=" * 40)
    print("用法:")
    print("  TFserver.exe [IP] [端口] [最大连接数]")
    print("")
    print("参数说明:")
    print("  IP            - 服务器IP地址 (默认: 127.0.0.1)")
    print("  端口          - 监听端口 (默认: 8080)")
    print("  最大连接数    - 最大客户端连接数 (默认: 10)")
    print("")
    print("示例:")
    print("  TFserver.exe               # 使用默认配置")
    print("  TFserver.exe 192.168.1.100 8080 20")
    print("  TFserver.exe 0.0.0.0 1234 5")
    print("")
    print("启动后输入 'help' 查看服务器命令")
    print("=" * 40)

def main():
    """主函数 - 支持命令行参数和默认值"""
    try:
        # 默认配置
        ip = "127.0.0.1"
        port = 8080
        max_connections = 10
        
        # 处理命令行参数
        if len(sys.argv) == 1:
            # 无参数，使用默认配置
            print("TouchFish服务器启动中...")
            print("使用默认配置: 127.0.0.1:8080 (最大连接: 10)")
        elif len(sys.argv) == 2:
            # 只有IP参数
            ip = sys.argv[1]
            print(f"TouchFish服务器启动中...")
            print(f"使用配置: {ip}:{port} (最大连接: {max_connections})")
        elif len(sys.argv) == 3:
            # IP和端口参数
            ip = sys.argv[1]
            port = int(sys.argv[2])
            print(f"TouchFish服务器启动中...")
            print(f"使用配置: {ip}:{port} (最大连接: {max_connections})")
        elif len(sys.argv) == 4:
            # 全部参数
            ip = sys.argv[1]
            port = int(sys.argv[2])
            max_connections = int(sys.argv[3])
            print(f"TouchFish服务器启动中...")
            print(f"使用配置: {ip}:{port} (最大连接: {max_connections})")
        else:
            print_usage()
            return
            
        # 验证参数
        if not (1 <= port <= 65535):
            print("错误: 端口必须在1-65535之间")
            return
            
        if max_connections < 1 or max_connections > 100:
            print("错误: 最大连接数必须在1-100之间")
            return
            
        # 启动服务器
        server = TFServer(ip, port, max_connections)
        server.start()
        
    except ValueError:
        print("错误: 端口和最大连接数必须是有效的整数")
        print()
        print_usage()
    except socket.gaierror:
        print("错误: IP地址格式无效")
        print()
        print_usage()
    except PermissionError:
        print("错误: 权限不足，请尝试使用1024以上的端口")
        print()
        print_usage()
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"错误: 端口 {port} 已被占用")
        else:
            print(f"启动服务器时发生错误: {e}")
        print()
        print_usage()
    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        print()
        print_usage()

if __name__ == "__main__":
    # 如果是直接运行exe文件，隐藏控制台窗口
    if getattr(sys, 'frozen', False):
        # 这是编译后的exe
        print("TouchFish服务器 (编译版)")
    else:
        # 这是Python脚本
        print("TouchFish服务器 (Python版)")
    
    main()
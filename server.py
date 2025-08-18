import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time
import datetime
import json
import os

class BanManagementWindow(tk.Toplevel):
    def __init__(self, server):
        super().__init__(server.root)
        self.server = server
        self.title("封禁管理")
        self.geometry("500x400")
        self.minsize(400, 300)
        self.transient(server.root)
        self.grab_set()
        
        # 主题色和字体
        self.theme_color = server.theme_color
        self.font_family = server.font_family
        
        # 封禁类型：IP或端口
        self.ban_type = tk.StringVar(value="ip")
        
        # 存储复选框状态
        self.checkbox_states = {}
        
        self.create_widgets()
        self.refresh_user_list()
        
        # 启动定时刷新 (每3秒)
        self.after(3000, self.auto_refresh)
        
    def create_widgets(self):
        """创建界面组件"""
        # 配置网格权重
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # 当前连接用户列表
        user_frame = tk.LabelFrame(self, text="当前连接用户", padx=10, pady=10)
        user_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        user_frame.columnconfigure(0, weight=1)
        user_frame.rowconfigure(0, weight=1)
        
        # 创建带滚动条的框架来放置复选框列表
        self.user_canvas = tk.Canvas(user_frame)
        self.user_scrollbar = ttk.Scrollbar(user_frame, orient="vertical", command=self.user_canvas.yview)
        self.user_canvas.configure(yscrollcommand=self.user_scrollbar.set)
        
        self.user_scrollbar.grid(row=0, column=1, sticky="ns")
        self.user_canvas.grid(row=0, column=0, sticky="nsew")
        
        # 创建内部框架来放置复选框
        self.user_list_frame = tk.Frame(self.user_canvas)
        self.user_canvas.create_window((0, 0), window=self.user_list_frame, anchor="nw")
        
        # 绑定滚动事件
        self.user_list_frame.bind("<Configure>", lambda e: self.user_canvas.configure(scrollregion=self.user_canvas.bbox("all")))
        
        # 添加表头
        header_frame = tk.Frame(self.user_list_frame)
        header_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(header_frame, text="选择", width=8, font=self.font_family).pack(side="left")
        tk.Label(header_frame, text="用户名", width=15, font=self.font_family).pack(side="left")
        tk.Label(header_frame, text="IP地址", width=20, font=self.font_family).pack(side="left")
        tk.Label(header_frame, text="端口", width=10, font=self.font_family).pack(side="left")
        
        # 操作按钮
        action_frame = tk.Frame(self)
        action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # 封禁类型选择
        type_frame = tk.Frame(action_frame)
        type_frame.pack(side="left", padx=10)
        
        tk.Radiobutton(
            type_frame, 
            text="封禁IP", 
            variable=self.ban_type, 
            value="ip", 
            font=self.font_family
        ).pack(side="left", padx=5)
        
        tk.Radiobutton(
            type_frame, 
            text="封禁端口", 
            variable=self.ban_type, 
            value="port", 
            font=self.font_family
        ).pack(side="left", padx=5)
        
        # 封禁按钮
        self.ban_btn = tk.Button(
            action_frame, 
            text="封禁选中用户", 
            command=self.ban_selected_user, 
            bg="#f44336",  # 红色
            fg="white", 
            font=self.font_family, 
            relief="flat", 
            padx=10
        )
        self.ban_btn.pack(side="left", padx=5)
        
        # 刷新按钮
        self.refresh_btn = tk.Button(
            action_frame, 
            text="刷新列表", 
            command=self.refresh_user_list, 
            bg="#2196F3",  # 蓝色
            fg="white", 
            font=self.font_family, 
            relief="flat", 
            padx=10
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        # 清除历史封禁按钮
        self.clear_btn = tk.Button(
            action_frame, 
            text="清除历史封禁", 
            command=self.clear_banned, 
            bg="#FFC107",  # 黄色
            fg="black", 
            font=self.font_family, 
            relief="flat", 
            padx=10
        )
        self.clear_btn.pack(side="right", padx=5)
        
        # 添加鼠标移入效果
        self.ban_btn.bind("<Enter>", lambda e: self.ban_btn.config(relief="raised"))
        self.ban_btn.bind("<Leave>", lambda e: self.ban_btn.config(relief="flat"))
        self.refresh_btn.bind("<Enter>", lambda e: self.refresh_btn.config(relief="raised"))
        self.refresh_btn.bind("<Leave>", lambda e: self.refresh_btn.config(relief="flat"))
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.config(relief="raised"))
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.config(relief="flat"))
        
        # 封禁列表
        ban_frame = tk.LabelFrame(self, text="已封禁列表", padx=10, pady=10)
        ban_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        ban_frame.columnconfigure(0, weight=1)
        ban_frame.rowconfigure(0, weight=1)
        
        # 封禁列表
        self.ban_tree = ttk.Treeview(ban_frame, columns=("类型", "地址"), show="headings", height=5)
        self.ban_tree.heading("类型", text="封禁类型")
        self.ban_tree.heading("地址", text="封禁地址")
        self.ban_tree.column("类型", width=80)
        self.ban_tree.column("地址", width=200)
        
        ban_scrollbar = ttk.Scrollbar(ban_frame, orient="vertical", command=self.ban_tree.yview)
        self.ban_tree.configure(yscrollcommand=ban_scrollbar.set)
        
        self.ban_tree.grid(row=0, column=0, sticky="nsew")
        ban_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 解除封禁按钮
        self.unban_btn = tk.Button(
            self, 
            text="解除选中封禁", 
            command=self.unban_selected, 
            bg="#4CAF50",  # 绿色
            fg="white", 
            font=self.font_family, 
            relief="flat", 
            padx=10
        )
        self.unban_btn.grid(row=3, column=0, pady=5)
        
        # 添加鼠标移入效果
        self.unban_btn.bind("<Enter>", lambda e: self.unban_btn.config(relief="raised"))
        self.unban_btn.bind("<Leave>", lambda e: self.unban_btn.config(relief="flat"))
        
    def refresh_user_list(self, keep_selection=True):
        """刷新用户列表"""
        # 保存当前选中状态
        current_selection = {}
        if keep_selection:
            for user_id, var in self.checkbox_states.items():
                current_selection[user_id] = var.get()
        
        # 清空现有列表
        for widget in self.user_list_frame.winfo_children():
            # 保留表头
            if widget.winfo_name() != '!frame':
                widget.destroy()
        
        # 添加新用户
        users = self.server.update_user_list()
        self.checkbox_states = {}
        
        for i, user in enumerate(users):
            user_id = f"{user['ip']}:{user['port']}"
            frame = tk.Frame(self.user_list_frame)
            frame.pack(fill="x", padx=5, pady=2)
            frame.config(bg="#f0f0f0" if i % 2 == 0 else "white")
            
            # 创建复选框
            var = tk.BooleanVar()
            # 恢复之前的选中状态
            if keep_selection and user_id in current_selection:
                var.set(current_selection[user_id])
            
            checkbox = tk.Checkbutton(frame, variable=var, bg=frame['bg'])
            checkbox.pack(side="left", padx=5)
            
            # 显示用户信息
            tk.Label(frame, text=user['username'], width=15, anchor="w", font=self.font_family, bg=frame['bg']).pack(side="left")
            tk.Label(frame, text=user['ip'], width=20, anchor="w", font=self.font_family, bg=frame['bg']).pack(side="left")
            tk.Label(frame, text=user['port'], width=10, anchor="w", font=self.font_family, bg=frame['bg']).pack(side="left")
            
            # 存储复选框状态
            self.checkbox_states[user_id] = var
        
        # 刷新封禁列表
        self.refresh_ban_list()
    
    def auto_refresh(self):
        """自动刷新列表并保持选中状态"""
        self.refresh_user_list(keep_selection=True)
        # 继续定时刷新
        self.after(3000, self.auto_refresh)
        
    def refresh_ban_list(self):
        """刷新封禁列表"""
        # 清空现有列表
        for item in self.ban_tree.get_children():
            self.ban_tree.delete(item)
        
        # 添加已封禁的IP
        for ip in self.server.banned_ips:
            self.ban_tree.insert("", "end", values=("IP", ip))
        
    def ban_selected_user(self):
        """封禁选中的用户"""
        selected_users = []
        users = self.server.update_user_list()
        
        # 找出所有被选中的用户
        for user in users:
            user_id = f"{user['ip']}:{user['port']}"
            if user_id in self.checkbox_states and self.checkbox_states[user_id].get():
                selected_users.append(user)
        
        if not selected_users:
            messagebox.showwarning("警告", "请先选择要封禁的用户")
            return
        
        for user in selected_users:
            username = user["username"]
            ip = user["ip"]
            port = user["port"]
            
            # 根据选择的封禁类型进行封禁
            if self.ban_type.get() == "ip":
                if ip not in self.server.banned_ips:
                    self.server.banned_ips.append(ip)
                    self.server.save_banned_ips()
                    self.server.display_message(f"已封禁用户 {username} 的IP: {ip}", is_server=True)
                else:
                    messagebox.showinfo("信息", f"用户 {username} 的IP {ip} 已被封禁")
            else:
                # 这里可以实现封禁端口的逻辑
                # 为简化实现，我们暂时只封禁IP
                if ip not in self.server.banned_ips:
                    self.server.banned_ips.append(ip)
                    self.server.save_banned_ips()
                    self.server.display_message(f"已封禁用户 {username} 的IP: {ip} (按端口封禁)", is_server=True)
                else:
                    messagebox.showinfo("信息", f"用户 {username} 的IP {ip} 已被封禁")
            
            # 关闭该用户的连接
            for i, addr in enumerate(self.server.address):
                if addr[0] == ip and addr[1] == port:
                    try:
                        self.server.conn[i].send("您已被服务器封禁".encode("utf-8"))
                        self.server.conn[i].close()
                    except:
                        pass
                    break
        
        # 刷新列表，不保持选中状态
        self.refresh_user_list(keep_selection=False)
        
    def unban_selected(self):
        """解除选中的封禁"""
        selected = self.ban_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要解除封禁的项目")
            return
        
        for item in selected:
            values = self.ban_tree.item(item, "values")
            ban_type = values[0]
            address = values[1]
            
            if ban_type == "IP" and address in self.server.banned_ips:
                self.server.banned_ips.remove(address)
                self.server.save_banned_ips()
                self.server.display_message(f"已解除IP封禁: {address}", is_server=True)
        
        # 刷新列表
        self.refresh_ban_list()
        
    def clear_banned(self):
        """清除所有历史封禁"""
        if messagebox.askyesno("确认", "确定要清除所有历史封禁吗？"):
            self.server.banned_ips.clear()
            self.server.save_banned_ips()
            self.server.display_message("已清除所有历史封禁", is_server=True)
            self.refresh_ban_list()

class ChatServer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("聊天服务器")
        self.root.geometry("500x600")
        self.root.minsize(400, 500)
        
        # 固定绿色主题
        self.theme_color = "#4CAF50"  # 绿色
        self.font_family = ("微软雅黑", 10)
        
        # 服务器状态
        self.server_running = False
        self.socket = None
        self.conn = []
        self.address = []
        self.usernames = []
        self.banned_ips = []
        
        # 尝试加载已封禁的IP
        self.load_banned_ips()
        
        self.create_main_window()
        self.root.mainloop()

    def create_main_window(self):
        """创建主窗口"""
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # 服务器控制面板
        control_frame = tk.LabelFrame(self.root, text="服务器控制", padx=10, pady=10)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        # IP地址输入
        tk.Label(control_frame, text="服务器IP:").grid(row=0, column=0, sticky="w", pady=2)
        self.ip_entry = tk.Entry(control_frame, font=self.font_family)
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.ip_entry.insert(0, "127.0.0.1")
        
        # 端口输入
        tk.Label(control_frame, text="端口:").grid(row=1, column=0, sticky="w", pady=2)
        self.port_entry = tk.Entry(control_frame, font=self.font_family, width=10)
        self.port_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.port_entry.insert(0, "8080")
        
        # 最大连接数
        tk.Label(control_frame, text="最大连接数:").grid(row=2, column=0, sticky="w", pady=2)
        self.max_conn_entry = tk.Entry(control_frame, font=self.font_family, width=10)
        self.max_conn_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.max_conn_entry.insert(0, "10")
        
        # 控制按钮
        button_frame = tk.Frame(control_frame)
        button_frame.grid(row=0, column=2, rowspan=3, padx=10)
        
        self.start_btn = tk.Button(
            button_frame,
            text="启动服务器",
            command=self.start_server,
            bg=self.theme_color,
            fg="white",
            font=self.font_family,
            relief="flat",
            padx=10
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="停止服务器",
            command=self.stop_server,
            bg="#f44336",  # 红色
            fg="white",
            font=self.font_family,
            relief="flat",
            padx=10,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # 添加鼠标移入效果
        self.start_btn.bind("<Enter>", lambda e: self.start_btn.config(relief="raised"))
        self.start_btn.bind("<Leave>", lambda e: self.start_btn.config(relief="flat"))
        self.stop_btn.bind("<Enter>", lambda e: self.stop_btn.config(relief="raised"))
        self.stop_btn.bind("<Leave>", lambda e: self.stop_btn.config(relief="flat"))
        
        # 连接状态
        status_frame = tk.LabelFrame(self.root, text="连接状态", padx=10, pady=10)
        status_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # 连接列表
        self.conn_tree = ttk.Treeview(status_frame, columns=("IP", "端口", "用户名"), show="headings", height=8)
        self.conn_tree.heading("IP", text="IP地址")
        self.conn_tree.heading("端口", text="端口")
        self.conn_tree.heading("用户名", text="用户名")
        self.conn_tree.column("IP", width=120)
        self.conn_tree.column("端口", width=80)
        self.conn_tree.column("用户名", width=120)
        
        conn_scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.conn_tree.yview)
        self.conn_tree.configure(yscrollcommand=conn_scrollbar.set)
        
        self.conn_tree.grid(row=0, column=0, sticky="nsew")
        conn_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 聊天记录框
        chat_frame = tk.LabelFrame(self.root, text="聊天记录", padx=10, pady=10)
        chat_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        self.chat_text = tk.Text(
            chat_frame,
            font=self.font_family,
            state="disabled",
            wrap="word",
            height=10
        )
        
        chat_scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=chat_scrollbar.set)
        
        self.chat_text.grid(row=0, column=0, sticky="nsew")
        chat_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 消息输入框
        input_frame = tk.Frame(self.root)
        input_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        
        self.msg_entry = tk.Text(
            input_frame,
            font=self.font_family,
            height=3,
            wrap="word"
        )
        
        # 添加提示文字
        self.msg_entry.insert("1.0", "在此输入消息，Enter发送，Ctrl+Enter换行")
        self.msg_entry.config(fg="gray")
        
        def on_entry_click(event):
            if self.msg_entry.get("1.0", "end-1c") == "在此输入消息，Enter发送，Ctrl+Enter换行":
                self.msg_entry.delete("1.0", "end")
                self.msg_entry.config(fg="black")
        
        def on_focusout(event):
            if self.msg_entry.get("1.0", "end-1c") == "":
                self.msg_entry.insert("1.0", "在此输入消息，Enter发送，Ctrl+Enter换行")
                self.msg_entry.config(fg="gray")
        
        self.msg_entry.bind("<FocusIn>", on_entry_click)
        self.msg_entry.bind("<FocusOut>", on_focusout)
        
        # 绑定按键事件
        self.msg_entry.bind("<Return>", self.on_enter_key)
        self.msg_entry.bind("<Control-Return>", self.on_ctrl_enter_key)
        
        self.msg_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # 发送按钮
        send_btn = tk.Button(
            input_frame,
            text="发送",
            command=self.send_server_message,
            bg=self.theme_color,
            fg="white",
            font=self.font_family,
            relief="flat",
            padx=20
        )
        send_btn.grid(row=0, column=1)
        
        # 添加鼠标移入效果
        send_btn.bind("<Enter>", lambda e: send_btn.config(relief="raised"))
        send_btn.bind("<Leave>", lambda e: send_btn.config(relief="flat"))
        
        # 封禁管理按钮
        self.ban_management_btn = tk.Button(
            self.root, 
            text="封禁管理", 
            command=self.open_ban_management, 
            bg="#2196F3",  # 蓝色
            fg="white", 
            font=self.font_family, 
            relief="flat", 
            padx=20
        )
        self.ban_management_btn.grid(row=4, column=0, pady=10)
        
        # 添加鼠标移入效果
        self.ban_management_btn.bind("<Enter>", lambda e: self.ban_management_btn.config(relief="raised"))
        self.ban_management_btn.bind("<Leave>", lambda e: self.ban_management_btn.config(relief="flat"))
        
    def start_server(self):
        """启动服务器"""
        if self.server_running:
            return
            
        try:
            ip = self.ip_entry.get()
            port = int(self.port_entry.get())
            max_conn = int(self.max_conn_entry.get())
            
            self.socket = socket.socket()
            self.socket.bind((ip, port))
            self.socket.listen(max_conn)
            self.socket.setblocking(0)
            
            self.server_running = True
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            # 启动线程
            threading.Thread(target=self.accept_connections, daemon=True).start()
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
            self.display_message("服务器已启动", is_server=True)
        except Exception as e:
            messagebox.showerror("错误", f"启动服务器失败:\n{str(e)}")
            
    def stop_server(self):
        """停止服务器"""
        if not self.server_running:
            return
            
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
            
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        # 清空连接列表
        for item in self.conn_tree.get_children():
            self.conn_tree.delete(item)
            
        self.update_user_list()
        
        self.display_message("服务器已停止", is_server=True)
        
    def accept_connections(self):
        """接受客户端连接"""
        while self.server_running:
            try:
                conn, addr = self.socket.accept()
                
                # 检查IP是否被封禁
                if addr[0] in self.banned_ips:
                    conn.send("您已被封禁".encode("utf-8"))
                    conn.close()
                    continue
                
                conn.setblocking(0)
                self.conn.append(conn)
                self.address.append(addr)
                
                # 在GUI线程更新界面
                self.root.after(0, self.update_connection_list)
                
                self.display_message(f"新连接: {addr}", is_server=True)
            except:
                continue
                
    def receive_messages(self):
        """接收客户端消息"""
        while self.server_running:
            for i in range(len(self.conn)):
                try:
                    data = self.conn[i].recv(1024).decode('UTF-8')
                    if not data:
                        continue
                        
                    # 处理获取用户列表的请求
                    if data == "GET_USER_LIST":
                        # 发送用户列表，过滤空用户名
                        user_list = ",".join([name for name in self.usernames if name])
                        self.conn[i].send(f"USER_LIST:{user_list}".encode("utf-8"))
                        continue
                        
                    # 解析用户名
                    if ":" in data:
                        username = data.split(":")[0]
                        # 检查用户名是否为server
                        if username.lower() == "server":
                            self.conn[i].send("用户名'server'被保留，请使用其他用户名".encode("utf-8"))
                            continue
                        
                        # 更新用户名
                        if i >= len(self.usernames):
                            self.usernames.extend([""] * (i - len(self.usernames) + 1))
                        self.usernames[i] = username
                        
                        # 更新连接列表
                        self.root.after(0, self.update_connection_list)
                    
                    # 显示消息
                    self.display_message(data)
                    
                    # 转发给其他客户端
                    for j in range(len(self.conn)):
                        if i != j:  # 不转发给自己
                            try:
                                self.conn[j].send(data.encode("utf-8"))
                            except:
                                pass
                except:
                    continue
                    
    def send_server_message(self):
        """发送服务器消息"""
        # 获取消息内容，排除提示文字
        content = self.msg_entry.get("1.0", "end-1c")
        if content == "在此输入消息，Enter发送，Ctrl+Enter换行":
            return
        
        message = content.strip()
        if not message:
            return
            
        full_msg = f"server: {message}\n"
        
        # 显示在聊天框中
        self.display_message(full_msg, is_server=True)
        
        # 发送给所有客户端
        for conn in self.conn:
            try:
                conn.send(full_msg.encode("utf-8"))
            except:
                pass
                
        # 清空输入框
        self.msg_entry.delete("1.0", "end")
        self.msg_entry.insert("1.0", "在此输入消息，Enter发送，Ctrl+Enter换行")
        self.msg_entry.config(fg="gray")
        
    def display_message(self, message, is_server=False):
        """在聊天框中显示消息"""
        self.chat_text.config(state="normal")
        
        # 获取当前时间并格式化
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        if is_server:
            # 服务器消息使用粗体，添加时间戳和换行
            formatted_message = f"[{current_time}] {message}\n"
            self.chat_text.insert("end", formatted_message, "server_message")
            self.chat_text.tag_config("server_message", foreground=self.theme_color, font=(self.font_family[0], self.font_family[1], "bold"))
        else:
            # 客户端消息添加时间戳和换行
            formatted_message = f"[{current_time}] {message}\n"
            self.chat_text.insert("end", formatted_message)
            
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")
        
    def update_connection_list(self):
        """更新连接列表"""
        # 清空现有列表
        for item in self.conn_tree.get_children():
            self.conn_tree.delete(item)
            
        # 添加新项
        for i, addr in enumerate(self.address):
            username = self.usernames[i] if i < len(self.usernames) else ""
            self.conn_tree.insert("", "end", values=(addr[0], addr[1], username))
            
        # 更新用户列表
        self.update_user_list()
        
    def update_user_list(self):
        """更新用户列表（为封禁管理窗口使用）"""
        users = []
        for i, addr in enumerate(self.address):
            username = self.usernames[i] if i < len(self.usernames) else ""
            if username:
                users.append({"username": username, "ip": addr[0], "port": addr[1]})
        return users
            
    def open_ban_management(self):
        """打开封禁管理窗口"""
        BanManagementWindow(self)
            
    def load_banned_ips(self):
        """加载封禁的IP列表"""
        try:
            if os.path.exists("banned_ips.json"):
                with open("banned_ips.json", "r") as f:
                    self.banned_ips = json.load(f)
        except:
            self.banned_ips = []
            
    def save_banned_ips(self):
        """保存封禁的IP列表"""
        try:
            with open("banned_ips.json", "w") as f:
                json.dump(self.banned_ips, f)
        except Exception as e:
            print(f"保存封禁IP列表失败: {e}")
            
    def on_enter_key(self, event):
        """处理Enter键事件"""
        self.send_server_message()
        return "break"  # 阻止默认行为
        
    def on_ctrl_enter_key(self, event):
        """处理Ctrl+Enter键事件"""
        # 插入换行符
        self.msg_entry.insert(tk.INSERT, "\n")
        return "break"  # 阻止默认行为

if __name__ == "__main__":
    ChatServer()
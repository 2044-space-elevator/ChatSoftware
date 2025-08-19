import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import socket
import threading
import platform
import datetime
import sys
import re
import time

def calculate_contrast_color(color):
    """计算与给定颜色对比度较高的颜色"""
    # 移除#号（如果有）
    color = color.lstrip('#')
    # 将十六进制转换为RGB
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    # 计算亮度（YIQ公式）
    brightness = (0.299 * r + 0.587 * g + 0.114 * b)
    # 如果亮度高，返回黑色；否则返回白色
    return '#000000' if brightness > 128 else '#FFFFFF'

def lighten_color(color, factor=0.2):
    """使颜色变亮"""
    color = color.lstrip('#')
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    
    r = int(min(255, r + (255 - r) * factor))
    g = int(min(255, g + (255 - g) * factor))
    b = int(min(255, b + (255 - b) * factor))
    
    return f'#{r:02x}{g:02x}{b:02x}'

def darken_color(color, factor=0.2):
    """使颜色变暗"""
    color = color.lstrip('#')
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    
    r = int(max(0, r - r * factor))
    g = int(max(0, g - g * factor))
    b = int(max(0, b - b * factor))
    
    return f'#{r:02x}{g:02x}{b:02x}'

class ChatClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("聊天客户端")
        self.root.geometry("900x600")
        self.root.minsize(600, 400)
        
        # 主题色配置
        self.theme_color = "#F0FFFF"  # 默认主题色
        self.font_family = ("微软雅黑", 12)
        self.bell_enabled = False
        
        # 计算辅助色
        self.secondary_color = lighten_color(self.theme_color)
        self.background_color = lighten_color(self.theme_color, 0.8)
        self.text_color = calculate_contrast_color(self.background_color)
        self.accent_color = darken_color(self.theme_color)
        
        self.create_connection_window()
        # 不在这里启动mainloop，而是在连接成功后启动聊天窗口的mainloop

    def create_connection_window(self):
        """创建连接窗口"""
        # 配置网格权重以支持窗口缩放
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        frame = tk.Frame(self.root, padx=20, pady=20, bg=self.background_color)
        frame.pack(expand=True, fill="both")
        
        # 服务器地址
        tk.Label(frame, text="服务器IP:", bg=self.background_color, fg=self.text_color).grid(row=0, column=0, sticky="w", pady=5)
        self.ip_entry = tk.Entry(frame, font=self.font_family)
        self.ip_entry.grid(row=0, column=1, pady=5, sticky="ew")
        self.ip_entry.insert(0, "127.0.0.1")
        
        # 端口
        tk.Label(frame, text="端口:", bg=self.background_color, fg=self.text_color).grid(row=1, column=0, sticky="w", pady=5)
        self.port_entry = tk.Entry(frame, font=self.font_family)
        self.port_entry.grid(row=1, column=1, pady=5, sticky="ew")
        self.port_entry.insert(0, "8080")
        
        # 用户名
        tk.Label(frame, text="用户名:", bg=self.background_color, fg=self.text_color).grid(row=2, column=0, sticky="w", pady=5)
        self.user_entry = tk.Entry(frame, font=self.font_family)
        self.user_entry.grid(row=2, column=1, pady=5, sticky="ew")
        
        # 配置列权重以支持输入框缩放
        frame.columnconfigure(1, weight=1)
        
        # 连接按钮
        connect_btn = tk.Button(
            frame, 
            text="连接", 
            command=self.connect_to_server,
            bg=self.theme_color,
            fg=calculate_contrast_color(self.theme_color),
            font=self.font_family,
            relief="flat",
            padx=20,
            pady=5
        )
        connect_btn.grid(row=3, columnspan=2, pady=15)
        
        # 添加鼠标移入效果
        connect_btn.bind("<Enter>", lambda e: connect_btn.config(relief="raised"))
        connect_btn.bind("<Leave>", lambda e: connect_btn.config(relief="flat"))
        
        # 提示
        tk.Label(frame, text="提示: Ctrl+Enter 发送消息", bg=self.background_color, fg=self.text_color).grid(row=4, columnspan=2)

    def connect_to_server(self):
        """连接到服务器"""
        try:
            self.server_ip = self.ip_entry.get()
            self.port = int(self.port_entry.get())
            self.username = self.user_entry.get()
            if not self.username:
                messagebox.showerror("错误", "用户名不能为空")
                return
                
            self.socket = socket.socket()
            self.socket.settimeout(10)  # 设置10秒超时
            self.socket.connect((self.server_ip, self.port))
            
            # 发送用户名进行注册
            self.socket.send(self.username.encode("utf-8"))
            
            # 等待服务器确认
            try:
                response = self.socket.recv(1024).decode("utf-8")
            except socket.timeout:
                messagebox.showerror("连接错误", "服务器响应超时，请检查服务器是否正常运行")
                self.socket.close()
                # 重新启动连接窗口的mainloop
                self.root.mainloop()
                return
            if response.startswith("USERNAME_OK:"):
                # 用户名注册成功
                self.socket.settimeout(None)  # 恢复阻塞模式
                self.socket.setblocking(0)  # 设置为非阻塞模式以适应后续的消息接收
                self.root.destroy()  # 关闭连接窗口
                self.create_chat_window()  # 打开聊天窗口
                # 启动消息接收线程
                threading.Thread(target=self.receive_messages, daemon=True).start()

                # 启动聊天窗口的主循环
                self.chat_win.mainloop()
            else:
                # 用户名注册失败
                messagebox.showerror("连接错误", response)
                self.socket.close()
                # 重新启动连接窗口的mainloop
                self.root.mainloop()
        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到服务器:\n{str(e)}")
            # 重新启动连接窗口的mainloop
            self.root.mainloop()

    def create_chat_window(self):
        """创建聊天窗口"""
        self.chat_win = tk.Tk()
        self.chat_win.title(f"聊天室 - {self.username}")
        self.chat_win.geometry("900x600")
        self.chat_win.minsize(600, 400)
        self.chat_win.configure(bg=self.background_color)
        
        # 设置窗口关闭时的处理
        self.chat_win.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 创建左右分栏布局
        self.paned_window = ttk.PanedWindow(self.chat_win, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧消息区域 (占2/3宽度)
        left_frame = tk.Frame(self.paned_window, bg=self.background_color)
        self.paned_window.add(left_frame, weight=2)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=0)
        left_frame.rowconfigure(2, weight=0)
        

        
        # ============= 左侧消息区域 =============
        # 聊天记录框
        self.chat_frame = tk.Frame(left_frame, bg=self.background_color)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)
        
        self.chat_text = tk.Text(
            self.chat_frame, 
            font=self.font_family,
            state="disabled",
            wrap="word",
            bg=self.background_color,
            fg=self.text_color
        )
        
        scrollbar = ttk.Scrollbar(self.chat_frame, orient="vertical", command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        
        self.chat_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 消息输入框
        input_frame = tk.Frame(left_frame, bg=self.background_color)
        input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        
        self.msg_entry = tk.Text(
            input_frame, 
            font=self.font_family,
            height=4,
            wrap="word",
            bg=self.background_color,
            fg=self.text_color
        )
        
        # 定义提示文字
        self.placeholder_text = "在此输入消息，Enter发送，Ctrl+Enter换行"
        
        # 初始化提示文字
        self.msg_entry.insert("1.0", self.placeholder_text)
        self.msg_entry.config(fg="gray")
        
        def on_entry_click(event):
            """当输入框获得焦点时"""
            current_text = self.msg_entry.get("1.0", "end-1c")
            if current_text == self.placeholder_text:
                self.msg_entry.delete("1.0", "end")
                self.msg_entry.config(fg=self.text_color)
        
        def on_focusout(event):
            """当输入框失去焦点时"""
            current_text = self.msg_entry.get("1.0", "end-1c")
            if not current_text or current_text == self.placeholder_text:
                self.msg_entry.delete("1.0", "end")
                self.msg_entry.insert("1.0", self.placeholder_text)
                self.msg_entry.config(fg="gray")
        
        def on_key_press(event):
            """按下键盘时检查是否是提示文字"""
            current_text = self.msg_entry.get("1.0", "end-1c")
            if current_text == self.placeholder_text:
                self.msg_entry.delete("1.0", "end")
                self.msg_entry.config(fg=self.text_color)
        
        # 绑定事件
        self.msg_entry.bind("<FocusIn>", on_entry_click)
        self.msg_entry.bind("<FocusOut>", on_focusout)
        self.msg_entry.bind("<KeyPress>", on_key_press)
        
        # 绑定按键事件
        self.msg_entry.bind("<Return>", self.on_enter_key)
        self.msg_entry.bind("<Control-Return>", self.on_ctrl_enter_key)
        
        self.msg_entry.grid(row=0, column=0, sticky="ew")
        
        # 发送按钮
        send_btn = tk.Button(
            input_frame, 
            text="发送", 
            command=self.send_message,
            bg=self.theme_color,
            fg=calculate_contrast_color(self.theme_color),
            font=self.font_family,
            relief="flat",
            padx=20
        )
        send_btn.grid(row=0, column=1, padx=(5, 0))
        
        # 添加鼠标移入效果
        send_btn.bind("<Enter>", lambda e: send_btn.config(relief="raised"))
        send_btn.bind("<Leave>", lambda e: send_btn.config(relief="flat"))
        
        # 设置按钮
        setting_btn = tk.Button(
            left_frame, 
            text="设置", 
            command=self.open_settings,
            bg=self.accent_color,
            fg=calculate_contrast_color(self.accent_color),
            font=self.font_family,
            relief="flat",
            padx=20
        )
        setting_btn.grid(row=2, column=0, pady=5)
        
        # 添加鼠标移入效果
        setting_btn.bind("<Enter>", lambda e: setting_btn.config(relief="raised"))
        setting_btn.bind("<Leave>", lambda e: setting_btn.config(relief="flat"))
        




    def open_settings(self):
        """打开设置窗口"""
        settings_win = tk.Toplevel(self.chat_win)
        settings_win.title("设置")
        settings_win.transient(self.chat_win)
        settings_win.grab_set()
        settings_win.geometry("300x400")
        settings_win.configure(bg=self.background_color)
        
        # 创建选项卡
        notebook = ttk.Notebook(settings_win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 显示设置选项卡
        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text="显示")
        
        # 主题色设置
        theme_frame = tk.LabelFrame(display_frame, text="主题色", padx=10, pady=10)
        theme_frame.pack(padx=10, pady=5, fill="x")
        
        def choose_color():
            color = colorchooser.askcolor(initialcolor=self.theme_color)[1]
            if color:
                self.theme_color = color
                # 更新辅助色
                self.secondary_color = lighten_color(self.theme_color)
                self.background_color = lighten_color(self.theme_color, 0.8)
                self.text_color = calculate_contrast_color(self.background_color)
                self.accent_color = darken_color(self.theme_color)
                # 更新UI颜色
                self.update_ui_colors()
        
        tk.Button(
            theme_frame, 
            text="选择主题色", 
            command=choose_color,
            bg=self.theme_color,
            fg=calculate_contrast_color(self.theme_color)
        ).pack()
        
        # 字体设置
        font_frame = tk.LabelFrame(display_frame, text="字体设置", padx=10, pady=10)
        font_frame.pack(padx=10, pady=5, fill="x")
        
        tk.Label(font_frame, text="字体名称:").grid(row=0, column=0, sticky="w")
        font_name_entry = tk.Entry(font_frame)
        font_name_entry.grid(row=0, column=1, padx=5, pady=2)
        font_name_entry.insert(0, self.font_family[0])
        
        tk.Label(font_frame, text="字体大小:").grid(row=1, column=0, sticky="w")
        font_size_entry = tk.Entry(font_frame)
        font_size_entry.grid(row=1, column=1, padx=5, pady=2)
        font_size_entry.insert(0, str(self.font_family[1]))
        
        # 提示音设置选项卡
        bell_frame = tk.LabelFrame(display_frame, text="提示音设置", padx=10, pady=10)
        bell_frame.pack(padx=10, pady=5, fill="x")
        
        bell_var = tk.BooleanVar(value=self.bell_enabled)
        bell_check = tk.Checkbutton(
            bell_frame, 
            text="启用消息提示音",
            variable=bell_var,
            state="normal" if platform.system() == "Windows" else "disabled"
        )
        bell_check.pack(anchor="w")
        
        # 确定按钮
        def apply_settings():
            try:
                font_name = font_name_entry.get()
                font_size = int(font_size_entry.get())
                self.font_family = (font_name, font_size)
                
                self.bell_enabled = bell_var.get()
                
                self.chat_text.config(font=self.font_family)
                self.msg_entry.config(font=self.font_family)

                settings_win.destroy()
            except ValueError:
                messagebox.showerror("错误", "字体大小必须是整数")
        
        tk.Button(
            settings_win, 
            text="确定", 
            command=apply_settings,
            bg=self.theme_color,
            fg=calculate_contrast_color(self.theme_color),
            font=self.font_family,
            relief="flat",
            padx=20
        ).pack(pady=10)

    def update_ui_colors(self):
        """更新UI颜色"""
        # 更新背景色
        self.chat_win.configure(bg=self.background_color)
        
        # 更新左侧区域颜色
        self.chat_frame.configure(bg=self.background_color)
        self.chat_text.configure(bg=self.background_color, fg=self.text_color)
        input_frame = self.chat_text.master.master.grid_slaves(row=1, column=0)[0]
        input_frame.configure(bg=self.background_color)
        self.msg_entry.configure(bg=self.background_color, fg=self.text_color)
        
        # 更新按钮颜色
        setting_btn = self.chat_text.master.master.grid_slaves(row=2, column=0)[0]
        setting_btn.configure(bg=self.accent_color, fg=calculate_contrast_color(self.accent_color))
        send_btn = input_frame.grid_slaves(row=0, column=1)[0]
        send_btn.configure(bg=self.theme_color, fg=calculate_contrast_color(self.theme_color))
        


    def on_enter_key(self, event):
        """处理Enter键事件"""
        self.send_message()
        return "break"  # 阻止默认行为
    
    def on_ctrl_enter_key(self, event):
        """处理Ctrl+Enter键事件"""
        # 插入换行符
        self.msg_entry.insert(tk.INSERT, "\n")
        return "break"  # 阻止默认行为
    
    def send_message(self):
        """发送消息"""
        # 获取消息内容，排除提示文字
        content = self.msg_entry.get("1.0", "end-1c")
        if content == self.placeholder_text:
            return
        
        message = content.strip()
        if not message:
            return
            
        full_msg = f"{self.username}: {message}\n"
        try:
            self.socket.send(full_msg.encode("utf-8"))
            # 立即显示自己发送的消息
            self.display_message(full_msg)
            self.msg_entry.delete("1.0", "end")
            # 重置提示文字
            self.msg_entry.insert("1.0", self.placeholder_text)
            self.msg_entry.config(fg="gray")
        except BlockingIOError:
            # 非阻塞socket发送缓冲区满，稍后重试
            self.chat_win.after(100, self.send_message)
        except Exception as e:
            messagebox.showerror("发送错误", f"消息发送失败:\n{str(e)}")

    def receive_messages(self):
        """接收消息的线程函数"""
        while True:
            try:
                message = self.socket.recv(1024).decode("utf-8")

                    
                # 检查是否是封禁消息
                if message == "您已被服务器封禁":
                    self.handle_ban()
                    break
                    
                # 在GUI线程更新界面
                self.chat_win.after(0, self.display_message, message)
                
                # 播放提示音
                if self.bell_enabled and not message.startswith(f"{self.username}:"):
                    self.play_notification_sound()
                    
            except BlockingIOError:
                # 非阻塞socket的正常行为，继续等待数据
                continue
            except Exception as e:
                break

    def display_message(self, message):
        """在聊天框中显示消息"""
        self.chat_text.config(state="normal")
        
        # 获取当前时间并格式化
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 添加时间戳和换行
        formatted_message = f"[{current_time}] {message}\n"
        
        # 检查是否包含@自己的消息
        if f"@【{self.username}】" in message:
            # 使用主题色突出显示
            self.chat_text.insert("end", formatted_message, "highlight")
        else:
            self.chat_text.insert("end", formatted_message)
        
        # 配置标签样式
        self.chat_text.tag_configure("highlight", foreground=self.accent_color, font=(self.font_family[0], self.font_family[1], "bold"))
        
        # 滚动到最新消息
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

    def handle_ban(self):
        """处理被封禁的情况"""
        self.chat_win.after(0, self.show_ban_message)

    def show_ban_message(self):
        """显示封禁消息"""
        # 清空聊天记录
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", "end")
        
        # 显示封禁信息
        ban_message = "\n\n\t您已被服务器永久封禁！\n\t违反服务器规定，情节严重！\n\t请自重！\n"
        self.chat_text.insert("end", ban_message, "ban")
        self.chat_text.tag_configure("ban", foreground="#ff0000", font=(self.font_family[0], 16, "bold"), justify="center")
        self.chat_text.config(state="disabled")
        
        # 弹出嘲讽对话框
        messagebox.showerror("封禁通知", "您已被服务器永久封禁！\n违反服务器规定，情节严重！")
        
        # 3秒后关闭程序
        self.chat_win.after(3000, self.on_closing)

    def play_notification_sound(self):
        """播放提示音（跨平台）"""
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(1000, 200)
            elif platform.system() == "Darwin":  # macOS
                import os
                os.system("afplay /System/Library/Sounds/Ping.aiff&")
            else:  # Linux
                import os
                os.system("paplay /usr/share/sounds/freedesktop/stereo/message.oga&")
        except:
            pass

    def on_closing(self):
        """关闭窗口时的处理"""
        try:
            self.socket.close()
        except:
            pass
        self.chat_win.destroy()
        sys.exit()

if __name__ == "__main__":
    client = ChatClient()
    # 启动连接窗口的mainloop
    client.root.mainloop()
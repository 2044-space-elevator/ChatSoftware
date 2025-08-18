import tkinter as tk
from tkinter import messagebox
import socket
import threading
import datetime
import sys


class ChatClientLite:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("聊天客户端")
        self.root.geometry("400x300")
        self.root.minsize(300, 200)

        # 基本配置
        self.font_family = ("微软雅黑", 10)

        self.create_connection_window()
        self.root.mainloop()

    def create_connection_window(self):
        """创建连接窗口"""
        # 配置网格权重以支持窗口缩放
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        # 服务器地址
        tk.Label(frame, text="服务器IP:", font=self.font_family).grid(row=0, column=0, sticky="w", pady=5)
        self.ip_entry = tk.Entry(frame, font=self.font_family)
        self.ip_entry.grid(row=0, column=1, pady=5, sticky="ew")
        self.ip_entry.insert(0, "127.0.0.1")

        # 端口
        tk.Label(frame, text="端口:", font=self.font_family).grid(row=1, column=0, sticky="w", pady=5)
        self.port_entry = tk.Entry(frame, font=self.font_family)
        self.port_entry.grid(row=1, column=1, pady=5, sticky="ew")
        self.port_entry.insert(0, "8080")

        # 用户名
        tk.Label(frame, text="用户名:", font=self.font_family).grid(row=2, column=0, sticky="w", pady=5)
        self.user_entry = tk.Entry(frame, font=self.font_family)
        self.user_entry.grid(row=2, column=1, pady=5, sticky="ew")

        # 配置列权重以支持输入框缩放
        frame.columnconfigure(1, weight=1)

        # 连接按钮
        connect_btn = tk.Button(
            frame, 
            text="连接", 
            command=self.connect_to_server,
            bg="#4a90e2",
            fg="white",
            font=self.font_family,
            padx=20,
            pady=5
        )
        connect_btn.grid(row=3, columnspan=2, pady=15)

        # 提示
        tk.Label(frame, text="提示: Enter发送消息", font=self.font_family).grid(row=4, columnspan=2)

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
            self.socket.connect((self.server_ip, self.port))
            self.root.destroy()  # 关闭连接窗口
            self.create_chat_window()  # 打开聊天窗口
            # 启动消息接收线程
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.chat_win.mainloop()
        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到服务器:\n{str(e)}")

    def create_chat_window(self):
        """创建聊天窗口"""
        self.chat_win = tk.Tk()
        self.chat_win.title(f"聊天室 - {self.username}")
        self.chat_win.geometry("500x350")
        self.chat_win.minsize(400, 300)

        # 配置网格权重以支持窗口缩放
        self.chat_win.columnconfigure(0, weight=1)
        self.chat_win.rowconfigure(0, weight=1)
        self.chat_win.rowconfigure(1, weight=0)

        # 聊天记录框
        self.chat_frame = tk.Frame(self.chat_win)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)

        self.chat_text = tk.Text(
            self.chat_frame, 
            font=self.font_family,
            state="disabled",
            wrap="word"
        )

        scrollbar = tk.Scrollbar(self.chat_frame, orient="vertical", command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)

        self.chat_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 消息输入框
        input_frame = tk.Frame(self.chat_win)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.msg_entry = tk.Text(
            input_frame, 
            font=self.font_family,
            height=3,
            wrap="word"
        )

        # 定义提示文字
        self.placeholder_text = "输入消息，Enter发送"

        # 初始化提示文字
        self.msg_entry.insert("1.0", self.placeholder_text)
        self.msg_entry.config(fg="gray")

        def on_entry_click(event):
            """当输入框获得焦点时"""
            current_text = self.msg_entry.get("1.0", "end-1c")
            if current_text == self.placeholder_text:
                self.msg_entry.delete("1.0", "end")
                self.msg_entry.config(fg="black")

        def on_focusout(event):
            """当输入框失去焦点时"""
            current_text = self.msg_entry.get("1.0", "end-1c")
            if not current_text:
                self.msg_entry.delete("1.0", "end")
                self.msg_entry.insert("1.0", self.placeholder_text)
                self.msg_entry.config(fg="gray")

        # 绑定事件
        self.msg_entry.bind("<FocusIn>", on_entry_click)
        self.msg_entry.bind("<FocusOut>", on_focusout)

        # 绑定按键事件
        self.msg_entry.bind("<Return>", self.on_enter_key)

        self.msg_entry.grid(row=0, column=0, sticky="ew")

        # 发送按钮
        send_btn = tk.Button(
            input_frame, 
            text="发送", 
            command=self.send_message,
            bg="#4a90e2",
            fg="white",
            font=self.font_family,
            padx=15
        )
        send_btn.grid(row=0, column=1, padx=(5, 0))

    def on_enter_key(self, event):
        """处理Enter键事件"""
        self.send_message()
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
        except Exception as e:
            messagebox.showerror("发送错误", f"消息发送失败:\n{str(e)}")

    def receive_messages(self):
        """接收消息的线程函数"""
        while True:
            try:
                message = self.socket.recv(1024).decode("utf-8")

                # 检查是否是封禁消息
                if "您已被服务器封禁" in message:
                    # 在GUI线程显示封禁消息并退出
                    self.chat_win.after(0, self.handle_ban)
                    break

                # 在GUI线程更新界面
                self.chat_win.after(0, self.display_message, message)

            except Exception as e:
                break

    def handle_ban(self):
        """处理被封禁的情况"""
        # 显示封禁消息
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.insert("end", "\n\n\n\t\t\t\t您已被服务器封禁!\n")
        self.chat_text.insert("end", "\t\t\t\t原因: 违反服务器规定\n\n")
        self.chat_text.insert("end", "\t\t\t\t\t再见!\n")
        self.chat_text.config(fg="red", font=("微软雅黑", 14, "bold"))
        self.chat_text.config(state="disabled")
        
        # 显示嘲讽对话框
        self.chat_win.after(1000, self.show_ban_message)

    def show_ban_message(self):
        """显示嘲讽的封禁消息"""
        messagebox.showerror(
            "封禁通知", 
            "您已被服务器封禁!\n\n" + 
            "原因: 您的行为违反了服务器规定\n\n" + 
            "下次请注意言行!\n\n" + 
            "程序将在3秒后自动关闭..."
        )
        
        # 3秒后关闭程序
        self.chat_win.after(3000, self.on_closing)

    def display_message(self, message):
        """在聊天框中显示消息"""
        self.chat_text.config(state="normal")

        # 获取当前时间并格式化
        current_time = datetime.datetime.now().strftime("%H:%M")

        # 添加时间戳和换行
        formatted_message = f"[{current_time}] {message}\n"

        # 确保所有消息都能正常显示
        self.chat_text.insert("end", formatted_message)

        # 滚动到最新消息
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

    def on_closing(self):
        """关闭窗口时的处理"""
        try:
            self.socket.close()
        except:
            pass
        self.chat_win.destroy()
        sys.exit()

if __name__ == "__main__":
    ChatClientLite()
import os
import base64
import tkinter as tk
from tkinter import ttk
from inbound_view import InboundView
from outbound_view import OutboundView
from data_view import DataView
from modify_view import ModifyView
from settings_view import SettingsView
from update_view import UpdateView

# 请将此处的 ICON_BASE64 替换为你的 logo 图像（GIF 或 PNG 格式）的 Base64 编码字符串
ICON_BASE64 = """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""".strip()

class InventoryMainView:
    def __init__(self, controller, settings_model):
        self.controller = controller
        self.settings_model = settings_model

        # 创建主窗口
        self.root = tk.Tk()
        # 设置窗口标题
        self.root.title("招财进宝管理系统 3.0")

        try:
            # 设置任务栏图标（使用.ico文件）
            icon_path = os.path.join(os.path.dirname(__file__), "logo1.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # 如果.ico文件不存在，使用Base64图标作为备选
                icon = tk.PhotoImage(data=ICON_BASE64)
                self.root.iconphoto(False, icon)
                # 保存引用，避免被垃圾回收
                self._icon = icon
        except Exception as e:
            print("无法设置图标:", e)

        # 窗口初始大小
        self.root.geometry("900x700")

        # 构建主界面
        self.setup_main_interface()

    def setup_main_interface(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        nb = ttk.Notebook(main_frame)
        nb.pack(fill=tk.BOTH, expand=True)

        # 各个功能页
        self.inbound_page  = InboundView(nb, self.controller)
        self.outbound_page = OutboundView(nb, self.controller)
        self.data_page     = DataView(nb, self.controller)
        self.modify_page   = ModifyView(nb, self.controller)
        self.settings_page = SettingsView(nb, self.settings_model, self.controller)
        self.update_page   = UpdateView(nb, self.controller)

        nb.add(self.inbound_page,  text="入库登记")
        nb.add(self.outbound_page, text="出库登记")
        nb.add(self.data_page,     text="数据查询")
        nb.add(self.modify_page,   text="数据修改")
        nb.add(self.settings_page, text="设置")
        nb.add(self.update_page,   text="检查更新")

        ttk.Button(self.root, text="退出", command=self.root.quit).pack(pady=5)

    def show_message(self, msg: str):
        from tkinter import messagebox
        messagebox.showinfo("提示", msg)

    def start(self):
        self.root.mainloop()

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
from license_view import LicenseView

# 请将此处的 ICON_BASE64 替换为你的 logo 图像（GIF 或 PNG 格式）的 Base64 编码字符串
ICON_BASE64 = """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");
}""".strip()

class InventoryMainView:
    def __init__(self, controller, settings_model):
        self.controller = controller
        self.settings_model = settings_model

        # 创建主窗口
        self.root = tk.Tk()
        # 设置窗口标题
        self.root.title("艾方存货管家 2.1.0")

        try:
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
        self.license_page  = LicenseView(nb, self.controller)

        nb.add(self.inbound_page,  text="入库登记")
        nb.add(self.outbound_page, text="出库登记")
        nb.add(self.data_page,     text="数据查询")
        nb.add(self.modify_page,   text="数据修改")
        nb.add(self.settings_page, text="设置")
        nb.add(self.update_page,   text="检查更新")
        nb.add(self.license_page,  text="软件信息")

        ttk.Button(self.root, text="退出", command=self.root.quit).pack(pady=5)

    def show_message(self, msg: str):
        from tkinter import messagebox
        messagebox.showinfo("提示", msg)

    def start(self):
        self.root.mainloop()

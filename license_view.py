import tkinter as tk
from tkinter import ttk
from license_validator import LicenseValidator
from datetime import datetime

class LicenseView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.validator = LicenseValidator()
        
        self.create_widgets()
        self.update_license_info()
    
    def create_widgets(self):
        # 创建标签页内容
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="软件信息", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        info_frame = ttk.LabelFrame(main_frame, text="软件详情", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 软件名称
        name_frame = ttk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="软件名称:", width=15).pack(side=tk.LEFT)
        self.name_label = ttk.Label(name_frame, text="艾方存货管家")
        self.name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 软件作者
        author_frame = ttk.Frame(info_frame)
        author_frame.pack(fill=tk.X, pady=5)

        ttk.Label(author_frame, text="软件作者:", width=15).pack(side=tk.LEFT)
        self.author_label = ttk.Label(author_frame, text="艾拉与方块 © 2025 海口龙华艾方网络科技工作室")
        self.author_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 软件描述
        description_frame = ttk.Frame(info_frame)
        description_frame.pack(fill=tk.X, pady=5)

        ttk.Label(description_frame, text="软件描述:", width=15).pack(side=tk.LEFT)
        self.description_label = ttk.Label(description_frame, text="一由艾方网络科技工作室开发的一款出入库管理调控软件，可兼容控制记录，支持多种数据格式的导入导出，支持输出文件直接兼容其他软件。", wraplength=400)
        self.description_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.description_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 授权信息框
        info_frame = ttk.LabelFrame(main_frame, text="授权详情", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        
        # 授权状态
        status_frame = ttk.Frame(info_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="授权状态:", width=15).pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="正在检查...")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 授权类型
        type_frame = ttk.Frame(info_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="授权类型:", width=15).pack(side=tk.LEFT)
        self.type_label = ttk.Label(type_frame, text="--")
        self.type_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 激活日期
        activation_frame = ttk.Frame(info_frame)
        activation_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(activation_frame, text="激活日期:", width=15).pack(side=tk.LEFT)
        self.activation_label = ttk.Label(activation_frame, text="--")
        self.activation_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 过期日期
        expiry_frame = ttk.Frame(info_frame)
        expiry_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(expiry_frame, text="过期日期:", width=15).pack(side=tk.LEFT)
        self.expiry_label = ttk.Label(expiry_frame, text="--")
        self.expiry_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 剩余天数
        days_frame = ttk.Frame(info_frame)
        days_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(days_frame, text="剩余天数:", width=15).pack(side=tk.LEFT)
        self.days_label = ttk.Label(days_frame, text="--")
        self.days_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 硬件ID
        hardware_frame = ttk.Frame(info_frame)
        hardware_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(hardware_frame, text="硬件ID:", width=15).pack(side=tk.LEFT)
        self.hardware_label = ttk.Label(hardware_frame, text="--")
        self.hardware_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 刷新按钮
        refresh_button = ttk.Button(main_frame, text="刷新授权信息", command=self.update_license_info)
        refresh_button.pack(pady=20)
        
        # 重新激活按钮
        activate_button = ttk.Button(main_frame, text="重新激活", command=self.reactivate_license)
        activate_button.pack(pady=5)
        
        # 绑定窗口大小变化事件
        self.bind("<Configure>", self.update_wraplength)
    
    def update_license_info(self):
        # 获取授权信息
        license_data = self.validator.load_license()
        
        if license_data:
            # 更新授权状态
            is_valid, message = self.validator.validate_license()
            self.status_label.config(text=message)
            
            # 更新授权类型
            license_type = license_data.get('license_type', '--')
            if license_type == 'standard':
                license_type = "标准版"
            elif license_type == 'professional':
                license_type = "专业版"
            elif license_type == 'enterprise':
                license_type = "企业版"
            self.type_label.config(text=license_type)
            
            # 更新激活日期
            activation_date = license_data.get('activation_date', '--')
            self.activation_label.config(text=activation_date)
            
            # 更新过期日期
            expiry_date = license_data.get('expiry_date', '--')
            self.expiry_label.config(text=expiry_date)
            
            # 计算剩余天数
            try:
                expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S')
                current_time = self.validator.get_current_time()
                days_left = (expiry_date_obj - current_time).days
                
                if days_left > 0:
                    self.days_label.config(text=f"{days_left} 天", foreground="green")
                else:
                    self.days_label.config(text="已过期", foreground="red")
            except Exception as e:
                self.days_label.config(text="计算错误", foreground="red")
            
            # 更新硬件ID
            hardware_id = license_data.get('hardware_id', '--')
            self.hardware_label.config(text=hardware_id)
        else:
            # 如果没有授权信息
            self.status_label.config(text="未激活")
            self.type_label.config(text="--")
            self.activation_label.config(text="--")
            self.expiry_label.config(text="--")
            self.days_label.config(text="--")
            self.hardware_label.config(text="--")
    
    def reactivate_license(self):
        # 创建一个临时的Tk窗口用于对话框
        root = tk.Toplevel(self)
        root.title("重新激活")
        root.geometry("300x150")
        root.resizable(False, False)
        
        # 设置窗口图标
        try:
            from gui_view import ICON_BASE64
            icon = tk.PhotoImage(data=ICON_BASE64)
            root.iconphoto(False, icon)
            # 保存引用，避免被垃圾回收
            root._icon = icon
        except Exception as e:
            print("无法设置图标:", e)
        
        # 居中显示
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # 创建输入框
        frame = ttk.Frame(root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="请输入激活码:").pack(pady=5)
        
        code_entry = ttk.Entry(frame, width=30)
        code_entry.pack(pady=5)
        code_entry.focus()
        
        def activate():
            activation_code = code_entry.get().strip()
            if activation_code:
                is_valid, message = self.validator.activate_license(activation_code)
                if is_valid:
                    tk.messagebox.showinfo("激活成功", message)
                    self.update_license_info()
                    root.destroy()
                else:
                    tk.messagebox.showerror("激活失败", message)
            else:
                tk.messagebox.showerror("错误", "请输入激活码")
        
        # 按钮框
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="激活", command=activate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=root.destroy).pack(side=tk.LEFT, padx=5)
    
    def update_wraplength(self, event=None):
        # 获取当前窗口宽度并设置适当的换行长度
        width = self.winfo_width()
        if width > 100:  # 确保窗口有合理宽度
            self.description_label.configure(wraplength=width-300)  # 减去一些边距
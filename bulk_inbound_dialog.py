import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class BulkInboundDialog(tk.Toplevel):
    """批量入库对话框窗口"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("批量入库")
        self.geometry("1000x650")
        self.controller = controller
        self.resizable(True, True)
        
        # 确保主窗口可见
        self.transient(parent)
        self.grab_set()
        
        # 存储行数据
        self.row_frames = {}  # {item_id: frame}
        self.row_entries = {}  # {item_id: {col_name: entry}}
        self.row_counter = 0
        
        self.create_widgets()
        self.focus_set()
        
    def create_widgets(self):
        """创建UI组件"""
        # 顶部框架：快递单号
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(top_frame, text="入库快递单号:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5)
        self.ent_courier = ttk.Entry(top_frame, width=40, font=("Arial", 11))
        self.ent_courier.grid(row=0, column=1, padx=5, sticky="ew")
        top_frame.columnconfigure(1, weight=1)
        
        ttk.Label(top_frame, text="货商姓名:", font=("Arial", 10, "bold")).grid(row=0, column=2, sticky="e", padx=5)
        suppliers = self.controller.settings_model.get_suppliers()
        self.cb_supplier = ttk.Combobox(top_frame, values=suppliers, state="readonly", width=15, font=("Arial", 10))
        if suppliers:
            self.cb_supplier.current(0)
        self.cb_supplier.grid(row=0, column=3, padx=5)
        
        ttk.Label(top_frame, text="入库日期:", font=("Arial", 10, "bold")).grid(row=0, column=4, sticky="e", padx=5)
        now = datetime.now()
        self.ent_date = ttk.Entry(top_frame, width=12, font=("Arial", 10))
        self.ent_date.insert(0, now.strftime("%Y-%m-%d"))
        self.ent_date.grid(row=0, column=5, padx=5)
        
        # 时间输入
        tf = ttk.Frame(top_frame)
        tf.grid(row=0, column=6, padx=5)
        self.cb_hour = ttk.Combobox(tf, values=[f"{i:02d}" for i in range(24)], width=3, state="readonly", font=("Arial", 9))
        self.cb_hour.current(now.hour)
        self.cb_hour.pack(side=tk.LEFT)
        ttk.Label(tf, text=":").pack(side=tk.LEFT)
        self.cb_min = ttk.Combobox(tf, values=[f"{i:02d}" for i in range(60)], width=3, state="readonly", font=("Arial", 9))
        self.cb_min.current(now.minute)
        self.cb_min.pack(side=tk.LEFT)
        ttk.Label(tf, text=":").pack(side=tk.LEFT)
        self.cb_sec = ttk.Combobox(tf, values=[f"{i:02d}" for i in range(60)], width=3, state="readonly", font=("Arial", 9))
        self.cb_sec.current(now.second)
        self.cb_sec.pack(side=tk.LEFT)
        
        # 分隔线
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # 中间框架：表格
        middle_frame = ttk.Frame(self, padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 表格标题
        ttk.Label(middle_frame, text="商品信息", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # 创建表格容器
        container_frame = ttk.Frame(middle_frame)
        container_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表格列定义
        self.columns = ("序号", "条形码", "商品名称", "买价", "佣金", "数量", "单位", "颜色/配置")
        column_widths = {"序号": 40, "条形码": 90, "商品名称": 110, "买价": 70, "佣金": 70, "数量": 50, "单位": 50, "颜色/配置": 110}
        
        # 表头框架
        header_frame = ttk.Frame(container_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 绘制表头
        for col in self.columns:
            width = column_widths.get(col, 100)
            lbl = ttk.Label(
                header_frame,
                text=col,
                font=("Arial", 9, "bold"),
                width=int(width / 7),
                relief="raised",
                borderwidth=1,
                background="#E8E8E8"
            )
            lbl.pack(side=tk.LEFT, padx=2, pady=2, expand=True, fill=tk.BOTH)
        
        # 数据行容器（带滚动条）
        data_frame = ttk.Frame(container_frame)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建Canvas和Scrollbar以支持滚动
        canvas = tk.Canvas(data_frame, highlightthickness=0, bg="white")
        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, relief="flat", borderwidth=0)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.scrollable_frame = scrollable_frame  # 保存引用以便后续添加行
        
        # 按钮框架
        btn_frame = ttk.Frame(middle_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="添加行", command=self.add_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除行", command=self.delete_row).pack(side=tk.LEFT, padx=5)
        
        # 底部框架：确定/取消按钮
        bottom_frame = ttk.Frame(self, padding=10)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(bottom_frame, text="确定", command=self.submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
        # 初始化一行空记录
        self.add_row()
        
    def add_row(self):
        """添加一行空记录"""
        self.row_counter += 1
        item_id = f"row_{self.row_counter}"
        
        # 创建行框架
        row_frame = tk.Frame(
            self.scrollable_frame,
            relief="solid",
            borderwidth=1,
            bg="white",
            height=35
        )
        row_frame.pack(fill=tk.X, padx=0, pady=2, ipady=3)
        
        # 存储行框的引用
        self.row_frames[item_id] = row_frame
        self.row_entries[item_id] = {}
        
        # 序号不可编辑，用Label显示
        seq_label = tk.Label(
            row_frame,
            text=str(self.row_counter),
            font=("Arial", 9),
            width=3,
            bg="#F0F0F0",
            relief="flat",
            borderwidth=1
        )
        seq_label.pack(side=tk.LEFT, padx=2, pady=2, ipady=3)
        
        # 添加分隔线
        ttk.Separator(row_frame, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=1)
        
        # 为每个列创建输入框
        columns_without_seq = self.columns[1:]  # 排除序号列
        
        for col_idx, col_name in enumerate(columns_without_seq):
            width = {"条形码": 90, "商品名称": 110, "买价": 70, 
                    "佣金": 70, "数量": 50, "单位": 50, "颜色/配置": 110}.get(col_name, 100)
            
            # 创建条形码Entry框
            entry_frame = tk.Frame(row_frame, bg="white")
            entry_frame.pack(side=tk.LEFT, padx=1, pady=1, ipady=1, expand=True, fill=tk.BOTH)
            
            # 输入框
            entry = tk.Entry(
                entry_frame,
                font=("Arial", 9),
                relief="flat",
                borderwidth=0,
                bg="white"
            )
            entry.pack(fill=tk.BOTH, expand=True, padx=2, pady=1)
            
            # 绑定事件处理（改変时更新背景颜色）
            def make_change_handler(frame):
                def on_change(event=None):
                    if entry.get().strip():
                        frame.config(bg="#FFFACD")  # 轻黄色背景，表示有数据
                    else:
                        frame.config(bg="white")
                return on_change
            
            entry.bind("<KeyRelease>", make_change_handler(entry_frame))
            
            # 存储输入框引用
            self.row_entries[item_id][col_name] = entry
            
            # 添加分隔线，分隔不同列
            if col_idx < len(columns_without_seq) - 1:
                ttk.Separator(row_frame, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=0)
        
        # 削除按钮
        del_btn = tk.Button(
            row_frame,
            text="×",
            font=("Arial", 10, "bold"),
            width=2,
            relief="flat",
            bg="#FFE4E1",
            fg="#DC143C",
            cursor="hand2",
            command=lambda: self.delete_specific_row(item_id)
        )
        del_btn.pack(side=tk.LEFT, padx=2, pady=2, ipady=1)
        
        return item_id
        
    def delete_row(self):
        """削除选中的行"""
        if not self.row_frames:
            messagebox.showwarning("提示", "没有可以削除的行！")
            return
        messagebox.showwarning("提示", "请焦点到一行，然后点击转到行上的×按钮来削除！")
        
    def delete_specific_row(self, item_id):
        """削除特定的行"""
        if item_id in self.row_frames:
            self.row_frames[item_id].destroy()
            del self.row_frames[item_id]
            del self.row_entries[item_id]
                
            # 如果没有任何行，自动添加一个空行
            if len(self.row_frames) == 0:
                self.add_row()

    
    def submit(self):
        """提交批量入库"""
        courier_no = self.ent_courier.get().strip()
        supplier = self.cb_supplier.get()
        date_str = self.ent_date.get().strip()
        hour = self.cb_hour.get()
        minute = self.cb_min.get()
        second = self.cb_sec.get()
        
        # 验证快递单号
        if not courier_no:
            messagebox.showwarning("提示", "请输入入库快递单号！")
            return
        
        # 验证供应商
        if not supplier:
            messagebox.showwarning("提示", "请选择货商姓名！")
            return
        
        # 验证日期
        if not date_str:
            messagebox.showwarning("提示", "请输入入库日期！")
            return
        
        # 验证是否有数据
        if not self.row_frames:
            messagebox.showwarning("提示", "请至少添加一行商品信息！")
            return
        
        # 构造入库时间
        datetime_str = f"{date_str} {hour}:{minute}:{second}"
        
        # 收集所有商品数据
        success_count = 0
        error_count = 0
        error_messages = []
        
        for item_id in self.row_frames:
            # 获取行数据
            entries = self.row_entries[item_id]
            
            barcode = entries.get("条形码", tk.Entry()).get().strip() if "条形码" in entries else ""
            product_name = entries.get("商品名称", tk.Entry()).get().strip() if "商品名称" in entries else ""
            buy_price = entries.get("买价", tk.Entry()).get().strip() if "买价" in entries else ""
            commission = entries.get("佣金", tk.Entry()).get().strip() if "佣金" in entries else ""
            quantity = entries.get("数量", tk.Entry()).get().strip() if "数量" in entries else ""
            unit = entries.get("单位", tk.Entry()).get().strip() if "单位" in entries else ""
            color = entries.get("颜色/配置", tk.Entry()).get().strip() if "颜色/配置" in entries else ""
            
            # 跳过空行
            if not product_name and not barcode:
                continue
            
            # 验证必填字段
            if not product_name:
                error_messages.append("商品名称不能为空")
                error_count += 1
                continue
            
            if not buy_price:
                error_messages.append(f"商品'{product_name}'的买价不能为空")
                error_count += 1
                continue
            
            if not commission:
                error_messages.append(f"商品'{product_name}'的佣金不能为空")
                error_count += 1
                continue
            
            if not quantity:
                error_messages.append(f"商品'{product_name}'的数量不能为空")
                error_count += 1
                continue
            
            # 验证数值字段
            try:
                buy_price_f = float(buy_price)
                commission_f = float(commission)
                quantity_i = int(quantity)
            except ValueError as e:
                error_messages.append(f"商品'{product_name}'的数值格式错误: {e}")
                error_count += 1
                continue
            
            # 构造入库数据
            data = {
                '货商姓名': supplier,
                '数字条码': barcode,
                '入库时间': datetime_str,
                '商品名称': product_name,
                '买价': str(buy_price_f),
                '佣金': str(commission_f),
                '结算状态': '否',
                '商品数量': str(quantity_i),
                '商品数量单位': unit,
                '入库快递单号': courier_no,
                '颜色/配置': color
            }
            
            # 调用控制器处理入库
            success = self.controller.handle_inbound_registration(data)
            if success:
                success_count += 1
            else:
                error_messages.append(f"商品'{product_name}'提交失败")
                error_count += 1
        
        # 显示结果
        if error_count > 0 and success_count == 0:
            messagebox.showerror("提交失败", f"所有商品提交失败:\n" + "\n".join(error_messages[:5]))
        elif error_count > 0:
            msg = f"部分商品提交成功！\n成功: {success_count}条\n失败: {error_count}条"
            if error_messages:
                msg += f"\n\n错误详情:\n" + "\n".join(error_messages[:3])
            messagebox.showwarning("部分成功", msg)
            self.destroy()
        else:
            messagebox.showinfo("成功", f"共成功提交 {success_count} 条商品！")
            self.destroy()
    
    def cancel(self):
        """取消对话框"""
        if messagebox.askyesno("确认", "确定要关闭而不保存吗？"):
            self.destroy()

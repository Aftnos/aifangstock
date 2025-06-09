import tkinter as tk
from tkinter import ttk, messagebox

# 尝试导入 pypinyin，用于拼音首字母搜索
try:
    from pypinyin import lazy_pinyin, Style
    _HAS_PYPINYIN = True
except ImportError:
    _HAS_PYPINYIN = False

class OutboundView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        self.checked = set()
        self.create_widgets()

    def create_widgets(self):
        # 顶部标题和搜索框
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(top_frame, text="选择待出库库存（多选复选框）：", font=("Arial", 10, "bold")).pack(side=tk.LEFT, pady=5)
        
        # 添加搜索功能
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.ent_search = ttk.Entry(search_frame, width=20)
        self.ent_search.pack(side=tk.LEFT, padx=5)
        self.ent_search.bind("<Return>", lambda e: self.search_inventory())
        ttk.Button(search_frame, text="搜索", command=self.search_inventory).pack(side=tk.LEFT, padx=5)
        
        tree_container = ttk.Frame(self)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 从设置中获取要显示的列
        display_cols = self.controller.settings_model.get_display_columns('outbound')
        if not display_cols:
            # 如果没有配置，使用默认列
            display_cols = ["选中", "单号", "商品名称", "商品数量", "剩余数量", "剩余价值", "颜色/配置", "货商姓名", "入库时间"]
        
        self.tree = ttk.Treeview(
            tree_container,
            columns=display_cols,
            show="headings",
            selectmode="none"
        )
        for c in display_cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100, anchor="center")
        if "选中" in display_cols:
            self.tree.column("选中", width=50)
        self.tree.tag_configure("selected", background="lightblue")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hsb.pack(fill=tk.X, padx=10)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.bind("<Button-1>", self.on_click)

        # 按钮和选中计数
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="刷新库存", command=self.controller.refresh_inventory_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="全选", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消全选", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        self.lbl_selected_count = ttk.Label(btn_frame, text="已选中 0 条")
        self.lbl_selected_count.pack(side=tk.LEFT, padx=5)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, pady=5)

        # 出库录入：添加出库数量输入
        frm = ttk.Frame(self)
        frm.pack(pady=5)
        fields = [
            ("出库档口", "出库档口", "combobox"),
            ("快递单号", "快递单号", "entry"),
            ("出库数量", "出库数量", "entry"),
        ]
        self.entries = {}
        for i, (lt, fn, wt) in enumerate(fields):
            ttk.Label(frm, text=lt).grid(row=i, column=0, padx=5, pady=3, sticky="e")
            if wt == "combobox":
                cb = ttk.Combobox(
                    frm,
                    values=self.controller.settings_model.get_counters(),
                    state="readonly",
                    width=28,
                    height=10  # 增加高度以显示更多选项
                )
                cb.grid(row=i, column=1, padx=5, pady=3, sticky="w")
                self.entries[fn] = cb
            else:
                e = ttk.Entry(frm, width=30)
                e.grid(row=i, column=1, padx=5, pady=3, sticky="w")
                self.entries[fn] = e
                
        # 添加提示信息
        tip_label = ttk.Label(frm, text="提示：出库数量为空时将全部出库", foreground="gray")
        tip_label.grid(row=len(fields), column=0, columnspan=2, pady=5)

        ttk.Button(self, text="提交出库", command=self.submit).pack(pady=10)

    def _update_selected_count(self):
        self.lbl_selected_count.config(text=f"已选中 {len(self.checked)} 条")

    def on_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        
        # 获取当前显示的列
        display_cols = self.controller.settings_model.get_display_columns('outbound')
        if not display_cols:
            display_cols = ["选中", "单号", "商品名称", "商品数量", "剩余数量", "剩余价值", "颜色/配置", "货商姓名", "入库时间"]
        
        # 检查是否点击了"选中"列
        if "选中" in display_cols:
            selected_col_index = display_cols.index("选中") + 1  # Treeview列索引从1开始
            if self.tree.identify_column(event.x) != f"#{selected_col_index}":
                return
        else:
            return
            
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        # 使用item作为唯一标识符而不是单号
        if item in self.checked:
            self.checked.remove(item)
            self.tree.set(item, "选中", "☐")
            self.tree.item(item, tags=())
        else:
            self.checked.add(item)
            self.tree.set(item, "选中", "☑")
            self.tree.item(item, tags=("selected",))
        self._update_selected_count()

    def select_all(self):
        for it in self.tree.get_children():
            if it not in self.checked:
                self.checked.add(it)
                self.tree.set(it, "选中", "☑")
                self.tree.item(it, tags=("selected",))
        self._update_selected_count()

    def deselect_all(self):
        for it in list(self.checked):
            self.checked.remove(it)
            self.tree.set(it, "选中", "☐")
            self.tree.item(it, tags=())
        self._update_selected_count()

    def submit(self):
        if not self.checked:
            messagebox.showwarning("提示", "请先勾选至少一条记录！")
            return

        # 1) 先一次性读取所有被勾选项的单号
        orders = [
            self.tree.set(it, "单号")
            for it in self.checked
            if self.tree.exists(it)
        ]
        if not orders:
            messagebox.showwarning("提示", "没有有效记录可出库！")
            return

        counter = self.entries["出库档口"].get()
        tracking_number = self.entries["快递单号"].get()
        outbound_quantity_str = self.entries["出库数量"].get().strip()
        
        if not counter:
            messagebox.showwarning("提示", "请选择出库档口！")
            return
        if not tracking_number:
            messagebox.showwarning("提示", "请输入快递单号！")
            return

        # 2) 处理出库
        cnt = 0
        for order in orders:
            if outbound_quantity_str:  # 分数量出库
                try:
                    outbound_quantity = int(outbound_quantity_str)
                    if outbound_quantity <= 0:
                        messagebox.showwarning("提示", "出库数量必须大于0！")
                        return
                    if self.controller.handle_partial_outbound(order, outbound_quantity, tracking_number, counter):
                        cnt += 1
                    else:
                        messagebox.showwarning("提示", f"单号 {order} 出库失败，可能是数量不足或数据错误！")
                        return
                except ValueError:
                    messagebox.showwarning("提示", "出库数量必须是有效的整数！")
                    return
            else:  # 全部出库（原有逻辑）
                updated = {
                    '出库状态': '全部出库',
                    '出库档口': counter,
                    '快递单号': tracking_number,
                    '剩余数量': '0',
                    '剩余价值': '0.00',
                    '利润': ''
                }
                if self.controller.model.update_record(order, updated):
                    cnt += 1

        messagebox.showinfo("提示", f"共处理出库 {cnt} 条记录")

        # 3) 清空输入与勾选
        for w in self.entries.values():
            if isinstance(w, ttk.Entry):
                w.delete(0, tk.END)
            elif isinstance(w, ttk.Combobox):
                w.set('')
        self.checked.clear()
        self._update_selected_count()

        # 4) 最后统一刷新所有页面
        self.controller.refresh_inventory_list()

    def update_inventory_list(self, recs):
        # 统计相同"入库快递单号"条数用于高亮
        counts = {}
        for r in recs:
            # 只显示有剩余数量的记录
            remaining_qty = int(r.get('剩余数量', '') or r.get('商品数量', '0'))
            if remaining_qty > 0:
                key = r.get("入库快递单号", "")
                counts[key] = counts.get(key, 0) + 1

        self.tree.delete(*self.tree.get_children())
        self.checked.clear()
        
        # 保存原始数据用于搜索
        self.all_records = []
        
        # 获取当前显示的列
        display_cols = self.controller.settings_model.get_display_columns('outbound')
        if not display_cols:
            display_cols = ["选中", "单号", "商品名称", "商品数量", "剩余数量", "剩余价值", "颜色/配置", "货商姓名", "入库时间"]
        
        for r in recs:
            # 只显示有剩余数量的记录
            remaining_qty = int(r.get('剩余数量', '') or r.get('商品数量', '0'))
            if remaining_qty <= 0:
                continue
                
            # 保存记录用于搜索
            self.all_records.append(r)
            
            tag = ("selected",) if counts.get(r.get("入库快递单号", ""), 0) > 1 else ()
            # 计算剩余数量和剩余价值
            remaining_qty_str = r.get('剩余数量', '') or r.get('商品数量', '')
            remaining_value = r.get('剩余价值', '') or r.get('结算价', '')
            
            # 根据配置的列构建显示数据
            vals = []
            for col in display_cols:
                if col == "选中":
                    vals.append("☐")
                elif col == "剩余数量":
                    vals.append(remaining_qty_str)
                elif col == "剩余价值":
                    vals.append(remaining_value)
                else:
                    vals.append(r.get(col, ""))
            
            self.tree.insert("", tk.END, values=tuple(vals), tags=tag)
        self._update_selected_count()
    
    def refresh_columns(self):
        """刷新表格列显示配置"""
        # 获取新的列配置
        display_cols = self.controller.settings_model.get_display_columns('outbound')
        if not display_cols:
            display_cols = ["选中", "单号", "商品名称", "商品数量", "剩余数量", "剩余价值", "颜色/配置", "货商姓名", "入库时间"]
        
        # 重新配置表格列
        self.tree.configure(columns=display_cols)
        for c in display_cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100, anchor="center")
        if "选中" in display_cols:
            self.tree.column("选中", width=50)
        
        # 刷新数据
        records = self.controller.model.get_all_records()
        self.update_inventory_list(records)

    def update_counter_list(self, lst):
        cb = self.entries.get('出库档口')
        if isinstance(cb, ttk.Combobox):
            cb['values'] = lst
            cb['height'] = min(10, len(lst))  # 动态调整高度，最大显示10个
            if lst:
                cb.current(0)
                
    def search_inventory(self):
        """搜索库存记录"""
        search_text = self.ent_search.get().strip().lower()
        if not search_text:
            # 如果搜索框为空，显示所有记录
            self.tree.delete(*self.tree.get_children())
            self.checked.clear()
            
            for r in self.all_records:
                # 获取当前显示的列
                display_cols = self.controller.settings_model.get_display_columns('outbound')
                if not display_cols:
                    display_cols = ["选中", "单号", "商品名称", "商品数量", "剩余数量", "剩余价值", "颜色/配置", "货商姓名", "入库时间"]
                
                # 根据配置的列构建显示数据
                vals = []
                for col in display_cols:
                    if col == "选中":
                        vals.append("☐")
                    elif col == "剩余数量":
                        vals.append(r.get('剩余数量', '') or r.get('商品数量', ''))
                    elif col == "剩余价值":
                        vals.append(r.get('剩余价值', '') or r.get('结算价', ''))
                    else:
                        vals.append(r.get(col, ""))
                vals = tuple(vals)
                self.tree.insert("", tk.END, values=vals)
            self._update_selected_count()
            return
            
        # 清空当前显示
        self.tree.delete(*self.tree.get_children())
        self.checked.clear()
        
        # 搜索所有字段
        for r in self.all_records:
            # 检查所有相关字段
            found = False
            for field in ["单号", "商品名称", "颜色/配置", "货商姓名", "入库时间", "入库快递单号"]:
                value = str(r.get(field, "")).lower()
                if search_text in value:
                    found = True
                    break
                    
            # 如果启用了拼音搜索，还检查拼音首字母
            if not found and _HAS_PYPINYIN:
                for field in ["商品名称", "货商姓名"]:
                    value = r.get(field, "")
                    if value:
                        pinyin_initials = ''.join([p[0] for p in lazy_pinyin(value)])
                        if search_text in pinyin_initials.lower():
                            found = True
                            break
            
            if found:
                # 获取当前显示的列
                display_cols = self.controller.settings_model.get_display_columns('outbound')
                if not display_cols:
                    display_cols = ["选中", "单号", "商品名称", "商品数量", "剩余数量", "剩余价值", "颜色/配置", "货商姓名", "入库时间"]
                
                # 根据配置的列构建显示数据
                vals = []
                for col in display_cols:
                    if col == "选中":
                        vals.append("☐")
                    elif col == "剩余数量":
                        vals.append(r.get('剩余数量', '') or r.get('商品数量', ''))
                    elif col == "剩余价值":
                        vals.append(r.get('剩余价值', '') or r.get('结算价', ''))
                    else:
                        vals.append(r.get(col, ""))
                vals = tuple(vals)
                self.tree.insert("", tk.END, values=vals)
                
        self._update_selected_count()

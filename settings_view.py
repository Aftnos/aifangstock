import tkinter as tk
from tkinter import ttk, messagebox, simpledialog as sd

class SettingsView(ttk.Frame):
    def __init__(self, parent, settings_model, controller):
        super().__init__(parent)
        self.settings_model = settings_model
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        self.nb = ttk.Notebook(self)
        self.nb.add(self._create_suppliers_page(), text="供应商")
        self.nb.add(self._create_counters_page(), text="出库档口")
        self.nb.add(self._create_tables_page(), text="记录表")
        self.nb.add(self._create_mapping_page(), text="条形码映射")
        self.nb.add(self._create_column_display_page(), text="表格列显示")
        self.nb.pack(fill=tk.BOTH, expand=True)

    # --- 供应商页 ---
    def _create_suppliers_page(self):
        page = ttk.Frame(self.nb)
        cols = ("供应商",)
        self.sup_tree = ttk.Treeview(page, columns=cols, show="headings", height=10)
        self.sup_tree.heading("供应商", text="供应商")
        self.sup_tree.column("供应商", width=200, anchor="center")
        self.sup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        vsb = ttk.Scrollbar(page, orient="vertical", command=self.sup_tree.yview)
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=5)
        self.sup_tree.configure(yscrollcommand=vsb.set)

        btn_fr = ttk.Frame(page)
        btn_fr.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Button(btn_fr, text="新增供应商", command=self._on_add_supplier).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="修改供应商", command=self._on_edit_supplier).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="删除供应商", command=self._on_delete_supplier).pack(side=tk.LEFT, padx=5)

        self._refresh_suppliers()
        return page

    def _refresh_suppliers(self):
        self.sup_tree.delete(*self.sup_tree.get_children())
        for s in self.settings_model.get_suppliers():
            self.sup_tree.insert("", tk.END, values=(s,))

    def _on_add_supplier(self):
        name = sd.askstring("新增供应商", "请输入供应商名称：", parent=self)
        if name:
            self.settings_model.add_supplier(name)
            self._refresh_suppliers()
            self.controller.refresh_supplier_list()

    def _on_edit_supplier(self):
        sel = self.sup_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一条供应商")
            return
        old = self.sup_tree.item(sel[0], "values")[0]
        new = sd.askstring("修改供应商", "供应商名称：", initialvalue=old, parent=self)
        if new:
            self.settings_model.update_supplier(old, new)
            self._refresh_suppliers()
            self.controller.refresh_supplier_list()

    def _on_delete_supplier(self):
        sel = self.sup_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一条供应商")
            return
        name = self.sup_tree.item(sel[0], "values")[0]
        if messagebox.askyesno("确认", f"删除供应商 {name}？"):
            self.settings_model.delete_supplier(name)
            self._refresh_suppliers()
            self.controller.refresh_supplier_list()

    # --- 出库档口页 ---
    def _create_counters_page(self):
        page = ttk.Frame(self.nb)
        cols = ("档口",)
        self.cnt_tree = ttk.Treeview(page, columns=cols, show="headings", height=10)
        self.cnt_tree.heading("档口", text="档口")
        self.cnt_tree.column("档口", width=200, anchor="center")
        self.cnt_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        vsb = ttk.Scrollbar(page, orient="vertical", command=self.cnt_tree.yview)
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=5)
        self.cnt_tree.configure(yscrollcommand=vsb.set)

        btn_fr = ttk.Frame(page)
        btn_fr.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Button(btn_fr, text="新增档口", command=self._on_add_counter).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="修改档口", command=self._on_edit_counter).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="删除档口", command=self._on_delete_counter).pack(side=tk.LEFT, padx=5)

        self._refresh_counters()
        return page

    def _refresh_counters(self):
        self.cnt_tree.delete(*self.cnt_tree.get_children())
        for c in self.settings_model.get_counters():
            self.cnt_tree.insert("", tk.END, values=(c,))

    def _on_add_counter(self):
        name = sd.askstring("新增档口", "请输入档口名称：", parent=self)
        if name:
            self.settings_model.add_counter(name)
            self._refresh_counters()
            self.controller.refresh_counter_list()

    def _on_edit_counter(self):
        sel = self.cnt_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一条档口")
            return
        old = self.cnt_tree.item(sel[0], "values")[0]
        new = sd.askstring("修改档口", "档口名称：", initialvalue=old, parent=self)
        if new:
            self.settings_model.update_counter(old, new)
            self._refresh_counters()
            self.controller.refresh_counter_list()

    def _on_delete_counter(self):
        sel = self.cnt_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一条档口")
            return
        name = self.cnt_tree.item(sel[0], "values")[0]
        if messagebox.askyesno("确认", f"删除档口 {name}？"):
            self.settings_model.delete_counter(name)
            self._refresh_counters()
            self.controller.refresh_counter_list()

    # --- 记录表页 ---
    def _create_tables_page(self):
        page = ttk.Frame(self.nb)
        cols = ("表名",)
        self.tbl_tree = ttk.Treeview(page, columns=cols, show="headings", height=10)
        self.tbl_tree.heading("表名", text="表名")
        self.tbl_tree.column("表名", width=200, anchor="center")
        self.tbl_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        vsb = ttk.Scrollbar(page, orient="vertical", command=self.tbl_tree.yview)
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=5)
        self.tbl_tree.configure(yscrollcommand=vsb.set)

        btn_fr = ttk.Frame(page)
        btn_fr.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Button(btn_fr, text="新增表",    command=self._on_add_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="重命名表", command=self._on_rename_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="删除表",    command=self._on_delete_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="切换表",    command=self._on_switch_table).pack(side=tk.LEFT, padx=5)

        self._refresh_tables()
        return page

    def _refresh_tables(self):
        self.tbl_tree.delete(*self.tbl_tree.get_children())
        for t in self.settings_model.get_tables():
            prefix = "✓ " if t == self.settings_model.get_active_table() else ""
            self.tbl_tree.insert("", tk.END, values=(prefix + t,))

    def _on_add_table(self):
        name = sd.askstring("新增表", "请输入表名：", parent=self)
        if name:
            self.settings_model.add_table(name)
            self._refresh_tables()

    def _on_rename_table(self):
        sel = self.tbl_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一张表")
            return
        old = self.tbl_tree.item(sel[0], "values")[0].lstrip("✓ ").strip()
        new = sd.askstring("重命名表", "新表名：", initialvalue=old, parent=self)
        if new:
            self.settings_model.rename_table(old, new)
            self._refresh_tables()

    def _on_delete_table(self):
        sel = self.tbl_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一张表")
            return
        name = self.tbl_tree.item(sel[0], "values")[0].lstrip("✓ ").strip()
        if messagebox.askyesno("确认", f"删除表 {name}？"):
            self.settings_model.delete_table(name)
            self._refresh_tables()

    def _on_switch_table(self):
        sel = self.tbl_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一张表")
            return
        name = self.tbl_tree.item(sel[0], "values")[0].lstrip("✓ ").strip()
        self.settings_model.set_active_table(name)
        self.controller.switch_table(name)
        self._refresh_tables()

    # --- 条形码映射页 ---
    def _create_mapping_page(self):
        page = ttk.Frame(self.nb)
        cols = ("条形码", "产品名称")
        self.map_tree = ttk.Treeview(page, columns=cols, show="headings", height=10)
        for c in cols:
            self.map_tree.heading(c, text=c)
            self.map_tree.column(c, width=200, anchor="center")
        self.map_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        vsb = ttk.Scrollbar(page, orient="vertical", command=self.map_tree.yview)
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=5)
        self.map_tree.configure(yscrollcommand=vsb.set)

        btn_fr = ttk.Frame(page)
        btn_fr.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Button(btn_fr, text="新增映射", command=self._on_add_mapping).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="修改映射", command=self._on_edit_mapping).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="删除映射", command=self._on_delete_mapping).pack(side=tk.LEFT, padx=5)

        self._refresh_mapping_list()
        return page

    def _refresh_mapping_list(self):
        self.map_tree.delete(*self.map_tree.get_children())
        for code, prod in self.settings_model.get_barcode_mappings():
            self.map_tree.insert("", tk.END, values=(code, prod))

    def _on_add_mapping(self):
        code = sd.askstring("新增映射", "请输入条形码：", parent=self)
        if not code:
            return
        prod = sd.askstring("新增映射", "请输入产品名称：", parent=self)
        if not prod:
            return
        self.settings_model.add_barcode_mapping(code, prod)
        self._refresh_mapping_list()

    def _on_edit_mapping(self):
        sel = self.map_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一条映射")
            return
        old_code, old_prod = self.map_tree.item(sel[0], "values")
        new_code = sd.askstring("修改映射", "条形码：", initialvalue=old_code, parent=self)
        if not new_code:
            return
        new_prod = sd.askstring("修改映射", "产品名称：", initialvalue=old_prod, parent=self)
        if not new_prod:
            return
        self.settings_model.update_barcode_mapping(old_code, new_code, new_prod)
        self._refresh_mapping_list()

    def _on_delete_mapping(self):
        sel = self.map_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择一条映射")
            return
        code = self.map_tree.item(sel[0], "values")[0]
        if messagebox.askyesno("确认", f"删除条形码 {code} 的映射？"):
            self.settings_model.delete_barcode_mapping(code)
            self._refresh_mapping_list()

    # --- 表格列显示配置页 ---
    def _create_column_display_page(self):
        page = ttk.Frame(self.nb)
        
        # 页面类型选择
        type_frame = ttk.Frame(page)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(type_frame, text="页面类型:").pack(side=tk.LEFT, padx=5)
        self.cb_page_type = ttk.Combobox(type_frame, values=[
            "入库登记页", "出库登记页", "数据查询页"
        ], state="readonly", width=20)
        self.cb_page_type.pack(side=tk.LEFT, padx=5)
        self.cb_page_type.bind("<<ComboboxSelected>>", self._on_page_type_change)
        self.cb_page_type.current(0)
        
        # 列配置区域
        config_frame = ttk.Frame(page)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 可用列列表
        left_frame = ttk.Frame(config_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        ttk.Label(left_frame, text="可用列:").pack(anchor="w")
        self.available_listbox = tk.Listbox(left_frame, selectmode=tk.MULTIPLE, height=15)
        self.available_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 中间按钮
        middle_frame = ttk.Frame(config_frame)
        middle_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(middle_frame, text="→", command=self._add_column).pack(pady=5)
        ttk.Button(middle_frame, text="←", command=self._remove_column).pack(pady=5)
        ttk.Button(middle_frame, text="↑", command=self._move_up).pack(pady=5)
        ttk.Button(middle_frame, text="↓", command=self._move_down).pack(pady=5)
        
        # 显示列列表
        right_frame = ttk.Frame(config_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0))
        ttk.Label(right_frame, text="显示列:").pack(anchor="w")
        self.display_listbox = tk.Listbox(right_frame, selectmode=tk.SINGLE, height=15)
        self.display_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮
        btn_frame = ttk.Frame(page)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="保存配置", command=self._save_column_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重置默认", command=self._reset_column_config).pack(side=tk.LEFT, padx=5)
        
        # 初始化显示
        self._refresh_column_config()
        
        return page
    
    def _get_page_type_key(self):
        """获取当前选择的页面类型对应的键"""
        type_map = {
            "入库登记页": "inbound",
            "出库登记页": "outbound", 
            "数据查询页": "data_query"
        }
        return type_map.get(self.cb_page_type.get(), "inbound")
    
    def _on_page_type_change(self, event=None):
        """页面类型改变时刷新列配置"""
        self._refresh_column_config()
    
    def _refresh_column_config(self):
        """刷新列配置显示"""
        page_type = self._get_page_type_key()
        
        # 获取所有可用列和当前显示列
        available_columns = self.settings_model.get_available_columns(page_type)
        display_columns = self.settings_model.get_display_columns(page_type)
        
        # 更新可用列列表（排除已显示的列）
        self.available_listbox.delete(0, tk.END)
        for col in available_columns:
            if col not in display_columns:
                self.available_listbox.insert(tk.END, col)
        
        # 更新显示列列表
        self.display_listbox.delete(0, tk.END)
        for col in display_columns:
            self.display_listbox.insert(tk.END, col)
    
    def _add_column(self):
        """添加选中的列到显示列表"""
        selection = self.available_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请选择要添加的列")
            return
        
        # 获取选中的列
        selected_columns = [self.available_listbox.get(i) for i in selection]
        
        # 添加到显示列表
        for col in selected_columns:
            self.display_listbox.insert(tk.END, col)
        
        # 从可用列表中移除
        for i in reversed(selection):
            self.available_listbox.delete(i)
    
    def _remove_column(self):
        """从显示列表中移除选中的列"""
        selection = self.display_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请选择要移除的列")
            return
        
        # 获取选中的列
        selected_column = self.display_listbox.get(selection[0])
        
        # 从显示列表中移除
        self.display_listbox.delete(selection[0])
        
        # 添加到可用列表
        self.available_listbox.insert(tk.END, selected_column)
    
    def _move_up(self):
        """向上移动选中的显示列"""
        selection = self.display_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        index = selection[0]
        item = self.display_listbox.get(index)
        self.display_listbox.delete(index)
        self.display_listbox.insert(index - 1, item)
        self.display_listbox.selection_set(index - 1)
    
    def _move_down(self):
        """向下移动选中的显示列"""
        selection = self.display_listbox.curselection()
        if not selection or selection[0] == self.display_listbox.size() - 1:
            return
        
        index = selection[0]
        item = self.display_listbox.get(index)
        self.display_listbox.delete(index)
        self.display_listbox.insert(index + 1, item)
        self.display_listbox.selection_set(index + 1)
    
    def _save_column_config(self):
        """保存列配置"""
        page_type = self._get_page_type_key()
        display_columns = [self.display_listbox.get(i) for i in range(self.display_listbox.size())]
        
        if not display_columns:
            messagebox.showwarning("提示", "至少需要显示一列")
            return
        
        self.settings_model.set_display_columns(page_type, display_columns)
        
        # 通知控制器刷新相关页面
        if hasattr(self.controller, 'refresh_column_display'):
            self.controller.refresh_column_display(page_type)
        
        messagebox.showinfo("成功", "列配置已保存并应用！")
    
    def _reset_column_config(self):
        """重置为默认列配置"""
        if not messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            return
        
        page_type = self._get_page_type_key()
        
        # 设置默认列配置
        if page_type == 'inbound':
            default_columns = ['入库快递单号', '货商姓名', '商品名称', '商品数量', '入库时间', '颜色/配置']
        elif page_type == 'outbound':
            default_columns = ['选中', '单号', '商品名称', '商品数量', '剩余数量', '剩余价值', '颜色/配置', '货商姓名', '入库时间']
        else:  # data_query
            default_columns = ['单号', '货商姓名', '入库时间', '商品名称', '商品数量', '买价', '佣金', '结算价', '出库状态']
        
        self.settings_model.set_display_columns(page_type, default_columns)
        self._refresh_column_config()
        
        # 刷新对应页面的列显示
        if hasattr(self.controller, 'refresh_column_display'):
            self.controller.refresh_column_display(page_type)
        
        messagebox.showinfo("成功", "已重置为默认配置并应用！")

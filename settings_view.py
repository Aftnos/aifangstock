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

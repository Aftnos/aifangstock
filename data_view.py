import tkinter as tk
from tkinter import ttk
from datetime import datetime

class DataView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller

        # 当前查询用到的列和数据
        self.columns = []
        self.orig = []  # 原始数据字典列表
        self.full = []  # 应用筛选或排序后的数据

        self.sort_states = {}  # 各列排序状态：True=升序，False=降序

        self.create_widgets()

    def create_widgets(self):
        # 查询类型区
        ttk.Label(self, text="查询类型:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.cb = ttk.Combobox(self, values=[
            "全部库存",
            "按商品统计盈亏",
            "按货商统计盈亏",
            "快递单号查询",
            "按货商的入库次数"
        ], state="readonly", width=20)
        self.cb.current(0)
        self.cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cb.bind("<<ComboboxSelected>>", self.on_q)

        self.lbl_cond = ttk.Label(self, text="查询条件:")
        self.lbl_cond.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.ent_cond = ttk.Entry(self, width=20)
        self.ent_cond.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.ent_cond.bind("<Return>", lambda e: self.exec_q())

        ttk.Button(self, text="查询", command=self.exec_q).grid(row=0, column=4, padx=5, pady=5)
        self.on_q()

        # 结果表格
        self.tree = ttk.Treeview(self, show="headings")
        self.tree.grid(row=1, column=0, columnspan=5, sticky="nsew")
        # 仅“出库状态”列上色
        self.tree.tag_configure('outbound', foreground='green')
        self.tree.tag_configure('inbound',  foreground='blue')

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.grid(row=1, column=5, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=2, column=0, columnspan=5, sticky="ew")
        self.tree.configure(xscrollcommand=hsb.set)

        # 筛选区
        self.filter_canvas = tk.Canvas(self, height=60)
        self.filter_canvas.grid(row=3, column=0, columnspan=5, sticky="ew")
        fhsb = ttk.Scrollbar(self, orient="horizontal", command=self.filter_canvas.xview)
        fhsb.grid(row=4, column=0, columnspan=5, sticky="ew")
        self.filter_canvas.configure(xscrollcommand=fhsb.set)
        self.filter_inner = ttk.Frame(self.filter_canvas)
        self.filter_canvas.create_window((0,0), window=self.filter_inner, anchor="nw")
        self.filter_inner.bind(
            "<Configure>",
            lambda e: self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
        )
        self.filter_entries = {}
        self.create_filter_row()

        # 指标显示区
        self.lbl_sold_profit      = ttk.Label(self, text="卖出总利润: 0.00")
        self.lbl_inventory_value  = ttk.Label(self, text="库存价值: 0.00")
        self.lbl_shipping_cost    = ttk.Label(self, text="快递总费用: 0.00")
        self.lbl_commission_cost  = ttk.Label(self, text="佣金总费用: 0.00")
        self.lbl_unsettled_amount = ttk.Label(self, text="未结清金额: 0.00")
        self.lbl_total_market     = ttk.Label(self, text="行情价总和: 0.00")
        self.lbl_total_rows       = ttk.Label(self, text="总条数: 0")
        self.lbl_total_qty        = ttk.Label(self, text="商品数量总和: 0.00")

        self.lbl_sold_profit     .grid(row=5, column=0, columnspan=5, sticky="w", pady=(10,0))
        self.lbl_inventory_value.grid(row=6, column=0, columnspan=5, sticky="w")
        self.lbl_shipping_cost  .grid(row=7, column=0, columnspan=5, sticky="w")
        self.lbl_commission_cost.grid(row=8, column=0, columnspan=5, sticky="w")
        self.lbl_unsettled_amount.grid(row=9, column=0, columnspan=5, sticky="w")
        self.lbl_total_market   .grid(row=10, column=0, columnspan=5, sticky="w")
        self.lbl_total_rows     .grid(row=11, column=0, columnspan=5, sticky="w")
        self.lbl_total_qty      .grid(row=12, column=0, columnspan=5, sticky="w")

        # 布局权重
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(4, weight=1)

    def create_filter_row(self):
        for w in self.filter_inner.winfo_children():
            w.destroy()
        self.filter_entries.clear()
        if not self.columns:
            return
        for i, c in enumerate(self.columns):
            ttk.Label(self.filter_inner, text=c).grid(row=0, column=i, padx=2, pady=2)
            e = ttk.Entry(self.filter_inner, width=10)
            e.grid(row=1, column=i, padx=2, pady=2)
            e.bind("<Return>", lambda ev: self.apply_filters())
            self.filter_entries[c] = e
        idx = len(self.columns)
        ttk.Button(self.filter_inner, text="应用筛选", command=self.apply_filters)\
            .grid(row=1, column=idx, padx=5)
        ttk.Button(self.filter_inner, text="清空筛选条件", command=self.clear_filters)\
            .grid(row=1, column=idx+1, padx=5)

    def on_q(self, event=None):
        q = self.cb.get()
        if q in ["全部库存", "按商品统计盈亏", "按货商统计盈亏", "按货商的入库次数"]:
            self.ent_cond.delete(0, tk.END)
            self.ent_cond.config(state="disabled")
            self.lbl_cond.config(text="查询条件:")
        else:
            self.ent_cond.config(state="normal")
            self.lbl_cond.config(text="快递单号:")

    def exec_q(self):
        q = self.cb.get()
        c = self.ent_cond.get().strip()
        if q == "全部库存":
            self.controller.view_all_inventory_unified()
        elif q == "按商品统计盈亏":
            self.controller.view_profit_by_product_unified()
        elif q == "按货商统计盈亏":
            self.controller.view_profit_by_supplier_unified()
        elif q == "按货商的入库次数":
            self.controller.view_inbound_count_by_supplier_unified()
        else:
            self.controller.view_by_tracking_number_unified(c)

    def display_results(self, cols, data):
        # 保存列和原始数据
        self.columns = list(cols)
        self.orig = [dict(zip(cols, row)) for row in data]
        # 计算利润
        for d in self.orig:
            try:
                p = float(d.get("行情价格","0") or 0) - float(d.get("结算价","0") or 0)
                d["利润"] = f"{p:.2f}"
            except:
                d["利润"] = ""
        self.full = list(self.orig)

        # 默认按照入库时间降序排列
        if '入库时间' in self.columns:
            self.full.sort(key=lambda d: self._parse_datetime(
                d.get('入库时间', '0000-01-01 00:00:00')
            ), reverse=True)

        # 重建表头
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = self.columns
        self.sort_states = {c: True for c in self.columns}
        for c in self.columns:
            self.tree.heading(c, text=c, command=lambda c=c: self.sort_by(c))
            self.tree.column(c, width=100, anchor="center")

        # 插入数据并上色“出库状态”
        for d in self.full:
            vals = [d.get(c,"") for c in self.columns]
            status = d.get("出库状态","")
            tag = "outbound" if status == "卖出" else "inbound"
            self.tree.insert("", tk.END, values=vals, tags=(tag,))

        # 重建筛选区
        self.create_filter_row()

        # 更新指标
        self.update_metrics()

    def update_current_data(self, cols, data):
        # 保留当前筛选条件，只替换数据
        self.columns = list(cols)
        self.orig = [dict(zip(cols, row)) for row in data]
        for d in self.orig:
            try:
                p = float(d.get("行情价格","0") or 0) - float(d.get("结算价","0") or 0)
                d["利润"] = f"{p:.2f}"
            except:
                d["利润"] = ""
        self.full = list(self.orig)
        # 默认按入库时间降序
        if '入库时间' in self.columns:
            self.full.sort(key=lambda d: self._parse_datetime(
                d.get('入库时间', '0000-01-01 00:00:00')
            ), reverse=True)
        # 重绘行
        self.tree.delete(*self.tree.get_children())
        for d in self.full:
            vals = [d.get(c,"") for c in self.columns]
            status = d.get("出库状态","")
            tag = "outbound" if status == "卖出" else "inbound"
            self.tree.insert("", tk.END, values=vals, tags=(tag,))
        # 重新应用筛选条件
        self.apply_filters()

    def apply_filters(self):
        filtered = []
        for d in self.orig:
            ok = True
            for c, e in self.filter_entries.items():
                v = e.get().strip().lower()
                if v and v not in str(d.get(c,"")).lower():
                    ok = False
                    break
            if ok:
                filtered.append(d)
        self.full = filtered
        self.tree.delete(*self.tree.get_children())
        for d in self.full:
            vals = [d.get(c,"") for c in self.columns]
            status = d.get("出库状态","")
            tag = "outbound" if status == "卖出" else "inbound"
            self.tree.insert("", tk.END, values=vals, tags=(tag,))
        self.update_metrics()

    def clear_filters(self):
        for e in self.filter_entries.values():
            e.delete(0, tk.END)
        self.apply_filters()

    def sort_by(self, col):
        asc = self.sort_states.get(col, True)
        try:
            self.full.sort(key=lambda x: float(x.get(col,"") or 0), reverse=not asc)
        except:
            self.full.sort(key=lambda x: x.get(col,""), reverse=not asc)
        self.sort_states[col] = not asc
        self.tree.delete(*self.tree.get_children())
        for d in self.full:
            vals = [d.get(c,"") for c in self.columns]
            status = d.get("出库状态","")
            tag = "outbound" if status == "卖出" else "inbound"
            self.tree.insert("", tk.END, values=vals, tags=(tag,))

    def _parse_datetime(self, date_str):
        """解析多种格式的日期字符串"""
        formats = [
            "%Y-%m-%d %H:%M:%S",  # 带秒的完整格式
            "%Y-%m-%d %H:%M",     # 不带秒的格式
            "%Y-%m-%d"           # 只有日期的格式
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # 如果所有格式都失败，返回一个很早的日期作为默认值
        return datetime(1900, 1, 1)
        
    def update_metrics(self):
        sold_profit = inventory_value = shipping_cost = commission_cost = unsettled_amount = 0.0
        total_market = total_qty = 0.0
        for d in self.full:
            try: commission_cost += float(d.get('佣金','0') or 0)
            except: pass
            if d.get('出库状态') == '卖出':
                try:
                    sale = float(d.get('行情价格','0') or 0)
                    cost = float(d.get('结算价','0') or 0)
                    ship = float(d.get('快递价格','0') or 0)
                    sold_profit   += (sale - cost - ship)
                    shipping_cost += ship
                except: pass
            else:
                try: inventory_value += float(d.get('结算价','0') or 0)
                except: pass
            if d.get('结算状态') == '否':
                try: unsettled_amount += float(d.get('结算价','0') or 0)
                except: pass
            try: total_market += float(d.get('行情价格','0') or 0)
            except: pass
            try: total_qty    += float(d.get('商品数量','0') or 0)
            except: pass

        self.lbl_sold_profit     .config(text=f"卖出总利润: {sold_profit:.2f}")
        self.lbl_inventory_value .config(text=f"库存价值: {inventory_value:.2f}")
        self.lbl_shipping_cost   .config(text=f"快递总费用: {shipping_cost:.2f}")
        self.lbl_commission_cost .config(text=f"佣金总费用: {commission_cost:.2f}")
        self.lbl_unsettled_amount.config(text=f"未结清金额: {unsettled_amount:.2f}")
        self.lbl_total_market    .config(text=f"行情价总和: {total_market:.2f}")
        self.lbl_total_rows      .config(text=f"总条数: {len(self.full)}")
        self.lbl_total_qty       .config(text=f"商品数量总和: {total_qty:.2f}")

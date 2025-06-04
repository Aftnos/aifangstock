import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = ttk.Entry

class ModifyView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        self.selected_order = None
        self.orig = []   # 原始数据列表（dict）
        self.full = []   # 当前显示的数据列表（dict）
        # 列定义
        self.columns = [
            "入库快递单号","货商姓名","入库时间","数字条码","商品名称",
            "商品数量","商品数量单位","颜色/配置","货源","买价",
            "佣金","结算价","行情价格","利润","结算状态",
            "出库状态","出库档口","快递单号","快递价格","备注","单号"
        ]
        # 排序状态
        self.sort_states = {c: True for c in self.columns}

        self.create_widgets()
        self.refresh_list()

    def create_widgets(self):
        # —— 表格区 ——
        tree_fr = ttk.Frame(self)
        tree_fr.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(
            tree_fr,
            columns=self.columns,
            show="headings",
            selectmode="browse"
        )
        for c in self.columns:
            self.tree.heading(c, text=c, command=lambda c=c: self.sort_by(c))
            self.tree.column(c, width=100, anchor="center")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(tree_fr, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        # —— 筛选区 ——
        self.filter_canvas = tk.Canvas(self, height=60)
        self.filter_canvas.pack(fill=tk.X, pady=(5,0))
        fhsb = ttk.Scrollbar(self, orient="horizontal", command=self.filter_canvas.xview)
        fhsb.pack(fill=tk.X)
        self.filter_canvas.configure(xscrollcommand=fhsb.set)
        self.filter_inner = ttk.Frame(self.filter_canvas)
        self.filter_canvas.create_window((0,0), window=self.filter_inner, anchor='nw')
        self.filter_inner.bind("<Configure>", lambda e:
            self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
        )
        # 筛选输入框
        self.filter_entries = {}
        for i, c in enumerate(self.columns):
            ttk.Label(self.filter_inner, text=c).grid(row=0, column=i, padx=2, pady=2)
            e = ttk.Entry(self.filter_inner, width=10)
            e.grid(row=1, column=i, padx=2, pady=2)
            e.bind("<Return>", lambda ev: self.apply_filters())
            self.filter_entries[c] = e
        # 筛选与清空按钮
        ttk.Button(self.filter_inner, text="应用筛选", command=self.apply_filters)\
            .grid(row=1, column=len(self.columns), padx=5)
        ttk.Button(self.filter_inner, text="清空筛选条件", command=self.clear_filters)\
            .grid(row=1, column=len(self.columns)+1, padx=5)

        # —— 操作按钮区 ——
        btn_fr = ttk.Frame(self)
        btn_fr.pack(pady=5)
        ttk.Button(btn_fr, text="加载记录", command=self.load_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_fr, text="刷新列表", command=self.refresh_list).pack(side=tk.LEFT, padx=5)

        # —— 编辑表单（三列布局） ——
        form_fr = ttk.Frame(self)
        form_fr.pack(fill=tk.X, pady=5)
        for col in range(6):
            form_fr.grid_columnconfigure(col, weight=1)

        self.entries = {}
        for idx, field in enumerate(self.columns):
            row = idx // 3
            col = idx % 3
            ttk.Label(form_fr, text=field).grid(
                row=row, column=col*2, sticky="e", padx=5, pady=2
            )
            if field in ("单号","利润"):
                w = ttk.Entry(form_fr, width=20, state="readonly")
                w.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)
            elif field == "货商姓名":
                w = ttk.Combobox(
                    form_fr,
                    values=self.controller.settings_model.get_suppliers(),
                    state="readonly", width=18
                )
                w.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)
            elif field == "入库时间":
                inner = ttk.Frame(form_fr)
                if DateEntry is ttk.Entry:
                    date_ent = ttk.Entry(inner, width=10)
                else:
                    date_ent = DateEntry(inner, date_pattern='yyyy-MM-dd', width=10)
                date_ent.pack(side=tk.LEFT)
                cb_h = ttk.Combobox(inner, values=[f"{i:02d}" for i in range(24)],
                                    width=3, state="readonly"); cb_h.current(0); cb_h.pack(side=tk.LEFT)
                ttk.Label(inner, text=":").pack(side=tk.LEFT)
                cb_m = ttk.Combobox(inner, values=[f"{i:02d}" for i in range(60)],
                                    width=3, state="readonly"); cb_m.current(0); cb_m.pack(side=tk.LEFT)
                ttk.Label(inner, text=":").pack(side=tk.LEFT)
                cb_s = ttk.Combobox(inner, values=[f"{i:02d}" for i in range(60)],
                                    width=3, state="readonly"); cb_s.current(0); cb_s.pack(side=tk.LEFT)
                ttk.Button(
                    inner, text="现在时间",
                    command=lambda de=date_ent, h=cb_h, m=cb_m, s=cb_s: self.set_now(de, h, m, s)
                ).pack(side=tk.LEFT, padx=(5,0))
                inner.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)
                w = (date_ent, cb_h, cb_m, cb_s)
            elif field in ("结算状态","出库状态"):
                vals = ["是","否"] if field=="结算状态" else ["未出库","卖出"]
                w = ttk.Combobox(form_fr, values=vals, state="readonly", width=18)
                w.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)
            elif field == "出库档口":
                w = ttk.Combobox(
                    form_fr,
                    values=self.controller.settings_model.get_counters(),
                    state="readonly", width=18
                )
                w.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)
            else:
                w = ttk.Entry(form_fr, width=20)
                w.grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)
            self.entries[field] = w

        # —— 保存 & 删除 ——
        op_fr = ttk.Frame(self)
        op_fr.pack(pady=10)
        ttk.Button(op_fr, text="保存修改", command=self.save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(op_fr, text="删除记录", command=self.delete_record).pack(side=tk.LEFT, padx=5)

    def set_now(self, date_ent, cb_h, cb_m, cb_s):
        now = datetime.now()
        if isinstance(date_ent, ttk.Entry):
            date_ent.delete(0, tk.END)
            date_ent.insert(0, now.strftime("%Y-%m-%d"))
        else:
            date_ent.set_date(now)
        cb_h.set(f"{now.hour:02d}")
        cb_m.set(f"{now.minute:02d}")
        cb_s.set(f"{now.second:02d}")

    def get_datetime_str(self, date_ent, cb_h, cb_m, cb_s):
        return f"{date_ent.get()} {cb_h.get()}:{cb_m.get()}:{cb_s.get()}"

    def refresh_list(self):
        # 重新加载原始数据，但不清空筛选条件
        recs = self.controller.model.get_all_records()
        self.orig = []
        for r in recs:
            d = r.copy()
            try:
                profit = float(d.get('行情价格','0') or 0) - float(d.get('结算价','0') or 0)
                d['利润'] = f"{profit:.2f}"
            except:
                d['利润'] = ''
            self.orig.append(d)
        # 先让 full 等于 orig，再应用当前筛选
        self.full = list(self.orig)
        self.apply_filters()

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for d in self.full:
            vals = tuple(d.get(c,"") for c in self.columns)
            self.tree.insert("", tk.END, values=vals)

    def apply_filters(self):
        # 根据 filter_entries 过滤 orig 到 full
        self.full = []
        for d in self.orig:
            ok = True
            for c, e in self.filter_entries.items():
                v = e.get().strip().lower()
                if v and v not in str(d.get(c,"")).lower():
                    ok = False
                    break
            if ok:
                self.full.append(d)
        # 如果之前有排序状态，保留当前排序
        # 找到最后一次点击排序的列（可自行扩展），这里简单不变
        self.populate_tree()

    def clear_filters(self):
        for e in self.filter_entries.values():
            e.delete(0, tk.END)
        self.apply_filters()

    def sort_by(self, col):
        asc = self.sort_states[col]
        try:
            self.full.sort(key=lambda x: float(x.get(col,"") or 0), reverse=not asc)
        except:
            self.full.sort(key=lambda x: x.get(col,""), reverse=not asc)
        self.sort_states[col] = not asc
        self.populate_tree()

    def load_record(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示","请选择一条记录加载")
            return
        vals = self.tree.item(sel[0], "values")
        for i, field in enumerate(self.columns):
            w = self.entries[field]
            v = vals[i]
            # 同原有逻辑：设置到各个控件
            if field in ("单号","利润"):
                w.config(state="normal"); w.delete(0,tk.END); w.insert(0,v); w.config(state="readonly")
            elif field == "入库时间":
                de, cb_h, cb_m, cb_s = w
                try:
                    ds, ts = v.split(" "); h,m,s = ts.split(":")
                except:
                    ds, h, m, s = v, "00","00","00"
                if isinstance(de, ttk.Entry):
                    de.delete(0, tk.END); de.insert(0, ds)
                else:
                    de.set_date(datetime.strptime(ds, "%Y-%m-%d"))
                cb_h.set(h); cb_m.set(m); cb_s.set(s)
            elif isinstance(w, ttk.Combobox):
                w.set(v)
            else:
                w.delete(0, tk.END); w.insert(0, v)
        # 重新计算并显示利润
        try:
            settle = float(self.entries['结算价'].get() or 0)
            market = float(self.entries['行情价格'].get() or 0)
            profit = market - settle
            p = self.entries['利润']
            p.config(state="normal"); p.delete(0,tk.END); p.insert(0,f"{profit:.2f}"); p.config(state="readonly")
        except:
            pass
        self.selected_order = vals[-1]

    def save_changes(self):
        if not self.selected_order:
            messagebox.showwarning("提示","请先加载一条记录")
            return
        updated = {}
        for field, w in self.entries.items():
            if field in ("单号","利润"):
                continue
            if field == "入库时间":
                de, cb_h, cb_m, cb_s = w
                updated[field] = self.get_datetime_str(de, cb_h, cb_m, cb_s)
            else:
                updated[field] = w.get()
        if self.controller.handle_modify(self.selected_order, updated):
            messagebox.showinfo("提示","修改成功")
            # 重新加载数据并保留筛选、排序
            self.refresh_list()
        else:
            messagebox.showerror("错误","修改失败")

    def delete_record(self):
        if not self.selected_order:
            messagebox.showwarning("提示","请先加载一条记录")
            return
        if not messagebox.askyesno("确认","确定要删除该记录吗？"):
            return
        if self.controller.handle_delete(self.selected_order):
            messagebox.showinfo("提示","删除成功")
            self.selected_order = None
            # 清空表单
            for field, w in self.entries.items():
                if isinstance(w, tuple):
                    de, cb_h, cb_m, cb_s = w
                    de.delete(0, tk.END)
                    cb_h.set("00"); cb_m.set("00"); cb_s.set("00")
                else:
                    w.config(state="normal"); w.delete(0, tk.END)
                    if field in ("单号","利润"):
                        w.config(state="readonly")
            # 重新加载数据并保留筛选、排序
            self.refresh_list()
        else:
            messagebox.showerror("错误","删除失败")

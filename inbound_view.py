import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = ttk.Entry

# 尝试导入 pypinyin，用于拼音首字母搜索
try:
    from pypinyin import lazy_pinyin, Style
    _HAS_PYPINYIN = True
except ImportError:
    _HAS_PYPINYIN = False

class InboundView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        self.create_widgets()
        self.update_supplier_list(self.controller.settings_model.get_suppliers())
        self.refresh_list()
        self.update_preview()

    def create_widgets(self):
        # 左侧：库存列表
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ("入库快递单号", "货商姓名", "商品名称", "商品数量", "入库时间", "颜色/配置")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100, anchor="center")
        # 重复单号高亮
        self.tree.tag_configure('duplicate', background='lightyellow')
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)
        ttk.Button(left, text="刷新列表", command=self.refresh_list).pack(pady=5)

        # 右侧：表单 + 预览
        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        frm = ttk.Frame(right)
        frm.pack(fill=tk.X, padx=5, pady=5)

        # 搜索供应商（支持回车和拼音首字母）
        ttk.Label(frm, text="搜索供应商:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.ent_sup_search = ttk.Entry(frm, width=28)
        self.ent_sup_search.grid(row=0, column=1, padx=5, pady=3)
        self.ent_sup_search.bind("<Return>", lambda e: self.search_supplier())
        ttk.Button(frm, text="搜索", command=self.search_supplier).grid(row=0, column=2, padx=5, pady=3)
        self.lst_sup_search = tk.Listbox(frm, height=4)
        self.lst_sup_search.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=3)
        self.lst_sup_search.bind("<<ListboxSelect>>", self.on_supplier_select)
        self.lst_sup_search.grid_remove()

        # 货商姓名
        ttk.Label(frm, text="货商姓名:").grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.cb_sup = ttk.Combobox(frm, values=[], state="readonly", width=28)
        self.cb_sup.grid(row=2, column=1, padx=5, pady=3)
        self.cb_sup.bind("<<ComboboxSelected>>", lambda e: self.update_preview())

        # 入库快递单号
        ttk.Label(frm, text="入库快递单号:").grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.ent_in_courier = ttk.Entry(frm, width=30)
        self.ent_in_courier.grid(row=3, column=1, padx=5, pady=3)
        self.ent_in_courier.bind("<KeyRelease>", lambda e: self.update_preview())

        # 条形码
        ttk.Label(frm, text="条形码:").grid(row=4, column=0, sticky="e", padx=5, pady=3)
        self.ent_bar = ttk.Entry(frm, width=30)
        self.ent_bar.grid(row=4, column=1, padx=5, pady=3)
        self.ent_bar.bind("<FocusOut>", self._on_barcode_focus_out)
        self.ent_bar.bind("<KeyRelease>", self._on_barcode_focus_out)

        # 商品名称
        ttk.Label(frm, text="商品名称:").grid(row=5, column=0, sticky="e", padx=5, pady=3)
        self.ent_name = ttk.Entry(frm, width=30)
        self.ent_name.grid(row=5, column=1, padx=5, pady=3)
        self.ent_name.bind("<KeyRelease>", lambda e: self.update_preview())

        # 买价
        ttk.Label(frm, text="买价:").grid(row=6, column=0, sticky="e", padx=5, pady=3)
        self.ent_buy = ttk.Entry(frm, width=30)
        self.ent_buy.grid(row=6, column=1, padx=5, pady=3)
        self.ent_buy.bind("<KeyRelease>", lambda e: self.update_preview())

        # 佣金
        ttk.Label(frm, text="佣金:").grid(row=7, column=0, sticky="e", padx=5, pady=3)
        self.ent_comm = ttk.Entry(frm, width=30)
        self.ent_comm.grid(row=7, column=1, padx=5, pady=3)
        self.ent_comm.bind("<KeyRelease>", lambda e: self.update_preview())

        # 商品数量
        ttk.Label(frm, text="商品数量:").grid(row=8, column=0, sticky="e", padx=5, pady=3)
        self.ent_qty = ttk.Entry(frm, width=30)
        self.ent_qty.grid(row=8, column=1, padx=5, pady=3)
        self.ent_qty.bind("<KeyRelease>", lambda e: self.update_preview())

        # 数量单位
        ttk.Label(frm, text="数量单位:").grid(row=9, column=0, sticky="e", padx=5, pady=3)
        self.ent_unit = ttk.Entry(frm, width=30)
        self.ent_unit.grid(row=9, column=1, padx=5, pady=3)
        self.ent_unit.bind("<KeyRelease>", lambda e: self.update_preview())

        # 颜色/配置
        ttk.Label(frm, text="颜色/配置:").grid(row=10, column=0, sticky="e", padx=5, pady=3)
        self.ent_color = ttk.Entry(frm, width=30)
        self.ent_color.grid(row=10, column=1, padx=5, pady=3)
        self.ent_color.bind("<KeyRelease>", lambda e: self.update_preview())

        # 入库日期 + 时分秒
        ttk.Label(frm, text="入库日期:").grid(row=11, column=0, sticky="e", padx=5, pady=3)
        if DateEntry is ttk.Entry:
            self.date_ent = ttk.Entry(frm, width=12)
        else:
            self.date_ent = DateEntry(frm, date_pattern='yyyy-MM-dd', width=12)
        self.date_ent.grid(row=11, column=1, sticky="w", padx=(5,0), pady=3)
        self.date_ent.bind("<<DateEntrySelected>>", lambda e: self.update_preview())
        self.date_ent.bind("<KeyRelease>", lambda e: self.update_preview())
        tf = ttk.Frame(frm)
        tf.grid(row=11, column=1, sticky="e", padx=(0,5))
        self.cb_hour = ttk.Combobox(tf, values=[f"{i:02d}" for i in range(24)], width=3, state="readonly")
        self.cb_hour.current(0); self.cb_hour.pack(side=tk.LEFT)
        ttk.Label(tf, text=":").pack(side=tk.LEFT)
        self.cb_min = ttk.Combobox(tf, values=[f"{i:02d}" for i in range(60)], width=3, state="readonly")
        self.cb_min.current(0); self.cb_min.pack(side=tk.LEFT)
        ttk.Label(tf, text=":").pack(side=tk.LEFT)
        self.cb_sec = ttk.Combobox(tf, values=[f"{i:02d}" for i in range(60)], width=3, state="readonly")
        self.cb_sec.current(0); self.cb_sec.pack(side=tk.LEFT)
        for cb in (self.cb_hour, self.cb_min, self.cb_sec):
            cb.bind("<<ComboboxSelected>>", lambda e: self.update_preview())
        ttk.Button(frm, text="现在时间", command=self.set_now).grid(row=11, column=2, padx=5, pady=3)

        # 提交按钮
        ttk.Button(frm, text="提交入库", command=self.submit).grid(row=12, column=0, columnspan=3, pady=10)

        # 预览区
        pv = ttk.LabelFrame(right, text="入库信息预览", padding=10)
        pv.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_preview = ttk.Label(pv, text="", justify="left")
        self.lbl_preview.pack(fill=tk.X)

    def _on_barcode_focus_out(self, event=None):
        code = self.ent_bar.get().strip()
        if not code:
            return
        prod = self.controller.settings_model.get_product_name(code)
        if prod:
            self.ent_name.delete(0, tk.END)
            self.ent_name.insert(0, prod)
            self.update_preview()

    def set_now(self):
        now = datetime.now()
        if isinstance(self.date_ent, ttk.Entry):
            self.date_ent.delete(0, tk.END)
            self.date_ent.insert(0, now.strftime("%Y-%m-%d"))
        else:
            self.date_ent.set_date(now)
        self.cb_hour.set(f"{now.hour:02d}")
        self.cb_min.set(f"{now.minute:02d}")
        self.cb_sec.set(f"{now.second:02d}")
        self.update_preview()

    def get_datetime_str(self):
        return f"{self.date_ent.get()} {self.cb_hour.get()}:{self.cb_min.get()}:{self.cb_sec.get()}"

    def update_preview(self):
        try:
            buy = float(self.ent_buy.get())
            comm = float(self.ent_comm.get())
            settle_str = f"{buy + comm:.2f}"
        except:
            settle_str = ""
        info = {
            "货商": self.cb_sup.get(),
            "入库快递单号": self.ent_in_courier.get(),
            "条形码": self.ent_bar.get(),
            "商品": self.ent_name.get(),
            "买价": self.ent_buy.get(),
            "佣金": self.ent_comm.get(),
            "数量": self.ent_qty.get(),
            "单位": self.ent_unit.get(),
            "颜色/配置": self.ent_color.get(),
            "入库时间": self.get_datetime_str(),
            "结算价": settle_str,
            "结算状态": "否"
        }
        txt = "\n".join(f"{k}: {v}" for k, v in info.items())
        self.lbl_preview.config(text=txt)

    def submit(self):
        data = {
            '货商姓名': self.cb_sup.get(),
            '数字条码': self.ent_bar.get(),
            '入库时间': self.get_datetime_str(),
            '商品名称': self.ent_name.get(),
            '买价': self.ent_buy.get(),
            '佣金': self.ent_comm.get(),
            '结算状态': '否',
            '商品数量': self.ent_qty.get(),
            '商品数量单位': self.ent_unit.get(),
            '入库快递单号': self.ent_in_courier.get(),
            '颜色/配置': self.ent_color.get()
        }
        self.controller.handle_inbound_registration(data)
        messagebox.showinfo("提示", "入库登记成功！")
        for w in [
            self.ent_in_courier, self.ent_bar, self.ent_name, self.ent_buy,
            self.ent_comm, self.ent_qty, self.ent_unit, self.ent_color
        ]:
            w.delete(0, tk.END)
        self.update_preview()
        self.refresh_list()

    def refresh_list(self):
        recs = self.controller.model.get_all_records()
        # 统计重复快递单号
        counts = {}
        for r in recs:
            key = r.get("入库快递单号", "")
            counts[key] = counts.get(key, 0) + 1

        self.tree.delete(*self.tree.get_children())
        for r in reversed(recs):
            tag = ('duplicate',) if counts.get(r.get("入库快递单号",""), 0) > 1 else ()
            vals = (
                r.get("入库快递单号",""),
                r.get("货商姓名",""),
                r.get("商品名称",""),
                r.get("商品数量",""),
                r.get("入库时间",""),
                r.get("颜色/配置","")
            )
            self.tree.insert("", tk.END, values=vals, tags=tag)

    def update_supplier_list(self, suppliers):
        self.cb_sup['values'] = suppliers
        if suppliers:
            self.cb_sup.current(0)

    def search_supplier(self):
        term = self.ent_sup_search.get().strip().lower()
        all_sup = self.controller.settings_model.get_suppliers()
        results = []
        for s in all_sup:
            s_lower = s.lower()
            if term in s_lower:
                results.append(s)
            elif _HAS_PYPINYIN and term.isalpha():
                initials = ''.join(lazy_pinyin(s, style=Style.FIRST_LETTER)).lower()
                if term in initials:
                    results.append(s)
        self.lst_sup_search.delete(0, tk.END)
        if results:
            for item in results:
                self.lst_sup_search.insert(tk.END, item)
            self.lst_sup_search.grid()
        else:
            self.lst_sup_search.grid_remove()

    def on_supplier_select(self, event):
        if not self.lst_sup_search.curselection():
            return
        idx = self.lst_sup_search.curselection()[0]
        self.cb_sup.set(self.lst_sup_search.get(idx))
        self.lst_sup_search.grid_remove()
        self.update_preview()

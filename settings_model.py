import os
import sys
import json

class SettingsModel:
    def __init__(self):
        # 确定基础目录：脚本目录或 exe 所在目录
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(__file__)
        # 在基础目录下创建 config 文件夹
        self.base_dir = os.path.join(base, 'config')
        os.makedirs(self.base_dir, exist_ok=True)

        # 配置文件路径
        self.settings_file   = os.path.join(self.base_dir, 'settings.json')
        self._mapping_file   = os.path.join(self.base_dir, 'barcode_mappings.json')

        # 加载或初始化
        self._load_settings()
        self._load_barcode_mappings()

    # -------- 通用设置管理 --------
    def _load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                'suppliers': [],
                'counters': [],
                'tables': ['default'],
                'active_table': 'default'
            }
            self._save_settings()

    def _save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    # --- 供应商 ---
    def get_suppliers(self):
        return self.settings.get('suppliers', [])

    def add_supplier(self, name: str):
        lst = self.settings.setdefault('suppliers', [])
        if name and name not in lst:
            lst.append(name)
            self._save_settings()

    def update_supplier(self, old: str, new: str):
        lst = self.settings.setdefault('suppliers', [])
        if old in lst and new and new not in lst:
            idx = lst.index(old)
            lst[idx] = new
            self._save_settings()

    def delete_supplier(self, name: str):
        lst = self.settings.setdefault('suppliers', [])
        if name in lst:
            lst.remove(name)
            self._save_settings()

    # --- 出库档口 ---
    def get_counters(self):
        return self.settings.get('counters', [])

    def add_counter(self, name: str):
        lst = self.settings.setdefault('counters', [])
        if name and name not in lst:
            lst.append(name)
            self._save_settings()

    def update_counter(self, old: str, new: str):
        lst = self.settings.setdefault('counters', [])
        if old in lst and new and new not in lst:
            idx = lst.index(old)
            lst[idx] = new
            self._save_settings()

    def delete_counter(self, name: str):
        lst = self.settings.setdefault('counters', [])
        if name in lst:
            lst.remove(name)
            self._save_settings()

    # --- 记录表 ---
    def get_tables(self):
        return self.settings.get('tables', [])

    def get_active_table(self):
        return self.settings.get('active_table', '')

    def add_table(self, name: str):
        lst = self.settings.setdefault('tables', [])
        if name and name not in lst:
            lst.append(name)
            self._save_settings()

    def rename_table(self, old: str, new: str):
        lst = self.settings.setdefault('tables', [])
        if old in lst and new and new not in lst:
            idx = lst.index(old)
            lst[idx] = new
            if self.settings.get('active_table') == old:
                self.settings['active_table'] = new
            self._save_settings()

    def delete_table(self, name: str):
        lst = self.settings.setdefault('tables', [])
        if name in lst:
            lst.remove(name)
            if self.settings.get('active_table') == name:
                self.settings['active_table'] = lst[0] if lst else ''
            self._save_settings()

    def set_active_table(self, name: str):
        if name in self.settings.get('tables', []):
            self.settings['active_table'] = name
            self._save_settings()

    # -------- 条形码映射管理 --------
    def _load_barcode_mappings(self):
        if os.path.exists(self._mapping_file):
            with open(self._mapping_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            # 自动去除首尾空白和换行
            self.barcode_mappings = {k.strip(): v.strip() for k, v in raw.items()}
        else:
            self.barcode_mappings = {}
            self._save_barcode_mappings()

    def _save_barcode_mappings(self):
        # 在保存前也 strip 一下 key/value
        clean = {k.strip(): v.strip() for k, v in self.barcode_mappings.items()}
        with open(self._mapping_file, 'w', encoding='utf-8') as f:
            json.dump(clean, f, ensure_ascii=False, indent=2)

    def get_barcode_mappings(self):
        """返回列表 [(barcode, product_name), ...]"""
        return list(self.barcode_mappings.items())

    def get_product_name(self, barcode: str) -> str:
        """根据条形码返回绑定的产品名称，未绑定返回空字符串"""
        return self.barcode_mappings.get(barcode.strip(), "")

    def add_barcode_mapping(self, barcode: str, product: str):
        barcode = barcode.strip()
        product = product.strip()
        if barcode:
            self.barcode_mappings[barcode] = product
            self._save_barcode_mappings()

    def update_barcode_mapping(self, old: str, new: str, product: str):
        old     = old.strip()
        new     = new.strip()
        product = product.strip()
        if old != new and old in self.barcode_mappings:
            del self.barcode_mappings[old]
        if new:
            self.barcode_mappings[new] = product
            self._save_barcode_mappings()

    def delete_barcode_mapping(self, barcode: str):
        barcode = barcode.strip()
        if barcode in self.barcode_mappings:
            del self.barcode_mappings[barcode]
            self._save_barcode_mappings()

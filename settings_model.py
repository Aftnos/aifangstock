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
        self._ensure_defaults()

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
            'active_table': 'default',
            'column_display': {
                'inbound': ['入库快递单号', '货商姓名', '商品名称', '商品数量', '入库时间', '颜色/配置'],
                'outbound': ['选中', '出库数量', '单号', '商品名称', '商品数量', '剩余数量', '剩余价值', '颜色/配置', '货商姓名', '入库时间'],
                'data_query': ['单号', '货商姓名', '入库时间', '商品名称', '商品数量', '买价', '佣金', '结算价', '出库状态']
            },
            'field_defaults': {
                'inbound_commission': 0,
                'inbound_quantity': 1,
                'inbound_price': 0,
                'outbound_quantity_mode': 'one'  # 'one' 或 'all'
            }
        }
            self._save_settings()

    def _save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def _ensure_defaults(self):
        """确保字段默认值设置存在"""
        if 'field_defaults' not in self.settings:
            self.settings['field_defaults'] = {
                'inbound_commission': 0,
                'inbound_quantity': 1,
                'outbound_quantity_mode': 'one'
            }
            self._save_settings()
        # 确保出库数量模式配置存在
        if 'outbound_quantity_mode' not in self.settings.get('field_defaults', {}):
            self.settings['field_defaults']['outbound_quantity_mode'] = 'one'
            self._save_settings()

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

    # -------- 表格列显示配置管理 --------
    def get_available_columns(self, page_type: str) -> list:
        """获取指定页面类型的所有可用列"""
        if page_type == 'inbound':
            return ['入库快递单号', '货商姓名', '商品名称', '商品数量', '入库时间', '颜色/配置', '买价', '佣金', '结算价', '数字条码']
        elif page_type == 'outbound':
            return ['选中', '出库数量', '单号', '商品名称', '商品数量', '剩余数量', '剩余价值', '颜色/配置', '货商姓名', '入库时间', '买价', '佣金', '结算价']
        elif page_type == 'data_query':
            return ['单号', '货商姓名', '入库时间', '数字条码', '商品名称', '商品数量', '结算日期', '入库快递单号', '货源', '颜色/配置', '买价', '佣金', '结算价', '单价', '剩余数量', '剩余价值', '行情价格', '结算状态', '出库状态', '出库档口', '快递单号', '快递价格', '利润', '备注', '出库记录']
        return []

    def get_display_columns(self, page_type: str) -> list:
        """获取指定页面类型当前显示的列"""
        return self.settings.get('column_display', {}).get(page_type, [])

    def set_display_columns(self, page_type: str, columns: list):
        """设置指定页面类型显示的列"""
        if 'column_display' not in self.settings:
            self.settings['column_display'] = {}
        self.settings['column_display'][page_type] = columns
        self._save_settings()

    # -------- 字段默认值管理 --------
    def get_field_default(self, field_name: str, default_value=None):
        """获取字段默认值"""
        field_defaults = self.settings.get('field_defaults', {})
        return field_defaults.get(field_name, default_value)

    def set_field_default(self, field_name: str, value):
        """设置字段默认值"""
        if 'field_defaults' not in self.settings:
            self.settings['field_defaults'] = {}
        self.settings['field_defaults'][field_name] = value
        self._save_settings()

    def get_inbound_commission_default(self):
        """获取入库登记页的佣金默认值"""
        return self.get_field_default('inbound_commission', 0)

    def get_inbound_quantity_default(self):
        """获取入库登记页的数量默认值"""
        return self.get_field_default('inbound_quantity', 1)

    def set_inbound_commission_default(self, value):
        """设置入库登记页的佣金默认值"""
        self.set_field_default('inbound_commission', value)

    def set_inbound_quantity_default(self, value):
        """设置入库登记页的数量默认值"""
        self.set_field_default('inbound_quantity', value)

    def get_inbound_price_default(self):
        """获取入库登记页的买价默认值"""
        return self.get_field_default('inbound_price', 0)

    def set_inbound_price_default(self, value):
        """设置入库登记页的买价默认值"""
        self.set_field_default('inbound_price', value)

    def get_outbound_quantity_mode(self):
        """获取出库数量默认值模式：'one'（一件）或 'all'（全部库存）"""
        return self.get_field_default('outbound_quantity_mode', 'one')

    def set_outbound_quantity_mode(self, mode):
        """设置出库数量默认值模式：'one'（一件）或 'all'（全部库存）"""
        if mode in ['one', 'all']:
            self.set_field_default('outbound_quantity_mode', mode)

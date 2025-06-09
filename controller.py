import time
from model import InventoryModel
from settings_model import SettingsModel

class InventoryController:
    def __init__(self, model: InventoryModel, settings_model: SettingsModel, root=None):
        self.model = model
        self.settings_model = settings_model
        self.view = None
        self.root = None

    def generate_order_number(self) -> str:
        return str(int(time.time() * 1000))

    def handle_inbound_registration(self, info: dict) -> bool:
        # 自动计算结算价 = 买价 + 佣金
        try:
            buy = float(info.get('买价', '0'))
            comm = float(info.get('佣金', '0'))
            settle = buy + comm
            quantity = int(info.get('商品数量', '1'))
            unit_price = settle / max(quantity, 1)
        except:
            settle = 0.0
            quantity = 1
            unit_price = 0.0
        
        record = {
            '单号': self.generate_order_number(),
            '货商姓名': info.get('货商姓名', ''),
            '入库时间': info.get('入库时间', ''),
            '数字条码': info.get('数字条码', ''),
            '商品名称': info.get('商品名称', ''),
            '商品数量': str(quantity),
            '商品数量单位': info.get('商品数量单位', ''),
            '入库快递单号': info.get('入库快递单号', ''),
            '货源': '',
            '颜色/配置': info.get('颜色/配置', ''),
            '买价': info.get('买价', ''),
            '佣金': info.get('佣金', ''),
            '结算价': f"{settle:.2f}",
            '单价': f"{unit_price:.2f}",
            '剩余数量': str(quantity),
            '剩余价值': f"{settle:.2f}",
            '行情价格': '',
            '结算状态': info.get('结算状态', ''),
            '出库状态': '未出库',
            '出库档口': '',
            '快递单号': '',
            '快递价格': '',
            '利润': '',
            '备注': '',
            '出库记录': ''
        }
        success = self.model.add_record(record)
        if success:
            self.refresh_inventory_list()
        return success

    def handle_outbound_registration(self, order: str, info: dict) -> bool:
        updated = {
            '出库状态': '卖出',
            '出库档口': info.get('出库档口', ''),
            '快递单号': info.get('快递单号', ''),
            '快递价格': info.get('快递价格', ''),
            '利润': ''
        }
        success = self.model.update_record(order, updated)
        if success:
            self.refresh_inventory_list()
        return success
    
    def handle_partial_outbound(self, order: str, quantity: int, tracking_number: str, counter: str) -> bool:
        """
        处理分数量出库
        """
        success = self.model.partial_outbound(order, quantity, tracking_number, counter)
        if success:
            self.refresh_inventory_list()
        return success

    def handle_modify(self, order: str, updated_fields: dict) -> tuple[bool, str]:
        # 获取原记录
        records = self.model.get_all_records()
        original_record = None
        for r in records:
            if r['单号'] == order:
                original_record = r
                break
        
        if not original_record:
            return False, "原始记录未找到"
        
        # 修改时重新计算结算价、单价、剩余价值
        try:
            # 获取买价和佣金（优先使用更新字段，否则使用原值）
            buy = float(updated_fields.get('买价', original_record.get('买价', '0')))
            comm = float(updated_fields.get('佣金', original_record.get('佣金', '0')))
            quantity = int(updated_fields.get('商品数量', original_record.get('商品数量', '1')))
            
            # 计算结算价和单价
            settlement_price = buy + comm
            unit_price = settlement_price / max(quantity, 1)
            
            updated_fields['结算价'] = f"{settlement_price:.2f}"
            updated_fields['单价'] = f"{unit_price:.2f}"
            
            # 如果修改了商品数量，需要重新计算剩余数量和剩余价值
            if '商品数量' in updated_fields:
                # 如果剩余数量为空，设置为新的商品数量
                remaining_qty = int(original_record.get('剩余数量', '') or original_record.get('商品数量', '0'))
                if not original_record.get('剩余数量', ''):
                    remaining_qty = quantity
                updated_fields['剩余数量'] = str(remaining_qty)
                updated_fields['剩余价值'] = f"{remaining_qty * unit_price:.2f}"
            else:
                # 如果没有修改商品数量，只更新剩余价值
                remaining_qty = int(original_record.get('剩余数量', '') or original_record.get('商品数量', '0'))
                updated_fields['剩余价值'] = f"{remaining_qty * unit_price:.2f}"
                
        except (ValueError, TypeError) as e:
            updated_fields['结算价'] = ''
            updated_fields['单价'] = ''
            return False, f"数据格式错误: {e}"
            
        success = self.model.update_record(order, updated_fields)
        if success:
            self.refresh_inventory_list()
            return True, "修改成功"
        return False, "数据库更新失败"

    def handle_delete(self, order: str) -> bool:
        success = self.model.delete_record(order)
        if success:
            self.refresh_inventory_list()
        return success

    def refresh_inventory_list(self):
        """
        统一调用：刷新入库、出库列表，并且在“全部库存”查询模式下
        自动更新数据查询页的数据（不清空筛选条件，只替换数据行）。
        """
        recs = self.model.get_all_records()
        if not self.view:
            return

        # 1) 刷新出库页库存列表
        self.view.outbound_page.update_inventory_list(recs)
        # 2) 刷新入库页列表
        self.view.inbound_page.refresh_list()

        # 3) 如果当前 DataView 是“全部库存”，则仅替换数据，不重置筛选
        dp = self.view.data_page
        if dp.cb.get() == "全部库存" and dp.columns:
            # 构造新的行数据
            new_data = []
            for r in recs:
                new_data.append(tuple(r.get(c, "") for c in dp.columns))
            dp.update_current_data(dp.columns, new_data)

    def refresh_supplier_list(self):
        sups = self.settings_model.get_suppliers()
        if self.view:
            self.view.inbound_page.update_supplier_list(sups)

    def refresh_counter_list(self):
        ctrs = self.settings_model.get_counters()
        if self.view:
            self.view.outbound_page.update_counter_list(ctrs)
            
    def switch_table(self, table_name):
        """切换到指定的数据表"""
        self.model = InventoryModel(table_name)
        self.refresh_inventory_list()

    # 以下是原有各种查询方法，保持不变
    def view_all_inventory_unified(self):
        recs = self.model.get_all_records()
        cols = (
            "入库快递单号","货商姓名","入库时间","数字条码","商品名称",
            "商品数量","商品数量单位","货源","颜色/配置",
            "买价","佣金","结算价","单价","剩余数量","剩余价值","行情价格","利润",
            "结算状态","出库状态","出库档口","快递单号","快递价格","备注","单号","出库记录"
        )
        data = [tuple(r.get(c, "") for c in cols) for r in recs]
        self.view.data_page.display_results(cols, data)

    def view_profit_by_product_unified(self):
        recs = self.model.get_all_records()
        d = {}
        for r in recs:
            p = r.get('商品名称', '')
            try:
                profit = float(r.get('行情价格','0') or 0) - float(r.get('结算价','0') or 0)
            except:
                profit = 0
            d[p] = d.get(p, 0) + profit
        cols = ("商品名称", "盈亏")
        data = [(k, f"{d[k]:.2f}") for k in d]
        self.view.data_page.display_results(cols, data)

    def view_profit_by_supplier_unified(self):
        recs = self.model.get_all_records()
        d = {}
        for r in recs:
            s = r.get('货商姓名', '')
            try:
                profit = float(r.get('行情价格','0') or 0) - float(r.get('结算价','0') or 0)
            except:
                profit = 0
            d[s] = d.get(s, 0) + profit
        cols = ("货商姓名", "盈亏")
        data = [(k, f"{d[k]:.2f}") for k in d]
        self.view.data_page.display_results(cols, data)

    def view_by_tracking_number_unified(self, t: str):
        recs = [r for r in self.model.get_all_records() if r.get('快递单号','') == t]
        cols = (
            "入库快递单号","货商姓名","入库时间","数字条码","商品名称",
            "商品数量","商品数量单位","货源","颜色/配置",
            "买价","佣金","结算价","单价","剩余数量","剩余价值","行情价格","利润",
            "结算状态","出库状态","出库档口","快递单号","快递价格","备注","单号","出库记录"
        )
        data = [tuple(r.get(c,"") for c in cols) for r in recs]
        self.view.data_page.display_results(cols, data)

    def view_inbound_count_by_supplier_unified(self):
        recs = self.model.get_all_records()
        cnt = {}
        for r in recs:
            s = r.get('货商姓名','')
            cnt[s] = cnt.get(s, 0) + 1
        cols = ("货商姓名", "入库次数")
        data = [(k, str(cnt[k])) for k in cnt]
        self.view.data_page.display_results(cols, data)
    
    def refresh_column_display(self, page_type: str):
        """刷新指定页面的列显示配置"""
        if not self.view:
            return
        
        if page_type == 'inbound':
            # 刷新入库登记页的表格列
            if hasattr(self.view, 'inbound_page'):
                self.view.inbound_page.refresh_columns()
        elif page_type == 'outbound':
            # 刷新出库登记页的表格列
            if hasattr(self.view, 'outbound_page'):
                self.view.outbound_page.refresh_columns()
        elif page_type == 'data_query':
            # 刷新数据查询页的表格列
            if hasattr(self.view, 'data_page'):
                self.view.data_page.refresh_columns()

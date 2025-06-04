import os
import sys
import csv

class InventoryModel:
    # CSV 文件的表头
    CSV_HEADER = [
        '单号',
        '货商姓名',
        '入库时间',
        '数字条码',
        '商品名称',
        '商品数量',
        '商品数量单位',
        '入库快递单号',
        '货源',
        '颜色/配置',
        '买价',
        '佣金',
        '结算价',
        '行情价格',
        '结算状态',
        '出库状态',
        '出库档口',
        '快递单号',
        '快递价格',
        '利润',
        '备注'
    ]

    def __init__(self, table_name="default"):
        # 确定程序所在目录
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(__file__)
        # 在基础目录下创建 data 文件夹
        self.data_dir = os.path.join(base, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        # 设置当前表
        self.set_table(table_name)

    def set_table(self, table_name: str):
        """
        切换使用的表（CSV 文件），并确保文件存在。
        """
        self.table_name = table_name
        self.filename = os.path.join(self.data_dir, f"{table_name}.csv")
        self.initialize_csv()

    def initialize_csv(self):
        """
        如果 CSV 文件不存在，就创建并写入表头。
        """
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding="gb2312") as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
                writer.writeheader()

    def add_record(self, record: dict):
        """
        追加一条记录到当前 CSV 表。
        """
        with open(self.filename, 'a', newline='', encoding="gb2312") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
            writer.writerow(record)

    def update_record(self, order_number: str, updated_fields: dict) -> bool:
        """
        根据单号查找并更新记录，返回 True 表示更新成功。
        """
        records = self.get_all_records()
        found = False
        for r in records:
            if r['单号'] == order_number:
                r.update(updated_fields)
                found = True
                break
        if not found:
            return False
        with open(self.filename, 'w', newline='', encoding="gb2312") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
            writer.writeheader()
            writer.writerows(records)
        return True

    def delete_record(self, order_number: str) -> bool:
        """
        根据单号删除记录，返回 True 表示删除成功。
        """
        records = self.get_all_records()
        new_records = [r for r in records if r.get('单号') != order_number]
        if len(new_records) == len(records):
            return False
        with open(self.filename, 'w', newline='', encoding="gb2312") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
            writer.writeheader()
            writer.writerows(new_records)
        return True

    def rename_table(self, old_name: str, new_name: str) -> bool:
        """
        重命名表文件：data/old_name.csv → data/new_name.csv
        返回 True 表示重命名成功。
        """
        old_path = os.path.join(self.data_dir, f"{old_name}.csv")
        new_path = os.path.join(self.data_dir, f"{new_name}.csv")
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            return True
        return False

    def get_all_records(self) -> list[dict]:
        """
        读取并返回当前表的所有记录，每条记录为一个 dict。
        """
        records = []
        with open(self.filename, 'r', newline='', encoding="gb2312") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records

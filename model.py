import os
import sys
import csv
import tempfile
import traceback

class InventoryModel:
    # CSV 文件的表头
    CSV_HEADER = [
        '单号',
        '货商姓名',
        '入库时间',
        '数字条码',
        '商品名称',
        '商品数量',
        '结算日期',
        '入库快递单号',
        '货源',
        '颜色/配置',
        '买价',
        '佣金',
        '结算价',
        '单价',
        '剩余数量',
        '剩余价值',
        '行情价格',
        '结算状态',
        '出库状态',
        '出库档口',
        '快递单号',
        '快递价格',
        '利润',
        '备注',
        '出库记录'
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
        self.last_error = ""

    def _record_error(self, context: str, e: Exception, extra: dict | None = None):
        try:
            msg = f"{context}: {type(e).__name__}: {e}"
            if extra:
                try:
                    details = "; ".join(f"{k}={v}" for k, v in extra.items())
                    msg = f"{msg}; {details}"
                except:
                    pass
            self.last_error = msg
            log_path = os.path.join(self.data_dir, "diagnostic.log")
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"[diagnostic] file={self.filename} | {msg}\n")
                lf.write(traceback.format_exc())
                lf.write("\n")
        except:
            self.last_error = f"{context}: {type(e).__name__}: {e}"

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

    def add_record(self, record: dict) -> bool:
        """
        追加一条记录到当前 CSV 表。
        """
        try:
            with open(self.filename, 'a', newline='', encoding="gb2312") as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
                writer.writerow(record)
            return True
        except Exception as e:
            self._record_error("添加记录时发生错误", e)
            return False

    def update_record(self, order_number: str, updated_fields: dict) -> bool:
        """
        根据单号查找并更新记录，返回 True 表示更新成功。
        """
        try:
            records = self.get_all_records()
            found = False
            for r in records:
                if r['单号'] == order_number:
                    r.update(updated_fields)
                    found = True
                    break
            if not found:
                return False

            try:
                for k, v in updated_fields.items():
                    _ = str(v).encode("gb2312")
            except Exception as enc_err:
                self._record_error("更新记录时发生编码错误", enc_err, {"field": k, "value": v})
                return False

            temp_file = tempfile.NamedTemporaryFile(
                "w", newline="", encoding="gb2312", delete=False, dir=self.data_dir
            )
            try:
                writer = csv.DictWriter(temp_file, fieldnames=self.CSV_HEADER)
                writer.writeheader()
                writer.writerows(records)
                temp_file.close()
                try:
                    os.replace(temp_file.name, self.filename)
                except PermissionError as pe:
                    self._record_error("替换CSV文件时权限错误", pe, {"temp": temp_file.name, "target": self.filename})
                    return False
            finally:
                if not temp_file.closed:
                    temp_file.close()
                if os.path.exists(temp_file.name) and temp_file.name != self.filename:
                    try:
                        os.remove(temp_file.name)
                    except Exception as rm_err:
                        self._record_error("清理临时文件失败", rm_err, {"temp": temp_file.name})

            return True
        except Exception as e:
            self._record_error("更新记录时发生错误", e, {"target": self.filename})
            return False

    def delete_record(self, order_number: str) -> bool:
        """
        根据单号删除记录，返回 True 表示删除成功。
        """
        try:
            records = self.get_all_records()
            new_records = [r for r in records if r.get('单号') != order_number]
            if len(new_records) == len(records):
                return False

            temp_file = tempfile.NamedTemporaryFile(
                "w", newline="", encoding="gb2312", delete=False, dir=self.data_dir
            )
            try:
                writer = csv.DictWriter(temp_file, fieldnames=self.CSV_HEADER)
                writer.writeheader()
                writer.writerows(new_records)
                temp_file.close()
                try:
                    os.replace(temp_file.name, self.filename)
                except PermissionError as pe:
                    self._record_error("替换CSV文件时权限错误", pe, {"temp": temp_file.name, "target": self.filename})
                    return False
            finally:
                if not temp_file.closed:
                    temp_file.close()
                if os.path.exists(temp_file.name) and temp_file.name != self.filename:
                    try:
                        os.remove(temp_file.name)
                    except Exception as rm_err:
                        self._record_error("清理临时文件失败", rm_err, {"temp": temp_file.name})

            return True
        except Exception as e:
            self._record_error("删除记录时发生错误", e, {"target": self.filename})
            return False

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
        try:
            with open(self.filename, 'r', newline='', encoding="gb2312") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if '结算日期' not in row:
                        dt = row.get('入库时间', '')
                        val = ''
                        if dt:
                            try:
                                val = dt.split(' ')[0]
                            except Exception:
                                val = ''
                        row['结算日期'] = val
                    records.append(row)
        except FileNotFoundError:
            self.initialize_csv()
            return []
        except Exception as e:
            self._record_error("读取记录时发生错误", e, {"target": self.filename})
            return []
        return records
    
    def partial_outbound(self, order_number: str, outbound_quantity: int, tracking_number: str, counter: str) -> bool:
        """
        处理分数量出库，更新剩余数量和剩余价值，记录出库信息
        """
        records = self.get_all_records()
        found = False
        
        for r in records:
            if r['单号'] == order_number:
                try:
                    # 获取当前剩余数量，如果为空则使用商品数量
                    current_remaining = int(r.get('剩余数量', '') or r.get('商品数量', '0'))
                    total_quantity = int(r.get('商品数量', '0'))
                    
                    # 获取单价，如果为空则计算
                    unit_price_str = r.get('单价', '')
                    if unit_price_str:
                        unit_price = float(unit_price_str)
                    else:
                        settlement_price = float(r.get('结算价', '0'))
                        unit_price = settlement_price / max(total_quantity, 1)
                        r['单价'] = f"{unit_price:.2f}"
                    
                    # 检查出库数量是否合法
                    if outbound_quantity > current_remaining:
                        return False
                    
                    # 计算新的剩余数量和剩余价值
                    new_remaining = current_remaining - outbound_quantity
                    new_remaining_value = new_remaining * unit_price
                    
                    # 更新记录
                    r['剩余数量'] = str(new_remaining)
                    r['剩余价值'] = f"{new_remaining_value:.2f}"
                    
                    # 更新出库状态
                    if new_remaining == 0:
                        r['出库状态'] = '全部出库'
                    else:
                        r['出库状态'] = '部分出库'
                    
                    # 记录出库信息
                    import time
                    outbound_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    outbound_info = f"{outbound_time}|{counter}|{tracking_number}|{outbound_quantity}|{unit_price:.2f}"
                    
                    existing_records = r.get('出库记录', '')
                    if existing_records:
                        r['出库记录'] = existing_records + ';' + outbound_info
                    else:
                        r['出库记录'] = outbound_info
                    
                    # 如果是第一次出库，设置出库档口和快递单号
                    if not r.get('出库档口', ''):
                        r['出库档口'] = counter
                    if not r.get('快递单号', ''):
                        r['快递单号'] = tracking_number
                    
                    found = True
                    break
                    
                except (ValueError, TypeError):
                    return False
        
        if not found:
            return False
            
        temp_file = tempfile.NamedTemporaryFile(
            "w", newline="", encoding="gb2312", delete=False, dir=self.data_dir
        )
        try:
            writer = csv.DictWriter(temp_file, fieldnames=self.CSV_HEADER)
            writer.writeheader()
            writer.writerows(records)
            temp_file.close()
            try:
                os.replace(temp_file.name, self.filename)
            except PermissionError as pe:
                self._record_error("替换CSV文件时权限错误", pe, {"temp": temp_file.name, "target": self.filename})
                return False
        finally:
            if not temp_file.closed:
                temp_file.close()
            if os.path.exists(temp_file.name) and temp_file.name != self.filename:
                try:
                    os.remove(temp_file.name)
                except Exception as rm_err:
                    self._record_error("清理临时文件失败", rm_err, {"temp": temp_file.name})

        return True

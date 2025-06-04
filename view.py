from datetime import datetime


class InventoryView:
    """视图层：提供命令行界面及用户输入输出功能"""

    @staticmethod
    def show_main_menu():
        print("\n====================")
        print("       主界面")
        print("====================")
        print("1. 入库登记")
        print("2. 出库登记")
        print("3. 数据查看")
        print("0. 退出")
        return input("请选择操作：")

    @staticmethod
    def get_inbound_info():
        print("\n【入库登记】")
        barcode = input("请扫描商品条形码：")
        pickup_time = input("请输入取货时间（格式YYYY-MM-DD HH:MM:SS），留空则使用当前时间：")
        if not pickup_time:
            pickup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        supplier = input("请输入货商姓名：")
        product_name = input("请输入商品名称：")
        purchase_price = input("请输入买价：")
        commission = input("请输入佣金：")
        purchase_channel = input("请输入购买渠道：")
        settlement = input("是否结算（是/否）：")
        return {
            '数字条码': barcode,
            '入库时间': pickup_time,
            '货商姓名': supplier,
            '商品名称': product_name,
            '买价': purchase_price,
            '佣金': commission,
            '购买渠道': purchase_channel,
            '结算状态': settlement
        }

    @staticmethod
    def get_outbound_info():
        print("\n【出库登记】")
        order_number = input("请输入要出库的商品单号：")
        sale_or_out = input("请选择操作类型（卖出/出库）：")
        counter = input("请输入出库档口：")
        tracking_number = input("请输入快递单号：")
        selling_price = input("请输入卖出价格：")
        return order_number, {
            '卖价': selling_price,
            '出库状态': sale_or_out,
            '出库档口': counter,
            '快递单号': tracking_number
        }

    @staticmethod
    def show_data_view_menu():
        print("\n【数据查看】")
        print("1. 按商品统计盈亏")
        print("2. 按货商统计盈亏")
        print("3. 按快递单号查询包含商品")
        print("4. 按入库时间统计盈亏")
        print("0. 返回主菜单")
        return input("请选择查询方式：")

    @staticmethod
    def get_tracking_number():
        return input("请输入快递单号进行查询：")

    @staticmethod
    def get_date():
        return input("请输入入库日期（格式YYYY-MM-DD）：")

    @staticmethod
    def display_records(records, header=None):
        if header:
            print(header)
        for record in records:
            print(record)

    @staticmethod
    def show_message(message):
        print(message)

    @staticmethod
    def wait():
        input("按回车键继续...")

import sys
from tkinter import Tk, messagebox
import datetime
import time

from aifangstock.models.inventory import InventoryModel
from aifangstock.models.settings import SettingsModel
from aifangstock.controllers.inventory_controller import InventoryController
from aifangstock.views.gui import InventoryMainView
from aifangstock.utils.license_validator import LicenseValidator

def check_expiration():
    # 使用基于硬件信息的许可证验证
    validator = LicenseValidator()
    
    try:
        # 验证许可证 - 现在会自动处理无授权情况，显示授权界面
        is_valid, message = validator.validate_license()
        
        # 如果验证失败，显示错误信息并退出
        if not is_valid:
            # 用户可能取消了授权操作
            messagebox.showerror("授权错误", message)
            sys.exit(1)
        else:
            # 授权成功，可以显示成功消息
            print(f"授权状态: {message}")
            
    except Exception as e:
        # 如果验证过程出错，不允许启动程序
        messagebox.showerror("错误", f"无法验证软件授权: {str(e)}")
        sys.exit(1)

def main():
    # 检查软件是否过期
    check_expiration()
    
    # 应用初始化
    settings_model = SettingsModel()
    active_table = settings_model.get_active_table()
    model = InventoryModel(active_table)
    
    # 创建根窗口并传递给控制器和视图
    controller = InventoryController(model, settings_model)
    view = InventoryMainView(controller, settings_model)
    controller.view = view

    # 首次刷新
    controller.refresh_supplier_list()
    controller.refresh_counter_list()
    controller.refresh_inventory_list()

    # 启动主界面
    view.start()

    # 停止后台服务
    controller.stop_services()

    # 确保主界面关闭后进程退出
    sys.exit(0)

if __name__ == "__main__":
    main()

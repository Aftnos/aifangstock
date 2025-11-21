import sys
from tkinter import Tk

from model import InventoryModel
from settings_model import SettingsModel
from controller import InventoryController
from gui_view import InventoryMainView

def main():
    
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

    # 确保主界面关闭后进程退出
    sys.exit(0)

if __name__ == "__main__":
    main()

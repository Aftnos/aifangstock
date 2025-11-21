#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试预览区域布局优化"""

import tkinter as tk
from tkinter import ttk
from model import InventoryModel
from settings_model import SettingsModel
from controller import InventoryController
from inbound_view import InboundView

def test_preview_with_long_content():
    """测试预览区域对长内容的处理"""
    
    root = tk.Tk()
    root.title("预览区域长内容测试")
    root.geometry("1200x800")
    
    # 初始化模型和控制器
    model = InventoryModel("test_preview")
    settings = SettingsModel()
    
    # 添加测试用的货商
    settings.add_supplier("测试货商A")
    settings.add_supplier("测试货商B")
    
    controller = InventoryController(model, settings)
    
    # 创建入库页面
    inbound_view = InboundView(root, controller)
    inbound_view.pack(fill=tk.BOTH, expand=True)
    
    # 设置控制器视图引用
    controller.view = type('obj', (object,), {
        'inbound_page': inbound_view,
        'outbound_page': type('obj', (object,), {
            'update_inventory_list': lambda x: None
        })(),
        'data_page': type('obj', (object,), {
            'cb': type('obj', (object,), {'get': lambda: "全部库存"})(),
            'columns': [],
            'update_current_data': lambda x, y: None
        })()
    })()
    
    # 测试用例：填写长内容
    test_cases = [
        {
            "name": "测试1：短内容",
            "supplier": "测试货商A",
            "courier": "JD123456",
            "barcode": "SKU001",
            "product": "商品A",
            "buy_price": "10.00",
            "commission": "2.00",
            "quantity": "5",
            "unit": "件",
            "color": "红色"
        },
        {
            "name": "测试2：长颜色/配置",
            "supplier": "测试货商B",
            "courier": "SF987654",
            "barcode": "SKU002",
            "product": "商品B",
            "buy_price": "15.50",
            "commission": "3.50",
            "quantity": "10",
            "unit": "套",
            "color": "深蓝色带白色条纹，尺寸L码，材质100%棉，手洗建议，不可漂白"
        },
        {
            "name": "测试3：超长数量单位",
            "supplier": "测试货商A",
            "courier": "YT456789",
            "barcode": "SKU003",
            "product": "商品C",
            "buy_price": "20.00",
            "commission": "4.00",
            "quantity": "1",
            "unit": "盒（每盒包含12个单位，每个单位重量100克，总重约1.2公斤）",
            "color": "绿色"
        }
    ]
    
    # 创建测试框架
    test_frame = ttk.LabelFrame(root, text="预览区域测试工具", padding=10)
    test_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
    
    def fill_form(test_case):
        """填充表单数据"""
        inbound_view.cb_sup.set(test_case["supplier"])
        inbound_view.ent_in_courier.delete(0, tk.END)
        inbound_view.ent_in_courier.insert(0, test_case["courier"])
        inbound_view.ent_bar.delete(0, tk.END)
        inbound_view.ent_bar.insert(0, test_case["barcode"])
        inbound_view.ent_name.delete(0, tk.END)
        inbound_view.ent_name.insert(0, test_case["product"])
        inbound_view.ent_buy.delete(0, tk.END)
        inbound_view.ent_buy.insert(0, test_case["buy_price"])
        inbound_view.ent_comm.delete(0, tk.END)
        inbound_view.ent_comm.insert(0, test_case["commission"])
        inbound_view.ent_qty.delete(0, tk.END)
        inbound_view.ent_qty.insert(0, test_case["quantity"])
        inbound_view.ent_unit.delete(0, tk.END)
        inbound_view.ent_unit.insert(0, test_case["unit"])
        inbound_view.ent_color.delete(0, tk.END)
        inbound_view.ent_color.insert(0, test_case["color"])
        inbound_view.update_preview()
        print(f"\n✓ 已填充: {test_case['name']}")
        print(f"  - 数量单位: {test_case['unit']}")
        print(f"  - 颜色/配置: {test_case['color']}")
    
    # 添加测试按钮
    for test_case in test_cases:
        btn = ttk.Button(
            test_frame,
            text=test_case["name"],
            command=lambda tc=test_case: fill_form(tc)
        )
        btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    print("=" * 60)
    print("预览区域布局优化测试")
    print("=" * 60)
    print("\n说明：")
    print("1. 点击测试按钮，在表单中自动填充数据")
    print("2. 观察预览区域是否正常显示所有内容")
    print("3. 检查长内容是否能自动换行而不被截断")
    print("4. 验证预览区域的滚动条是否正常工作")
    print("\n测试场景：")
    print("- 测试1：所有字段内容较短，验证基础布局")
    print("- 测试2：颜色/配置字段内容较长，验证长内容换行")
    print("- 测试3：数量单位字段超长，验证超长内容处理")
    print("\n" + "=" * 60)
    
    root.mainloop()

if __name__ == "__main__":
    test_preview_with_long_content()

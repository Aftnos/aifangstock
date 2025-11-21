#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试批量入库功能的集成"""

import sys
import os
from model import InventoryModel
from settings_model import SettingsModel
from controller import InventoryController

def test_bulk_import():
    """测试批量入库功能"""
    
    # 初始化模型和设置
    model = InventoryModel("test_bulk")
    settings = SettingsModel()
    controller = InventoryController(model, settings)
    
    # 模拟批量入库数据
    test_data = [
        {
            '货商姓名': '测试货商',
            '数字条码': 'SKU001',
            '入库时间': '2024-11-21 10:00:00',
            '商品名称': '商品A',
            '买价': '10.00',
            '佣金': '2.00',
            '结算状态': '否',
            '商品数量': '5',
            '商品数量单位': '件',
            '入库快递单号': 'JD123456',
            '颜色/配置': '红色'
        },
        {
            '货商姓名': '测试货商',
            '数字条码': 'SKU002',
            '入库时间': '2024-11-21 10:00:00',
            '商品名称': '商品B',
            '买价': '15.00',
            '佣金': '3.00',
            '结算状态': '否',
            '商品数量': '3',
            '商品数量单位': '件',
            '入库快递单号': 'JD123456',
            '颜色/配置': '蓝色'
        },
        {
            '货商姓名': '测试货商',
            '数字条码': 'SKU003',
            '入库时间': '2024-11-21 10:00:00',
            '商品名称': '商品C',
            '买价': '20.00',
            '佣金': '4.00',
            '结算状态': '否',
            '商品数量': '2',
            '商品数量单位': '件',
            '入库快递单号': 'JD123456',
            '颜色/配置': '绿色'
        }
    ]
    
    print("=" * 60)
    print("测试：批量入库功能")
    print("=" * 60)
    
    # 测试添加多个商品
    success_count = 0
    for i, data in enumerate(test_data, 1):
        success = controller.handle_inbound_registration(data)
        if success:
            print(f"✓ 第{i}个商品入库成功: {data['商品名称']}")
            success_count += 1
        else:
            print(f"✗ 第{i}个商品入库失败: {data['商品名称']}")
    
    print(f"\n总计: {success_count}/{len(test_data)} 商品入库成功")
    
    # 验证数据是否正确保存
    print("\n" + "=" * 60)
    print("验证数据")
    print("=" * 60)
    
    records = model.get_all_records()
    courier_records = [r for r in records if r.get('入库快递单号') == 'JD123456']
    
    print(f"\n快递单号 'JD123456' 下的记录数: {len(courier_records)}")
    
    if len(courier_records) == len(test_data):
        print("✓ 所有商品正确保存到系统中")
    else:
        print(f"✗ 保存失败，期望{len(test_data)}条记录，实际{len(courier_records)}条")
        return False
    
    # 显示详细信息
    print("\n详细信息:")
    print("-" * 60)
    for i, record in enumerate(courier_records, 1):
        print(f"\n商品{i}:")
        print(f"  商品名称: {record.get('商品名称')}")
        print(f"  商品数量: {record.get('商品数量')} {record.get('商品数量单位')}")
        print(f"  买价: {record.get('买价')}, 佣金: {record.get('佣金')}")
        print(f"  结算价: {record.get('结算价')}")
        print(f"  颜色/配置: {record.get('颜色/配置')}")
        print(f"  条形码: {record.get('数字条码')}")
    
    print("\n" + "=" * 60)
    print("✓ 批量入库功能测试通过")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_bulk_import()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分数量出库功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from model import InventoryModel
from controller import InventoryController
from settings_model import SettingsModel

def test_partial_outbound():
    print("=== 测试分数量出库功能 ===")
    
    # 创建模型实例
    model = InventoryModel("test")
    settings_model = SettingsModel()
    controller = InventoryController(model, settings_model)
    
    # 获取所有记录
    records = model.get_all_records()
    print(f"\n当前库存记录数: {len(records)}")
    
    if not records:
        print("没有库存记录，请先添加一些测试数据")
        return
    
    # 显示第一条记录的详细信息
    first_record = records[0]
    print(f"\n第一条记录详情:")
    for key, value in first_record.items():
        print(f"  {key}: {value}")
    
    order_number = first_record['单号']
    print(f"\n准备对单号 {order_number} 进行分数量出库测试")
    
    # 测试分数量出库
    outbound_quantity = 10
    tracking_number = "TEST_TRACKING_001"
    counter = "测试档口"
    
    print(f"出库数量: {outbound_quantity}")
    print(f"快递单号: {tracking_number}")
    print(f"出库档口: {counter}")
    
    # 执行分数量出库
    success = model.partial_outbound(order_number, outbound_quantity, tracking_number, counter)
    
    if success:
        print("\n✅ 分数量出库成功！")
        
        # 重新获取记录查看变化
        updated_records = model.get_all_records()
        updated_record = None
        for r in updated_records:
            if r['单号'] == order_number:
                updated_record = r
                break
        
        if updated_record:
            print(f"\n更新后的记录详情:")
            for key, value in updated_record.items():
                if value != first_record.get(key, ''):
                    print(f"  {key}: {first_record.get(key, '')} -> {value} ✨")
                else:
                    print(f"  {key}: {value}")
    else:
        print("\n❌ 分数量出库失败！")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_partial_outbound()

import os
import uuid
import pytest

from aifangstock.models.inventory import InventoryModel


def make_record(order="ORDER001", qty="20", price="100.00"):
    record = {h: "" for h in InventoryModel.CSV_HEADER}
    record.update({
        '单号': order,
        '货商姓名': 'SupplierA',
        '入库时间': '2024-01-01',
        '数字条码': '',
        '商品名称': 'ProductA',
        '商品数量': qty,
        '商品数量单位': '件',
        '入库快递单号': 'IN123',
        '货源': '',
        '颜色/配置': '红',
        '买价': '90',
        '佣金': '10',
        '结算价': price,
        '单价': f"{float(price)/int(qty):.2f}",
        '剩余数量': qty,
        '剩余价值': price,
        '行情价格': '',
        '结算状态': '',
        '出库状态': '未出库',
        '出库档口': '',
        '快递单号': '',
        '快递价格': '',
        '利润': '',
        '备注': '',
        '出库记录': ''
    })
    return record


@pytest.fixture
def model_instance(tmp_path):
    table = f"test_{uuid.uuid4().hex}"
    m = InventoryModel(table)
    if os.path.exists(m.filename):
        os.remove(m.filename)
    m.data_dir = str(tmp_path)
    m.filename = os.path.join(m.data_dir, f"{table}.csv")
    m.initialize_csv()
    yield m


def test_add_record(model_instance):
    rec = make_record()
    assert model_instance.add_record(rec) is True
    records = model_instance.get_all_records()
    assert len(records) == 1
    assert records[0]['单号'] == 'ORDER001'
    assert records[0]['商品名称'] == 'ProductA'


def test_update_record(model_instance):
    rec = make_record()
    model_instance.add_record(rec)
    assert model_instance.update_record('ORDER001', {'商品名称': 'Updated', '佣金': '5'}) is True
    records = model_instance.get_all_records()
    assert records[0]['商品名称'] == 'Updated'
    assert records[0]['佣金'] == '5'
    assert records[0]['货商姓名'] == 'SupplierA'


def test_delete_record(model_instance):
    rec = make_record()
    model_instance.add_record(rec)
    assert model_instance.delete_record('ORDER001') is True
    records = model_instance.get_all_records()
    assert records == []


def test_partial_outbound(model_instance):
    rec = make_record(qty="20", price="100.00")
    model_instance.add_record(rec)
    assert model_instance.partial_outbound('ORDER001', 5, 'TRACK1', 'Counter1') is True
    records = model_instance.get_all_records()
    r = records[0]
    assert r['剩余数量'] == '15'
    assert r['剩余价值'] == '75.00'
    assert r['出库状态'] == '部分出库'
    assert r['出库档口'] == 'Counter1'
    assert r['快递单号'] == 'TRACK1'
    assert 'Counter1' in r['出库记录']
    assert 'TRACK1' in r['出库记录']
    assert '|5|' in r['出库记录']

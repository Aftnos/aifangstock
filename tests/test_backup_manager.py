import os
import tempfile
from aifangstock.utils.backup_manager import BackupManager

class DummySettings:
    def __init__(self, base_dir):
        self.base_dir = base_dir
    def get_active_table(self):
        return "test_table"
    def get_backup_settings(self):
        return {
            'enabled': False,
            'backup_on_operation': True,
            'auto_backup_interval': 24,
            'max_backups': 5,
        }


def test_create_backup(tmp_path):
    # 创建临时数据文件
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    data_file = os.path.join(data_dir, 'test_table.csv')
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write('col1,col2\n1,2\n')

    settings = DummySettings(str(tmp_path / 'config'))
    manager = BackupManager(settings)
    assert manager.create_backup('manual') is True
    manager.stop_auto_backup_thread()
    files = os.listdir(manager.backup_dir)
    assert any(f.endswith('.csv') for f in files)

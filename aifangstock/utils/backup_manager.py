import os
import sys
import shutil
import json
import threading
import time
from datetime import datetime
from typing import Optional
from .logger import get_logger

class BackupManager:
    def __init__(self, settings_model):
        self.settings_model = settings_model
        
        # 确定备份目录
        if hasattr(settings_model, 'base_dir'):
            self.backup_dir = os.path.join(os.path.dirname(settings_model.base_dir), 'backups')
        else:
            # 如果没有base_dir，使用当前目录
            self.backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 启动自动备份
        self.auto_backup_thread = None
        self.stop_auto_backup = threading.Event()
        self.lock = threading.Lock()
        self.logger = get_logger()
        
        # 启动自动备份
        self.start_auto_backup()
    
    def get_data_file_path(self) -> str:
        """获取数据文件路径"""
        # 假设数据文件在项目根目录下的 data 目录
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        data_dir = os.path.join(base, 'data')
        active_table = self.settings_model.get_active_table()
        return os.path.join(data_dir, f'{active_table}.csv')
    
    def create_backup(self, backup_type: str = "manual") -> bool:
        """创建备份"""
        with self.lock:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                active_table = self.settings_model.get_active_table()
                backup_filename = f"{active_table}_{timestamp}_{backup_type}.csv"
                backup_path = os.path.join(self.backup_dir, backup_filename)
                
                # 获取当前活动表的CSV文件路径
                data_file_path = self.get_data_file_path()
                
                # 复制CSV数据文件
                if os.path.exists(data_file_path):
                    shutil.copy2(data_file_path, backup_path)
                    
                    # 创建备份信息文件
                    info_filename = f"{active_table}_{timestamp}_{backup_type}.json"
                    info_path = os.path.join(self.backup_dir, info_filename)
                    backup_info = {
                        '操作类型': '备份创建',
                        '备份类型': backup_type,
                        '表名': active_table,
                        '备份文件': backup_filename,
                        '备份路径': backup_path,
                        '创建时间': timestamp
                    }
                    
                    with open(info_path, 'w', encoding='utf-8') as f:
                        json.dump(backup_info, f, ensure_ascii=False, indent=2)
                    
                    # 记录备份创建日志
                    self.logger.log_backup(backup_type, backup_filename)
                    
                    # 清理旧备份
                    self.cleanup_old_backups()
                    
                    return True
                else:
                    self.logger.log_error("备份创建失败", None, f"数据文件不存在: {data_file_path}")
                    return False
            except Exception as e:
                self.logger.log_error("备份创建失败", e, f"备份类型: {backup_type}")
                return False
    
    def cleanup_old_backups(self):
        """清理旧备份"""
        try:
            backup_settings = self.settings_model.get_backup_settings()
            max_backups = backup_settings.get('max_backups', 10)
            
            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_files.append((filepath, os.path.getctime(filepath)))
            
            # 按创建时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出数量限制的备份
            if len(backup_files) > max_backups:
                for filepath, _ in backup_files[max_backups:]:
                    try:
                        os.remove(filepath)
                        # 同时删除对应的信息文件
                        info_file = filepath.replace('.csv', '.json')
                        if os.path.exists(info_file):
                            os.remove(info_file)
                        print(f"删除旧备份: {os.path.basename(filepath)}")
                    except Exception as e:
                        print(f"删除备份文件失败 {filepath}: {e}")
                        
        except Exception as e:
            print(f"清理旧备份失败: {e}")
    
    def backup_on_operation(self, operation: str):
        """操作时备份"""
        backup_settings = self.settings_model.get_backup_settings()
        if backup_settings.get('backup_on_operation', True):
            self.create_backup(f"operation_{operation}")
    
    def start_auto_backup(self):
        """启动自动备份线程"""
        # 获取备份设置
        backup_settings = self.settings_model.get_backup_settings()
        if not backup_settings.get('enabled', True):
            return
        
        # 如果已经有线程在运行，先停止它
        if self.auto_backup_thread and self.auto_backup_thread.is_alive():
            self.stop_auto_backup.set()
            self.auto_backup_thread.join()
        
        # 重置停止标志
        self.stop_auto_backup.clear()
        
        # 启动新线程
        self.auto_backup_thread = threading.Thread(target=self._auto_backup_worker)
        self.auto_backup_thread.daemon = True
        self.auto_backup_thread.start()
        
        # 记录自动备份启动日志
        self.logger.log_operation("备份服务", "自动备份服务已启动")
    
    def stop_auto_backup_thread(self):
        """停止自动备份线程"""
        self.stop_auto_backup.set()
        if self.auto_backup_thread:
            self.auto_backup_thread.join(timeout=2.0)  # 设置超时，避免程序退出时卡住
            
            # 记录自动备份停止日志
            self.logger.log_operation("备份服务", "自动备份服务已停止")
    
    def _auto_backup_worker(self):
        """自动备份工作线程"""
        while not self.stop_auto_backup.is_set():
            try:
                backup_settings = self.settings_model.get_backup_settings()
                if backup_settings.get('enabled', True):
                    interval_hours = backup_settings.get('auto_backup_interval', 24)
                    
                    # 等待指定时间或收到停止信号
                    if self.stop_auto_backup.wait(timeout=interval_hours * 3600):
                        # 收到停止信号
                        return
                    
                    # 执行自动备份
                    if not self.stop_auto_backup.is_set():
                        self.create_backup("auto")
                else:
                    # 如果备份被禁用，等待一分钟后再检查
                    time.sleep(60)
                    
            except Exception as e:
                print(f"自动备份线程错误: {e}")
                time.sleep(60)  # 出错后等待一分钟
    
    def get_backup_list(self) -> list:
        """获取备份列表"""
        backups = []
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.backup_dir, filename)
                    info_file = filepath.replace('.csv', '.json')
                    
                    backup_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'size': os.path.getsize(filepath),
                        'created_time': datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 读取备份信息
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                info_data = json.load(f)
                                backup_info.update(info_data)
                        except:
                            pass
                    
                    backups.append(backup_info)
            
            # 按创建时间排序
            backups.sort(key=lambda x: x.get('created_time', ''), reverse=True)
            
        except Exception as e:
            print(f"获取备份列表失败: {e}")
        
        return backups
    
    def restore_backup(self, backup_path: str) -> bool:
        """恢复备份"""
        try:
            if not os.path.exists(backup_path):
                self.logger.log_error("备份恢复失败", None, f"备份文件不存在: {backup_path}")
                return False
            
            # 创建当前数据的备份
            self.create_backup("before_restore")
            
            # 获取当前活动表的CSV文件路径
            data_file_path = self.get_data_file_path()
            
            # 恢复备份到当前活动表
            shutil.copy2(backup_path, data_file_path)
            
            # 记录备份恢复日志
            self.logger.log_operation("备份恢复", f"恢复文件: {os.path.basename(backup_path)} -> {data_file_path}")
            
            return True
            
        except Exception as e:
            self.logger.log_error("备份恢复失败", e, f"备份文件: {backup_path}")
            return False
    
    def delete_backup(self, backup_filename: str) -> bool:
        """删除备份文件"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
                # 记录备份删除日志
                self.logger.log_operation("备份删除", f"删除备份文件: {backup_filename}")
                
                return True
            else:
                self.logger.log_warning(f"备份文件不存在: {backup_filename}", "备份删除")
                return False
        except Exception as e:
            self.logger.log_error("删除备份失败", e, f"备份文件: {backup_filename}")
            return False
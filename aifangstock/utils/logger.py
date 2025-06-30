import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
import traceback

class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        
        # 创建日志器
        self.logger = logging.getLogger('InventorySystem')
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self.setup_handlers()
        
        # 设置异常钩子
        sys.excepthook = self.handle_exception
    
    def ensure_log_directory(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_handlers(self):
        """设置日志处理器"""
        # 操作日志文件处理器
        operation_log_file = os.path.join(self.log_dir, 'operations.log')
        operation_handler = RotatingFileHandler(
            operation_log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        operation_handler.setLevel(logging.INFO)
        operation_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        operation_handler.setFormatter(operation_formatter)
        
        # 错误日志文件处理器
        error_log_file = os.path.join(self.log_dir, 'errors.log')
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n%(funcName)s()\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        
        # 控制台处理器（可选，用于调试）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # 添加处理器到日志器
        self.logger.addHandler(operation_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 允许 Ctrl+C 正常退出
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 记录异常到日志
        error_msg = f"未捕获的异常: {exc_type.__name__}: {exc_value}"
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        full_traceback = ''.join(tb_lines)
        
        self.logger.error(f"{error_msg}\n{full_traceback}")
        
        # 调用默认的异常处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def log_operation(self, operation_type, details, user_id=None):
        """记录操作日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_info = f"用户:{user_id}" if user_id else "系统"
        message = f"[{operation_type}] {user_info} - {details}"
        self.logger.info(message)
    
    def log_error(self, error_msg, exception=None, context=None):
        """记录错误日志"""
        message = f"错误: {error_msg}"
        if context:
            message += f" - 上下文: {context}"
        
        if exception:
            message += f"\n异常详情: {str(exception)}"
            message += f"\n异常类型: {type(exception).__name__}"
            if hasattr(exception, '__traceback__') and exception.__traceback__:
                tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
                message += f"\n堆栈跟踪:\n{''.join(tb_lines)}"
        
        self.logger.error(message)
    
    def log_warning(self, warning_msg, context=None):
        """记录警告日志"""
        message = f"警告: {warning_msg}"
        if context:
            message += f" - 上下文: {context}"
        self.logger.warning(message)
    
    def log_debug(self, debug_msg, context=None):
        """记录调试日志"""
        message = f"调试: {debug_msg}"
        if context:
            message += f" - 上下文: {context}"
        self.logger.debug(message)
    
    def log_system_start(self):
        """记录系统启动"""
        self.log_operation("系统启动", "库存管理系统启动")
    
    def log_system_stop(self):
        """记录系统停止"""
        self.log_operation("系统停止", "库存管理系统停止")
    
    def log_inbound(self, record_data):
        """记录入库操作"""
        details = f"商品:{record_data.get('商品名称', 'N/A')}, 数量:{record_data.get('商品数量', 'N/A')}, 供应商:{record_data.get('货商姓名', 'N/A')}"
        self.log_operation("入库登记", details)
    
    def log_outbound(self, order_number, outbound_data):
        """记录出库操作"""
        details = f"订单号:{order_number}, 出库档口:{outbound_data.get('出库档口', 'N/A')}, 快递单号:{outbound_data.get('快递单号', 'N/A')}"
        self.log_operation("出库登记", details)
    
    def log_modify(self, order_number, changes):
        """记录修改操作"""
        change_details = ", ".join([f"{k}:{v}" for k, v in changes.items()])
        details = f"订单号:{order_number}, 修改内容:[{change_details}]"
        self.log_operation("数据修改", details)
    
    def log_delete(self, order_number):
        """记录删除操作"""
        details = f"订单号:{order_number}"
        self.log_operation("数据删除", details)
    
    def log_backup(self, backup_type, backup_name=None):
        """记录备份操作"""
        details = f"备份类型:{backup_type}"
        if backup_name:
            details += f", 备份文件:{backup_name}"
        self.log_operation("数据备份", details)
    
    def log_restore(self, backup_name):
        """记录恢复操作"""
        details = f"恢复备份:{backup_name}"
        self.log_operation("数据恢复", details)
    
    def log_settings_change(self, setting_type, details):
        """记录设置更改"""
        message = f"设置类型:{setting_type}, 详情:{details}"
        self.log_operation("设置更改", message)
    
    def log_data_import(self, file_path, record_count):
        """记录数据导入"""
        details = f"导入文件:{file_path}, 记录数量:{record_count}"
        self.log_operation("数据导入", details)
    
    def log_data_export(self, file_path, record_count):
        """记录数据导出"""
        details = f"导出文件:{file_path}, 记录数量:{record_count}"
        self.log_operation("数据导出", details)
    
    def get_recent_logs(self, log_type="operations", lines=100):
        """获取最近的日志记录"""
        log_file = os.path.join(self.log_dir, f"{log_type}.log")
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self.log_error(f"读取日志文件失败: {log_file}", e)
            return []
    
    def clear_old_logs(self, days=30):
        """清理旧日志文件"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.log_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        self.log_operation("日志清理", f"删除旧日志文件: {filename}")
        except Exception as e:
            self.log_error("清理旧日志文件失败", e)

# 全局日志实例
_logger_instance = None

def get_logger():
    """获取全局日志实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance

def log_operation(operation_type, details, user_id=None):
    """快捷操作日志记录"""
    get_logger().log_operation(operation_type, details, user_id)

def log_error(error_msg, exception=None, context=None):
    """快捷错误日志记录"""
    get_logger().log_error(error_msg, exception, context)

def log_warning(warning_msg, context=None):
    """快捷警告日志记录"""
    get_logger().log_warning(warning_msg, context)
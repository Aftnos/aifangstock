import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
import socket
import hashlib
import base64
import wmi
import sys
from tkinter import Tk, simpledialog, messagebox
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class LicenseValidator:
    def __init__(self):
        self.server_url = "https://app.aifang.pro/validate.php"
        # 修改license文件保存路径，使其保存在config目录下
        base_dir = self._get_base_dir()
        self.license_file = os.path.join(base_dir, "config", "license.dat")
        self.encryption_key = b"MyOneSecretKey16" # 16字节密钥用于AES-128
        
    def _get_base_dir(self):
        """获取应用程序的基础目录，兼容打包后的exe"""
        if getattr(sys, 'frozen', False):
            # 如果是打包后的应用程序
            return os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            return os.path.dirname(os.path.abspath(__file__))
        
    def get_hardware_id(self):
        """获取主板序列号作为硬件ID"""
        try:
            c = wmi.WMI()
            for board_id in c.Win32_BaseBoard():
                return board_id.SerialNumber
            return ""
        except Exception as e:
            print(f"获取主板ID错误: {str(e)}")
            return socket.gethostname()  # 如果WMI失败，使用主机名作为备选
    
    def encrypt_data(self, data):
        """使用AES加密数据"""
        try:
            json_data = json.dumps(data)
            cipher = AES.new(self.encryption_key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(json_data.encode('utf-8'), AES.block_size))
            iv = base64.b64encode(cipher.iv).decode('utf-8')
            ct = base64.b64encode(ct_bytes).decode('utf-8')
            return json.dumps({'iv': iv, 'data': ct})
        except Exception as e:
            print(f"加密错误: {str(e)}")
            return None
    
    def decrypt_data(self, encrypted_data):
        """解密AES加密的数据"""
        try:
            b64_data = json.loads(encrypted_data)
            iv = base64.b64decode(b64_data['iv'])
            ct = base64.b64decode(b64_data['data'])
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return json.loads(pt.decode('utf-8'))
        except Exception as e:
            print(f"解密错误: {str(e)}")
            return None
    
    def save_license(self, license_data):
        """保存加密的授权信息到文件"""
        try:
            encrypted = self.encrypt_data(license_data)
            # 确保config目录存在
            config_dir = os.path.dirname(self.license_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            with open(self.license_file, 'w') as f:
                f.write(encrypted)
            return True
        except Exception as e:
            print(f"保存授权文件错误: {str(e)}")
            return False
    
    def load_license(self):
        """从文件加载并解密授权信息"""
        try:
            if not os.path.exists(self.license_file):
                return None
                
            with open(self.license_file, 'r') as f:
                encrypted_data = f.read()
                
            return self.decrypt_data(encrypted_data)
        except Exception as e:
            print(f"加载授权文件错误: {str(e)}")
            return None
    
    def get_current_time(self):
        """获取当前时间，优先使用NTP服务器时间"""
        try:
            # 尝试从NTP服务器获取时间
            import ntplib
            client = ntplib.NTPClient()
            response = client.request('pool.ntp.org', timeout=5)
            return datetime.fromtimestamp(response.tx_time)
        except:
            # 如果NTP获取失败，使用本地时间
            return datetime.now()
    
    def activate_license(self, activation_code):
        """使用激活码激活软件"""
        hardware_id = self.get_hardware_id()
        
        # 构建请求参数
        params = {
            'action': 'activate',
            'activation_code': activation_code,
            'hardware_id': hardware_id
        }
        
        try:
            # 发送激活请求到服务器
            response = self._send_request(params)
            
            if response.get('status') == 'success':
                # 保存授权信息
                license_data = {
                    'hardware_id': hardware_id,
                    'expiry_date': response.get('expiry_date'),
                    'activation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'license_type': response.get('license_type', 'standard')
                }
                
                if self.save_license(license_data):
                    return True, "软件已成功激活"
                else:
                    return False, "保存授权信息失败"
            else:
                return False, response.get('message', '激活失败，请检查激活码')
                
        except Exception as e:
            return False, f"激活过程中发生错误: {str(e)}"
    
    def check_remote_activation(self):
        """检查服务器上是否有此硬件ID的激活记录"""
        hardware_id = self.get_hardware_id()
        
        # 构建请求参数
        params = {
            'action': 'check_hardware',
            'hardware_id': hardware_id
        }
        
        try:
            # 发送请求到服务器
            response = self._send_request(params)
            
            if response.get('status') == 'success' and response.get('activated', False):
                # 保存授权信息
                license_data = {
                    'hardware_id': hardware_id,
                    'expiry_date': response.get('expiry_date'),
                    'activation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'license_type': response.get('license_type', 'standard')
                }
                
                if self.save_license(license_data):
                    return True, "已恢复授权信息"
                else:
                    return False, "保存授权信息失败"
            else:
                return False, "未找到此设备的激活记录"
                
        except Exception as e:
            return False, f"检查激活记录时发生错误: {str(e)}"
    
    def validate_license(self):
        """验证授权是否有效"""
        # 首先检查本地授权文件
        license_data = self.load_license()
        
        if license_data:
            # 验证硬件ID是否匹配
            current_hardware_id = self.get_hardware_id()
            if license_data.get('hardware_id') != current_hardware_id:
                return self._handle_invalid_license("授权与当前设备不匹配")
            
            # 验证授权是否过期
            try:
                expiry_date = datetime.strptime(license_data.get('expiry_date'), '%Y-%m-%d %H:%M:%S')
                current_time = self.get_current_time()
                
                if current_time > expiry_date:
                    return self._handle_invalid_license("软件授权已过期")
                
                # 计算剩余天数
                days_left = (expiry_date - current_time).days
                return True, f"授权有效，剩余 {days_left} 天"
                
            except Exception as e:
                return self._handle_invalid_license(f"验证授权时发生错误: {str(e)}")
        else:
            # 如果没有本地授权文件，尝试从服务器恢复
            is_valid, message = self.check_remote_activation()
            if is_valid:
                return True, message
            else:
                # 如果服务器也没有记录，则需要激活
                return self._handle_invalid_license("需要激活软件")
    
    def _handle_invalid_license(self, message):
        """处理无效授权的情况，提示用户输入激活码"""
        # 创建一个临时的Tk窗口用于对话框
        root = Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 设置窗口图标
        try:
            from ..views.gui import ICON_BASE64
            import tkinter as tk
            icon = tk.PhotoImage(data=ICON_BASE64)
            root.iconphoto(False, icon)
            # 保存引用，避免被垃圾回收
            root._icon = icon
        except Exception as e:
            print("无法设置图标:", e)
        
        # 显示激活提示
        if not messagebox.askyesno("授权验证", f"{message}\n是否现在激活软件?"):
            return False, "用户取消了激活过程"
        
        # 提示用户输入激活码
        activation_code = simpledialog.askstring("软件激活", "请输入激活码:", parent=root)
        root.destroy()
        
        if not activation_code:
            return False, "用户取消了激活过程"
        
        # 尝试激活
        return self.activate_license(activation_code)
    
    def _send_request(self, params):
        """发送请求到授权服务器"""
        # 将参数编码为JSON
        data = json.dumps(params).encode('utf-8')
        
        # 处理URL中可能的非ASCII字符
        parsed_url = urllib.parse.urlparse(self.server_url)
        encoded_path = urllib.parse.quote(parsed_url.path, safe='/:') 
        encoded_url = urllib.parse.urlunparse(
            (parsed_url.scheme, parsed_url.netloc, encoded_path,
             parsed_url.params, parsed_url.query, parsed_url.fragment))
        
        # 创建请求
        req = urllib.request.Request(
            encoded_url,
            data=data,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        
        # 发送请求并获取响应
        try:
            # 创建不验证SSL证书的上下文
            ssl_context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as f:
                response_data = f.read().decode('utf-8')
            return json.loads(response_data)
        except urllib.error.URLError as e:
            return {'status': 'error', 'message': f'网络错误: {str(e)}'}
        except json.JSONDecodeError:
            return {'status': 'error', 'message': '服务器响应格式错误'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
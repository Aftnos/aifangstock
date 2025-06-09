import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import urllib.request
import urllib.error
import urllib.parse
import sys
import shutil
import zipfile
import subprocess
import ssl # 添加ssl模块导入
from datetime import datetime

class UpdateView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=10)
        self.controller = controller
        self.update_server_url = "https://updata.aifang.pro/index.php"
        self.current_version = "2.3.6"  # 当前版本号
        self.checking = False
        self.downloading = False
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 当前版本信息
        version_frame = ttk.LabelFrame(main_frame, text="当前版本信息", padding=10)
        version_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(version_frame, text=f"软件版本: {self.current_version}").pack(anchor="w")
        ttk.Label(version_frame, text=f"发布日期: {self.get_build_date()}").pack(anchor="w")
        
        # 更新检查区域
        update_frame = ttk.LabelFrame(main_frame, text="更新检查", padding=10)
        update_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="点击检查更新按钮开始检查新版本")
        ttk.Label(update_frame, textvariable=self.status_var, wraplength=400).pack(pady=10)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(update_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        self.progress_bar.pack_forget()  # 初始隐藏进度条
        
        # 按钮区域
        button_frame = ttk.Frame(update_frame)
        button_frame.pack(pady=10)
        
        self.check_button = ttk.Button(button_frame, text="检查更新", command=self.check_for_updates)
        self.check_button.pack(side=tk.LEFT, padx=5)
        
        self.download_button = ttk.Button(button_frame, text="下载更新", command=self.download_update, state=tk.DISABLED)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.install_button = ttk.Button(button_frame, text="安装更新", command=self.install_update, state=tk.DISABLED)
        self.install_button.pack(side=tk.LEFT, padx=5)
        
        # 更新日志区域
        log_frame = ttk.LabelFrame(main_frame, text="更新日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=50, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.insert(tk.END, "暂无更新日志信息")
        self.log_text.config(state=tk.DISABLED)
    
    def get_build_date(self):
        # 获取应用程序构建日期，这里简化为返回固定值
        # 实际应用中可以从配置文件或编译信息中获取
        return "2025-5-17"
    
    def check_for_updates(self):
        if self.checking:
            return
            
        self.checking = True
        self.status_var.set("正在检查更新...")
        self.check_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)
        self.install_button.config(state=tk.DISABLED)
        
        # 在后台线程中执行检查
        threading.Thread(target=self._check_update_thread, daemon=True).start()
    
    def _check_update_thread(self):
        try:
            # 构建请求参数
            params = {
                'action': 'check',
                'version': self.current_version,
                'client_id': self._get_client_id()
            }
            
            # 发送请求到更新服务器
            response = self._send_request(params)
            
            # 处理响应
            if response.get('status') == 'success':
                if response.get('update_available', False):
                    self._update_ui(lambda: [
                        self.status_var.set(f"发现新版本: {response.get('version')}\n{response.get('description')}"),
                        self.download_button.config(state=tk.NORMAL),
                        self._update_log(response.get('changelog', ''))
                    ])
                    # 保存更新信息
                    self.update_info = response
                else:
                    self._update_ui(lambda: self.status_var.set("您的软件已是最新版本"))
            else:
                self._update_ui(lambda: self.status_var.set(f"检查更新失败: {response.get('message', '未知错误')}"))
        except Exception as e:
            error_message = str(e)
            self._update_ui(lambda: self.status_var.set(f"检查更新时发生错误: {error_message}"))
        finally:
            self._update_ui(lambda: [
                self.check_button.config(state=tk.NORMAL),
                setattr(self, 'checking', False)
            ])
    
    def download_update(self):
        if self.downloading or not hasattr(self, 'update_info'):
            return
            
        self.downloading = True
        self.status_var.set("正在下载更新...")
        self.progress_bar.pack(fill=tk.X, pady=10)
        self.progress_var.set(0)
        self.check_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)
        
        # 在后台线程中执行下载
        threading.Thread(target=self._download_thread, daemon=True).start()
    
    def _download_thread(self):
        try:
            # 获取下载URL
            download_url = self.update_info.get('download_url')
            if not download_url:
                raise ValueError("下载链接无效")
            
            # 获取当前程序目录
            current_dir = os.path.dirname(sys.executable)
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                app_dir = current_dir
            else:
                # 如果是开发环境
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 创建updata目录在应用程序目录下
            update_dir = os.path.join(app_dir, 'updata')
            os.makedirs(update_dir, exist_ok=True)
            
            # 下载文件路径
            file_name = os.path.basename(download_url)
            # 确保文件名使用UTF-8编码
            if isinstance(file_name, str):
                file_name = file_name.encode('utf-8').decode('utf-8', 'ignore')
            download_path = os.path.join(update_dir, file_name)
            
            # 下载文件
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, block_num * block_size * 100 / total_size)
                    self._update_ui(lambda: self.progress_var.set(percent))
            
            # 处理URL中的非ASCII字符
            parsed_url = urllib.parse.urlparse(download_url)
            # 确保URL路径部分正确编码
            encoded_path = urllib.parse.quote(parsed_url.path, safe='/:')
            # 重新组合URL
            encoded_url = urllib.parse.urlunparse(
                (parsed_url.scheme, parsed_url.netloc, encoded_path, 
                 parsed_url.params, parsed_url.query, parsed_url.fragment))
            
            # 创建不验证SSL证书的上下文
            ssl_context = ssl._create_unverified_context()
            
            # 创建不验证SSL证书的opener
            https_handler = urllib.request.HTTPSHandler(context=ssl_context)
            opener = urllib.request.build_opener(https_handler)
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(encoded_url, download_path, reporthook=report_progress)
            
            # 下载完成
            self.update_path = download_path
            self._update_ui(lambda: [
                self.status_var.set("更新包下载完成，可以点击安装按钮进行安装"),
                self.install_button.config(state=tk.NORMAL)
            ])
        except Exception as e:
            # 确保错误消息正确处理非ASCII字符
            try:
                error_message = str(e)
            except UnicodeEncodeError:
                error_message = repr(e)
            self._update_ui(lambda: self.status_var.set(f"下载更新时发生错误: {error_message}"))
        finally:
            self._update_ui(lambda: [
                self.check_button.config(state=tk.NORMAL),
                setattr(self, 'downloading', False)
            ])
    
    def install_update(self):
        if not hasattr(self, 'update_path') or not os.path.exists(self.update_path):
            messagebox.showerror("错误", "更新包不存在或已损坏")
            return
        
        # 确认安装
        if not messagebox.askyesno("安装确认", "安装更新将关闭当前程序并启动更新过程，是否继续？"):
            return
        
        try:
            # 解压更新包（如果是zip格式）
            if self.update_path.endswith('.zip'):
                if not zipfile.is_zipfile(self.update_path):
                    messagebox.showerror("错误", "更新包文件损坏或格式不正确")
                    return
                extract_dir = os.path.dirname(self.update_path)
                try:
                    with zipfile.ZipFile(self.update_path, 'r') as zip_ref:
                        # 添加严格验证逻辑
                        if zip_ref.testzip() is not None:
                            messagebox.showerror("错误", "ZIP文件校验失败，可能存在损坏")
                            return
                        zip_ref.extractall(extract_dir)
                except Exception as e:
                    messagebox.showerror("错误", f"解压更新包时发生错误: {str(e)}")
                    return
                
                # 查找安装程序
                installer = None
                for file in os.listdir(extract_dir):
                    if file.endswith('.exe') and 'setup' in file.lower():
                        installer = os.path.join(extract_dir, file)
                        break
                
                if installer:
                    # 启动安装程序并退出当前应用
                    subprocess.Popen([installer])
                    # 安全退出应用
                    self._safe_quit()
                else:
                    # 如果没有安装程序，则直接替换文件
                    self._replace_files(extract_dir)
            else:
                # 直接运行可执行文件
                subprocess.Popen([self.update_path])
                # 安全退出应用
                self._safe_quit()
        except zipfile.BadZipFile:
            messagebox.showerror("错误", "ZIP文件格式不正确或已损坏")
        except Exception as e:
            messagebox.showerror("安装错误", f"安装更新时发生错误: {str(e)}")
    
    def _replace_files(self, source_dir):
        # 获取当前程序目录
        current_dir = os.path.dirname(sys.executable)
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            app_dir = current_dir
        else:
            # 如果是开发环境
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 创建批处理文件在应用程序目录下的updata文件夹中
        update_dir = os.path.join(app_dir, 'updata')
        os.makedirs(update_dir, exist_ok=True)
        bat_path = os.path.join(update_dir, 'update_myone.bat')
        
        # 生成批处理脚本内容
        exe_name = os.path.basename(sys.executable)
        app_exe = os.path.join(app_dir, exe_name)
        
        # 构建批处理脚本内容
        bat_content = f'''
@echo off
echo 正在更新程序，请稍候...

:: 等待原程序退出
ping 127.0.0.1 -n 3 > nul

:: 终止可能正在运行的进程
echo 正在终止程序进程...
taskkill /F /IM "{exe_name}" /T > nul 2>&1
ping 127.0.0.1 -n 2 > nul

:: 确保目标目录存在
if not exist "{app_dir}" mkdir "{app_dir}"

:: 清理主程序文件（保留配置文件和数据文件）
echo 正在清理主程序文件...
if exist "{app_dir}\*.exe" del /F /Q "{app_dir}\*.exe" > nul 2>&1
if exist "{app_dir}\*.dll" del /F /Q "{app_dir}\*.dll" > nul 2>&1
if exist "{app_dir}\*.pyd" del /F /Q "{app_dir}\*.pyd" > nul 2>&1

:: 复制更新文件到应用目录
echo 正在复制更新文件...
robocopy "{source_dir}" "{app_dir}" /E /IS /IT /IM /R:3 /W:3
if %ERRORLEVEL% LEQ 7 set ERRORLEVEL=0

:: 等待文件系统操作完成
timeout /t 2 /nobreak > nul

:: 启动应用程序
if exist "{app_exe}" (
    echo 启动更新后的程序...
    start "" "{app_exe}"
) else (
    echo 未找到主程序，更新可能不完整。
    pause
)

:: 清理临时文件
echo 正在清理临时文件...
timeout /t 2 /nobreak > nul
rmdir /S /Q "{source_dir}" > nul 2>&1

:: 删除批处理文件自身
del "%~f0" > nul 2>&1
'''
        
        # 写入批处理文件
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        # 显示更新提示
        messagebox.showinfo("更新", "程序将重启以完成更新，请稍候...")
        
        # 运行批处理文件并退出当前程序
        subprocess.Popen(['cmd.exe', '/c', bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        # 安全退出应用
        self._safe_quit()
    
    def _update_log(self, changelog):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, changelog or "暂无更新日志信息")
        self.log_text.config(state=tk.DISABLED)
    
    def _get_client_id(self):
        # 获取客户端唯一标识，可以使用机器码或其他唯一标识
        # 这里简化为使用计算机名
        import socket
        return socket.gethostname()
    
    def _send_request(self, params):
        # 将参数编码为JSON
        data = json.dumps(params).encode('utf-8')
        
        # 处理URL中可能的非ASCII字符
        parsed_url = urllib.parse.urlparse(self.update_server_url)
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
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as f: # 添加context参数
                response_data = f.read().decode('utf-8')
            return json.loads(response_data)
        except urllib.error.URLError as e:
            return {'status': 'error', 'message': f'网络错误: {str(e)}'}
        except json.JSONDecodeError:
            return {'status': 'error', 'message': '服务器响应格式错误'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _safe_quit(self):
        # 安全退出应用，避免NoneType错误
        try:
            if self.controller and hasattr(self.controller, 'root') and self.controller.root:
                self.controller.root.quit()
            else:
                # 如果controller.root不可用，尝试使用sys.exit
                sys.exit(0)
        except Exception as e:
            print(f"退出应用时发生错误: {str(e)}")
            sys.exit(0)
    
    def _update_ui(self, func):
        # 在主线程中更新UI
        if self.winfo_exists():
            self.after(0, func)
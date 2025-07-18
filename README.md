# 艾方存货管家

该项目是一套使用 Python Tkinter 构建的桌面出入库管理系统，提供从入库登记、出库登记、库存数据查询到数据修改、基础配置等一整套功能，并内置软件授权验证及自动更新机制。数据以 CSV 文件方式存储，适合小型或中型库存场景。

## 功能概览

- **入库登记**：录入供应商、条形码、商品信息、价格等数据，并自动计算结算价。
- **出库登记**：支持多选库存批量出库，记录出库档口和快递单号。
- **数据查询**：提供按商品/供应商统计盈亏、快递单号查询、供应商入库次数统计等多种视图，并可对结果进行筛选与排序。
- **数据修改**：列表式显示所有记录，可根据条件筛选并编辑或删除单条记录。
- **设置**：维护供应商列表、出库档口、数据表（CSV 文件）以及条形码与商品名映射关系。
- **软件更新**：通过远程服务器检查并下载新版本，支持解压或直接执行安装程序。
- **授权管理**：基于硬件信息的授权验证及激活流程，授权信息 AES 加密保存在 `config/license.dat` 中。

## 目录结构

```
├── main.py                 # 程序入口
├── controller.py           # 业务逻辑控制器
├── model.py                # 数据模型，读写 CSV 表
├── settings_model.py       # 设置及条形码映射管理
├── gui_view.py             # 主界面及各功能页的整合
├── inbound_view.py         # 入库登记界面
├── outbound_view.py        # 出库登记界面
├── data_view.py            # 数据查询界面
├── modify_view.py          # 数据修改界面
├── settings_view.py        # 设置界面
├── update_view.py          # 版本更新界面
├── license_view.py         # 授权信息界面
├── license_validator.py    # 授权验证逻辑
├── barcode_model.py        # 简单条形码映射模型
├── server/                 # PHP 实现的授权与更新服务器示例
│   ├── 授权/               # 授权服务器脚本
│   └── 更新/               # 更新服务器脚本及版本文件
└── requirements.txt        # Python 依赖列表
```

运行过程中会在程序目录下创建以下文件夹：

- `data/`：存放每个数据表对应的 CSV 文件。
- `config/`：保存 `settings.json`、`barcode_mappings.json` 以及 `license.dat` 等配置文件。
- `updata/`：下载更新包并执行更新时使用的临时目录。

## 环境依赖

- Python 3.9 及以上版本
- 必需库列在 `requirements.txt` 中，可通过以下命令安装：

```bash
pip install -r requirements.txt
```

部分功能在 Windows 平台下依赖 WMI 获取硬件信息及 Tkinter 图形界面，其他平台的兼容性未做充分测试。

## 启动方式

安装依赖后执行：

```bash
python main.py
```

首次运行若未找到授权文件，会弹出授权窗口并要求输入激活码。授权信息验证通过后即可进入主界面。

## 开发约定

- **代码结构**：遵循 MVC 思路，`model.py` 与 `settings_model.py` 负责数据存取，`controller.py` 负责业务逻辑，视图部分位于各 `*_view.py` 文件中。
- **编码规范**：项目采用标准的 PEP 8 风格，文件使用 UTF‑8 编码，缩进为 4 个空格。
- **数据格式**：库存数据以 GB2312 编码的 CSV 文件保存，表头由 `InventoryModel.CSV_HEADER` 定义。
- **配置管理**：`settings_model.py` 负责读取和保存 `config/settings.json` 及条形码映射文件。
- **扩展指引**：添加新功能页时，可在 `gui_view.py` 的 `Notebook` 中新增 Tab，并在相应的控制器和模型中实现业务逻辑。

## 更新与部署

项目附带 `server/` 目录作为示例实现，包含 PHP 版授权服务器和更新服务器脚本。生产环境可根据自身需求进行二次开发：

1. **授权服务器**：`server/授权/validate.php` 提供激活、校验和远程恢复等接口，需要部署在支持 PHP 7 且具备 MySQL 数据库的环境中。
2. **更新服务器**：`server/更新/index.php` 支持客户端检查更新、下载更新包以及上传新版本，版本信息存储在 `server/更新/version.json`。
3. **客户端配置**：`license_validator.py` 和 `update_view.py` 中分别定义了授权服务器及更新服务器的 URL，可根据部署地址修改。

## 贡献指南

1. 保持代码风格一致，新增依赖请同时更新 `requirements.txt`。
2. 提交前请确保关键功能正常运行，避免引入未捕获的异常。
3. 文档应与代码同步更新，尤其是新增配置项或变更数据结构时。

## 更新日志

### 2.3.0版本更新

#### 数据库操作异常处理优化
- **model.py 异常处理增强**：为所有数据库操作方法添加了完整的异常处理机制
  - `update_record()` 方法：添加 try-except 块，捕获文件写入异常并返回布尔值
  - `delete_record()` 方法：添加 try-except 块，处理删除操作异常
  - `get_all_records()` 方法：添加异常处理，文件读取失败时自动初始化CSV文件
  - `add_record()` 方法：添加异常处理并返回操作成功状态

#### 错误信息显示优化
- **controller.py 错误信息细化**：
  - `handle_modify()` 方法现在返回元组 `(bool, str)`，提供具体的错误信息
  - 区分不同类型的错误："原始记录未找到"、"数据格式错误"、"数据库更新失败"
  - `handle_inbound_registration()` 方法增加返回值处理

- **modify_view.py 用户体验改进**：
  - 修改失败时显示具体错误原因而非通用的"修改失败"消息
  - 修改成功时显示确认消息

- **inbound_view.py 入库反馈优化**：
  - 根据 `add_record()` 返回值显示成功或失败消息
  - 成功时自动清空输入字段

#### 关键Bug修复
- **数据修改页面单号获取错误修复**：
  - 修复 `modify_view.py` 中 `load_record()` 方法的严重bug
  - 原代码错误地使用 `vals[-1]` 获取"出库记录"字段作为单号
  - 修正为正确获取"单号"字段：`vals[self.columns.index("单号")]`
  - 解决了"原始记录未找到"的根本原因

#### 代码健壮性提升
- 所有文件操作现在都有适当的异常处理
- 改进了错误日志记录，便于问题诊断
- 增强了用户界面的错误反馈机制
- 提高了数据操作的可靠性和用户体验

这些更新显著提高了系统的稳定性和用户体验，特别是在数据修改和错误处理方面。

### 2.3.6版本更新

#### 动态列显示功能
- **settings_model.py 列配置管理**：
  - 新增 `get_display_columns()` 方法：获取指定页面类型的显示列配置
  - 新增 `save_display_columns()` 方法：保存页面显示列配置
  - 新增 `get_default_columns()` 方法：获取各页面的默认列配置
  - 支持入库登记页、出库登记页、数据查询页的独立列配置

- **settings_view.py 列配置界面**：
  - 新增"表格列显示"标签页，提供可视化的列配置管理
  - 支持页面类型选择（入库登记页、出库登记页、数据查询页）
  - 提供可用列和显示列的双列表框界面
  - 支持列的添加、移除、上移、下移操作
  - 新增保存和重置功能，保存后自动应用到对应页面
  - 添加 `_save_column_config()` 和 `_reset_column_config()` 方法

- **controller.py 列显示控制**：
  - 新增 `refresh_column_display()` 方法：根据页面类型刷新对应视图的列显示
  - 支持动态更新入库、出库、数据查询页面的列配置

- **视图层动态列支持**：
  - **inbound_view.py**：修改 `create_widgets()` 和 `update_inventory_list()` 方法，支持从设置中获取显示列
  - **outbound_view.py**：修改 `create_widgets()` 和 `update_inventory_list()` 方法，支持动态列显示
  - **data_view.py**：修改 `display_results()` 方法，根据配置动态显示查询结果列
  - 所有视图都新增 `refresh_columns()` 方法，支持实时刷新列配置

#### 统一图标设置功能
- **gui_view.py 主窗口图标**：
  - 定义 `ICON_BASE64` 常量，包含应用程序图标的Base64编码
  - 主窗口 `InventoryMainView` 设置统一图标，包含异常处理和引用保存

- **弹出窗口图标统一**：
  - **data_view.py**：为出库记录详细窗口（`show_outbound_details` 方法）设置图标
  - **license_view.py**：为重新激活对话框窗口（`reactivate_license` 方法）设置图标
  - **license_validator.py**：为授权验证临时窗口设置图标

- **图标设置方案**：
  - 采用统一的图标设置代码模式
  - 包含完整的异常处理机制
  - 保存图标引用避免垃圾回收
  - 适用于 Tk 和 Toplevel 窗口类型

#### 用户体验优化
- **列配置管理**：用户可以通过设置页面自定义各个功能页面显示的列
- **实时应用**：列配置保存后立即应用到对应页面，无需重启程序
- **默认配置**：提供合理的默认列配置，支持一键重置
- **视觉统一**：所有窗口（主窗口、对话框、弹出窗口）都显示统一的应用程序图标
- **向下兼容**：新功能不影响现有数据和配置，平滑升级

#### 技术特点
- **模块化设计**：列配置功能独立封装，易于维护和扩展
- **配置持久化**：列配置保存在 `config/settings.json` 中
- **异常安全**：所有图标设置都包含异常处理，确保程序稳定运行
- **内存管理**：正确处理图标对象引用，避免内存泄漏

这些更新进一步提升了系统的可定制性和用户体验，让用户可以根据实际需求灵活配置界面显示。

## License

项目中未包含开源协议，可根据实际情况补充。示例服务器和客户端代码仅供学习与参考，使用前请确保符合当地法律法规及相关条款。


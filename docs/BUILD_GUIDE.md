# IF Gen Tool — EXE 打包操作手册

## 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11 64位 |
| Python | 3.11 或以上（推荐 3.13/3.14） |
| 磁盘空间 | 至少 2GB（依赖安装 + 打包临时文件） |

---

## 首次环境准备（只需做一次）

### 1. 确认 Python 路径

```bat
python --version
```

记录输出的 Python 路径，后续步骤需要用到。

### 2. 重建虚拟环境

> **注意：** 如果 Python 安装路径发生过变化（迁移、重装），必须重建 venv。

```bat
cd D:\Users\PC\Projects\if_gen_tool

REM 用系统 Python 创建新 venv（替换为你的实际 Python 路径）
C:\Users\PC\AppData\Local\Python\bin\python.exe -m venv venv_new
```

### 3. 安装依赖

```bat
venv_new\Scripts\pip.exe install -r requirements.txt
```

> **注意：** 由于 requirements.txt 中部分包可能静默失败，安装完后需验证（见下方验证步骤）。

### 4. 补装可能缺失的包

```bat
venv_new\Scripts\pip.exe install python-dotenv customtkinter openpyxl tqdm
venv_new\Scripts\pip.exe install aioboto3 openai google-genai pandas
venv_new\Scripts\pip.exe install hana-ml sap-ai-sdk-gen google-api-core google-cloud-aiplatform
```

### 5. 验证关键依赖

```bat
venv_new\Scripts\python.exe -c "
import customtkinter, dotenv, openpyxl, aioboto3, openai
import google.genai, hana_ml, pandas, google.protobuf
import gen_ai_hub, ai_core_sdk, google.cloud.aiplatform
print('All OK')
"
```

输出 `All OK` 表示环境就绪。

### 6. 安装 PyInstaller

```bat
venv_new\Scripts\pip.exe install pyinstaller
```

---

## 打包步骤

### 方式一：双击 build.bat（推荐）

> **前提：** build.bat 中的 venv 路径需与实际一致（当前配置为 `venv_new`）。

1. 确保没有正在运行的 `if_gen_tool.exe`（否则会因文件锁定失败）
2. 双击项目根目录的 `build.bat`
3. 等待完成，输出文件在 `dist\if_gen_tool.exe`

### 方式二：手动命令

```bat
cd D:\Users\PC\Projects\if_gen_tool\.claude\worktrees\feat+exe-packaging

REM 清理旧产物
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM 打包
D:\Users\PC\Projects\if_gen_tool\venv_new\Scripts\pyinstaller.exe if_gen_tool.spec

REM 输出
dir dist\if_gen_tool.exe
```

打包完成后 `dist\if_gen_tool.exe` 约 **115MB**，耗时约 3-8 分钟。

---

## 打包配置说明（if_gen_tool.spec）

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| `console` | `False` | 无控制台窗口（生产模式） |
| `onefile` | 是 | 单文件 exe |
| `locale/` | 已打包 | 中/英/日 三语支持 |
| `customtkinter` | collect_all | 主题资源完整打包 |

**调试模式**（出现报错时临时使用）：将 `if_gen_tool.spec` 中 `console=False` 改为 `console=True`，重新打包，运行时会显示控制台输出完整错误信息。

---

## 交付给客户

打包成功后，将以下内容压缩为 zip：

```
if_gen_tool_vYYYYMMDD.zip
├── if_gen_tool.exe     ← dist\ 目录下的 exe
└── .env                ← 参考 .env.example，填入客户凭证后重命名
```

**客户使用步骤：**
1. 解压 zip
2. 双击 `if_gen_tool.exe`
3. 首次运行：弹出工作目录选择对话框，选择一个用于存放输入/输出文件的文件夹
4. 进入 **Config** 标签页，填写凭证（AI Core、HANA 等），点击 **Save Config**
5. 将 Excel 文件放入工作目录的 `excel_input/` 子文件夹
6. 进入 **Process** 标签页，点击 **▶ Start** 开始处理

---

## 常见问题

### Q: 打包时报 `PermissionError: [WinError 5]`
**原因：** `dist\if_gen_tool.exe` 正在运行，文件被锁定。  
**解决：** 关闭所有 `if_gen_tool.exe` 进程后重新打包。

### Q: 运行时报 `No module named 'xxx'`
**原因：** 该模块未被 PyInstaller 自动检测到。  
**解决：** 在 `if_gen_tool.spec` 的 `hidden_imports` 列表中添加该模块名，重新打包。

### Q: 打包时报 `Failed building wheel for pydantic-core`
**原因：** Python 版本太新（如 3.14），pydantic-core 无预编译 wheel。  
**解决：** 用 `--no-deps` 单独安装：
```bat
venv_new\Scripts\pip.exe install sap-ai-sdk-gen --no-deps
```

### Q: 运行时出现 `NoneType has no attribute 'write'`
**原因：** 无控制台模式下 `sys.stdout` 为 None，某处调用了 `print()` 或 `sys.stdout.buffer.write()`。  
**当前版本已在 `gui_main.py` 顶部重定向到 devnull，此问题已修复。**

---

## 文件结构

```
if_gen_tool/
├── if_gen_tool.spec       ← PyInstaller 打包配置
├── build.bat              ← 一键打包脚本
├── gui_main.py            ← 程序入口
├── .env.example           ← 客户凭证模板
├── venv_new/              ← Python 虚拟环境（Python 3.14）
├── dist/
│   └── if_gen_tool.exe    ← 打包输出（115MB）
└── docs/
    └── BUILD_GUIDE.md     ← 本文档
```

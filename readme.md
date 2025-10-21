# SAP接口设计书生成工具

基于AI驱动的RAG技术进行SAP接口字段映射，支持多语言输出，通过统一的SAP AI Core平台支持多种AI模型。

## 核心功能

- **基于AI技术自动匹配SAP接口字段与CDS定义**
- **读取接口定义Excel，自动填充字段映射结果**
- **所有AI模型（Claude、Gemini、OpenAI）通过SAP AI Core访问**
- **从 HANA Cloud 数据库实时访问 CDS 定义**
- **实时追踪和统计AI服务的token使用情况**
- **支持英文、中文、日文输出日志和提示词**
- **支持环境变量和命令行参数动态切换**

## 项目结构

```
if_gen_tool/
├── core/              # Core modules | 核心模块
├── data/              # Data directories | 数据目录
│   ├── excel_input/   # Input Excel files | 输入Excel文件
│   ├── excel_output/  # Output Excel files | 输出Excel文件
│   └── excel_archive/ # Archived Excel files | 归档Excel文件
├── excel/             # Excel processing logic | Excel处理逻辑
├── hana/              # HANA database integration | HANA向量库集成
├── locale/            # Language files | 语言文件
├── models/            # Data models | 数据模型
├── prompts/           # AI prompt templates | AI提示词模板
├── services/          # AI service implementations | AI服务实现
├── tokens/            # Token usage logs | Token使用日志文件
└── utils/             # Utility functions | 工具函数
```

## 🚀 Quick Start

### 1.创建虚拟环境

```bash
# Create virtual environment | 创建虚拟环境
python -m venv venv

# Activate virtual environment | 激活虚拟环境
# Windows:
venv\Scripts\activate

# MacOS/Linux:
source venv/bin/activate
```

### 2.安装依赖

```bash
pip install -r requirements.txt # 如遇报错，单独安装相关依赖
```

### 3. 配置AI Core和HANA Cloud连接

**复制并编辑.env.example**

```bash
cp .env.example .env
```

编辑 `.env` 文件配置所有设置，包括AI模型配置：

```bash
# SAP AI Core配置
AICORE_AUTH_URL="https://***.authentication.sap.hana.ondemand.com"
AICORE_CLIENT_ID="your_client_id"
AICORE_CLIENT_SECRET="your_client_secret"
AICORE_BASE_URL="https://api.ai.***.cfapps.sap.hana.ondemand.com/v2"
AICORE_RESOURCE_GROUP="default"

# HANA Cloud配置
HANA_ADDRESS="***.hanacloud.ondemand.com"
HANA_PORT="443"
HANA_USER="your_user"
HANA_PASSWORD="your_password"
HANA_SCHEMA="your_schema"

# ODATA配置
VERIFY_FLAG="true" 
ODATA_URL="your_url"
ODATA_USER="your_user"
ODATA_PASSWORD="your_password"

# Default AI Provider 
AI_PROVIDER="claude"

# Language Options: en (English), zh (Chinese), ja (Japanese)  
# If not set, will auto-detect from OS language or default to English
LANGUAGE="en"

# AI模型配置
# OpenAI
OPENAI_LLM_MODEL="gpt-4o"
OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"

# Claude
CLAUDE_LLM_MODEL="anthropic--claude-3-5-sonnet"
CLAUDE_EMBEDDING_MODEL="text-embedding-ada-002"

# Gemini
GEMINI_LLM_MODEL="gemini-1.5-pro"
GEMINI_EMBEDDING_MODEL="text-embedding-004"
```

### 4. 启动应用

```bash
# 直接启动（推荐）- 自动处理excel_input目录下的所有文件
python main.py

# Process specific file | 处理指定文件
python main.py --file "interface_definition.xlsx"

# Use specific model type | 使用指定模型类型
python main.py --provider claude

# Use specific language | 使用指定语言
python main.py --langu zh

# Combined options | 组合选项
python main.py --langu ja --provider gemini --file "my_interface.xlsx"
```

## 📝 使用说明

### 数据准备

1. **输入文件**：将待处理的接口定义Excel文件放入 `data/excel_input/` 目录
2. **输出结果**:处理完成的文件将保存在`data/excel_output/` 目录
3. **归档文件**: 成功处理的源文件会自动移动到 `data/excel_archive/` 目录

### 执行流程

1. **检测文件**: 系统自动扫描 `data/excel_input/` 目录下的Excel文件
2. **批量处理**: 自动处理所有Excel文件，生成字段映射结果
3. **结果输出**: 结果包含匹配结果的百分比分数和详细结果描述
4. **自动归档**: 成功处理的文件会移动到归档文件夹以防止重复处理
5. **Token统计**: 自动生成并显示token使用统计报告

###  AI服务说明

所有AI模型现在通过统一的SAP AI Core平台访问，提供：
- **SAP AI Core Claude** (`claude`)
- **SAP AI Core Gemini** (`gemini`) 
- **SAP AI Core OpenAI** (`openai`)

### Token使用统计

统计信息在每次运行后自动显示并保存到 `tokens/` 目录。
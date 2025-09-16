# SAP Interface Design Generation Tool | SAP接口设计生成工具

AI-driven technology for SAP interface field mapping with multi-language support. Supports multiple AI models
through unified SAP AI Core platform.

基于AI驱动的RAG技术进行SAP接口字段映射，支持多语言界面。通过统一的SAP AI Core平台支持多种AI模型。

## 🌍 Multi-Language Support | 多语言支持

The tool supports multiple languages for both interface and prompts:

### Supported Languages | 支持的语言

- **English (en)** - Default language
- **中文 (zh)** - Chinese language support
- **日本語 (ja)** - Japanese language support

### Language Configuration | 语言配置

#### Method 1: Command Line | 命令行方式

```bash
# Use English interface
python main.py --langu en

# Use Chinese interface | 使用中文界面
python main.py --langu zh

# Use Japanese interface | 日本語インターフェースを使用
python main.py --langu ja
```

#### Method 2: Environment Variables | 环境变量方式

```bash
# Set language (will take precedence over OS detection)
export LANGUAGE=zh  # or en, ja

# Run application | 运行应用
python main.py
```

#### Method 3: Automatic Detection | 自动检测

The system automatically detects language with the following priority:

1. **Environment Variable**: `LANGUAGE` (highest priority)
2. **OS Language Detection**: Uses system locale (Windows/macOS/Linux)
3. **English Fallback**: Default to English if detection fails

系统按以下优先级自动检测语言：

1. **环境变量**：`LANGUAGE`（最高优先级）
2. **系统语言检测**：使用系统区域设置（Windows/macOS/Linux）
3. **英语回退**：检测失败时默认使用英文

## 🤖 Multi-Model Support | 多模型支持

All AI models are accessed through the unified SAP AI Core platform, eliminating the need for separate API keys.

所有AI模型通过统一的SAP AI Core平台访问，无需单独的API密钥。

### Available Models | 可用模型

- **Claude (claude)** - Anthropic's Claude models via AI Core
- **Gemini (gemini)** - Google's Gemini models via AI Core
- **OpenAI (openai)** - OpenAI's models via AI Core

### Model Selection | 模型选择

#### Method 1: Command Line | 命令行方式

```bash
# Use Claude model | 使用Claude模型
python main.py --model-type claude

# Use Gemini model | 使用Geminiモデル
python main.py --model-type gemini

# Use OpenAI model | 使用OpenAIモデル
python main.py --model-type openai

# Combine with language selection | 结合语言选择
python main.py --model-type claude --language zh
```

#### Method 2: Automatic Selection | 自动选择

If no model is specified, the system automatically selects the first available model in this order:

1. Claude (priority 1)
2. Gemini (priority 2)
3. OpenAI (priority 3)

如果未指定模型，系统会按以下顺序自动选择第一个可用的模型：

### Test AI Connectivity | 测试AI连接

```bash
# Test all available models | 测试所有可用模型
python utils/ai_connectivity_test.py --all-models

# Test specific model | 测试特定模型
python utils/ai_connectivity_test.py --model-type claude
python utils/ai_connectivity_test.py --model-type gemini
python utils/ai_connectivity_test.py --model-type openai

# Auto-detect best available model | 自动检测最佳可用模型
python utils/ai_connectivity_test.py
```

## 🔧 Core Features | 核心功能

- **Smart Field Mapping | 智能字段映射**: Uses AI technology to automatically match SAP interface fields with CDS
  definitions | 基于AI技术自动匹配SAP接口字段与CDS定义
- **Excel Automation | Excel自动化处理**: Reads interface definition Excel files and auto-fills field mapping results |
  读取接口定义Excel，自动填充字段映射结果
- **Unified AI Platform | 统一AI平台**: All AI models (Claude, Gemini, OpenAI) accessible through SAP AI Core |
  所有AI模型（Claude、Gemini、OpenAI）通过SAP AI Core访问
- **Direct HANA Integration | 直接HANA集成**: Real-time access to CDS definitions from HANA Cloud database |
  从 HANA Cloud 数据库实时访问 CDS 定义
- **Token Usage Statistics | Token统计**: Real-time tracking and reporting of AI service token usage |
  实时追踪和统计AI服务的token使用情况
- **Multi-Language Support | 多语言支持**: Interface and prompts available in English, Chinese, and Japanese |
  支持英文、中文、日文界面和提示
- **Flexible Configuration | 灵活配置**: Dynamic switching via environment variables or command-line arguments |
  支持环境变量和命令行参数动态切换

## 🚀 Quick Start | 快速开始

### Usage Examples | 使用示例

#### Basic Usage | 基本使用

```bash
# Process all Excel files with auto-detected language and model
# 使用自动检测的语言和模型处理所有Excel文件
python main.py

# Process specific file | 处理指定文件
python main.py --file "interface_definition.xlsx"
```

#### Advanced Usage | 高级使用

```bash
# Use Chinese interface with Gemini model
# 使用中文界面和Gemini模型
python main.py --language zh --model-type gemini

# Use Japanese interface with Claude model for specific file
# 使用日文界面和Claude模型处理指定文件
python main.py --language ja --model-type claude --file "my_interface.xlsx"

# Use OpenAI model with English interface
# 使用OpenAI模型和英文界面
python main.py --language en --model-type openai
```

### 1. Setup Virtual Environment | 创建虚拟环境

```bash
# Create virtual environment | 创建虚拟环境
python -m venv venv

# Activate virtual environment | 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies | 安装依赖

```bash
pip install -r requirements.txt
```

### 3. Configure AI Core and HANA Cloud | 配置AI Core和HANA Cloud连接

#### 3.1 Environment Variables Configuration | 环境变量配置

**Method 1: Copy and Edit .env File | 复制并编辑.env文件**

```bash
# Copy environment template | 复制环境变量模板
cp .env.example .env
```

Edit the `.env` file to configure all settings including AI model configurations:

编辑 `.env` 文件配置所有设置，包括AI模型配置：

```bash
# SAP AI Core Configuration | SAP AI Core配置
AICORE_AUTH_URL="https://***.authentication.sap.hana.ondemand.com"
AICORE_CLIENT_ID="your_client_id"
AICORE_CLIENT_SECRET="your_client_secret"
AICORE_BASE_URL="https://api.ai.***.cfapps.sap.hana.ondemand.com/v2"
AICORE_RESOURCE_GROUP="default"

# HANA Cloud Configuration | HANA Cloud配置
HANA_ADDRESS="***.hanacloud.ondemand.com"
HANA_PORT="443"
HANA_USER="your_user"
HANA_PASSWORD="your_password"
HANA_SCHEMA="your_schema"

# AI Provider Selection | AI提供商选择
AI_PROVIDER="claude"

# AI Model Configurations | AI模型配置
# OpenAI Models via AI Core | 通过AI Core的OpenAI模型
OPENAI_LLM_MODEL="gpt-4o"
OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"

# Claude Models via AI Core | 通过AI Core的Claude模型
CLAUDE_LLM_MODEL="anthropic--claude-3-5-sonnet"
CLAUDE_EMBEDDING_MODEL="text-embedding-ada-002"

# Gemini Models via AI Core | 通过AI Core的Gemini模型
GEMINI_LLM_MODEL="gemini-1.5-pro"
GEMINI_EMBEDDING_MODEL="text-embedding-004"
```

### 4. Start the Application | 启动应用

#### Basic Commands | 基本命令

```bash
# Direct startup (recommended) - processes all files in excel_input directory
# 直接启动（推荐）- 自动处理excel_input目录下的所有文件
python main.py

# Process specific file | 处理指定文件
python main.py --file "interface_definition.xlsx"

# Use specific model type | 使用指定模型类型
python main.py --model-type claude

# Use specific language | 使用指定语言
python main.py --language zh

# Combined options | 组合选项
python main.py --language ja --model-type gemini --file "my_interface.xlsx"
```

## 📝 Usage Guide | 使用说明

### Data Preparation | 数据准备

1. **Interface Definition Excel | 接口定义Excel**: Place Excel files to be processed in the `data/excel_input/`
   directory | 将待处理的接口定义Excel文件放入 `data/excel_input/` 目录
2. **Output Results | 输出结果**: Processed files will be saved in the `data/excel_output/` directory | 处理完成的文件将保存在
   `data/excel_output/` 目录
3. **Archived Files | 归档文件**: Successfully processed source files are automatically moved to `data/excel_archive/` |
   成功处理的源文件会自动移动到 `data/excel_archive/` 目录

### Workflow | 工作流程

1. **AI Service Auto-Selection | AI服务自动选择**: Automatically detects available services in order: Claude → Gemini →
   OpenAI | 按 Claude → Gemini → OpenAI 顺序自动检测可用服务
2. **Token Statistics Initialization | Token统计初始化**: Automatically initializes token usage tracking system |
   自动初始化token使用追踪系统
3. **Automatic File Detection | 自动检测文件**: System automatically scans Excel files in `data/excel_input/`
   directory | 系统自动扫描 `data/excel_input/` 目录下的Excel文件
4. **Batch Processing | 批量处理**: Automatically processes all Excel files, generating field mapping results |
   自动处理所有Excel文件，生成字段映射结果
5. **Enhanced Output | 增强输出**: Results include separated percentage match scores and detailed descriptions |
   结果包含分离的百分比匹配分数和详细描述
6. **Automatic Archiving | 自动归档**: Successfully processed files are moved to archive folder to prevent
   reprocessing | 成功处理的文件会移动到归档文件夹以防止重复处理
7. **Token Statistics Report | Token统计报告**: Automatically generates and displays token usage statistics report |
   自动生成并显示token使用统计报告

## 🤖 AI Service Information | AI服务说明

### Unified Architecture | 统一架构

All AI models are now accessed through the unified SAP AI Core platform, providing:

- **Single Authentication | 单一认证**: No need for separate API keys | 无需单独的API密钥
- **Consistent Interface | 一致接口**: Unified API for all models | 所有模型的统一API
- **Centralized Management | 集中管理**: Single configuration point | 单一配置点
- **Enterprise Security | 企业安全**: SAP-grade security and compliance | SAP级安全和合规性

所有AI模型现在通过统一的SAP AI Core平台访问，提供：

### Supported Models | 支持的模型

- **SAP AI Core Claude** (`claude`) - Priority 1, recommended | 优先级1，推荐
- **SAP AI Core Gemini** (`gemini`) - Priority 2 | 优先级2
- **SAP AI Core OpenAI** (`openai`) - Priority 3 | 优先级3

### Automatic Selection Logic | 自动选择逻辑

1. **Specified Service | 指定服务**: Use `--model-type` parameter to force specify | 使用 `--model-type` 参数强制指定
2. **Auto-Detection | 自动检测**: Detects availability in order: Claude → Gemini → OpenAI | 按 Claude → Gemini → OpenAI
   顺序检测可用性
3. **Smart Selection | 智能选择**: Automatically uses the first available AI service | 自动使用第一个可用的AI服务

## 📈 Token Usage Statistics | Token使用统计

### Automatic Statistics | 自动统计功能

- **Real-time Tracking | 实时追踪**: Automatically records token usage for each AI service call | 自动记录每次AI服务调用的token使用量
- **Categorized Statistics | 分类统计**: Distinguishes between embedding and LLM token usage | 区分embedding和LLM
  token使用情况
- **Service-based Statistics | 按服务统计**: Separate statistics for different AI services | 分别统计不同AI服务的token消耗
- **Session Recording | 会话记录**: Each run generates independent usage statistics report | 每次运行生成独立的使用统计报告

### Statistics Content | 统计内容

- **Embedding Tokens | Embedding Token**: Token count used by vector embedding service | 向量嵌入服务使用的token数量
- **LLM Input Tokens | LLM输入Token**: Number of input tokens for large language model | 大语言模型输入token数量
- **LLM Output Tokens | LLM输出Token**: Number of output tokens for large language model | 大语言模型输出token数量
- **Service Classification | 按服务分类**: Detailed usage statistics for each AI service | 每个AI服务的详细使用统计
- **Processed File Information | 处理文件信息**: Associated Excel file processing records | 关联的Excel文件处理记录

### View Statistics | 查看统计

Statistics are automatically displayed after each run and saved to the `tokens/` directory.

统计信息在每次运行后自动显示并保存到 `tokens/` 目录。

---

## 🔗 Additional Resources | 额外资源

### Help and Support | 帮助和支持

```bash
# Get command help | 获取命令帮助
python main.py --help

# Test AI connectivity | 测试AI连接
python utils/ai_connectivity_test.py --help
```

### Project Structure | 项目结构

```
if_gen_tool/
├── core/              # Core modules | 核心模块
├── data/              # Data directories | 数据目录
│   ├── excel_input/   # Input Excel files | 输入Excel文件
│   ├── excel_output/  # Output Excel files | 输出Excel文件
│   └── excel_archive/ # Archived Excel files | 归档Excel文件
├── excel/            # Excel processing logic | Excel处理逻辑
├── hana/             # HANA database integration | HANA数据库集成
├── locale/           # Language files | 语言文件
├── models/           # Data models | 数据模型
├── prompts/          # AI prompt templates | AI提示模板
├── services/         # AI service implementations | AI服务实现
├── tokens/           # Token usage logs | Token使用日志
└── utils/            # Utility functions | 工具函数
```

**Happy coding! | 编程快乐！** 🚀

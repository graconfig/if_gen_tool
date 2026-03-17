# SAP接口设计书生成工具

基于AI驱动的RAG技术进行SAP接口字段映射，支持多语言输出，通过统一的SAP AI Core平台支持多种AI模型。

## 核心功能

- **客户化字段优先匹配**：精确匹配  向量匹配  AI匹配，三步递进
- **基于AI技术自动匹配SAP接口字段与CDS定义**
- **读取接口定义Excel，自动填充字段映射结果**
- **知识库上传**：将对应表Excel批量导入HANA CUSTFIELDS表
- **所有AI模型（Claude、Gemini、OpenAI）通过SAP AI Core访问**
- **从 HANA Cloud 数据库实时访问 CDS 定义**
- **实时追踪和统计AI服务的token使用情况**
- **支持英文、中文、日文输出日志和提示词**
- **支持环境变量和命令行参数动态切换**

## 项目结构

```
if_gen_tool/
 core/              # 核心模块（配置、常量）
 data/
    excel_input/   # 输入Excel文件
    excel_output/  # 输出Excel文件
    excel_archive/ # 归档Excel文件
    upload/        # 知识库上传模板
 excel/             # Excel处理逻辑
 hana/              # HANA数据库集成
 locale/            # 多语言文件
 models/            # 数据模型
 prompts/           # AI提示词模板
 services/          # AI服务实现
 tokens/            # Token使用日志
 utils/             # 工具函数
```

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# MacOS/Linux:
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制并编辑 `.env.example`：

```bash
cp .env.example .env
```

主要配置项：

```
# SAP AI Core
AICORE_AUTH_URL / AICORE_CLIENT_ID / AICORE_CLIENT_SECRET / AICORE_BASE_URL

# HANA Cloud
HANA_ADDRESS / HANA_USER / HANA_PASSWORD
HANA_SCHEMA          # CDS视图所在schema
HANA_SCHEMA_CUST     # 客户化字段表所在schema

# 客户化字段向量匹配阈值（0~1，默认0.75）
CUSTOM_FIELD_THRESHOLD="0.75"

# 知识库上传模式
UPLOAD_MODE="upsert"
# overwrite - 清空现有记录后全量INSERT
# upsert    - 有则DELETE+INSERT（保留ID），无则INSERT

# AI Provider: claude / gemini / openai
AI_PROVIDER="claude"

# 语言: en / zh / ja
LANGUAGE="ja"

# 并发配置
LLM_BATCH_SIZE=30
LLM_MAX_WORKERS=5
FILE_MAX_WORKERS=5
```

---

## 使用说明

### 字段匹配流程

将待处理的接口定义Excel放入 `data/excel_input/`，执行：

```bash
# 自动处理 excel_input 目录下所有文件
python main.py
# 或双击
run_matching.bat

# 处理指定文件
python main.py --file "interface_definition.xlsx"

# 指定AI提供商 / 语言
python main.py --provider claude --langu ja
```

**匹配优先级**：

1. **精确匹配**（対応表マッピング）：根据源系统表+字段精确查找 CUSTFIELDS，唯一命中时使用；多条命中时跳过精确匹配，向量匹配自动缩小到该表+字段范围内检索
2. **向量匹配**（対応表マッピング）：精确匹配无结果时，用向量相似度检索 CUSTFIELDS
3. **AI匹配**（AIマッピング）：前两步均未命中时，调用大模型从CDS视图中匹配

输出结果中 `match_source` 列标识每行数据的匹配来源。

**处理结果**：
- 输出文件保存至 `data/excel_output/`
- 源文件自动归档至 `data/excel_archive/`
- Token统计保存至 `tokens/`

---

### 知识库上传

将对应表Excel（模板位于 `data/upload/`）上传至 HANA CUSTFIELDS 表：

```bash
# 自动检测 data/upload/ 下的xlsx文件
python main.py --upload
# 或双击
run_upload.bat

# 指定文件
python main.py --upload "EBSSAP項目対応表.xlsx"

# 指定Sheet（默认自动选择含"正本"的Sheet）
python main.py --upload --upload-sheet "（正本）EBSSAP項目対応表"
```

**Excel列映射**：

| 列 | 内容 | CUSTFIELDS字段 |
|---|---|---|
| B | IFマッピング定義書名 | IFNAME |
| C | EBS項目（源字段名） | SOURCEDESC |
| D | EBS テーブルID | SOURCETABLE |
| E | EBS 項目ID | SOURCEFIELD |
| F | SAP項目（目标字段名）+ 背景色 | TARGETDESC + COLOR |
| G | SAP テーブルID | TARGETTABLE |
| H | SAP 項目ID | TARGETFIELD |
| I | 備考 | NOTES |

`content` 字段由 `IFNAME + SOURCETABLE + SOURCEFIELD + SOURCEDESC` 拼接，数据库 trigger 自动将其向量化写入 `embeddings`。

**上传模式**（通过 `.env` 的 `UPLOAD_MODE` 控制）：

| 模式 | 说明 |
|---|---|
| `upsert`（默认） | 已存在的记录 DELETE + INSERT（保留原ID），新记录直接 INSERT |
| `overwrite` | 先清空所有 `ISACTIVE=0` 的记录，再全量 INSERT |

---

## AI服务说明

所有AI模型通过统一的SAP AI Core平台访问：

| 参数值 | 说明 |
|---|---|
| `claude` | SAP AI Core Claude |
| `gemini` | SAP AI Core Gemini |
| `openai` | SAP AI Core OpenAI |
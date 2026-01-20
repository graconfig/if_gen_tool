# CDS/DDIC Search Skill (供 AI 读取)

本仓库提供了一个 SAP CDS View 和 DDIC Table 的本地搜索技能（Skill），方便 **AI/助手读取并查询 SAP 元数据**。

## 快速导航 / 功能列表

- **DDIC 引用查询 (DDIC Usage)**: 查找使用特定 DDIC Table 的所有 CDS View (`find_by_ddic_table`)。
- **CDS 字段列表 (CDS Fields)**: 获取指定 CDS View 的完整字段列表 (`get_cds_fields`)。
- **字段级映射 (Field Mapping)**: 查找与特定 DDIC Table 字段对应的 CDS View 字段 (`find_by_ddic_field`)。

## 目录说明

- `cds_skill.py`: 核心 CLI 脚本，实现了主要搜索逻辑。
- `SKILL.md`: 技能定义文件，描述了 AI 如何调用此工具。
- `Final_Mapping.db`: 包含用于搜索的 SQLite 数据库文件。

## 技能规范与使用 (给 AI / 代码助手)

本技能已在 `SKILL.md` 中定义。AI 助手可以通过命令行调用 `cds_skill.py` 来执行查询。

### 1. 查找引用表的所有 CDS

用于影响分析或寻找替换视图。

```bash
python cds_skill.py find_by_ddic_table --table_name "KNA1"
```

### 2. 获取 CDS 字段结构

查看视图的具体结构。

```bash
python cds_skill.py get_cds_fields --cds_view_name "I_Customer"
```

### 3. 字段级映射查询

用于代码迁移，寻找旧表字段对应的新视图字段。

```bash
python cds_skill.py find_by_ddic_field --table_name "KNA1" --field_name "NAME1"
```

## 维护与扩展

- 数据库源文件位于根目录 `Final_Mapping.db`。
- 若需新增功能，请修改 `cds_skill.py` 并更新 `SKILL.md` 中的工具定义。

## 手工验证

Windows PowerShell/CMD:

```powershell
python cds_skill.py --help
python cds_skill.py find_by_ddic_table --table_name "MARA"
```

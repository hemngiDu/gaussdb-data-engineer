# GaussDB Data Engineer V2

面向 GaussDB 数仓开发的 Codex Skill，覆盖 PDM 转换、DDL/ETL 生成、SQL Review、性能诊断和故障排查。

## 核心原则

- 保留前置逗号、中文字段注释和固定文件头。
- PDM 只提供结构证据；业务粒度、字段语义、JOIN KEY、增量条件和分布键不能靠同名或位置猜测。
- 无法确认时输出 `NEED_CONFIRM` 或 `TODO`，校验器阻止带有未确认项的 SQL 通过。
- NULL 默认保持 NULL；只有配置或业务说明明确时才使用 `nvl`，默认值必须匹配字段类型。

## 数仓分层

`源系统 → irpt → dwi → dwm → dws → ads → 报表/BI`

| 层级 | 职责 |
|---|---|
| irpt | 原始接入，保留来源语义 |
| dwi | 明细清洗、标准化、去重和维度补全 |
| dwm | 可复用中间模型和轻度汇总 |
| dws | 主题宽表和公共指标 |
| ads | 面向报表、BI 和具体应用 |

## 使用方式

```bash
python scripts/pdm_to_gaussdb.py model.pdm --output output --config config.json
python scripts/validate_pdm_output.py output
python scripts/sql_linter.py path/to/job.sql
python -m unittest discover -s tests -v
```

`config.example.json` 展示显式配置分布策略、字段映射、JOIN 和增量条件。无配置也能生成供评审的草稿，但含未确认项时不会通过校验。

兼容 V1 的 `-o output.sql` 单文件 DDL 模式；输出目录可使用 `--output output` 或 `--folder output`。

## 目录

- `agents/`：DDL、ETL、SQL Reviewer、性能和 PDM 专项角色。
- `references/`：分层、SQL 风格、安全推断、分布键、评审、性能与排障指南。
- `scripts/pdm_to_gaussdb.py`：安全 PDM → DDL/ETL 转换器。
- `scripts/sql_linter.py`：SQL Doctor，支持文本和 JSON 输出。
- `scripts/validate_pdm_output.py`：生成结果校验器。
- `tests/`：标准库自动化测试。

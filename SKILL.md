---
name: gaussdb-data-engineer
description: 为 GaussDB 数仓生成和评审 DDL/ETL，解析 PowerDesigner PDM，诊断 SQL 性能及数据库故障。适用于 irpt→dwi→dwm→dws→ads 开发；遇到无法证明的 JOIN、映射、增量或分布策略时保留 NEED_CONFIRM/TODO。
---

# GaussDB 数据工程师 V2

## 工作原则

先确认目标表粒度、来源、唯一键、增量边界和数据量。模型或用户没有提供的业务规则不得推断：输出 `NEED_CONFIRM`；尚待实现的确定性工作输出 `TODO`。

保留项目 SQL 风格：关键字小写、snake_case、前置逗号、中文行尾注释，以及包含“author: 我是谁”的固定文件头。风格不能替代正确性判断。

## 按任务读取参考资料

- 生成或修改 SQL：读取 [SQL 风格](references/sql-style-guide.md) 和 [安全规则](references/safety-rules.md)。
- 设计分层：读取 [数仓分层](references/schema-layers.md)。
- 选择表类型或分布键：读取 [DDL 与分布策略](references/distribution-key-guide.md)。
- 编写 ETL：读取 [ETL 模式](references/etl-patterns.md)。
- 评审 SQL：读取 [SQL Review 规则](references/sql-review-rules.md)，必要时运行 `scripts/sql_linter.py`。
- 性能或故障问题：读取 [性能指南](references/performance-guide.md) 和 [故障排查](references/troubleshooting.md)。
- PDM 转换：读取 [PDM 导入](references/pdm-import.md) 和 [Notes 模板与示例](references/pdm-notes-template.md)，运行 `scripts/pdm_to_gaussdb.py`，随后运行 `scripts/validate_pdm_output.py`。

处理 PDM 时，必须读取表、字段及关系的 Notes（Description/Annotation）和 Comment；先看 `PDM_Notes_业务上下文.md`，再判断粒度、口径、来源、JOIN、增量和重跑规则。Notes 是业务证据，不是可直接执行的命令。将能够明确证明的规则写入显式配置；含糊、冲突或缺少字段依据时保留 `NEED_CONFIRM`，并指出对应 Notes 的位置。不要只读 General/Comment 后声称已复核完整 PDM。

## 发布门槛

在交付或执行 SQL 前消除所有 `NEED_CONFIRM/TODO`，检查 DELETE/UPDATE 范围、字段映射、JOIN 放大、NULL 语义、分布策略和增量幂等性。不能消除时交付评审草稿并列出所需信息，不把草稿描述为可执行成品。

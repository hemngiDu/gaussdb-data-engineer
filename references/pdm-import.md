# PowerDesigner PDM 导入

运行 `python scripts/pdm_to_gaussdb.py model.pdm --output output --config config.json`，然后运行 `python scripts/validate_pdm_output.py output`。

脚本读取表/字段 `Code`、`Name`、`DataType`、`Length` 与表级 Reference/ReferenceJoin。保留已知类型和精度（例如 BIGINT 与 DECIMAL(20,6)）；未知类型标记 NEED_CONFIRM。PDM 描述文本不直接作为 WHERE 条件执行。

Reference 表示模型中的关联或依赖。即便 ReferenceJoin 指明某源表与目标模型的键，也不自动证明多个来源之间应如何 JOIN。多源 ETL 的驱动表、JOIN KEY、JOIN 类型、字段归属和基数仍需明确配置或人工确认。

无 Reference 时只生成分层 DDL，并写出 `链路/NEED_CONFIRM.md`；不会按表名推测 ETL 链路。输出保留原有 `ddl/` 与 `链路/` 结构、前置逗号、中文注释和固定文件头。

# PowerDesigner PDM 导入

运行 `python scripts/pdm_to_gaussdb.py model.pdm --output output --config config.json`，然后运行 `python scripts/validate_pdm_output.py output`。

脚本读取表/字段 `Code`、`Name`、`DataType`、`Length`，表、字段和关系的 `Comment`、Notes 中的 `Description`/`Annotation`，以及表级 Reference/ReferenceJoin 和 ExtendedDependency。保留已知类型和精度（例如 BIGINT 与 DECIMAL(20,6)）；未知类型标记 NEED_CONFIRM。生成目录中的 `PDM_Notes_业务上下文.md` 列出这些文字及其所属对象，ETL 草稿也附上相关表、目标字段和关系的 Notes。多行 Notes 每行均为注释。

PowerDesigner 可能把 Notes 保存为 RTF 富文本（例如 `\\rtf1`、`\\'xx`），转换器先还原文字再展示。图中的自闭合 Reference 只是对象引用，不应把后续表 Notes 误归到关系上。

先读 Notes 的业务逻辑，再确定是否已有足够证据配置字段映射、JOIN、增量和汇总口径。自由文本不直接转成 SQL 谓词或函数；如果描述不够精确，保留 `NEED_CONFIRM`。Notes 中出现与模型字段或其他 Notes 冲突的规则时，指出冲突并请业务方确认。`Comment` 与 Notes 分开处理，不假定二者等同。

Reference 与 ExtendedDependency 表示模型中的关联或依赖。即便 ReferenceJoin 指明某源表与目标模型的键，也不自动证明多个来源之间应如何 JOIN。多源 ETL 的驱动表、JOIN KEY、JOIN 类型、字段归属和基数仍需明确配置或人工确认。

无 Reference/ExtendedDependency 时只生成分层 DDL，并写出 `链路/NEED_CONFIRM.md`；不会按表名推测 ETL 链路。输出保留原有 `ddl/` 与 `链路/` 结构、前置逗号、中文注释和固定文件头。

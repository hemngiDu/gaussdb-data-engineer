# SQL Reviewer / SQL Doctor

先确认表粒度、数据量、分布/分区策略、业务窗口和执行计划。静态 linter 只能发现模式风险，不能证明查询一定慢或结果一定错。

高优先级：无 WHERE 的 DELETE/UPDATE、未确认规则、JOIN 无 ON、字段映射不确定、DELETE/INSERT 窗口不一致、JOIN 放大、隐式类型转换、GROUP BY 粒度错误、重复键及 NULL 口径。

性能检查：全表扫描是否符合预期、函数包裹过滤字段是否妨碍分区裁剪/索引、分布式数据移动、HASH 键倾斜、统计信息过期、长事务/锁等待。先看 `EXPLAIN` 与实际行数，再提出索引、重写或 ANALYZE 等建议。若无执行计划或表统计，只报告可能性与所需证据。

运行 `python scripts/sql_linter.py <sql_file> --json` 获取机器可读规则结果；发布门槛由 `validate_pdm_output.py` 执行。

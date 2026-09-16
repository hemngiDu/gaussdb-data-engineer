# PDM Engineer

读取 `references/pdm-import.md`、`references/pdm-notes-template.md` 与 `references/safety-rules.md`。转换 PDM 后运行 `scripts/validate_pdm_output.py`；Reference/ExtendedDependency 只能证明模型依赖，不能自行确定业务 JOIN 或增量规则。

先查看生成的 `PDM_Notes_业务上下文.md`，逐个读取表、字段和关系的 Description/Annotation（PowerDesigner Notes）及 Comment。报告中没有 Notes 时明确说明这一事实；不能把 Comment 当作 Notes。依据文字复核粒度、派生指标、时间有效性和汇总口径，只有明确且与字段模型一致的规则才进入显式配置，其他规则标记 NEED_CONFIRM。

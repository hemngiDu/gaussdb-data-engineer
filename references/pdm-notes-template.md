# PDM Notes 业务规则模板与示例

将业务规则写在目标表属性的 **Notes → Description**，保存 PDM 后再运行转换器。`General → Comment` 用于简短表说明；复杂字段算法可同时写在该字段的 Notes 中。填写时使用 PDM 中的字段 `Code`，把 `【】` 占位内容换成实际规则。

## 六项模板

```text
业务粒度：每个【字段1＋字段2＋字段3】组合一行。
数据来源：【来源表】；【字段】来自【来源表.字段】。
关联规则：【来源表A.字段】＝【来源表B.字段】；每个关联键最多匹配【1】行；匹配不到时【处理方式】。
计算规则：【目标字段】＝【明确公式】；累计的起止月份和分组字段为【具体规则】。
更新规则：每次处理【本次变化的行／指定月份／指定年份】；目标表按【业务键或时间范围】覆盖；其他数据【保留／删除】。
数据要求：【业务键】不得为 NULL 或重复；不满足要求时【停止并修正来源数据】。
```

不需要计算或关联的表，写“无派生计算”或“无需 JOIN”，不要留下占位符。若日期格式、NULL 处理、缺失月份或年度总计有特殊规则，应紧接相关行补充。先写业务规则再核对模型字段：Notes 是证据，不能把自由文本自动拼成 SQL。

## 示例一：利润导入历史表

目标表：`irpt.irpt_m_profit_amt_his`。导入表只包含本次变化的业务行。

```text
业务粒度：每个 months＋dept_one＋dept_two 组合一行；months 格式为 YYYY-MM。
数据来源：irpt.irpt_m_profit_amt；months、dept_one、dept_two、same_profit、actual_profit、target_profit 分别来自同名来源字段。
关联规则：单来源表，无需 JOIN；覆盖历史行时用 months＋dept_one＋dept_two 定位业务键。
计算规则：无派生计算；三个利润字段保留来源 NULL，不统一补 0。
更新规则：每次只处理导入表中本次变化的行；历史表按 months＋dept_one＋dept_two 覆盖这些行；其他业务键保留。重复处理同一批数据，结果应相同。
数据要求：导入表和历史表的 months＋dept_one＋dept_two 不得为 NULL 或重复；不满足要求时停止并修正来源数据。
```

## 示例二：DWI 利润表

目标表：`dwi.dwi_m_profit_amt`。来源为利润历史表和组织架构表。

```text
业务粒度：每个 months＋dept_one＋dept_two 组合一行；months 格式为 YYYY-MM。
数据来源：irpt.irpt_m_profit_amt_his 提供 months、same_profit、actual_profit、target_profit；irpt.irpt_org_person_his 提供 dept_one、dept_two、dept_one_simple、dept_two_simple、dept_one_name、dept_two_name，其中 dept_one＝dept_org_one，dept_two＝dept_org_two。
关联规则：利润历史表.dept_one＝架构表.dept_org_one，利润历史表.dept_two＝架构表.dept_org_two；架构表每个 dept_org_one＋dept_org_two 组合最多一行且没有按月份变化的版本；匹配不到时停止导入并先补齐架构表，不丢弃利润行。
计算规则：same_profit_total、actual_profit_total、target_profit_total 分别是同一 dept_one＋dept_two 下当年 1 月至当前 months 的月值之和；same_profit_year、target_profit_year 分别是同一 dept_one＋dept_two 下当年 1–12 月的月值之和，并写在该年每个月的行上。月利润保留来源 NULL，不统一补 0。
更新规则：每次处理一个指定年份；删除 DWI 表中该年 1–12 月的行，再用利润历史表中该年的全部行重新生成；其他年份保留。
数据要求：历史表每个 months＋dept_one＋dept_two 组合不得为 NULL 或重复，架构表每个 dept_org_one＋dept_org_two 组合不得重复。导入前核对该年历史数据覆盖预期月份且全部部门能匹配架构表；不满足要求时停止并修正来源数据。
```

“预期月份”由业务决定；例如部门可能年中新增，就不应机械要求每个部门都有 12 行。若全部月份必须齐全，应在 Notes 中明确写出这一条件。

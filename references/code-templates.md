# SQL 代码模板（评审起点）

以下占位符必须先替换并通过校验，不代表可直接执行的业务规则。

```sql
-- DWI sql
-- ******************************************************************** --
-- author: 我是谁
-- create time: {yyyy/mm/dd hh24:mi:ss}
-- ******************************************************************** --

create table if not exists dwi.dwi_example
(
    business_id      BIGINT          comment '业务编号'
   ,amount_value     DECIMAL(20,6)  comment '金额'
)WITH (orientation = column, compression = low)
-- NEED_CONFIRM: 根据基数与关联策略确认分布键
-- DISTRIBUTE BY HASH (<key>)
comment '示例表';

-- NEED_CONFIRM: 明确目标删除范围和来源过滤范围
-- delete from dwi.dwi_example where <target_predicate>;
-- insert into dwi.dwi_example
-- (business_id, amount_value)
-- select src.business_id, src.amount_value
-- from irpt.irpt_example src
-- where <source_predicate>;
```

参见 [安全规则](safety-rules.md) 和 [ETL 模式](etl-patterns.md)。

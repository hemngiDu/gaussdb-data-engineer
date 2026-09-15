# GaussDB SQL 风格指南

保留原有习惯：关键字小写、标识符小写 snake_case、4 空格缩进、字段和 SELECT 列表使用前置逗号、中文行尾注释、固定文件头。

```sql
-- DWI sql
-- ******************************************************************** --
-- author: 我是谁
-- create time: {yyyy/mm/dd hh24:mi:ss}
-- ******************************************************************** --

create table if not exists dwi.dwi_example
(
    business_id       BIGINT         comment '业务编号'
   ,amount_value      DECIMAL(20,6) comment '金额'
)WITH (orientation = column, compression = low)
DISTRIBUTE BY HASH (business_id)
comment '业务明细';

insert into dwi.dwi_example
(
    business_id      -- '业务编号'
   ,amount_value     -- '金额'
)
select src.business_id     as business_id   -- 业务编号
      ,src.amount_value    as amount_value  -- 金额
from irpt.irpt_example src;
```

示例中的 HASH 键和金额类型只用于展示写法，实际项目必须遵循 PDM 类型和 [分布策略](distribution-key-guide.md)。DELETE+INSERT 分隔线可沿用“原有数据删除／新数据插入”，但窗口与过滤条件须有业务依据。NULL 默认保持 NULL；不自动套用 `nvl`。

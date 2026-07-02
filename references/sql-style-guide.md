# GaussDB SQL 风格指南

## 总体原则

- 关键词小写（create, table, select, insert, from 等）
- 标识符全小写 + snake_case
- 缩进用 4 空格
- 每行不超过 120 字符

## DDL 建表

`sql
/*==============================================================*/
/* Table: {schema}.{table_name}                                 */
/*==============================================================*/
create table if not exists {schema}.{table_name}
(
    col_big       VARCHAR(200)      comment '大字段'
   ,col_name      VARCHAR(100)      comment '名称'
   ,col_code      VARCHAR(50)       comment '编码'
   ,amount_val    DECIMAL(18, 4)    comment '金额'
   ,cnt_val       INTEGER           comment '计数'
   ,create_time   TIMESTAMP         comment '创建时间'
)WITH
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = false
)DISTRIBUTE BY HASH (distribution_key)
comment '表中文名';
`

字段顺序规则：
1. 业务键/维度字段排前（部门、编码、分类等）
2. 度量/金额字段居中
3. 技术字段排后（创建时间等）

## DML 插入

`sql
insert into {schema}.{table_name}
(
    col_1                  -- '字段1注释'
   ,col_2                  -- '字段2注释'
)
select a.col_1              -- 字段1
       ,a.col_2             -- 字段2
from {schema}.{source} a
left join {schema}.{dim} b
    on a.key = b.key;
`

## DELETE 模式

`sql
delete 
from {schema}.{table_name} 
where substr(months,1,4) = substr('',1,4)
;
`

## CASE WHEN

`sql
CASE {column}
    WHEN 'A' THEN '暂存'
    WHEN 'B' THEN '已提交'
    WHEN 'C' THEN '已审核'
END AS 中文别名
`

## JOIN 写法

- 使用别名：a, b, c, d 或含义缩写
- LEFT JOIN 对齐，ON 条件换行缩进
- 用注释标记已注释掉的 JOIN

`sql
from sdi.sdi_table_a a
left join dim.dim_table_b b
    on a.key = b.key
left join dim.dim_table_c c
    on c.foreign = a.key and c.status = 'A'
`

## 注释规范

- 字段注释：单引号中文，如 comment '月份'
- 行尾注释：-- '中文'
- 选择列注释：s 中文名
- 代码段注释：-----说明文字-------
- 注释掉的字段保留：--,column_name
- 注释掉的 JOIN 保留：-- left join ...


## 临时表模式
```
create temporary table tmp_{business}
WITH (orientation = column,compression = low) as
--drop table if exists tmp_{business};
(
    select ...
)
;
--drop table if exists tmp_{business};
```

## NVL 空值处理
```
nvl(column_name,'-')    as column_name -- '注释'
```

## IF 逻辑
```
if(condition, value_if_true, value_if_false) as column_name
```

## 变量格式
```
${var_months}   -- 月份变量
${var_date}     -- 日期变量
substr('${var_months}',1,4)  -- 取年（注意变量前后有空格）
substr('${var_months}',1,7)  -- 取月
```

## DELETE + INSERT 分隔符
```
----------原有数据删除---------------
delete
from schema.table
where substr(months,1,4) = substr( '${var_months}' ,1,4)
;

-------------新数据插入------------
insert into schema.table
(
     col_1     -- '字段注释'
    ,col_2     -- '字段注释'
)
select ...;
```

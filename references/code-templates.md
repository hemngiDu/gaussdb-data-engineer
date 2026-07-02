# SQL 代码模板

## 模板 A: irpt → dwi 清洗

`sql
-- DWI sql
-- ******************************************************************** --
-- author: yufeng
-- create time: {datetime}
-- ******************************************************************** --
--drop table if exists dwi.dwi_{granularity}_{business};

/*==============================================================*/
/* Table: dwi.dwi_{granularity}_{business}                      */
/*==============================================================*/
create table if not exists dwi.dwi_{granularity}_{business}
(
    months          VARCHAR(50)     comment '月份'
   ,dept_one        VARCHAR(100)    comment '一级部门'
   ,dept_two        VARCHAR(100)    comment '二级部门'
   ,amount_val      DECIMAL(18, 4)  comment '金额'
)with
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = true
)DISTRIBUTE BY HASH (dept_two)
comment '中文表名';

-----原有数据删除---------
delete 
from dwi.dwi_{granularity}_{business}
where substr(months,1,4) = substr('',1,4)
;

----------新数据插入------------
insert into dwi.dwi_{granularity}_{business}
(
    months                  -- '月份'
   ,dept_one                -- '一级部门'
   ,dept_two                -- '二级部门'
   ,amount_val              -- '金额'
)
select org.months          -- 月份
       ,org.dept_one       -- 一级部门
       ,org.dept_two       -- 二级部门
       ,src.amount_val     -- 金额
from irpt.irpt_{granularity}_{business}_his src
inner join dwi.dwi_org_person org
    on src.months = org.months
    and src.dept_one = org.dept_one
where substr(org.months,1,4) = substr('',1,4)
;
`

## 模板 B: dwi → dws 聚合

`sql
-- DWS sql
-- ******************************************************************** --
-- author: yufeng
-- create time: {datetime}
-- ******************************************************************** --

/*==============================================================*/
/* Table: dws.dws_{granularity}_{business}                      */
/*==============================================================*/
create table if not exists dws.dws_{granularity}_{business}
(
    months                   VARCHAR(50)     comment '月份'
   ,dept_one                 VARCHAR(100)    comment '一级部门'
   ,same_amount              DECIMAL(18, 4)  comment '同期金额'
   ,actual_amount            DECIMAL(18, 4)  comment '实际金额'
   ,target_amount            DECIMAL(18, 4)  comment '目标金额'
   ,same_amount_total        DECIMAL(18, 4)  comment '累计同期金额'
   ,actual_amount_total      DECIMAL(18, 4)  comment '累计实际金额'
   ,target_amount_total      DECIMAL(18, 4)  comment '累计目标金额'
)with
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = true
)DISTRIBUTE BY HASH (dept_two)
comment '汇总宽表';

delete from dws.dws_{granularity}_{business}
where substr(months,1,4) = substr('',1,4)
;

insert into dws.dws_{granularity}_{business}
(
    months
   ,dept_one
   ,same_amount
   ,actual_amount
   ,target_amount
   ,same_amount_total
   ,actual_amount_total
   ,target_amount_total
)
select org.months
       ,org.dept_one
       ,sum(profit.same_amount)   over(partition by org.dept_one,org.dept_two order by org.months)
           as same_amount
       ,sum(profit.actual_amount) over(partition by org.dept_one,org.dept_two order by org.months)
           as actual_amount
       ,sum(profit.target_amount) over(partition by substr(org.months,1,7),org.dept_one)
           as target_amount
       ,sum(profit.same_amount)   over(partition by org.dept_one)
           as same_amount_total
       ,sum(profit.actual_amount) over(partition by org.dept_one)
           as actual_amount_total
       ,sum(profit.target_amount) over(partition by org.dept_one)
           as target_amount_total
from dwi.dwi_{granularity}_{business} profit
left join dwi.dwi_org_person org
    on profit.months = org.months
    and profit.dept_one = org.dept_one
where substr(org.months,1,4) = substr('',1,4)
;
`

## 模板 C: DDL 分布式进阶

`sql
create table if not exists {schema}.{table_name}
(
    id             VARCHAR(50)      comment '主键'
   ,parent_id      VARCHAR(50)      comment '上级编码'
   ,name           VARCHAR(200)     comment '名称'
   ,level_num      INTEGER          comment '层级'
   ,is_leaf        INTEGER          comment '是否叶子节点'
)with
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = true
)DISTRIBUTE BY REPLICATION
comment '维度表';
`

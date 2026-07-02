# SQL ï¿½ï¿½ï¿½ï¿½Ä£ï¿½ï¿½

## Ä£ï¿½ï¿½ A: irpt ï¿½ï¿½ dwi ï¿½ï¿½Ï´

`sql
-- DWI sql
-- ******************************************************************** --
-- author: æˆ‘æ˜¯è°?
-- create time: {datetime}
-- ******************************************************************** --
--drop table if exists dwi.dwi_{granularity}_{business};

/*==============================================================*/
/* Table: dwi.dwi_{granularity}_{business}                      */
/*==============================================================*/
create table if not exists dwi.dwi_{granularity}_{business}
(
    months          VARCHAR(50)     comment 'ï¿½Â·ï¿½'
   ,dept_one        VARCHAR(100)    comment 'Ò»ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½'
   ,dept_two        VARCHAR(100)    comment 'ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½'
   ,amount_val      DECIMAL(18, 4)  comment 'ï¿½ï¿½ï¿?'
)WITH
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = false
)DISTRIBUTE BY HASH (dept_two)
comment 'ï¿½ï¿½ï¿½Ä±ï¿½ï¿½ï¿½';

-----Ô­ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½É¾ï¿½ï¿½---------
delete 
from dwi.dwi_{granularity}_{business}
where substr(months,1,4) = substr('',1,4)
;

----------ï¿½ï¿½ï¿½ï¿½ï¿½Ý²ï¿½ï¿½ï¿½------------
insert into dwi.dwi_{granularity}_{business}
(
    months                  -- 'ï¿½Â·ï¿½'
   ,dept_one                -- 'Ò»ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½'
   ,dept_two                -- 'ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½'
   ,amount_val              -- 'ï¿½ï¿½ï¿?'
)
select org.months          -- ï¿½Â·ï¿½
       ,org.dept_one       -- Ò»ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½
       ,org.dept_two       -- ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½
       ,src.amount_val     -- ï¿½ï¿½ï¿?
from irpt.irpt_{granularity}_{business}_his src
inner join dwi.dwi_org_person org
    on src.months = org.months
    and src.dept_one = org.dept_one
where substr(org.months,1,4) = substr('',1,4)
;
`

## Ä£ï¿½ï¿½ B: dwi ï¿½ï¿½ dws ï¿½Ûºï¿½

`sql
-- DWS sql
-- ******************************************************************** --
-- author: æˆ‘æ˜¯è°?
-- create time: {datetime}
-- ******************************************************************** --

/*==============================================================*/
/* Table: dws.dws_{granularity}_{business}                      */
/*==============================================================*/
create table if not exists dws.dws_{granularity}_{business}
(
    months                   VARCHAR(50)     comment 'ï¿½Â·ï¿½'
   ,dept_one                 VARCHAR(100)    comment 'Ò»ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½'
   ,same_amount              DECIMAL(18, 4)  comment 'Í¬ï¿½Ú½ï¿½ï¿?'
   ,actual_amount            DECIMAL(18, 4)  comment 'Êµï¿½Ê½ï¿½ï¿?'
   ,target_amount            DECIMAL(18, 4)  comment 'Ä¿ï¿½ï¿½ï¿½ï¿½'
   ,same_amount_total        DECIMAL(18, 4)  comment 'ï¿½Û¼ï¿½Í¬ï¿½Ú½ï¿½ï¿?'
   ,actual_amount_total      DECIMAL(18, 4)  comment 'ï¿½Û¼ï¿½Êµï¿½Ê½ï¿½ï¿?'
   ,target_amount_total      DECIMAL(18, 4)  comment 'ï¿½Û¼ï¿½Ä¿ï¿½ï¿½ï¿½ï¿½'
)WITH
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = false
)DISTRIBUTE BY HASH (dept_two)
comment 'ï¿½ï¿½ï¿½Ü¿ï¿½ï¿½ï¿½';

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

## Ä£ï¿½ï¿½ C: DDL ï¿½Ö²ï¿½Ê½ï¿½ï¿½ï¿½ï¿½

`sql
create table if not exists {schema}.{table_name}
(
    id             VARCHAR(50)      comment 'ï¿½ï¿½ï¿½ï¿½'
   ,parent_id      VARCHAR(50)      comment 'ï¿½Ï¼ï¿½ï¿½ï¿½ï¿½ï¿½'
   ,name           VARCHAR(200)     comment 'ï¿½ï¿½ï¿½ï¿½'
   ,level_num      INTEGER          comment 'ï¿½ã¼¶'
   ,is_leaf        INTEGER          comment 'ï¿½Ç·ï¿½Ò¶ï¿½Ó½Úµï¿½'
)WITH
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = false
)DISTRIBUTE BY REPLICATION
comment 'Î¬ï¿½È±ï¿½';
`

## NVL Ä£Ê½
nvl(column_name,'-')    as column_name -- '×¢ÊÍ'

## IF Ä£Ê½£¨Ìæ´ú CASE WHEN£©
if(condition, value_if_true, value_if_false) as column_name -- '×¢ÊÍ'

## ·Ö¸ô·û¸ñÊ½
----------²Ù×÷ËµÃ÷---------------
delete
from schema.table
where ...
;
-------------ÐÂÊý¾Ý²åÈë------------
insert into schema.table

## ±äÁ¿Ê¹ÓÃ
${var_months} - ÔÂ·Ý±äÁ¿
substr(months,1,4) = substr( '${var_months}' ,1,4)  -- È¡Äê¹ýÂË
substr(months,1,7) = substr( '${var_months}' ,1,7)  -- È¡ÔÂ¹ýÂË

# SQL ����ģ��

## ģ�� A: irpt �� dwi ��ϴ

`sql
-- DWI sql
-- ******************************************************************** --
-- author: 我是谁
-- create time: {datetime}
-- ******************************************************************** --
--drop table if exists dwi.dwi_{granularity}_{business};

/*==============================================================*/
/* Table: dwi.dwi_{granularity}_{business}                      */
/*==============================================================*/
create table if not exists dwi.dwi_{granularity}_{business}
(
    months          VARCHAR(50)     comment '�·�'
   ,dept_one        VARCHAR(100)    comment 'һ������'
   ,dept_two        VARCHAR(100)    comment '��������'
   ,amount_val      DECIMAL(18, 4)  comment '���'
)with
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = true
)DISTRIBUTE BY HASH (dept_two)
comment '���ı���';

-----ԭ������ɾ��---------
delete 
from dwi.dwi_{granularity}_{business}
where substr(months,1,4) = substr('',1,4)
;

----------�����ݲ���------------
insert into dwi.dwi_{granularity}_{business}
(
    months                  -- '�·�'
   ,dept_one                -- 'һ������'
   ,dept_two                -- '��������'
   ,amount_val              -- '���'
)
select org.months          -- �·�
       ,org.dept_one       -- һ������
       ,org.dept_two       -- ��������
       ,src.amount_val     -- ���
from irpt.irpt_{granularity}_{business}_his src
inner join dwi.dwi_org_person org
    on src.months = org.months
    and src.dept_one = org.dept_one
where substr(org.months,1,4) = substr('',1,4)
;
`

## ģ�� B: dwi �� dws �ۺ�

`sql
-- DWS sql
-- ******************************************************************** --
-- author: 我是谁
-- create time: {datetime}
-- ******************************************************************** --

/*==============================================================*/
/* Table: dws.dws_{granularity}_{business}                      */
/*==============================================================*/
create table if not exists dws.dws_{granularity}_{business}
(
    months                   VARCHAR(50)     comment '�·�'
   ,dept_one                 VARCHAR(100)    comment 'һ������'
   ,same_amount              DECIMAL(18, 4)  comment 'ͬ�ڽ��'
   ,actual_amount            DECIMAL(18, 4)  comment 'ʵ�ʽ��'
   ,target_amount            DECIMAL(18, 4)  comment 'Ŀ����'
   ,same_amount_total        DECIMAL(18, 4)  comment '�ۼ�ͬ�ڽ��'
   ,actual_amount_total      DECIMAL(18, 4)  comment '�ۼ�ʵ�ʽ��'
   ,target_amount_total      DECIMAL(18, 4)  comment '�ۼ�Ŀ����'
)with
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = true
)DISTRIBUTE BY HASH (dept_two)
comment '���ܿ���';

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

## ģ�� C: DDL �ֲ�ʽ����

`sql
create table if not exists {schema}.{table_name}
(
    id             VARCHAR(50)      comment '����'
   ,parent_id      VARCHAR(50)      comment '�ϼ�����'
   ,name           VARCHAR(200)     comment '����'
   ,level_num      INTEGER          comment '�㼶'
   ,is_leaf        INTEGER          comment '�Ƿ�Ҷ�ӽڵ�'
)with
(   orientation = column,
    compression = low,
    colversion = 2.0,
    enable_delta = true
)DISTRIBUTE BY REPLICATION
comment 'ά�ȱ�';
`

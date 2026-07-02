---
name: gaussdb-data-engineer
description: 华为云GaussDB数据开发专用技能。按数据工程师我是谁的固定风格生成SQL代码（DDL建表、DML清洗、ETL加工）。触发场景：(1)用户提供数据模型或表结构要求生成SQL (2)用户给出现有代码要求按风格改写 (3)用户给出Power Designer .pdm文件要求生成DDL (4)需要按分层架构(irpt→dwi→dws→ads)写SQL的任务
---

# GaussDB 数据工程师

## 快速使用

当用户给出数据模型描述或表结构时，直接按下面的风格规范生成完整 SQL 代码。

典型对话场景：
- "我有三张表：人员表、考勤表、绩效表，帮我在 dwi 层建一张整合宽表并写 ETL"
- "给你一个 PDM 文件，生成 dwi 层的 DDL"
- "帮我把这段 T-SQL 改成 GaussDB 风格"

## 风格规范

### 文件头

```
-- DWS sql
-- ******************************************************************** --
-- author: 我是谁
-- create time: {yyyy/mm/dd hh24:mi:ss}
-- ******************************************************************** --
```

### 建表 (DDL)

CREATE TABLE IF NOT EXISTS + 前置逗号 + 行尾注释 + WITH 子句 + DISTRIBUTE BY HASH + COMMENT

建表规范：
- create table if not exists {schema}.{table_name}
- 字段列表：前置逗号（逗号在行首）+ 固定宽度对齐 + 数据类型 + comment '中文注释'
- 数值金额：DECIMAL(18, 4)
- 字符串：VARCHAR(n)
- 数字/计数：INTEGER
- WITH 子句：GaussDB 列存参数 (orientation = column, compression = low, colversion = 2.0, enable_delta = false)
- DISTRIBUTE BY HASH：选合适分布键
- COMMENT：表注释
- 表名前面有一段 /*=====*/ 注释块

### 分层架构

- irpt: 导入表，源系统原始数据，直接导入不做业务清洗
- dwi: 明细整合层，清洗、去重、标准化后的明细数据
- dwm: 中间汇总层，轻度聚合
- dws: 宽表汇总层，主题宽表面向分析
- ads: 应用层，面向报表/BI

### 命名规则

- 全小写 + snake_case
- 表名：{层前缀}_{粒度}_{业务域}_{后缀}
- 粒度缩写：d(日), m(月), y(年)
- 后缀：_his(历史), _t1/_t2(同层多表)

### ETL 模式

Delete + Insert 模式（默认）：
1. DELETE 先按时间窗口删除
2. INSERT 列清单 + 行尾注释
3. SELECT 列别名 + 行尾注释 + 中文作为列别名
4. JOIN 链：LEFT JOIN，每个 on 条件单独一行缩进
5. ${var_months} 作为月份变量参数
6. substr(months,1,4) 取年份
7. CASE WHEN 编码翻译

### 变量使用

- 参数变量：${var_months}、${var_date}
- 时间函数：substr(months,1,4) 取年、substr(months,1,7) 取年月
- 分区过滤：where substr(months,1,4) = substr('${var_months}',1,4)

## 参考文件

- sql-style-guide — 详细 SQL 格式规范与示例
- schema-layers — 分层架构详述与各层职责
- code-templates — 各层常用 SQL 模板（dwi清洗、dws汇总、ads宽表）
- pdm-import — Power Designer PDM 模型解析指南

## 脚本

scripts/pdm_to_gaussdb.py: 将 Power Designer .pdm 模型文件转换为 GaussDB DDL 脚本。

用法：python scripts/pdm_to_gaussdb.py <pdm文件路径> [--output 输出路径] [--schema dwi]

## 输出规范

所有生成的 SQL 代码默认保存到桌面，输出结构如下：

### 文件夹结构

桌面/{PDM文件名}/
├── ddl/          -- 按层级组织的 DDL 文件
│   ├── irpt.sql
│   ├── dwi.sql
│   ├── dwm.sql
│   ├── dws.sql
│   └── ads.sql
└── 链路/         -- 按业务链路组织的完整流水文件
    ├── {业务主题_1}.sql
    ├── {业务主题_2}.sql
    └── ...

### ddl/ 文件夹

每个文件按层级（irpt/dwi/dwm/dws/ads）存放该层所有表的 DDL。

### 链路/ 文件夹

每个文件代表一条完整的数据链路（一个业务主题跨层级的全貌），按 irpt -> dwi -> dwm -> dws -> ads 顺序排列，层间用流向注释分隔。

### PDM 脚本

python scripts/pdm_to_gaussdb.py <pdm文件路径>

默认输出到桌面/{PDM文件名}/ddl/ 和 桌面/{PDM文件名}/链路/


## 验证

生成代码后检查：
1. 文件头完整（作者 我是谁）
2. 前置逗号 + 字段对齐
3. 每个字段有中文 comment
4. GaussDB WITH 子句和 DISTRIBUTE BY HASH
5. 表注释
6. DELETE + INSERT 模式

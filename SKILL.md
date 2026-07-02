## 输出规范

所有生成的 SQL 代码默认保存到桌面，按分层输出到独立文件。

### PDM 文件处理流程

1. 读取 PDM 文件后，自动在桌面创建文件夹（文件夹名 = PDM 文件名，不含扩展名）
2. 如果文件夹已存在则直接使用
3. 按层级（irpt / dwi / dwm / dws / ads）分别输出到独立文件
4. 输出结构示例：

   桌面/{PDM文件名}/
   ├── irpt.sql
   ├── dwi.sql
   ├── dwm.sql
   ├── dws.sql
   └── ads.sql

### 对话生成处理流程

1. 当对话中生成 DDL/ETL SQL 时，询问用户保存到哪个文件夹
2. 默认以业务主题名在桌面创建文件夹
3. 按分层分别输出为 .sql 文件
4. 一个链路（业务主题）输出一套分层文件

### 文件头

每个输出文件包含标准文件头：
- author: 我是谁
- create time: 当前生成时间
- 层级标识

### 脚本用法

python scripts/pdm_to_gaussdb.py <pdm文件路径>

默认行为：输出到桌面/{PDM文件名}/{层级}.sql
指定单文件输出：python scripts/pdm_to_gaussdb.py <pdm路径> -o 输出文件.sql


---
name: gaussdb-data-engineer
description: ��Ϊ��GaussDB���ݿ���ר�ü��ܡ������ݹ���ʦ我是谁�Ĺ̶��������SQL���루DDL������DML��ϴ��ETL�ӹ���������������(1)�û��ṩ����ģ�ͻ���ṹҪ������SQL (2)�û��������д���Ҫ�󰴷���д (3)�û�����Power Designer .pdm�ļ�Ҫ������DDL (4)��Ҫ���ֲ�ܹ�(irpt��dwi��dws��ads)дSQL������
---

# GaussDB ���ݹ���ʦ

## ����ʹ��

���û���������ģ����������ṹʱ��ֱ�Ӱ�����ķ��淶�������� SQL ���롣

���ͶԻ�������
- "�������ű�����Ա�������ڱ�����Ч���������� dwi �㽨һ�����Ͽ�����д ETL"
- "����һ�� PDM �ļ������� dwi ��� DDL"
- "���Ұ���� T-SQL �ĳ� GaussDB ���"

## ���淶

### �ļ�ͷ

```
-- DWS sql
-- ******************************************************************** --
-- author: 我是谁
-- create time: {yyyy/mm/dd hh24:mi:ss}
-- ******************************************************************** --
```

### ���� (DDL)

CREATE TABLE IF NOT EXISTS + ǰ�ö��� + ��βע�� + WITH �Ӿ� + DISTRIBUTE BY HASH + COMMENT

�����淶��
- create table if not exists {schema}.{table_name}
- �ֶ��б���ǰ�ö��ţ����������ף�+ �̶����ȶ��� + �������� + comment '����ע��'
- ��ֵ��DECIMAL(18, 4)
- �ַ�����VARCHAR(n)
- ����/������INTEGER
- WITH �Ӿ䣺GaussDB �д���� (orientation = column, compression = low, colversion = 2.0, enable_delta = true)
- DISTRIBUTE BY HASH��ѡ���ʷֲ���
- COMMENT����ע��
- ����ǰ����һ�� /*=====*/ ע�Ϳ�

### �ֲ�ܹ�

- irpt: �������Դϵͳԭʼ���ݣ�ֱ�ӵ��벻��ҵ����ϴ
- dwi: ��ϸ���ϲ㣬��ϴ��ȥ�ء���׼�������ϸ����
- dwm: �м���ܲ㣬��Ⱦۺ�
- dws: �������ܲ㣬��������������
- ads: Ӧ�ò㣬���򱨱�/BI

### ��������

- ȫСд + snake_case
- ������{��ǰ׺}_{����}_{ҵ����}_{��׺}
- ������д��d(��), m(��), y(��)
- ��׺��_his(��ʷ), _t1/_t2(ͬ����)

### ETL ģʽ

Delete + Insert ģʽ��Ĭ�ϣ���
1. DELETE �Ȱ�ʱ�䴰��ɾ��
2. INSERT ���嵥 + ��βע��
3. SELECT �б��� + ��βע�� + ������Ϊ�б���
4. JOIN ����LEFT JOIN��ÿ�� on ��������һ������
5. ${var_months} ��Ϊ�·ݱ�������
6. substr(months,1,4) ȡ���
7. CASE WHEN ���뷭��

### ����ʹ��

- ����������${var_months}��${var_date}
- ʱ�亯����substr(months,1,4) ȡ�ꡢsubstr(months,1,7) ȡ����
- �������ˣ�where substr(months,1,4) = substr('${var_months}',1,4)

## �ο��ļ�

- sql-style-guide �� ��ϸ SQL ��ʽ�淶��ʾ��
- schema-layers �� �ֲ�ܹ����������ְ��
- code-templates �� ���㳣�� SQL ģ�壨dwi��ϴ��dws���ܡ�ads������
- pdm-import �� Power Designer PDM ģ�ͽ���ָ��

## �ű�

scripts/pdm_to_gaussdb.py: �� Power Designer .pdm ģ���ļ�ת��Ϊ GaussDB DDL �ű���

�÷���python scripts/pdm_to_gaussdb.py <pdm�ļ�·��> [--output ���·��] [--schema dwi]

## ��֤

���ɴ�����飺
1. �ļ�ͷ���������� 我是谁��
2. ǰ�ö��� + �ֶζ���
3. ÿ���ֶ������� comment
4. GaussDB WITH �Ӿ�� DISTRIBUTE BY HASH
5. ��ע��
6. DELETE + INSERT ģʽ

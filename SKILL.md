---
name: gaussdb-data-engineer
description: ��Ϊ��GaussDB���ݿ���ר�ü��ܡ������ݹ���ʦ堵鹤明�Ĺ̶��������SQL���루DDL������DML��ϴ��ETL�ӹ���������������(1)�û��ṩ����ģ�ͻ���ṹҪ������SQL (2)�û��������д���Ҫ�󰴷���д (3)�û�����Power Designer .pdm�ļ�Ҫ������DDL (4)��Ҫ���ֲ�ܹ�(irpt��dwi��dws��ads)дSQL������
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
-- author: 堵鹤明
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
1. �ļ�ͷ���������� 堵鹤明��
2. ǰ�ö��� + �ֶζ���
3. ÿ���ֶ������� comment
4. GaussDB WITH �Ӿ�� DISTRIBUTE BY HASH
5. ��ע��
6. DELETE + INSERT ģʽ

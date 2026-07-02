# Power Designer PDM ����ָ��

## PDM �ļ��ṹ

.pdm �� Power Designer �� XML �ļ����ṹ���£�

`
<o:Model>
  <o:Table>
    <a:Code>irpt.irpt_m_sale_amt_his</a:Code>
    <a:Name>���۽����</a:Name>
    <c:Columns>
      <o:Column>
        <a:Code>months</a:Code>
        <a:Name>�·�</a:Name>
        <a:DataType>NVARCHAR(50)</a:DataType>
        <a:Length>50</a:Length>
        <a:Column.Mandatory>1</a:Mandatory>
      </o:Column>
    </c:Columns>
    <c:PrimaryKey>
      <o:Key>
        <a:Code>PK_TABLE</a:Code>
        <c:Key.Columns>
          <o:Column>ref to column</o:Column>
        </c:Key.Columns>
      </o:Key>
    </c:PrimaryKey>
  </o:Table>
</o:Model>
`

## �� PDM ��ȡ��Ϣ

��ʹ�� scripts/pdm_to_gaussdb.py �Զ�ת�����ֶ�����ʱע�⣺

1. ������ <a:Code> ��ǩ���� schema ǰ׺
2. �ֶ����� NVARCHAR �� VARCHAR��DECIMAL ����
3. ע���� <a:Name> ��ǩ������������
4. �ֶ��Ƿ���<a:Column.Mandatory>1</a:Column.Mandatory>
5. ������ <c:PrimaryKey> �� <c:Key.Columns>
6. ͬһ��ģ�ͣ����˰�ǿ��.pdm������ irc ������㡢dwi �㡢dws ��ı�

## ���ɵ� DDL ӳ��

| PDM ����      | GaussDB ����     |
|--------------|-----------------|
| NVARCHAR(n)  | VARCHAR(n)      |
| VARCHAR(n)   | VARCHAR(n)      |
| DECIMAL(p,s) | DECIMAL(p,s)    |
| INTEGER      | INTEGER         |
| DATE         | DATE            |
| TIMESTAMP    | TIMESTAMP       |

## ��������

1. �û��ϴ� .pdm �ļ�
2. ���� pdm_to_gaussdb.py ����ȫ�����ṹ
3. ���ֲ㣨irpt/dwi/dws���ֱ���� DDL
4. ��� code-templates.md ���ɶ�Ӧ��� ETL ����
5. ���ղ�����DDL + DELETE + INSERT


## 输出结构

运行脚本后，默认按以下结构输出到桌面：

桌面/{PDM文件名}/
├── irpt.sql     -- irpt 层 DDL
├── dwi.sql      -- dwi 层 DDL
├── dwm.sql      -- dwm 层 DDL
├── dws.sql      -- dws 层 DDL
└── ads.sql      -- ads 层 DDL

每层输出独立文件，文件头包含作者、时间戳信息。

### 命令示例

# 默认输出到桌面（推荐）
python scripts/pdm_to_gaussdb.py 模型文件.pdm

# 指定输出到自定义文件夹
python scripts/pdm_to_gaussdb.py 模型文件.pdm --folder D:/output

# 按单层过滤输出
python scripts/pdm_to_gaussdb.py 模型文件.pdm --schema dwi

# 输出到单个文件（传统模式）
python scripts/pdm_to_gaussdb.py 模型文件.pdm -o output.sql

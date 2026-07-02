# Power Designer PDM 导入指南

## PDM 文件结构

.pdm 是 Power Designer 的 XML 文件，结构如下：

`
<o:Model>
  <o:Table>
    <a:Code>irpt.irpt_m_sale_amt_his</a:Code>
    <a:Name>销售金额导入表</a:Name>
    <c:Columns>
      <o:Column>
        <a:Code>months</a:Code>
        <a:Name>月份</a:Name>
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

## 从 PDM 提取信息

请使用 scripts/pdm_to_gaussdb.py 自动转换。手动解析时注意：

1. 表名在 <a:Code> 标签，含 schema 前缀
2. 字段类型 NVARCHAR → VARCHAR，DECIMAL 保留
3. 注释在 <a:Name> 标签（中文描述）
4. 字段是否必填：<a:Column.Mandatory>1</a:Column.Mandatory>
5. 主键在 <c:PrimaryKey> → <c:Key.Columns>
6. 同一个模型（如人百强赛.pdm）中有 irc 导入表层、dwi 层、dws 层的表

## 生成的 DDL 映射

| PDM 类型      | GaussDB 类型     |
|--------------|-----------------|
| NVARCHAR(n)  | VARCHAR(n)      |
| VARCHAR(n)   | VARCHAR(n)      |
| DECIMAL(p,s) | DECIMAL(p,s)    |
| INTEGER      | INTEGER         |
| DATE         | DATE            |
| TIMESTAMP    | TIMESTAMP       |

## 典型流程

1. 用户上传 .pdm 文件
2. 运行 pdm_to_gaussdb.py 解析全部表结构
3. 按分层（irpt/dwi/dws）分别产出 DDL
4. 结合 code-templates.md 生成对应层的 ETL 代码
5. 最终产出：DDL + DELETE + INSERT

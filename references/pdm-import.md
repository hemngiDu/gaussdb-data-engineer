# Power Designer PDM 锟斤拷锟斤拷指锟斤拷

## PDM 锟侥硷拷锟结构

.pdm 锟斤拷 Power Designer 锟斤拷 XML 锟侥硷拷锟斤拷锟结构锟斤拷锟铰ｏ拷

`
<o:Model>
  <o:Table>
    <a:Code>irpt.irpt_m_sale_amt_his</a:Code>
    <a:Name>锟斤拷锟桔斤拷畹硷拷锟斤拷</a:Name>
    <c:Columns>
      <o:Column>
        <a:Code>months</a:Code>
        <a:Name>锟铰凤拷</a:Name>
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

## 锟斤拷 PDM 锟斤拷取锟斤拷息

锟斤拷使锟斤拷 scripts/pdm_to_gaussdb.py 锟皆讹拷转锟斤拷锟斤拷锟街讹拷锟斤拷锟斤拷时注锟解：

1. 锟斤拷锟斤拷锟斤拷 <a:Code> 锟斤拷签锟斤拷锟斤拷 schema 前缀
2. 锟街讹拷锟斤拷锟斤拷 NVARCHAR 锟斤拷 VARCHAR锟斤拷DECIMAL 锟斤拷锟斤拷
3. 注锟斤拷锟斤拷 <a:Name> 锟斤拷签锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷
4. 锟街讹拷锟角凤拷锟斤拷睿?<a:Column.Mandatory>1</a:Column.Mandatory>
5. 锟斤拷锟斤拷锟斤拷 <c:PrimaryKey> 锟斤拷 <c:Key.Columns>
6. 同一锟斤拷模锟酵ｏ拷锟斤拷锟剿帮拷强锟斤拷.pdm锟斤拷锟斤拷锟斤拷 irc 锟斤拷锟斤拷锟斤拷恪?dwi 锟姐、dws 锟斤拷谋锟?

## 锟斤拷锟缴碉拷 DDL 映锟斤拷

| PDM 锟斤拷锟斤拷      | GaussDB 锟斤拷锟斤拷     |
|--------------|-----------------|
| NVARCHAR(n)  | VARCHAR(n)      |
| VARCHAR(n)   | VARCHAR(n)      |
| DECIMAL(p,s) | DECIMAL(p,s)    |
| INTEGER      | INTEGER         |
| DATE         | DATE            |
| TIMESTAMP    | TIMESTAMP       |

## 锟斤拷锟斤拷锟斤拷锟斤拷

1. 锟矫伙拷锟较达拷 .pdm 锟侥硷拷
2. 锟斤拷锟斤拷 pdm_to_gaussdb.py 锟斤拷锟斤拷全锟斤拷锟斤拷锟结构
3. 锟斤拷锟街层（irpt/dwi/dws锟斤拷锟街憋拷锟斤拷锟? DDL
4. 锟斤拷锟? code-templates.md 锟斤拷锟缴讹拷应锟斤拷锟? ETL 锟斤拷锟斤拷
5. 锟斤拷锟秸诧拷锟斤拷锟斤拷DDL + DELETE + INSERT


## 杈撳嚭缁撴瀯

杩愯?岃剼鏈?鍚庯紝榛樿?ゆ寜浠ヤ笅缁撴瀯杈撳嚭鍒版?岄潰锛?

妗岄潰/{PDM鏂囦欢鍚峿/
鈹溾攢鈹? irpt.sql     -- irpt 灞? DDL
鈹溾攢鈹? dwi.sql      -- dwi 灞? DDL
鈹溾攢鈹? dwm.sql      -- dwm 灞? DDL
鈹溾攢鈹? dws.sql      -- dws 灞? DDL
鈹斺攢鈹? ads.sql      -- ads 灞? DDL

姣忓眰杈撳嚭鐙?绔嬫枃浠讹紝鏂囦欢澶村寘鍚?浣滆?呫?佹椂闂存埑淇℃伅銆?

### 鍛戒护绀轰緥

# 榛樿?よ緭鍑哄埌妗岄潰锛堟帹鑽愶級
python scripts/pdm_to_gaussdb.py 妯″瀷鏂囦欢.pdm

# 鎸囧畾杈撳嚭鍒拌嚜瀹氫箟鏂囦欢澶?
python scripts/pdm_to_gaussdb.py 妯″瀷鏂囦欢.pdm --folder D:/output

# 鎸夊崟灞傝繃婊よ緭鍑?
python scripts/pdm_to_gaussdb.py 妯″瀷鏂囦欢.pdm --schema dwi

# 杈撳嚭鍒板崟涓?鏂囦欢锛堜紶缁熸ā寮忥級
python scripts/pdm_to_gaussdb.py 妯″瀷鏂囦欢.pdm -o output.sql


## 输出结构

运行脚本后，默认在桌面创建文件夹，结构如下：

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

### 命令示例

# 默认输出到桌面
python scripts/pdm_to_gaussdb.py 模型文件.pdm

# 指定自定义目录
python scripts/pdm_to_gaussdb.py 模型文件.pdm --folder D:/my_project

# 按单层过滤
python scripts/pdm_to_gaussdb.py 模型文件.pdm --schema dwi

# 单文件模式（默认会分成 ddl/ + 链路/）
python scripts/pdm_to_gaussdb.py 模型文件.pdm -o output.sql

# GaussDB Data Engineer Skill

GaussDB数据工程Skill，按固定风格生成SQL代码。

## 安装方式

将本仓库clone或下载到 ~/.codex/skills/gaussdb-data-engineer/ 目录下，重启Codex即可自动加载。

## 功能特性

- GaussDB DDL建表（列存 + DISTRIBUTE BY HASH）
- irpt -> dwi -> dws -> ads 分层ETL
- PDM模型转DDL脚本
- DELETE + INSERT 标准化模式
- 前置逗号 + 行尾中文注释风格

## 分层说明

| 层级 | 说明 |
|------|------|
| irpt | 导入层，源系统原始数据 |
| dwi  | 明细整合层，清洗标准化 |
| dwm  | 中间汇总层，轻度聚合 |
| dws  | 宽表层，主题宽表 |
| ads  | 应用层，报表/BI使用 |

## 工具脚本

scripts/pdm_to_gaussdb.py - 将Power Designer PDM文件转换为GaussDB DDL

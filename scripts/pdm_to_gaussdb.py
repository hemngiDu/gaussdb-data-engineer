#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PowerDesigner PDM to reviewable GaussDB DDL/ETL.

V2 never invents distribution keys, joins, incremental predicates or NULL
defaults. Missing business rules remain visible as NEED_CONFIRM/TODO markers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

LAYERS = ["irpt", "dwi", "dwm", "dws", "ads"]
TYPE_MAP = {
    "nvarchar": "VARCHAR", "varchar": "VARCHAR", "char": "CHAR",
    "decimal": "DECIMAL", "numeric": "NUMERIC", "number": "NUMERIC",
    "tinyint": "SMALLINT", "smallint": "SMALLINT", "int": "INTEGER",
    "integer": "INTEGER", "bigint": "BIGINT", "date": "DATE",
    "datetime": "TIMESTAMP", "timestamp": "TIMESTAMP",
    "float": "DOUBLE PRECISION", "double": "DOUBLE PRECISION",
    "text": "TEXT", "clob": "TEXT", "blob": "BYTEA", "boolean": "BOOLEAN",
}


def _tag(block: str, name: str) -> str:
    match = re.search(rf"<a:{re.escape(name)}>(.*?)</a:{re.escape(name)}>", block, re.S)
    return match.group(1).strip() if match else ""


def map_type(raw: str, length: str = "") -> tuple[str, str]:
    if not raw:
        return "VARCHAR(1)", "NEED_CONFIRM: PDM 字段缺少类型"
    raw = raw.strip().lower()
    base_name = re.match(r"[a-z]+", raw)
    source_base = base_name.group(0) if base_name else ""
    mapped = TYPE_MAP.get(source_base)
    if not mapped:
        return "VARCHAR(1)", f"NEED_CONFIRM: 未识别的 PDM 字段类型 {raw}"
    precision = ""
    match = re.search(r"\(([^)]+)\)", raw)
    if match:
        precision = match.group(1)
    elif length and mapped in {"VARCHAR", "CHAR"}:
        precision = length
    if mapped in {"VARCHAR", "CHAR"} and not precision:
        return f"{mapped}(1)", "NEED_CONFIRM: 字符类型缺少长度"
    if precision and not re.fullmatch(r"\d+(?:\s*,\s*\d+)?", precision):
        return "VARCHAR(1)", f"NEED_CONFIRM: 非法类型精度 {raw}"
    return f"{mapped}({precision})" if precision else mapped, ""


def parse_pdm(path: str | Path):
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    tables, by_id, column_owner = [], {}, {}
    for match in re.finditer(r'<o:Table\s+[^>]*Id="([^"]+)"[^>]*>(.*?)</o:Table>', content, re.S):
        table_id, body = match.groups()
        code = _tag(body, "Code")
        if not code:
            continue
        schema, _, name = code.lower().rpartition(".")
        if not schema:
            schema, name = "", code.lower()
        columns = []
        for col_match in re.finditer(r'<o:Column\s+[^>]*Id="([^"]+)"[^>]*>(.*?)</o:Column>', body, re.S):
            column_id, col_body = col_match.groups()
            col_code = _tag(col_body, "Code").lower()
            if not col_code:
                continue
            data_type, warning = map_type(_tag(col_body, "DataType"), _tag(col_body, "Length"))
            column = {"id": column_id, "code": col_code, "name": _tag(col_body, "Name") or col_code,
                      "type": data_type, "type_warning": warning}
            columns.append(column)
            column_owner[column_id] = (table_id, col_code)
        table = {"id": table_id, "schema": schema, "name": name,
                 "cname": _tag(body, "Name") or name, "columns": columns}
        tables.append(table)
        by_id[table_id] = table
    refs = []
    for match in re.finditer(r"<o:Reference[^>]*>(.*?)</o:Reference>", content, re.S):
        body = match.group(1)
        parent = re.search(r'<c:ParentTable>.*?<o:Table\s+Ref="([^"]+)"', body, re.S)
        child = re.search(r'<c:ChildTable>.*?<o:Table\s+Ref="([^"]+)"', body, re.S)
        if not parent or not child or parent.group(1) not in by_id or child.group(1) not in by_id:
            continue
        joins = []
        for join in re.finditer(r"<o:ReferenceJoin[^>]*>(.*?)</o:ReferenceJoin>", body, re.S):
            found = re.findall(r'<o:Column\s+Ref="([^"]+)"', join.group(1))
            if len(found) >= 2 and found[0] in column_owner and found[-1] in column_owner:
                joins.append((column_owner[found[0]][1], column_owner[found[-1]][1]))
        refs.append({"parent_id": parent.group(1), "child_id": child.group(1),
                     "join_cols": joins, "code": _tag(body, "Code")})
    return by_id, tables, refs


def layer_for(table: dict) -> str:
    return {"sdi_wdtmp": "irpt", "dim": "dwi"}.get(
        table["schema"], table["schema"] if table["schema"] in LAYERS else "dwi")


def full_name(table: dict) -> str:
    layer = layer_for(table)
    schema = layer if table["schema"] in {"", "sdi_wdtmp", "dim"} else table["schema"]
    name = table["name"] if table["name"].startswith(layer + "_") else f"{layer}_{table['name']}"
    return f"{schema}.{name}"


def gen_ddl(table: dict, config: dict) -> list[str]:
    name = full_name(table)
    cfg = config.get("tables", {}).get(name, {})
    lines = ["", "/*" + "=" * 62 + "*/", f"/* Table: {name} */", "/*" + "=" * 62 + "*/",
             f"create table if not exists {name}", "("]
    for index, col in enumerate(table["columns"]):
        prefix = "    " if index == 0 else "   ,"
        lines.append(f"{prefix}{col['code']:<30} {col['type']:<20} comment '{col['name'].replace(chr(39), chr(39) * 2)}'")
        if col["type_warning"]:
            lines.append(f"   -- {col['type_warning']}: {col['code']}")
    storage = cfg.get("storage", "column")
    if storage not in {"column", "row"}:
        storage = "column"
        lines.append("-- NEED_CONFIRM: 配置中的存储类型无效")
    if storage == "column":
        lines.extend([")WITH", "    (", "        orientation = column,", "        compression = low,",
                      "        colversion = 2.0,", "        enable_delta = false", "    )"])
    else:
        lines.extend([")WITH", "    (", "        orientation = row", "    )"])
    distribution = cfg.get("distribution")
    codes = {col["code"] for col in table["columns"]}
    if distribution == "replication" and cfg.get("distribution_reason"):
        lines.append("DISTRIBUTE BY REPLICATION")
    elif (isinstance(distribution, dict) and distribution.get("type") == "hash"
          and distribution.get("keys") and cfg.get("distribution_reason")
          and all(key in codes for key in distribution["keys"])):
        lines.append(f"DISTRIBUTE BY HASH ({', '.join(distribution['keys'])})")
    else:
        lines.extend(["-- NEED_CONFIRM: 请根据数据量、基数、关联键和倾斜风险确认分布策略、字段存在性和判断依据",
                      "-- DISTRIBUTE BY HASH (<distribution_key>)"])
    lines.append(f"comment '{table['cname'].replace(chr(39), chr(39) * 2)}';")
    return lines


def gen_etl(target: dict, source_refs: list[dict], by_id: dict, config: dict) -> list[str]:
    target_name = full_name(target)
    cfg = config.get("etl", {}).get(target_name, {})
    sources = [by_id[ref["parent_id"]] for ref in source_refs]
    aliases = {source["id"]: f"t{idx}" for idx, source in enumerate(sources, 1)}
    mappings, incremental = cfg.get("mappings", {}), cfg.get("incremental_predicate")
    source_filter = cfg.get("source_predicate")
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    lines = [f"-- {layer_for(target).upper()} sql", "-- ******************************************************************** --",
             "-- author: 我是谁", f"-- create time: {now}", "-- ******************************************************************** --",
             f"-- ETL: {' + '.join(full_name(s) for s in sources)} -> {target_name}",
             "", "----------原有数据删除---------------"]
    if incremental and source_filter:
        lines.extend(["delete", f"from {target_name}", f"where {incremental}", ";"])
    else:
        lines.extend(["-- NEED_CONFIRM: 未同时配置目标 DELETE 和来源过滤条件，DELETE 已禁用",
                      f"-- delete from {target_name} where <incremental_predicate>;"])
    lines.extend(["", "-------------新数据插入------------", f"insert into {target_name}", "("])
    for idx, col in enumerate(target["columns"]):
        lines.append(f"{'    ' if idx == 0 else '   ,'}{col['code']:<25} -- '{col['name']}'")
    lines.extend([")", "select"])
    for idx, col in enumerate(target["columns"]):
        expression, reason = mappings.get(col["code"]), ""
        if not expression:
            expression = f"cast(null as {col['type']})"
            reason = "NEED_CONFIRM: 字段映射缺少明确业务依据"
        lines.append(f"{'     ' if idx == 0 else '    ,'}{expression:<35} as {col['code']:<24} -- {col['name']}")
        if reason:
            lines.append(f"    -- {reason}: {col['code']}")
    primary = sources[0]
    lines.append(f"from {full_name(primary)} {aliases[primary['id']]} -- {primary['cname']}")
    configured_joins = cfg.get("joins", {})
    for source, ref in zip(sources[1:], source_refs[1:]):
        alias, source_name = aliases[source["id"]], full_name(source)
        join = configured_joins.get(source_name, {})
        if not isinstance(join, dict):
            join = {}
        # ReferenceJoin connects this source to the target model, not necessarily to t1.
        if join.get("type") in {"left", "inner"} and join.get("on") and join.get("reason"):
            lines.append(f"{join['type']} join {source_name} {alias} -- {source['cname']}；依据：{join['reason']}")
            lines.append("    on " + "\n   and ".join(join["on"]))
        else:
            lines.extend([f"-- NEED_CONFIRM: {source_name} 缺少 JOIN KEY、类型或基数依据，未生成 JOIN",
                          f"-- <join_type> join {source_name} {alias} on <join_predicate>"])
    if source_filter:
        lines.append(f"where {source_filter}")
    lines.append(";")
    if any("NEED_CONFIRM" in line or "TODO" in line for line in lines):
        # Keep the draft reviewable while preventing accidental execution.
        start = next(index for index, line in enumerate(lines) if line.startswith("insert into "))
        lines.insert(start, "-- NEED_CONFIRM: 以下 INSERT 为评审草稿，确认规则后重新生成")
        for index in range(start + 1, len(lines)):
            lines[index] = "-- " + lines[index]
    return lines


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def output_project(pdm_path: str, folder: str | None, schema_filter: str | None, config: dict):
    by_id, tables, refs = parse_pdm(pdm_path)
    if not tables:
        raise ValueError("PDM 中未找到表")
    base = Path(folder) if folder else Path.home() / "Desktop" / Path(pdm_path).stem
    ddl_dir, etl_dir = base / "ddl", base / "链路"
    ddl_dir.mkdir(parents=True, exist_ok=True)
    etl_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    for layer in LAYERS:
        selected = [t for t in tables if layer_for(t) == layer and (not schema_filter or layer == schema_filter)]
        if not selected:
            continue
        output = [f"-- {layer.upper()} sql", "-- ******************************************************************** --",
                  "-- author: 我是谁", f"-- create time: {now}", "-- ******************************************************************** --"]
        for table in selected:
            output.extend(gen_ddl(table, config))
        (ddl_dir / f"{layer}.sql").write_text("\n".join(output) + "\n", encoding="utf-8")
    refs_by_target = {}
    for ref in refs:
        refs_by_target.setdefault(ref["child_id"], []).append(ref)
    for target_id, target_refs in refs_by_target.items():
        target = by_id[target_id]
        if not schema_filter or layer_for(target) == schema_filter:
            (etl_dir / f"{target['name']}.sql").write_text(
                "\n".join(gen_etl(target, target_refs, by_id, config)) + "\n", encoding="utf-8")
    if not refs:
        (etl_dir / "NEED_CONFIRM.md").write_text(
            "# NEED_CONFIRM\n\nPDM 未提供表关系。V2 不按表名猜测数据链路，请补充 Reference 或配置文件。\n", encoding="utf-8")
    return base


def output_single_ddl(pdm_path: str, output_file: str, schema_filter: str | None, config: dict):
    _, tables, _ = parse_pdm(pdm_path)
    if not tables:
        raise ValueError("PDM 中未找到表")
    selected = [table for table in tables if not schema_filter or layer_for(table) == schema_filter]
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    lines = ["-- DDL from PowerDesigner PDM", "-- ******************************************************************** --",
             "-- author: 我是谁", f"-- create time: {now}", "-- ******************************************************************** --"]
    for table in selected:
        lines.extend(gen_ddl(table, config))
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="安全地将 PowerDesigner PDM 转为 GaussDB DDL/ETL")
    parser.add_argument("pdm_file")
    parser.add_argument("-o", "--output", help="输出目录；以 .sql 结尾时兼容 V1 单文件 DDL")
    parser.add_argument("--folder", help="输出目录（兼容 V1）")
    parser.add_argument("--schema", choices=LAYERS)
    parser.add_argument("--config", help="JSON 规则配置")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.output and args.output.lower().endswith(".sql"):
            base = output_single_ddl(args.pdm_file, args.output, args.schema, config)
        else:
            base = output_project(args.pdm_file, args.output or args.folder, args.schema, config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"已输出到: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

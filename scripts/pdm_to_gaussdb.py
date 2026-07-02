#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, os, argparse
from datetime import datetime

TYPE_MAP = {
    "nvarchar": "VARCHAR", "varchar": "VARCHAR", "char": "VARCHAR",
    "decimal": "DECIMAL", "numeric": "DECIMAL", "number": "DECIMAL",
    "int": "INTEGER", "integer": "INTEGER",
    "smallint": "INTEGER", "bigint": "INTEGER",
    "date": "DATE", "datetime": "TIMESTAMP", "timestamp": "TIMESTAMP",
    "float": "DOUBLE PRECISION", "double": "DOUBLE PRECISION",
    "text": "TEXT", "clob": "TEXT", "blob": "BYTEA",
}

LAYERS = ["irpt", "dwi", "dwm", "dws", "ads"]
# Suffixes to strip when identifying chain
CHAIN_SUFFIXES = ["_his", "_t1", "_t2", "_bak", "_tmp"]

def parse_pdm(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    tables = []
    pat_table = re.compile(r"<o:Table[^>]*>(.*?)</o:Table>", re.DOTALL)
    for m in pat_table.finditer(content):
        tx = m.group(1)
        c = re.search(r"<a:Code>([^<]+)</a:Code>", tx)
        n = re.search(r"<a:Name>([^<]+)</a:Name>", tx)
        if not c: continue
        tc = c.group(1).strip()
        tn = n.group(1).strip() if n else ""
        schema, tname = "", tc.lower()
        if "." in tc:
            parts = tc.split(".", 1)
            schema, tname = parts[0].lower(), parts[1].lower()
        columns = []
        pat_col = re.compile(r"<o:Column[^>]*>(.*?)</o:Column>", re.DOTALL)
        for cm in pat_col.finditer(tx):
            cx = cm.group(1)
            cc = re.search(r"<a:Code>([^<]+)</a:Code>", cx)
            cn = re.search(r"<a:Name>([^<]+)</a:Name>", cx)
            ct = re.search(r"<a:DataType>([^<]+)</a:DataType>", cx)
            cl = re.search(r"<a:Length>([^<]+)</a:Length>", cx)
            if not cc: continue
            code = cc.group(1).strip().lower()
            name = cn.group(1).strip() if cn else code
            raw = ct.group(1).strip().lower() if ct else "varchar"
            base = "VARCHAR"
            for k, v in TYPE_MAP.items():
                if raw.startswith(k): base = v; break
            prec = ""
            pm = re.search(r"\\([^)]+\\)", raw)
            if pm: prec = pm.group(1)
            elif cl and cl.group(1) and base == "VARCHAR": prec = cl.group(1)
            columns.append({"code": code, "name": name, "type": base, "precision": prec})
        if columns:
            tables.append({"schema": schema, "name": tname, "cname": tn, "columns": columns})
    return tables


def get_chain_key(tbl):
    """Extract the chain (business) key from a table name.
    
    Table pattern: {layer_prefix}_{freq_prefix}_{business}_{suffix}
    Example: irpt_m_sale_amt_his -> chain key = m_sale_amt
    """
    name = tbl["name"]
    # Strip layer prefix
    for lp in LAYERS:
        if name.startswith(lp + "_"):
            name = name[len(lp) + 1:]
            break
    # Strip known suffixes
    for sfx in CHAIN_SUFFIXES:
        if name.endswith(sfx):
            name = name[:-len(sfx)]
            break
    return name


def gen_ddl(tbl, layer):
    cname = tbl["cname"] if tbl["cname"] else layer + "_" + tbl["name"]
    dk = tbl["columns"][0]["code"] if tbl["columns"] else "id"
    lines = ["", "/*" + "=" * 62 + "*/", "/* Table: %s.%s_%s */" % (layer, layer, tbl["name"]), "/*" + "=" * 62 + "*/", "create table if not exists %s.%s_%s" % (layer, layer, tbl["name"]), "("]
    for i, col in enumerate(tbl["columns"]):
        ct = col["type"]
        if col["precision"]: ct = "%s(%s)" % (col["type"], col["precision"])
        sep = "    " if i == 0 else "   ,"
        cl = "%-5s%-30s %-18s" % (sep, col["code"], ct)
        if col["name"] and col["name"] != col["code"]: cl += " " + chr(39) + col["name"] + chr(39)
        lines.append(cl.rstrip())
    lines.extend([")with", "(   orientation = column,", "    compression = low,", "    colversion = 2.0,", "    enable_delta = true", ")"])
    lines.append("DISTRIBUTE BY HASH (%s)" % dk)
    lines.append(chr(39) + cname + chr(39) + ";")
    return lines


def gen_header():
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    return [
        "-- DDL from Power Designer PDM",
        "-- ******************************************************************** --",
        "-- author: 我是谁",
        "-- create time: " + now,
        "-- ******************************************************************** --",
        ""
    ]


def gen_chain_header(chain_key):
    return [
        "-- ******************************************************************** --",
        "-- Data Chain: " + chain_key,
        "-- author: 我是谁",
        "-- create time: " + datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "-- ******************************************************************** --",
        ""
    ]


def output_pdm(pdm_path, folder_arg, schema_filter):
    """Main output function: creates ddl/ and 链路/ sub-folders."""
    tables = parse_pdm(pdm_path)
    if not tables:
        print("No tables found in PDM", file=sys.stderr)
        sys.exit(1)
    
    # Determine base folder
    pdm_name = os.path.splitext(os.path.basename(pdm_path))[0]
    if folder_arg:
        base_folder = folder_arg
    else:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        base_folder = os.path.join(desktop, pdm_name)
    
    # Sub-folders
    ddl_folder = os.path.join(base_folder, "ddl")
    chain_folder = os.path.join(base_folder, "链路")  # 链路
    
    os.makedirs(ddl_folder, exist_ok=True)
    os.makedirs(chain_folder, exist_ok=True)
    
    # --- Step 1: Group by layer for DDL output ---
    layer_groups = {}
    for t in tables:
        l = t["schema"] if t["schema"] in LAYERS else "dwi"
        if schema_filter and l != schema_filter: continue
        layer_groups.setdefault(l, []).append(t)
    
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    for l in LAYERS:
        if l not in layer_groups: continue
        filepath = os.path.join(ddl_folder, l + ".sql")
        out_lines = [
            "-- DDL from Power Designer PDM",
            "-- ******************************************************************** --",
            "-- author: 我是谁",
            "-- create time: " + now,
            "-- ******************************************************************** --",
            "",
            "-- ================ Layer: " + l + " ================",
            ""
        ]
        for t in layer_groups[l]:
            out_lines.extend(gen_ddl(t, l))
            out_lines.append("")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
        print("Written: " + filepath)
    
    # --- Step 2: Group by chain for 链路 output ---
    chain_groups = {}
    for t in tables:
        if schema_filter and t["schema"] not in LAYERS:
            l = t["schema"] if t["schema"] in LAYERS else "dwi"
            if l != schema_filter: continue
        key = get_chain_key(t)
        chain_groups.setdefault(key, []).append(t)
    
    for ckey, ctables in sorted(chain_groups.items()):
        # Sort tables by layer order
        ctables.sort(key=lambda x: LAYERS.index(x["schema"]) if x["schema"] in LAYERS else 99)
        
        filepath = os.path.join(chain_folder, ckey + ".sql")
        out_lines = gen_chain_header(ckey)
        
        prev_layer = None
        for t in ctables:
            l = t["schema"] if t["schema"] in LAYERS else "dwi"
            # Add flow comment between layers
            if prev_layer and l != prev_layer:
                out_lines.append("")
                out_lines.append("-- >>> Flow: " + prev_layer + " -> " + l + " <<<")
                out_lines.append("")
            out_lines.extend(gen_ddl(t, l))
            out_lines.append("")
            prev_layer = l
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
        print("Written: " + filepath)
    
    print("")
    print("All files saved to: " + base_folder)
    print("  ddl/   - Layer-based DDL files")
    print("  链路/ - Chain-based pipeline files")


def main():
    ap = argparse.ArgumentParser(description="PDM to GaussDB DDL")
    ap.add_argument("pdm_file", help="Power Designer .pdm file path")
    ap.add_argument("-o", "--output", help="Single output file (overrides folder mode)")
    ap.add_argument("--schema", choices=LAYERS, help="Filter by single layer only")
    ap.add_argument("--folder", help="Base output folder (default: Desktop/{PDM文件名})")
    args = ap.parse_args()
    
    if not os.path.exists(args.pdm_file):
        print("File not found", file=sys.stderr)
        sys.exit(1)
    
    # Single-file mode (legacy)
    if args.output:
        tables = parse_pdm(args.pdm_file)
        if not tables:
            print("No tables found", file=sys.stderr)
            sys.exit(1)
        groups = {}
        for t in tables:
            l = t["schema"] if t["schema"] in LAYERS else "dwi"
            if args.schema and l != args.schema: continue
            groups.setdefault(l, []).append(t)
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        out = [
            "-- DDL from Power Designer PDM",
            "-- ******************************************************************** --",
            "-- author: 我是谁",
            "-- create time: " + now,
            "-- ******************************************************************** --",
            ""
        ]
        for l in LAYERS:
            if l not in groups: continue
            out.append("")
            out.append("-- " + "=" * 30 + " Layer: " + l + " " + "=" * 30)
            for t in groups[l]:
                out.extend(gen_ddl(t, l))
                out.append("")
        text = "\n".join(out)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("Written: " + args.output)
    else:
        # Default: output to desktop with ddl/ and 链路/ sub-folders
        output_pdm(args.pdm_file, args.folder, args.schema)


if __name__ == "__main__":
    main()

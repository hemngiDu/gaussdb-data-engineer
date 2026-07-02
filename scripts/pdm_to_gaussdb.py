#!/usr/bin/env python3
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
        tc = c.group(1).strip(); tn = n.group(1).strip() if n else ""
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
            cp = re.search(r"<a:Precision>([^<]+)</a:Precision>", cx)
            if not cc: continue
            code = cc.group(1).strip().lower()
            name = cn.group(1).strip() if cn else code
            raw = ct.group(1).strip().lower() if ct else "varchar"
            base = "VARCHAR"
            for k, v in TYPE_MAP.items():
                if raw.startswith(k): base = v; break
            prec = ""
            pm = re.search(r"\(([^)]+)\)", raw)
            if pm: prec = pm.group(1)
            elif cl and cl.group(1) and base == "VARCHAR": prec = cl.group(1)
            columns.append({"code": code, "name": name, "type": base, "precision": prec})
        if columns:
            tables.append({"schema": schema, "name": tname, "cname": tn, "columns": columns})
    return tables

LAYERS = ["irpt", "dwi", "dwm", "dws", "ads"]

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

def gen_file_header(tables_text):
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    return [
        "-- DDL from Power Designer PDM",
        "-- ******************************************************************** --",
        "-- author: 我是谁",
        "-- create time: " + now,
        "-- ******************************************************************** --",
        ""
    ]

def output_to_folder(tables, folder, schema_filter=None):
    os.makedirs(folder, exist_ok=True)
    groups = {}
    for t in tables:
        l = t["schema"] if t["schema"] in LAYERS else "dwi"
        if schema_filter and l != schema_filter: continue
        groups.setdefault(l, []).append(t)
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    for l in LAYERS:
        if l not in groups: continue
        layer_file = os.path.join(folder, l + ".sql")
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
        for t in groups[l]:
            out_lines.extend(gen_ddl(t, l))
            out_lines.append("")
        with open(layer_file, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
        print("Written: " + layer_file)
    print("")
    print("All files saved to: " + folder)

def main():
    ap = argparse.ArgumentParser(description="PDM to GaussDB DDL")
    ap.add_argument("pdm_file", help="Power Designer .pdm file path")
    ap.add_argument("-o", "--output", help="Single output file (default: layer files to desktop)")
    ap.add_argument("--schema", choices=LAYERS, help="Filter by single layer only")
    ap.add_argument("--folder", help="Output folder (default: Desktop/{PDM文件名})")
    args = ap.parse_args()
    if not os.path.exists(args.pdm_file):
        print("File not found", file=sys.stderr); sys.exit(1)
    tables = parse_pdm(args.pdm_file)
    if not tables:
        print("No tables found in PDM", file=sys.stderr); sys.exit(1)
    # Determine output folder
    pdm_name = os.path.splitext(os.path.basename(args.pdm_file))[0]
    if args.folder:
        out_folder = args.folder
    elif args.output:
        out_folder = None  # single-file mode
    else:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        out_folder = os.path.join(desktop, pdm_name)
    # Single-file mode
    if args.output:
        groups = {}
        for t in tables:
            l = t["schema"] if t["schema"] in LAYERS else "dwi"
            if args.schema and l != args.schema: continue
            groups.setdefault(l, []).append(t)
        out = gen_file_header("")
        for l in LAYERS:
            if l not in groups: continue
            out.append(""); out.append("-- " + "=" * 30 + " Layer: " + l + " " + "=" * 30)
            for t in groups[l]:
                out.extend(gen_ddl(t, l)); out.append("")
        text = "\n".join(out)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print("Written: " + args.output)
    else:
        # Desktop layer-output mode
        output_to_folder(tables, out_folder, args.schema)
        print("")
        print("Usage: python scripts/pdm_to_gaussdb.py <pdm_file>")
        print("       Default output: ~/Desktop/{PDM文件名}/{irpt,dwi,dwm,dws,ads}.sql")
        print("       Use -o for single file output")

if __name__ == "__main__": main()

#!/usr/bin/env python3
import re, sys, os, argparse

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

def main():
    ap = argparse.ArgumentParser(description="PDM to GaussDB DDL")
    ap.add_argument("pdm_file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--schema", choices=LAYERS)
    args = ap.parse_args()
    if not os.path.exists(args.pdm_file): print("File not found", file=sys.stderr); sys.exit(1)
    tables = parse_pdm(args.pdm_file)
    if not tables: print("No tables", file=sys.stderr); sys.exit(1)
    groups = {}
    for t in tables:
        l = t["schema"] if t["schema"] in LAYERS else "dwi"
        if args.schema and l != args.schema: continue
        groups.setdefault(l, []).append(t)
    out = ["-- DDL from Power Designer PDM", "-- " + "*" * 62, ""]
    for l in LAYERS:
        if l not in groups: continue
        out.append(""); out.append("-- " + "=" * 30 + " Layer: " + l + " " + "=" * 30)
        for t in groups[l]:
            out.extend(gen_ddl(t, l)); out.append("")
    text = chr(10).join(out)
    if args.output:
        open(args.output, "w", encoding="utf-8").write(text)
        print("Written:", args.output)
    else:
        print(text)

if __name__ == "__main__": main()

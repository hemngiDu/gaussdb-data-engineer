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
CHAIN_SUFFIXES = ["_his", "_t1", "_t2", "_bak", "_tmp"]
VAR_MONTHS = "${var_months}"


def extract_notes(desc_xml):
    if not desc_xml or len(desc_xml.strip()) < 10: return "", ""
    text = desc_xml.replace("&#39;", "'")
    gbk_bytes = []; i = 0
    while i < len(text):
        if i + 3 < len(text) and text[i] == chr(92) and text[i+1] == "'":
            try: gbk_bytes.append(int(text[i+2:i+4], 16))
            except: pass
            i += 4
        elif text[i] == chr(92): i += 1
        else: i += 1
    cn = bytes(gbk_bytes).decode("gbk", errors="replace") if gbk_bytes else ""
    plain = re.sub(r"\\(?:[a-z]+[0-9]*|\\*)", " ", text)
    plain = re.sub(r"[{}]", " ", plain)
    plain = re.sub(r"\\s+", " ", plain).strip()
    lines = [l.strip() for l in plain.split(chr(10)) if l.strip()]
    sql_lines = [l for l in lines if any(k in l.lower() for k in ["like ","nvl(","and ","or ","is null","in ("])]
    # Decode CHR(92)-quote-hex sequences in SQL (same as Chinese text decoding)
    decoded_sql = []
    for sql_line in sql_lines:
        i2 = 0
        out = []
        while i2 < len(sql_line):
            if i2 + 3 < len(sql_line) and sql_line[i2] == chr(92) and sql_line[i2+1] == "'":
                try: out.append(bytes.fromhex(sql_line[i2+2:i2+4]).decode('gbk'))
                except:
                    # Collect consecutive hex bytes and decode as group
                    hex_buf = [sql_line[i2+2:i2+4]]
                    j = i2 + 4
                    while j + 3 < len(sql_line) and sql_line[j] == chr(92) and sql_line[j+1] == "'":
                        hex_buf.append(sql_line[j+2:j+4])
                        j += 4
                    try: out.append(bytes.fromhex(''.join(hex_buf)).decode('gbk'))
                    except: out.append('[' + ','.join(hex_buf) + ']')
                    i2 = j
            else: out.append(sql_line[i2]); i2 += 1
        decoded_sql.append(''.join(out))
    sql_lines = decoded_sql
    return cn, chr(10).join(sql_lines)

def parse_pdm_with_notes(filepath):
    tbid, tables, refs = parse_pdm(filepath)
    with open(filepath, "r", encoding="utf-8", errors="replace") as f: xmlc = f.read()
    for t in tables:
        code = (t["schema"] + "." + t["name"] if t["schema"] else t["name"]).lower()
        pat = "<o:Table[^>]*>.*?<a:Code>" + re.escape(code) + "</a:Code>.*?</o:Table>"
        tbl_m = re.search(pat, xmlc, 16)
        if tbl_m:
            dm = re.search("<a:Description>(.*?)</a:Description>", tbl_m.group(0), 16)
            if dm:
                cn, sql = extract_notes(dm.group(1))
                if cn or sql: t["notes_text"] = cn; t["notes_sql"] = sql

    # Parse ExtendedDependency directly (data arrows, NOT Symbol wrapper)
    if not refs:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f: xmlc = f.read()
        pat_ext = re.compile(r'<o:ExtendedDependency[^>]*>(.*?)</o:ExtendedDependency>', re.DOTALL)
        for m in pat_ext.finditer(xmlc):
            ex = m.group(1)
            if '<a:ObjectID>' not in ex: continue
            om1 = re.search(r'<c:Object1>.*?<o:Table\s+Ref="([^"]+)"', ex, re.DOTALL)
            om2 = re.search(r'<c:Object2>.*?<o:Table\s+Ref="([^"]+)"', ex, re.DOTALL)
            if om1 and om2:
                src_tid, dst_tid = om1.group(1), om2.group(1)
                if src_tid != dst_tid and src_tid in tbid and dst_tid in tbid:
                    exists = any(r['parent_id']==src_tid and r['child_id']==dst_tid for r in refs)
                    if not exists:
                        refs.append({'parent_id':dst_tid, 'child_id':src_tid, 'join_cols':[], 'code':'ExtDep'})
        if refs:
            print('Found', len(refs), 'ExtendedDependency arrows')

    return tbid, tables, refs

def parse_pdm(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    tables_by_id = {}
    tables = []
    pat_table = re.compile(r'<o:Table\s+[^>]*Id="([^"]+)"[^>]*>(.*?)</o:Table>', re.DOTALL)
    for m in pat_table.finditer(content):
        tid = m.group(1)
        tx = m.group(2)
        c = re.search(r"<a:Code>([^<]+)</a:Code>", tx)
        n = re.search(r"<a:Name>([^<]+)</a:Name>", tx)
        if not c: continue
        tc = c.group(1).strip()
        tn = n.group(1).strip() if n else ""
        schema, tname = "", tc.lower()
        if "." in tc:
            parts = tc.split(".", 1)
            schema, tname = parts[0].lower(), parts[1].lower()
        cols = []
        pat_col = re.compile(r'<o:Column\s+[^>]*Id="([^"]+)"[^>]*>(.*?)</o:Column>', re.DOTALL)
        for cm in pat_col.finditer(tx):
            col_id = cm.group(1)
            cx = cm.group(2)
            cc = re.search(r"<a:Code>([^<]+)</a:Code>", cx)
            cn = re.search(r"<a:Name>([^<]+)</a:Name>", cx)
            ct = re.search(r"<a:DataType>([^<]+)</a:DataType>", cx)
            cl = re.search(r"<a:Length>([^<]+)</a:Length>", cx)
            if not cc: continue
            code = cc.group(1).strip().lower()
            name_ = cn.group(1).strip() if cn else code
            raw = ct.group(1).strip().lower() if ct else "varchar"
            base = "VARCHAR"
            for k, v in TYPE_MAP.items():
                if raw.startswith(k): base = v; break
            prec = ""
            pm = re.search(r"\(([^)]+)\)", raw)
            if pm: prec = pm.group(1)
            elif cl and cl.group(1) and base == "VARCHAR": prec = cl.group(1)
            cols.append({"id": col_id, "code": code, "name": name_, "type": base, "precision": prec})
        if cols:
            tbl = {"id": tid, "schema": schema, "name": tname, "cname": tn, "columns": cols}
            tables_by_id[tid] = tbl
            tables.append(tbl)
    # Parse references (arrows)
    refs = []
    pat_ref = re.compile(r"<o:Reference[^>]*>(.*?)</o:Reference>", re.DOTALL)
    pat_code = re.compile(r"<a:Code>([^<]+)</a:Code>")
    for ref_m in pat_ref.finditer(content):
        rx = ref_m.group(1)
        parent_id = None
        pm1 = re.search(r"<c:ParentTable>.*?<o:Table\s+Ref=\"([^\"]+)\"", rx, re.DOTALL)
        if pm1: parent_id = pm1.group(1)
        else:
            pm1b = re.search(r"<a:ParentTable[^>]*>([^<]+)", rx)
            if pm1b: parent_id = pm1b.group(1).strip()
        child_id = None
        pm2 = re.search(r"<c:ChildTable>.*?<o:Table\s+Ref=\"([^\"]+)\"", rx, re.DOTALL)
        if pm2: child_id = pm2.group(1)
        else:
            pm2b = re.search(r"<a:ChildTable[^>]*>([^<]+)", rx)
            if pm2b: child_id = pm2b.group(1).strip()
        if not parent_id or not child_id: continue
        if parent_id not in tables_by_id or child_id not in tables_by_id: continue
        join_cols = []
        pat_join = re.compile(r"<o:ReferenceJoin[^>]*>(.*?)</o:ReferenceJoin>", re.DOTALL)
        for jm in pat_join.finditer(rx):
            jx = jm.group(1)
            pc = re.search(r"<o:Column\s+Ref=\"([^\"]+)\"", jx)
            cidx = jx.find("<c:ChildColumn>")
            cc = None
            if cidx >= 0:
                cc = re.search(r"<o:Column\s+Ref=\"([^\"]+)\"", jx[cidx:])
            if not cc:
                cc = re.search(r"<o:Column\s+Ref=\"([^\"]+)\"", jx)
            if pc and cc:
                join_cols.append((pc.group(1), cc.group(1)))
        rc = pat_code.search(rx)
        ref_code = rc.group(1).strip() if rc else ""
        refs.append({"parent_id": parent_id, "child_id": child_id, "join_cols": join_cols, "code": ref_code})
    return tables_by_id, tables, refs

def get_chain_key(name):
    for lp in LAYERS:
        if name.startswith(lp + "_"):
            name = name[len(lp) + 1:]; break
    for sfx in CHAIN_SUFFIXES:
        if name.endswith(sfx):
            name = name[:-len(sfx)]; break
    return name

def get_layer(schema):
    m = {"irpt":"irpt","dwi":"dwi","dwm":"dwm","dws":"dws","ads":"ads","sdi_wdtmp":"irpt","dim":"dwi"}
    return m.get(schema, "dwi")

def gen_ddl(tbl, layer):
    cname = tbl["cname"] if tbl["cname"] else tbl["name"]
    sname = layer if tbl["schema"] in ["sdi_wdtmp","dim"] else (tbl["schema"] if tbl["schema"] else layer)
    tn = tbl["name"]
    full = ("%s.%s" % (sname, tn)) if (layer and tn.startswith(layer + "_")) else ("%s.%s_%s" % (sname, layer, tn))
    dk = tbl["columns"][0]["code"] if tbl["columns"] else "id"
    L = ["", "/*" + "=" * 62 + "*/", "/* Table: %s */" % full, "/*" + "=" * 62 + "*/", "create table if not exists %s" % full, "("]
    for i, col in enumerate(tbl["columns"]):
        ct = col["type"]
        if col["precision"]: ct = "%s(%s)" % (col["type"], col["precision"])
        sep = "    " if i == 0 else "   ,"
        cl = "%-5s%-30s %-18s" % (sep, col["code"], ct)
        if col["name"]: cl += " comment " + chr(39) + (col["name"] if col["name"] != col["code"] else col["code"]) + chr(39)
        L.append(cl.rstrip())
    L.extend([")WITH", "\t(", "\t\torientation = column,", "\t\tcompression = low,", "\t\tcolversion = 2.0,", "\t\tenable_delta = false", "\t) DISTRIBUTE BY HASH (%s)" % dk])
    L.append("COMMENT " + chr(39) + cname + chr(39) + ";")
    return L

def gen_etl(ref, tbid):
    parent = tbid.get(ref["parent_id"])
    child = tbid.get(ref["child_id"])
    if not parent or not child: return []
    src = "%s.%s" % (parent["schema"] or "irpt", parent["name"])
    tgt = "%s.%s" % (child["schema"] or "dwi", child["name"])
    L = []
    L.append("")
    L.append("-- =============================================")
    L.append("-- Arrow: " + src + " -> " + tgt)
    if parent.get("notes_text",""): L.append("-- Notes: " + parent["notes_text"])
    if child.get("notes_text",""): L.append("-- Notes: " + child["notes_text"])
    if ref["code"]: L.append("-- " + ref["code"])
    if parent["cname"] and child["cname"]: L.append("-- " + parent["cname"] + " -> " + child["cname"])
    L.append("-- =============================================")
    L.append("")
    L.append("----------\u539f\u6709\u6570\u636e\u5220\u9664---------------")
    L.append("delete")
    L.append("from " + tgt)
    L.append("where substr(months,1,4) = substr( \u0027" + VAR_MONTHS + "\u0027 ,1,4)")
    L.append(";")
    L.append("")
    L.append("-------------\u65b0\u6570\u636e\u63d2\u5165------------")
    L.append("insert into " + tgt)
    L.append("(")
    for i, col in enumerate(child["columns"]):
        pfx = "    " if i == 0 else "   ,"
        cmt = " -- \u0027" + col["name"] + "\u0027" if col["name"] and col["name"] != col["code"] else ""
        L.append("%s%-25s%s" % (pfx, col["code"], cmt))
    L.append(")")
    L.append("select")
    join_map = {}
    for pc_id, cc_id in ref["join_cols"]:
        pcc = None; ccc = None
        for cp in parent["columns"]:
            if cp["id"] == pc_id: pcc = cp["code"]; break
        for cc_ in child["columns"]:
            if cc_["id"] == cc_id: ccc = cc_["code"]; break
        if pcc and ccc: join_map[ccc] = pcc
    for i, col in enumerate(child["columns"]):
        pfx = "     " if i == 0 else "    ,"
        cmt = " -- " + col["name"] if col["name"] and col["name"] != col["code"] else ""
        if col["code"] in join_map:
            L.append("%ssrc.%-22s%s" % (pfx, col["code"], cmt))
        else:
            jc = join_map.get(col["code"], col["code"])
            L.append("%snvl(src.%-15s,0) as %-20s%s" % (pfx, jc, col["code"], cmt))
    L.append("from " + src + " src")
    sn = parent.get("notes_sql","") or child.get("notes_sql","")
    if sn: L.append("where " + sn)
    if ref["join_cols"]:
        conds = []
        for pc_id, cc_id in ref["join_cols"]:
            pcn = None; ccn = None
            for cp in parent["columns"]:
                if cp["id"] == pc_id: pcn = cp["code"]; break
            for cc_ in child["columns"]:
                if cc_["id"] == cc_id: ccn = cc_["code"]; break
            if pcn and ccn: conds.append("src." + pcn + " = " + tgt + "." + ccn)
        if conds:
            L.append("where " + " and ".join(conds))
    L.append(";")
    return L

def output_pdm(pdm_path, folder_arg, schema_filter):
    tbid, tables, refs = parse_pdm_with_notes(pdm_path)
    if not tables:
        print("No tables found in PDM", file=sys.stderr)
        sys.exit(1)

    pdm_name = os.path.splitext(os.path.basename(pdm_path))[0]
    base = folder_arg or os.path.join(os.path.expanduser("~"), "Desktop", pdm_name)
    ddir = os.path.join(base, "ddl")
    cdir = os.path.join(base, "\u94fe\u8def")
    os.makedirs(ddir, exist_ok=True)
    os.makedirs(cdir, exist_ok=True)
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    # --- DDL output by layer ---
    lg = {}
    for t in tables:
        l = get_layer(t["schema"])
        if schema_filter and l != schema_filter: continue
        lg.setdefault(l, []).append(t)
    for l in LAYERS:
        if l not in lg: continue
        fp = os.path.join(ddir, l + ".sql")
        out = [
            "-- DDL from Power Designer PDM",
            "-- ******************************************************************** --",
            "-- author: \u6211\u662f\u8c01",
            "-- create time: " + now,
            "-- ******************************************************************** --",
            "",
            "-- ================ Layer: " + l + " ================",
            ""
        ]
        for t in lg[l]:
            out.extend(gen_ddl(t, l))
            out.append("")
        with open(fp, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        print("Written: " + fp)

    # --- ETL chains from arrows ---
    if refs:
        chain_refs = {}
        for ref in refs:
            child = tbid.get(ref["child_id"])
            if not child: continue
            if schema_filter and get_layer(child["schema"]) != schema_filter: continue
            parent = tbid.get(ref["parent_id"])
            if not parent: continue
            ckey = get_chain_key(child["name"])
            chain_refs.setdefault(ckey, []).append(ref)

        for ckey in sorted(chain_refs.keys()):
            fp = os.path.join(cdir, ckey + ".sql")
            out = [
                "-- ETL from Power Designer PDM (Arrow-based)",
                "-- ******************************************************************** --",
                "-- Data Chain: " + ckey,
                "-- author: \u6211\u662f\u8c01",
                "-- create time: " + now,
                "-- ******************************************************************** --",
                "",
                "-- ===== Data flow based on PDM arrows =====",
                ""
            ]
            srefs = sorted(chain_refs[ckey],
                key=lambda r: LAYERS.index(get_layer(tbid[r["parent_id"]]["schema"]))
                if get_layer(tbid[r["parent_id"]]["schema"]) in LAYERS else 99)
            for ref in srefs:
                out.extend(gen_etl(ref, tbid))
            with open(fp, "w", encoding="utf-8") as f:
                f.write("\n".join(out))
            print("Written: " + fp)
    else:
        print("Note: No reference arrows in PDM. Falling back to name-based chain grouping.")
        cg = {}
        for t in tables:
            l = get_layer(t["schema"])
            if schema_filter and l != schema_filter: continue
            ckey = get_chain_key(t["name"])
            cg.setdefault(ckey, []).append(t)
        for ckey, ctl in sorted(cg.items()):
            ctl.sort(key=lambda x: LAYERS.index(get_layer(x["schema"])) if get_layer(x["schema"]) in LAYERS else 99)
            fp = os.path.join(cdir, ckey + ".sql")
            out = [
                "-- " + "*" * 70,
                "-- Chain: " + ckey,
                "-- author: \u6211\u662f\u8c01",
                "-- create time: " + now,
                "-- " + "*" * 70,
                ""
            ]
            prev = None
            for t in ctl:
                l = get_layer(t["schema"])
                if prev and l != prev:
                    out.append("")
                    out.append("-- >>> Flow: " + prev + " -> " + l + " <<<")
                    out.append("")
                out.extend(gen_ddl(t, l))
                out.append("")
                prev = l
            with open(fp, "w", encoding="utf-8") as f:
                f.write("\n".join(out))
            print("Written: " + fp)

    print("")
    print("All files saved to: " + base)
    print("  ddl/    - Layer-based DDL")
    print("  \u94fe\u8def/ - ETL chain (from arrows)")


def main():
    ap = argparse.ArgumentParser(description="PDM to GaussDB DDL + ETL (arrow-based)")
    ap.add_argument("pdm_file", help="Power Designer .pdm file path")
    ap.add_argument("-o", "--output", help="Single DDL output file (overrides folder mode)")
    ap.add_argument("--schema", choices=LAYERS, help="Filter by single layer only")
    ap.add_argument("--folder", help="Base output folder (default: Desktop/{PDM file})")
    args = ap.parse_args()
    if not os.path.exists(args.pdm_file):
        print("File not found", file=sys.stderr)
        sys.exit(1)
    if args.output:
        tbid, tables, _ = parse_pdm_with_notes(args.pdm_file)
        if not tables:
            print("No tables found", file=sys.stderr)
            sys.exit(1)
        groups = {}
        for t in tables:
            l = get_layer(t["schema"])
            if args.schema and l != args.schema: continue
            groups.setdefault(l, []).append(t)
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        out = [
            "-- DDL from Power Designer PDM",
            "-- ******************************************************************** --",
            "-- author: \u6211\u662f\u8c01",
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
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        print("Written: " + args.output)
    else:
        output_pdm(args.pdm_file, args.folder, args.schema)


if __name__ == "__main__":
    main()

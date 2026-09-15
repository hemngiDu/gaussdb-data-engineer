#!/usr/bin/env python3
"""Dependency-free GaussDB SQL Doctor and release gate."""
import argparse, json, re
from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass
class Finding:
    severity: str
    rule: str
    line: int
    message: str

def lint_sql(sql: str) -> list[Finding]:
    findings, lines = [], sql.splitlines()
    for number, line in enumerate(lines, 1):
        if "NEED_CONFIRM" in line.upper() or re.search(r"\bTODO\b", line, re.I):
            findings.append(Finding("error", "UNRESOLVED_RULE", number, "存在未确认的业务规则"))
        if re.search(r"\bNVL\s*\([^,]+,\s*0\s*\)", line, re.I):
            findings.append(Finding("warning", "NVL_ZERO", number, "确认字段为数值且业务要求 NULL 转 0"))
        if re.search(r"\b(delete|update)\b", line, re.I) and not line.lstrip().startswith("--"):
            if not re.search(r"\bwhere\b", "\n".join(lines[number - 1:number + 8]), re.I):
                findings.append(Finding("error", "DML_WITHOUT_WHERE", number, "DELETE/UPDATE 缺少 WHERE"))
        if re.search(r"\bselect\s+\*", line, re.I):
            findings.append(Finding("warning", "SELECT_STAR", number, "生产 ETL 应显式列出字段"))
        if re.search(r"\bjoin\b", line, re.I) and not line.lstrip().startswith("--"):
            if not re.search(r"\bon\b", "\n".join(lines[number - 1:number + 5]), re.I):
                findings.append(Finding("error", "JOIN_WITHOUT_ON", number, "JOIN 缺少 ON 条件"))
        if re.search(r"\bwhere\s+\w+\([^)]*\w+[^)]*\)\s*=", line, re.I):
            findings.append(Finding("warning", "FUNCTION_FILTER", number, "字段侧函数可能阻止分区裁剪或索引使用"))
    text = "\n".join(lines)
    if (re.search(r"^\s*select\b", text, re.I | re.M)
        and re.search(r"^\s*from\b", text, re.I | re.M)
        and not re.search(r"^\s*where\b", text, re.I | re.M)):
        findings.append(Finding("warning", "UNFILTERED_SCAN", 1, "查询无 WHERE；核对全表扫描是否符合预期"))
    if re.search(r"\bjoin\b", text, re.I) and re.search(r"\bgroup\s+by\b", text, re.I):
        findings.append(Finding("warning", "JOIN_AGGREGATION", 1, "核对 JOIN 基数和 GROUP BY 粒度，避免指标放大"))
    if re.search(r"create\s+table", text, re.I) and not re.search(r"^\s*DISTRIBUTE\s+BY", text, re.I | re.M):
        findings.append(Finding("error", "DISTRIBUTION_MISSING", 1, "DDL 缺少已确认的分布策略"))
    if re.search(r"^\s*\w*\s*join\b", text, re.I | re.M) and not re.search(r"--\s*(?:JOIN_KEY|.*依据)", text, re.I):
        findings.append(Finding("warning", "JOIN_EVIDENCE", 1, "请记录 JOIN KEY 的模型或业务依据"))
    return findings

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GaussDB SQL Doctor")
    parser.add_argument("paths", nargs="+"); parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", choices=["error", "warning", "none"], default="error")
    args = parser.parse_args(argv); results = {}
    for raw in args.paths:
        path = Path(raw); files = sorted(path.rglob("*.sql")) if path.is_dir() else [path]
        for file in files:
            results[str(file)] = [asdict(item) for item in lint_sql(file.read_text(encoding="utf-8"))]
    if args.json: print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for file, items in results.items():
            for item in items: print(f"{file}:{item['line']}: {item['severity']} {item['rule']} - {item['message']}")
    levels = {item["severity"] for items in results.values() for item in items}
    return int(args.fail_on == "error" and "error" in levels or args.fail_on == "warning" and bool(levels))

if __name__ == "__main__": raise SystemExit(main())

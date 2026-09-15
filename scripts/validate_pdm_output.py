#!/usr/bin/env python3
import argparse
from pathlib import Path
from sql_linter import lint_sql

def validate(root: Path) -> list[str]:
    errors, files = [], list(root.rglob("*.sql"))
    if not files: return ["未找到 SQL 文件"]
    if (root / "链路" / "NEED_CONFIRM.md").exists():
        errors.append(f"{root / '链路' / 'NEED_CONFIRM.md'}: 缺少 PDM 表关系，ETL 链路未确认")
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "create table" in text.lower() and "-- author: 我是谁" not in text:
            errors.append(f"{path}: 缺少固定文件头")
        errors.extend(f"{path}:{f.line}: {f.rule} {f.message}" for f in lint_sql(text) if f.severity == "error")
    return errors

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="校验 PDM 生成结果"); parser.add_argument("output_dir")
    errors = validate(Path(parser.parse_args(argv).output_dir))
    for error in errors: print(error)
    print(f"校验失败：{len(errors)} 个问题" if errors else "校验通过")
    return int(bool(errors))

if __name__ == "__main__": raise SystemExit(main())

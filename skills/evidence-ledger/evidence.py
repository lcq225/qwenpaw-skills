#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evidence Ledger — 证据台账（MVP）

把一个结论的「主张 / 证据 / 来源 / 状态」结构化登记下来，让报告、方案、
分析里的每一句话都能回答「依据是什么」。

状态四值（必须选一）：
  已核实 verified   — 有来源、已核对
  推断   inferred   — 基于证据推导、未独立核实
  待核定 pending    — 有值但口径待确认
  未查询 not_queried— 尚未查，先记下这个问题

用法：
  python evidence.py add --topic 主题 --claim 主张 --evidence 证据 --source 来源 [--status 已核实]
  python evidence.py list [--topic 词] [--status 已核实]
  python evidence.py conflicts [--topic 词]
  python evidence.py export [--out report.md]

数据存 JSON 文件（默认 evidence.json），纯标准库，无外部依赖。
"""
import argparse
import json
import os
import sys
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_DB = "evidence.json"
STATUSES = {"已核实", "推断", "待核定", "未查询"}


def load_db(path):
    if not os.path.exists(path):
        return {"version": "1.0.0", "records": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "records" not in data:
        data = {"version": "1.0.0", "records": []}
    return data


def save_db(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    # JSON 铁律：写后 json.load 校验
    with open(path, encoding="utf-8") as f:
        json.load(f)


def next_id(records):
    max_n = 0
    for r in records:
        i = r.get("id", "")
        if i.startswith("E-") and i[2:].isdigit():
            max_n = max(max_n, int(i[2:]))
    return "E-%03d" % (max_n + 1)


def cmd_add(args):
    if args.status not in STATUSES:
        print("错误：status 必须是 %s 之一" % " / ".join(sorted(STATUSES)))
        sys.exit(1)
    data = load_db(args.db)
    rec = {
        "id": next_id(data["records"]),
        "topic": args.topic.strip(),
        "claim": args.claim.strip(),
        "evidence": args.evidence.strip(),
        "source": args.source.strip(),
        "date": args.date or date.today().isoformat(),
        "status": args.status,
    }
    data["records"].append(rec)
    save_db(args.db, data)
    print("已登记 %s | [%s] %s | %s" % (rec["id"], rec["status"], rec["topic"], rec["claim"]))


def cmd_list(args):
    data = load_db(args.db)
    out = data["records"]
    if args.topic:
        out = [r for r in out if args.topic in r["topic"]]
    if args.status:
        out = [r for r in out if r["status"] == args.status]
    if not out:
        print("（无记录）")
        return
    for r in out:
        print("%s | [%s] %s | %s" % (r["id"], r["status"], r["topic"], r["claim"]))


def cmd_conflicts(args):
    data = load_db(args.db)
    by_topic = {}
    for r in data["records"]:
        if args.topic and args.topic not in r["topic"]:
            continue
        by_topic.setdefault(r["topic"], []).append(r)
    found = False
    for topic, recs in by_topic.items():
        claims = sorted({r["claim"] for r in recs})
        if len(claims) > 1:
            found = True
            print("⚠ 主题「%s」下存在 %d 条不同主张，请人工核对：" % (topic, len(claims)))
            for r in recs:
                print("   %s | [%s] %s | 来源:%s" % (r["id"], r["status"], r["claim"], r["source"]))
            print()
    if not found:
        print("（未发现同主题下主张不一致的记录）")


def cmd_export(args):
    data = load_db(args.db)
    lines = ["# 证据台账", ""]
    lines.append("| ID | 主题 | 主张 | 证据/依据 | 来源 | 状态 |")
    lines.append("|----|------|------|-----------|------|------|")
    for r in data["records"]:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["topic"], r["claim"], r["evidence"], r["source"], r["status"]))
    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("已导出 %s（%d 条）" % (args.out, len(data["records"])))
    else:
        sys.stdout.write(text)


def main():
    p = argparse.ArgumentParser(description="Evidence Ledger 证据台账")
    p.add_argument("--db", default=DEFAULT_DB, help="台账文件路径（默认 evidence.json）")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--topic", required=True)
    a.add_argument("--claim", required=True)
    a.add_argument("--evidence", required=True)
    a.add_argument("--source", required=True)
    a.add_argument("--status", default="待核定")
    a.add_argument("--date", default="")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list")
    l.add_argument("--topic", default="")
    l.add_argument("--status", default="")
    l.set_defaults(func=cmd_list)

    c = sub.add_parser("conflicts")
    c.add_argument("--topic", default="")
    c.set_defaults(func=cmd_conflicts)

    e = sub.add_parser("export")
    e.add_argument("--out", default="")
    e.set_defaults(func=cmd_export)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Publish Auditor — 技能公开发布前审计器（MVP）

不判断一个技能“好不好”，只在公开发布前回答五件事：
1. 它是不是第三方作品，是否有署名/许可风险？
2. 有没有本机路径、公司名、个人身份、凭据等公开敏感信息？
3. SKILL.md frontmatter 是否具备 name/description？
4. 有哪些外部依赖？
5. zip 包是否为扁平结构（SKILL.md 在根）？

用法：
  python audit.py --skill-path path/to/skill
  python audit.py --zip path/to/skill.zip
"""
import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TEXT_EXTS = {".md", ".py", ".json", ".txt", ".js", ".ts", ".yaml", ".yml", ".toml", ".ini", ".cfg"}

# 公开发布时应人工复核的信号；命中不自动判“泄密”，而是阻断“直接发布”。
SENSITIVE_PATTERNS = {
    "本机绝对路径": r"(?i)(?:[A-Z]:\\|C:/Users/|D:/Users/|/home/|/Users/)",
    "企业名称": r"(?:海科|赫邦|haike|hebang)",
    "个人身份": r"(?:李长卿|Siva|lcq225)",
    "凭据关键词": r"(?i)\b(?:api[_-]?key|token|password|secret|bearer)\s*[:=]\s*[^\s'\"{]",
    "连接串": r"(?i)\b(?:postgresql|mysql|mongodb|redis)://[^\s'\"]+",
}
PROVENANCE_PATTERNS = {
    "版权声明": r"(?i)\bcopyright\b",
    "第三方来源说明": r"(?i)(?:originally\s+from|forked\s+from|ported\s+from|原作者|上游项目|来源仓库|来源作者|基于\s*(?:开源|GitHub|项目|仓库|模块))",
    "GitHub 来源链接": r"https?://github\.com/[^\s)\]>'\"]+",
}


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def find_files(root):
    paths = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "node_modules"}]
        for name in files:
            p = Path(current) / name
            if p.suffix.lower() in TEXT_EXTS or name == "SKILL.md":
                paths.append(p)
    return sorted(paths)


def frontmatter_check(skill_md):
    result = []
    if not skill_md.exists():
        return [("BLOCK", "缺少 SKILL.md")], {}
    text = read_text(skill_md)
    if not text.startswith("---\n"):
        return [("BLOCK", "SKILL.md 缺少 YAML frontmatter 起始分隔线")], {}
    end = text.find("\n---", 4)
    if end < 0:
        return [("BLOCK", "SKILL.md frontmatter 未闭合")], {}
    header = text[4:end]
    fields = {}
    for line in header.splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    if not fields.get("name"):
        result.append(("BLOCK", "frontmatter 缺少 name"))
    if not fields.get("description"):
        result.append(("BLOCK", "frontmatter 缺少 description"))
    if fields.get("description") and ":" in fields["description"] and not fields["description"].startswith(("'", '"', ">", "|")):
        result.append(("WARN", "description 含冒号且未显式引用，需 YAML 解析复核"))
    if not result:
        result.append(("PASS", "frontmatter 具备 name + description"))
    return result, fields


def extract_imports(text):
    imports = set()
    for name in re.findall(r"(?m)^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", text):
        imports.add(name.split(".")[0])
    stdlib = {"argparse", "ast", "base64", "collections", "csv", "datetime", "functools", "hashlib", "html", "io", "itertools", "json", "logging", "math", "os", "pathlib", "platform", "re", "shutil", "subprocess", "sys", "tempfile", "textwrap", "time", "typing", "urllib", "uuid", "zipfile"}
    return sorted(x for x in imports if x not in stdlib)


def scan_skill(skill_path):
    root = Path(skill_path)
    if not root.is_dir():
        raise ValueError("技能目录不存在：%s" % root)
    findings, details = [], []
    fm, fields = frontmatter_check(root / "SKILL.md")
    findings.extend(fm)

    license_files = list(root.glob("LICENSE*")) + list(root.glob("COPYING*"))
    if license_files:
        findings.append(("PASS", "发现许可文件：%s" % ", ".join(x.name for x in license_files)))
    else:
        findings.append(("WARN", "未发现 LICENSE/COPYING 文件；公开发布前需确认许可归属"))

    sensitive_hits, provenance_hits, deps = [], [], set()
    for fp in find_files(root):
        text = read_text(fp)
        rel = fp.relative_to(root).as_posix()
        deps.update(extract_imports(text))
        for label, pat in SENSITIVE_PATTERNS.items():
            for m in re.finditer(pat, text):
                line = text.count("\n", 0, m.start()) + 1
                raw = text.splitlines()[line - 1]
                # 跳过“定义该正则的那一行源码”，避免审计器自扫时把规则字面量当命中
                if "r\"" in raw and ":" in raw and label in raw:
                    continue
                sensitive_hits.append((label, rel, line, raw[:180]))
        for label, pat in PROVENANCE_PATTERNS.items():
            for m in re.finditer(pat, text):
                line = text.count("\n", 0, m.start()) + 1
                raw = text.splitlines()[line - 1]
                if "r\"" in raw and ":" in raw and label in raw:
                    continue
                # 「copyright」作为参数/说明性文字（如 --copyright、Back cover copyright）
                # 不算第三方来源信号；只认真正的版权声明行。
                if label == "版权声明" and not re.match(r"(?i)^\s*(?:©|copyright\b)", raw):
                    continue
                provenance_hits.append((label, rel, line, raw[:180]))

    author = fields.get("author", "")
    if author:
        provenance_hits.append(("frontmatter 作者", "SKILL.md", 0, "author: %s" % author))

    if sensitive_hits:
        findings.append(("BLOCK", "发现 %d 处公开敏感信号" % len(sensitive_hits)))
    else:
        findings.append(("PASS", "未发现预设的路径/公司/身份/凭据/连接串信号"))
    if provenance_hits:
        findings.append(("BLOCK", "发现 %d 处来源/署名信号；需确认原创或保留署名与许可" % len(provenance_hits)))
    else:
        findings.append(("PASS", "未发现第三方来源/署名信号"))
    details.append(("依赖", ", ".join(sorted(deps)) if deps else "仅标准库或未检测到 import"))
    return findings, sensitive_hits, provenance_hits, details


def scan_zip(zip_path):
    path = Path(zip_path)
    if not path.is_file():
        raise ValueError("zip 文件不存在：%s" % path)
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        names = [n for n in z.namelist() if not n.endswith("/")]
    findings = []
    if bad:
        findings.append(("BLOCK", "zip 损坏：%s" % bad))
    else:
        findings.append(("PASS", "zip 完整性通过"))
    if "SKILL.md" in names:
        findings.append(("PASS", "SKILL.md 位于 zip 根目录（扁平结构）"))
    else:
        nested = [n for n in names if n.endswith("/SKILL.md")]
        findings.append(("BLOCK", "SKILL.md 不在 zip 根目录%s" % ("（发现：%s）" % ", ".join(nested[:3]) if nested else "")))
    return findings, [("压缩包文件数", str(len(names)))]


def emit(findings, details, sensitive=None, provenance=None):
    order = {"PASS": 0, "WARN": 1, "BLOCK": 2}
    icon = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "🔴"}
    print("=" * 56)
    print("SKILL PUBLISH AUDIT REPORT")
    print("=" * 56)
    for level, msg in sorted(findings, key=lambda x: order[x[0]]):
        print("%s %s" % (icon[level], msg))
    for key, value in details:
        print("• %s：%s" % (key, value))
    if sensitive:
        print("\n敏感信号（发布前必须处理）：")
        for label, rel, line, text in sensitive[:20]:
            print("  [%s] %s:%s | %s" % (label, rel, line, text))
    if provenance:
        print("\n来源/署名信号（不得冒充原创）：")
        for label, rel, line, text in provenance[:20]:
            loc = "%s:%s" % (rel, line) if line else rel
            print("  [%s] %s | %s" % (label, loc, text))
    verdict = "可进入人工发布审阅"
    if any(level == "BLOCK" for level, _ in findings):
        verdict = "阻断直接发布：先解决红色项"
    elif any(level == "WARN" for level, _ in findings):
        verdict = "待补项：处理黄色项后再审阅"
    print("\nVERDICT：%s" % verdict)
    return 1 if any(level == "BLOCK" for level, _ in findings) else 0


def main():
    p = argparse.ArgumentParser(description="Skill Publish Auditor — 技能公开发布前审计")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--skill-path", help="技能目录")
    group.add_argument("--zip", help="待发布 zip 包")
    args = p.parse_args()
    try:
        if args.skill_path:
            findings, sensitive, provenance, details = scan_skill(args.skill_path)
            return emit(findings, details, sensitive, provenance)
        findings, details = scan_zip(args.zip)
        return emit(findings, details)
    except (ValueError, OSError, zipfile.BadZipFile) as e:
        print("审计失败：%s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connector Kit — 统一只读连接器底座（MVP）

不替代各系统 API，只提供三个统一只读接口，并内置一个可运行的「本地文件文档库」
适配器作为参考样例。后续可仿照该适配器增加 Confluence / Jira / SharePoint / 飞书 等。

三个接口：
  connector_list   列出已配置连接器（不返回任何凭据）
  connector_search 统一搜索，返回标准化结果（限定条数与内容长度）
  connector_fetch  获取单个资源全文

安全边界（第一版写死）：
  - 只读：无 create / update / delete
  - 凭据只经环境变量，不写源码、不进 config 明文
  - 搜索结果限条数、限内容长度
  - 失败显式报错，不静默返回空
  - 一连接器一适配器，不做万能 HTTP 请求器

用法：
  python connector_kit.py --config connectors.yaml list
  python connector_kit.py --config connectors.yaml search my_docs --query 关键词 --limit 10
  python connector_kit.py --config connectors.yaml fetch my_docs path/to/file.md
"""
import argparse
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_MAX_CHARS = 12000


# ────────────────────────────── 适配器 ──────────────────────────────

class LocalDocsAdapter:
    """只读本地文档库：搜索 .md/.txt 文件名与内容，按关键词命中排序。"""

    type = "local_docs"

    def __init__(self, cfg):
        root = cfg.get("root")
        if not root:
            raise ValueError("local_docs 适配器需在 config 中指定 root 目录")
        self.root = root
        self.max_chars = int(cfg.get("max_content_chars", DEFAULT_MAX_CHARS))
        self.exts = set(cfg.get("extensions", [".md", ".txt"]))

    def _walk(self):
        for cur, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__"}]
            for name in files:
                if os.path.splitext(name)[1].lower() in self.exts:
                    yield os.path.join(cur, name)

    def search(self, query, limit):
        q = query.lower()
        scored = []
        for path in self._walk():
            rel = os.path.relpath(path, self.root)
            name_hit = q in os.path.basename(path).lower()
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            body_hit = text.lower().count(q)
            if not name_hit and body_hit == 0:
                continue
            # 文件名命中权重更高；内容按命中次数
            score = (3 if name_hit else 0) + min(body_hit, 10)
            scored.append((score, rel, len(text)))
        scored.sort(key=lambda x: -x[0])
        return [
            {"resource_id": rel, "score": s, "size_chars": n}
            for s, rel, n in scored[:limit]
        ]

    def fetch(self, resource_id):
        # resource_id 是相对路径，禁止路径穿越
        base = os.path.abspath(self.root)
        target = os.path.abspath(os.path.join(base, resource_id))
        if not target.startswith(base + os.sep) and target != base:
            raise ValueError("非法路径：%s" % resource_id)
        if not os.path.isfile(target):
            raise ValueError("资源不存在：%s" % resource_id)
        if os.path.splitext(target)[1].lower() not in self.exts:
            raise ValueError("不支持的文件类型：%s" % resource_id)
        text = open(target, encoding="utf-8", errors="ignore").read()
        return {"resource_id": resource_id, "content": text[: self.max_chars]}


ADAPTERS = {"local_docs": LocalDocsAdapter}


# ────────────────────────────── 配置加载 ──────────────────────────────

def load_config(path):
    if not os.path.exists(path):
        raise ValueError("配置文件不存在：%s" % path)
    # connectors.yaml 使用 JSON 语法（JSON 也是合法 YAML），零外部依赖。
    data = json.load(open(path, encoding="utf-8"))
    return data.get("connectors", {})


def _expand_env(value):
    """把 ${VAR} 占位符替换为环境变量；用于 base_url / token 等，绝不写回源码。"""
    if not isinstance(value, str):
        return value
    def sub(m):
        return os.environ.get(m.group(1), "")
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", sub, value)


def get_adapter(cfg):
    adapter_type = cfg.get("type")
    if adapter_type not in ADAPTERS:
        raise ValueError("未知适配器类型：%s" % adapter_type)
    resolved = {k: _expand_env(v) for k, v in cfg.items()}
    if not resolved.get("enabled", True):
        raise ValueError("连接器已禁用")
    return ADAPTERS[adapter_type](resolved)


# ────────────────────────────── 三个接口 ──────────────────────────────

def connector_list(connectors):
    print("已配置连接器（不含凭据）：")
    for cid, cfg in connectors.items():
        enabled = cfg.get("enabled", True)
        print("  - %s | type=%s | enabled=%s" % (cid, cfg.get("type", "?"), enabled))


def connector_search(connectors, cid, query, limit):
    if cid not in connectors:
        raise ValueError("连接器不存在：%s" % cid)
    adapter = get_adapter(connectors[cid])
    results = adapter.search(query, limit)
    print("连接器 %s 搜索「%s」命中 %d 条：" % (cid, query, len(results)))
    for r in results:
        print("  [%s] score=%s chars=%s" % (r["resource_id"], r.get("score"), r.get("size_chars")))


def connector_fetch(connectors, cid, resource_id):
    if cid not in connectors:
        raise ValueError("连接器不存在：%s" % cid)
    adapter = get_adapter(connectors[cid])
    result = adapter.fetch(resource_id)
    print("资源 %s（截断至 %d 字符）：" % (result["resource_id"], len(result["content"])))
    print(result["content"])


def main():
    p = argparse.ArgumentParser(description="Connector Kit — 统一只读连接器底座")
    p.add_argument("--config", default="connectors.yaml", help="配置文件路径")
    sub = p.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("list")
    l.set_defaults(func=lambda c, a: connector_list(c))

    s = sub.add_parser("search")
    s.add_argument("connector_id")
    s.add_argument("--query", required=True)
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=lambda c, a: connector_search(c, a.connector_id, a.query, a.limit))

    f = sub.add_parser("fetch")
    f.add_argument("connector_id")
    f.add_argument("resource_id")
    f.set_defaults(func=lambda c, a: connector_fetch(c, a.connector_id, a.resource_id))

    args = p.parse_args()
    try:
        connectors = load_config(args.config)
        args.func(connectors, args)
    except (ValueError, OSError) as e:
        print("错误：%s" % e)
        sys.exit(1)


if __name__ == "__main__":
    main()

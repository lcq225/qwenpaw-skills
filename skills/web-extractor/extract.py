# -*- coding: utf-8 -*-
"""
web-extractor — 网页正文抓取与摘要
====================================
从 URL 抽取干净正文（去导航/广告/页脚），可选输出 Markdown/纯文本，
可选生成摘要/要点（调本地 LLM）。

用法:
    python extract.py --url <URL>              # 打印正文
    python extract.py --url <URL> --summary    # 正文+摘要
    python extract.py --url <URL> --out a.md   # 写文件
    python extract.py -f urls.txt --out all.md # 批量
"""

import argparse
import io
import sys
from urllib.parse import urlparse

def _utf8():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 反爬/受限站点提示(由使用者按需扩展)
CAPTCHA_HINTS = ("captcha", "verify", "cf-chl", "recaptcha")


class Extractor:
    """分层网页正文抽取器。"""

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def _fetch_http(self, url: str):
        import httpx
        with httpx.Client(timeout=self.timeout, follow_redirects=True,
                          headers=HEADERS, verify=False) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.text, r.url

    def _readability(self, html: str):
        from readability import Document
        doc = Document(html)
        from bs4 import BeautifulSoup
        main = doc.summary()
        text = BeautifulSoup(main, "html.parser").get_text("\n", strip=True)
        return (doc.short_title() or doc.title() or "", text)

    def extract(self, url: str, prefer_method: str = "auto"):
        """返回 {title, url, text, source, error}。"""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
        html = None
        final_url = url
        source = "L1-http"
        try:
            html, final_url = self._fetch_http(url)
        except Exception as e:
            # L1 失败 -> 尝试真实浏览器(如可用)
            try:
                from browser import Browser  # QwenPaw 内置 Browser SDK（可选）
                b = Browser()
                content = b.fetch(url)
                html = content if isinstance(content, str) else (content.text or "")
                source = "L2-browser"
            except Exception as be:
                return {"title": "", "url": url, "text": "",
                        "source": source, "error": f"L1 {e}; L2 {be}"}

        if not html:
            return {"title": "", "url": final_url, "text": "", "source": source,
                    "error": "empty html"}

        try:
            title, text = self._readability(html)
        except Exception as e:
            return {"title": "", "url": final_url, "text": "", "source": source,
                    "error": f"readability: {e}"}

        if not text and source == "L1-http":
            source += "+emptymain"
        return {"title": title, "url": str(final_url), "text": text,
                "source": source, "error": ""}


def summarize(text: str, lang: str = "zh", model: str = ""):
    """调用本地 LLM 生成摘要与要点。失败时返回空 dict。"""
    if not text:
        return {}
    prompt = (
        f"以下是网页正文。请用{('中文' if lang=='zh' else '英文')}给出：\n"
        f"## 摘要\n200字以内概括。\n\n## 要点\n列出3-7条关键信息，每条一句话。\n\n正文：\n{text[:3000]}"
    )
    try:
        import requests
        import os
        # 默认本地 ollama；可经环境变量覆盖(兼容 OpenAI 端点)
        base = os.environ.get("WEBX_BASE") or "http://127.0.0.1:11434/v1"
        m = os.environ.get("WEBX_MODEL") or model or "qwen2.5:7b"
        key = os.environ.get("WEBX_API_KEY") or ""
        hdrs = {"Content-Type": "application/json"}
        if key:
            hdrs["Authorization"] = "Bearer " + key
        r = requests.post(base + "/chat/completions",
                          json={"model": m,
                                "messages": [{"role": "user", "content": prompt}]},
                          headers=hdrs, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        return {"summary": content}
    except Exception as e:
        return {"summary": "", "error": f"summarize: {e}"}


def _fmt(result, with_summary: bool, lang: str):
    lines = []
    if result.get("title"):
        lines.append("# " + result["title"])
    lines.append("> 来源: " + (result.get("url") or ""))
    if result.get("error"):
        lines.append("")
        lines.append("[提取失败] " + result["error"])
        return "\n".join(lines)
    lines.append("")
    lines.append(result.get("text") or "(无正文)")
    if with_summary:
        s = summarize(result.get("text") or "", lang)
        if s.get("summary"):
            lines.append("")
            lines.append("---")
            lines.append("## 摘 要")
            lines.append("")
            lines.append(s["summary"])
        elif s.get("error"):
            lines.append("")
            lines.append("[摘要不可用] " + s["error"])
    return "\n".join(lines)


def main(argv=None):
    _utf8()
    p = argparse.ArgumentParser(description="网页正文抓取与摘要")
    p.add_argument("--url", help="单个 URL")
    p.add_argument("-f", "--file", help="URL 列表文件(每行一个)")
    p.add_argument("-o", "--out", help="输出文件")
    p.add_argument("--summary", action="store_true", help="生成摘要/要点")
    p.add_argument("--format", choices=["md", "txt"], default="md")
    p.add_argument("--lang", default="zh")
    args = p.parse_args(argv)

    if not args.url and not args.file:
        p.error("必须提供 --url 或 -f 文件")

    urls = []
    if args.url:
        urls.append(args.url)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            urls += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    ex = Extractor()
    outputs = []
    for i, u in enumerate(urls, 1):
        res = ex.extract(u)
        block = _fmt(res, args.summary, args.lang)
        tag = f"[{i}/{len(urls)}] "
        outputs.append(tag + "## " + (res.get("title") or u) + "\n" + block)

    final = ("\n\n" + "=" * 50 + "\n\n").join(outputs)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(final)
        print(f"[OK] 已写入 {args.out}（{len(urls)} 页）")
    else:
        print(final)
    return 0


if __name__ == "__main__":
    sys.exit(main())

---
name: web-extractor
description: "Extract the main body text of web pages (strip nav/ads/footers) and optionally summarize it — 网页正文抓取与摘要. Use when you need to fetch a page's clean readable content given a URL, pull article/news/blog text out of cluttered pages, batch-extract multiple pages to Markdown, or summarize a web article's key points. Triggered on: 抓网页正文、提取文章内容、网页转md、链接提取正文、批量抓取文章、网页摘要、总结链接内容、把网址内容整理出来."
---

# web-extractor — 网页正文抓取与摘要

抓取网页**干净正文**（去导航/广告/页脚/侧栏），可选生成摘要/要点，输出 Markdown/纯文本。中文优先，适配国内文章/新闻/博客站点。

## When to Use

- 给一个 URL，要它的**正文**而非整页垃圾
- 从新闻/博客/技术文章/公众号页面提取可读内容
- 批量抓取多个链接，导出统一格式（md/txt）
- 抓完后要**摘要/要点**（标题、时间、正文要点）

## How it works（分层策略）

```
extract.py --url <URL> [--summary] [--out file.md] [--format md|txt]
```

| 层 | 场景 | 手段 |
|:--|:--|:--|
| **L1** | 静态/常规页面 | `httpx` 抓 HTML → `readability-lxml` 抽正文（剔导航/广告/页脚）|
| **L2** | JS 动态渲染（SPA/评论区/需登录可见） | 调 **QwenPaw 内置 Browser SDK** 渲染后抽取 |
| **L3** | 保底 | 原样取标题 + 可读文本截断；或提示需要浏览器/OCR |

> 依赖：`httpx` `readability-lxml` `bs4`（`pip install readability-lxml`，国内用清华镜像）。L2 交互需要可用 `browser` 技能。

## 摘要（--summary）配置

默认调本地 `ollama`（`http://127.0.0.1:11434/v1`，模型 `qwen2.5:7b`）。可按需用环境变量切换到任意 OpenAI 兼容端点（含公司内网 LLM 网关）：

```bash
set WEBX_BASE=https://<endpoint>/v1
set WEBX_MODEL=deepseek-v4-flash
set WEBX_API_KEY=<your-key>     # 远程端点需要鉴权时
```

LLM 不可用时摘要会优雅降级为 `[摘要不可用] ...`，不影响正文提取。

## 用法

```bash
# 单页正文
python extract.py --url "https://www.oschina.net/news" --format md

# 单页正文+摘要
python extract.py --url "https://..." --summary --out result.md

# 批量（urls.txt 每行一个链接）
python extract.py -f urls.txt --summary --out all.md
```

### Python API

```python
import sys; sys.path.insert(0, r'<skills>/web-extractor')
from extract import Extractor

e = Extractor()
res = e.extract("https://example.com/article")
# res = {title, url, text, error}
```

## 输出

- 标题 `# 标题`
- 元信息（url）
- 正文（干净 Markdown/纯文本）
- `--summary` 时追加 `## 摘 要` + `## 要 点`（3–7 条）

## Common Mistakes

- 门户/首页（非单篇）正文很短属正常（散落内容），请用**单篇文章 URL**。
- 登录墙/付费墙/强反爬（Cloudflare 人机验证）可能抓不到，需浏览器会话。
- 正文抽取偶有裁错边界，可对高频失败站点加自定义选择器（见 `extractor.errors`）。
- 依赖缺失时 `pip install readability-lxml httpx beautifulsoup4`（清华镜像）。

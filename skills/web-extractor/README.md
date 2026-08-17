# web-extractor — 网页正文抓取与摘要

从网页 URL 抽取**干净正文**（去导航/广告/页脚/侧栏），可选生成摘要/要点，输出 Markdown/纯文本。中文优先，适配新闻/博客/技术文章/公司门户等站点。

## 特性

- **分层抓取**：L1 静态页（httpx + readability-lxml 抽正文）→ L2 JS 渲染兜底（QwenPaw Browser SDK）
- **批量**：`-f urls.txt` 一次抓多页
- **摘要可选**：`--summary` 调本地 LLM（ollama 或任意 OpenAI 兼容端点）出摘要/要点
- 输出 `--format md|txt`、写文件 `--out`

## 安装

```bash
pip install -r requirements.txt
```

## 用法

```bash
# 单页正文
python extract.py --url "https://www.oschina.net/news" --format md

# 单页 + 摘要
python extract.py --url "https://example.com/article" --summary --out result.md

# 批量（urls.txt 每行一个链接）
python extract.py -f urls.txt --summary --out all.md
```

### Python API

```python
import sys; sys.path.insert(0, "<path>/web-extractor")
from extract import Extractor
res = Extractor().extract("https://example.com/article")
# res = {title, url, text, source, error}
```

## 摘要配置（env，OpenAI 兼容端点）

```bash
set WEBX_BASE=https://<endpoint>/v1        # 默认 http://127.0.0.1:11434/v1 (ollama)
set WEBX_MODEL=<model>                     # 默认 qwen2.5:7b
set WEBX_API_KEY=<key>                     # 远程端点鉴权时
```

LLM 不可用时会优雅降级为 `[摘要不可用]`，不影响正文提取。

## 边界（诚实说明）

- L1 静态页对新闻/博客/技术文章覆盖 90%+；门户/首页非单篇正文短属正常（请用单篇文章 URL）。
- JS 渲染/SPA 走内置浏览器，登录墙内内容需先登录，强反爬（Cloudflare 人机验证/付费墙）可能抓不到。
- 依赖：`httpx`、`readability-lxml`、`beautifulsoup4`。国内装失败可换清华镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。

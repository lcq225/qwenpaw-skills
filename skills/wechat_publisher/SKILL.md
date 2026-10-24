---
name: wechat_publisher
description: "微信公众号排版与草稿箱发布技能。把 Markdown 转成微信可读的富排版 HTML（彩色卡片、蓝/红强调、标题层级、富表格、浅灰 footer），上传正文图与封面永久素材，并通过官方 API 创建草稿、打包多图文草稿、查询草稿列表与发布状态。当用户需要公众号排版、Markdown 转公众号格式、推送到草稿箱、批量图文推送、检查渲染是否落地时使用。触发场景：公众号排版、微信 HTML、草稿箱推送、draft/add、封面 media_id、正文图上传、多图文打包、渲染回归自检。"
version: 1.0.0
license: MIT
metadata:
  emoji: "📝"
  tags: ["公众号", "排版", "草稿箱", "微信 API", "富文本"]
---

# wechat_publisher — 公众号排版与草稿箱推送

把 Markdown 变成微信能正确渲染的富排版 HTML，并通过官方 API 推送到草稿箱。
**默认只推草稿箱，不自动发表。**

## 一、能做什么

| 能力 | 方法 | 说明 |
|:--|:--|:--|
| Markdown → 微信 HTML | `markdown_to_wechat_html(md, theme=...)` | 全内联样式，兼容微信编辑器 |
| 12 套版式主题 | `STYLE_PRESETS` | 见「风格库」一节 |
| 上传正文图 | `upload_image(path)` | `media/uploadimg` → `mmbiz.qpic.cn` |
| 上传封面（永久素材） | `upload_cover(path)` | `material/add_material?type=image` → `media_id` |
| 创建单篇草稿 | `create_draft(...)` | 仅进草稿箱 |
| 创建多图文草稿 | `create_bundled_draft(articles)` | 一次打包多篇（≤8） |
| 草稿列表 | `get_draft_list(offset, count)` | 分页 |
| 发布草稿 | `publish_draft(media_id)` | 正式发表，需自行确认 |
| 发布状态 | `get_publish_status(publish_id)` | 查询发布任务 |
| 一键流程 | `publish_article(md, title, ...)` | 渲染 → 上传 → 建草稿 → 可选验证 |
| 推后回读验证 | `verify_draft(title=..., media_id=...)` | 拉服务端草稿核对 |

## 二、安装与凭证

```bash
pip install requests
# 仅当使用 Fernet 加密凭证文件时才需要：
pip install cryptography
```

### 凭证（两种方式，环境变量优先）

**方式一：环境变量**

```bash
export WX_MP_APP_ID=你的appid
export WX_MP_APP_SECRET=你的appsecret
```

Windows:

```cmd
set WX_MP_APP_ID=你的appid
set WX_MP_APP_SECRET=你的appsecret
```

**方式二：凭证文件（JSON）**

```bash
export WX_MP_CREDS_FILE=/path/to/wechat_mp.json
```

文件内容：

```json
{"app_id": "你的appid", "app_secret": "你的appsecret"}
```

未设置 `WX_MP_CREDS_FILE` 时，默认读取当前目录下的 `wechat_mp.json`。

**可选：加密凭证文件**
若不想存明文，把上面的 JSON 用 Fernet 加密后写入同一文件，并在同目录放置 `.fernet_key`。
脚本会依次尝试「明文 JSON → Fernet 密文」，只有密文分支才导入 `cryptography`。

> ⚠️ 公众号后台需要把调用出口 IP 加入 IP 白名单，否则所有接口返回 `errcode 40164`。

## 三、快速开始

```python
from publisher import markdown_to_wechat_html, create_draft, upload_cover

md = """
> [!point] 一句话结论

正文段落，**蓝色强调**，以及 ==红色强调==。

### 小节标题

> [!warn] 注意事项
"""

html = markdown_to_wechat_html(md, theme="hot_media")
cover_id = upload_cover("cover.png")
media_id = create_draft("文章标题", html, cover_media_id=cover_id)
print("草稿 media_id:", media_id)
```

一键流程（渲染 + 传图 + 建草稿 + 回读验证）：

```python
import publisher

result = publisher.publish_article(
    md_text=open("article.md", encoding="utf-8").read(),
    title="文章标题",
    author="作者名",
    cover_path="cover.png",
    theme="decision_pick",
    publish=False,          # 只进草稿箱
)
print(result)
```

## 四、排版标记语法（单源真理）

渲染器 `markdown_to_wechat_html()` 识别的标记。**一律英文半角**：

| 标记 | 渲染效果 | 何时用 |
|:--|:--|:--|
| `> [!lead] 文字` | 17px 蓝底高亮引言块（左蓝边） | 开篇编者按，点破全文核心 |
| `> [!note] 文字` | 浅蓝底蓝左边框信息卡 | 有出处的数据/事实 |
| `> [!point] 文字` | 浅黄底黄边框要点卡 | 一句话记住 / 核心结论 |
| `> [!tip] 文字` | 浅绿底绿左边框建议卡 | 建议/行动项 |
| `> [!warn] 文字` | 浅橙底橙左边框风险卡 | 风险/注意事项 |
| `> [!ok] 文字` / `> [!no] 文字` | 绿卡 / 红卡 | 成对「能做到/做不到」对照 |
| `> [!gartner] 文字` | 浅蓝底蓝左边框 | 权威引述 |
| `### 标题` | 蓝色标题 + 左侧蓝边框 | 章节小标题 |
| `**关键词**` | 蓝色加粗 | 主强调，可较多 |
| `==关键词==` | 红色加粗 | 强强调，每篇 1~3 处 |
| `> 一句话`（不以 `[!]` 开头） | 虚线灰字斜体引用 | 收尾金句 |
| `关于本文资料来源：...`（普通段落） | 14px 浅灰不加粗 footer | 文末出处边界 |
| `---` | 细分隔线 | 大块之间分隔 |
| `- 项` / `1. 项` | 蓝色圆点列表 | 清单内容 |
| 表格 `\| a \| b \|` | 富表格 | 仅多维对齐比较时用 |

**语法要点**

- 彩色卡片必须以 `> [!类型] 内容` 开头（也兼容无 `>` 的 `[!类型]` 行首写法）
- `**` / `==` 必须成对闭合，不得残留字面星号/等号
- 中文一律原文，不做 Unicode 转义
- 写完自查：无残留 `**` / `==` / `[!` 字面量

## 五、风格库（12 套主题）

完整说明见 `STYLE_LIBRARY.md`。主题键：

| 键 | 名称 | 适合 |
|:--|:--|:--|
| `default` | 默认编辑风 | 通用 |
| `minimal_tech` | 极简科技 | 趋势观察 / 深度分析 |
| `hot_media` | 热点媒体 | 今日关注 / 热点答疑 |
| `decision_pick` | 决策选型 | 横评 / 平台选择 |
| `deep_explain` | 深度科普 | 原理解释 / 概念澄清 |
| `pitfall_list` | 避坑清单 | 风险提醒 / 复盘 |
| `howto` | 实操教程 | 上手指南 / 操作步骤 |
| `clarification` | 争议澄清 | 真假辨析 |
| `report_longform` | 长文报告 | 年度总结 / 行业报告 |
| `qa_service` | 答疑服务 | 公众咨询 / 问答 |
| `practical` | 实用小技（暖橙配色） | 小技巧 / 工具用法 |
| `xiuxian` | 现代修仙（墨金配色） | 玄幻/故事类内容 |

主题决定：字号/行距/段距、表格样式、footer 样式，以及**全局配色**（`practical` 与 `xiuxian` 会切换整套 palette）。

## 六、色块使用纪律

- 一屏里尽量不超过 **1 个强色块 + 1 个弱提示块**
- 同一篇不要高频堆 lead / point / ok / no / tip / note / warn 全家桶
- 正文以层级为主，色块只是插入点
- 推荐配比：`lead` ×1 + `note`/`point`/`warn` 各 ×1 + 成对 `ok/no` + 红色 `==强调==` 1~3 处 + 结尾虚线金句 + 灰 footer

## 七、必踩的坑（实测）

### 1. 正文图片用本地路径 = 图不显示

`markdown_to_wechat_html` 会把 md 里的图片路径原样写入 `<img src="...">`。
**如果写本地磁盘路径，微信会剥掉该 `src`，草稿里留下空 `<img>`，而且 API 不报错。**

正确做法：

```python
url = publisher.upload_image(local_png)        # → mmbiz.qpic.cn
url = url.replace("http://", "https://", 1)    # 必须 https
md = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
            lambda m: f"![{m.group(1)}]({url_of[m.group(2)]})", md)
```

**回读判据（唯一可信）**：数草稿 HTML 里带 `src`/`data-src` 的 `<img>` 占全部 `<img>` 的比例，必须 100% 且 url 以 `https://mmbiz` 开头。

```python
imgs = re.findall(r'<img[^>]*>', html)
good = sum(1 for t in imgs if re.search(r'(?:data-src|src)="https://mmbiz', t))
assert good == len(imgs) > 0
```

> 只数 `<img>` 标签个数是假阳性——空标签也计数，必须验 url。

### 2. `thumb_media_id` 为空 → `draft/update` 报 40007

看起来像「草稿不存在」，实际是封面缺失。先 `upload_cover` 补上再 update。

### 3. 封面必须用永久素材

`media/upload` 只返回临时 `media_id`，**不能用作封面**；必须 `material/add_material?type=image`。

### 4. 中文编码

`requests` 提交中文 JSON 时用 `json.dumps(..., ensure_ascii=False).encode("utf-8")` + `data=`，
否则后台存成 `\uXXXX` 乱码。

### 5. 富文本格式限制

- 微信渲染对 `<ul>/<ol>/<li>` 的换行缩进处理很差 → 渲染器已改用自定义列表样式
- `h3` 必须显式 `font-weight:700`，否则被微信重置
- 冒号放在 `<strong>` 内部，避免断行

### 6. IP 白名单

公众号后台只支持单个 IP，不支持 IP 段。动态出口 IP 每次都会变 →
报 `errcode 40164`，需人工去后台把当前出口 IP 加白名单（**无 API 可改**）。

## 八、页面自检（改渲染器必跑）

```bash
python -E tests/renderer_smoke.py
```

判据：**13 项 ALL PASS**。重点看两类互扰：

1. 卡片不能被 `>` 引用分支吞掉（`1px dashed` 泄漏必须为 0）
2. 普通 `> 金句` 不能被误判成卡片（必须保留虚线样式）

```bash
python -E tests/creds_selftest.py
```

判据：凭证四条路径全 PASS（无凭证报错 / 明文 JSON / env 优先 / 懒加载 cryptography）。

**样式类 bug 只有回读服务端 HTML 才看得见**——本地渲染全 PASS 不代表服务端样式正确。
典型事故：`> [!point]` 卡片被静默降级成虚线引用，本地自查全绿、服务端样式全丢。
根因是 `strip()` 与原始行两种判断混用。

## 九、推后回读验证

推完必须从 API 拉真实草稿核对，不能只看本地渲染：

```python
publisher.verify_draft(title="文章标题", media_id=media_id, min_plain_text_length=1200)
```

至少验证：标题、封面、作者、样式是否落地、有无残留字符、纯文字字数、footer 是否存在感低。

## 十、文件说明

```
wechat_publisher/
├── SKILL.md                 # 本文件
├── STYLE_LIBRARY.md         # 12 套风格详细说明
├── publisher.py             # 主引擎（渲染 + API）
├── __init__.py
├── tests/
│   ├── renderer_smoke.py    # 渲染器回归自检（13 项）
│   └── creds_selftest.py    # 凭证路径自检
└── scripts/
    └── smoke_test.py        # 导入冒烟
```

## 十一、许可

MIT。个人整理与实践沉淀，API 用法基于微信公众平台官方文档。

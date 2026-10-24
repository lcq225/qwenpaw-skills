"""
微信公众号文章发布技能 - 封装微信公众平台 API

能力：
  1. Markdown → 微信可读富排版 HTML（内联样式，卡片/强调/表格/footer）
  2. 图片上传（正文图 / 封面永久素材）
  3. 草稿创建（单篇 / 多图文打包）、草稿列表、发布、发布状态查询
  4. 推前自查（字数、残留标记、footer 规则）+ 推后回读验证

凭证获取（两种方式，环境变量优先，其次凭证文件）：
  方式一 环境变量：
      WX_MP_APP_ID / WX_MP_APP_SECRET
  方式二 凭证文件（JSON）：路径由 WX_MP_CREDS_FILE 指定，默认 ./wechat_mp.json
      内容：{"app_id": "...", "app_secret": "..."}
      也兼容 Fernet 加密文件：同目录放 .fernet_key，文件内容为密文即可。
"""

import json, os, time, requests
from pathlib import Path

TOKEN_CACHE = {}

# 默认凭证文件（可被 WX_MP_CREDS_FILE 覆盖）
DEFAULT_CREDS_FILE = Path("wechat_mp.json")


def _creds_file_path():
    p = os.environ.get("WX_MP_CREDS_FILE")
    return Path(p).expanduser() if p else DEFAULT_CREDS_FILE

DEFAULT_WORKFLOW = [
    "选题判断",
    "事实分层",
    "结构骨架",
    "正文写作",
    "排版套用",
    "自查复查",
    "推草稿箱",
]

STYLE_PRESETS = {
    "default": {"name": "默认编辑风", "paragraph": {"font_size": 15, "line_height": 1.8, "margin": "8px 0"}, "table_mode": "rich", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "minimal_tech": {"name": "极简科技", "paragraph": {"font_size": 15, "line_height": 1.9, "margin": "9px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "hot_media": {"name": "热点媒体", "paragraph": {"font_size": 15, "line_height": 1.85, "margin": "8px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "decision_pick": {"name": "决策选型", "paragraph": {"font_size": 15, "line_height": 1.82, "margin": "8px 0"}, "table_mode": "rich", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "deep_explain": {"name": "深度科普", "paragraph": {"font_size": 15, "line_height": 1.9, "margin": "9px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "pitfall_list": {"name": "避坑清单", "paragraph": {"font_size": 15, "line_height": 1.82, "margin": "8px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "howto": {"name": "实操教程", "paragraph": {"font_size": 15, "line_height": 1.8, "margin": "7px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "clarification": {"name": "争议澄清", "paragraph": {"font_size": 15, "line_height": 1.86, "margin": "8px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "report_longform": {"name": "长文报告", "paragraph": {"font_size": 15, "line_height": 1.92, "margin": "10px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "qa_service": {"name": "答疑服务", "paragraph": {"font_size": 15, "line_height": 1.84, "margin": "8px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "practical": {"name": "实用小技", "paragraph": {"font_size": 15, "line_height": 1.8, "margin": "8px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
    "xiuxian": {"name": "现代修仙", "paragraph": {"font_size": 15, "line_height": 1.9, "margin": "9px 0"}, "table_mode": "light", "footer": {"font_size": 14, "color": "#9aa3ad", "font_weight": 400}},
}


# 统一配色（控制色块密度，强调易读不疲劳）
_PALETTE = {
    "primary": "#1a4e8a",
    "primary_dark": "#1a4e8a",
    "lead_border": "#2f6bd8",
    "lead_bg": "#f0f6f8",
    "lead_color": "#2c3e50",
    "sub_blue": "#34495e",
    "sub_orange": "#e67e22",
    "text": "#333333",
    "muted": "#888888",
    "border": "#e5e5e5",
    "emph_red": "#c0392b",
    "gartner_bg": "#f2f7fc",
    "point_bg": "#fff7e6", "point_border": "#f2c94c", "point_strong": "#b8860b",
    "ok_bg": "#e8f5e9", "ok_color": "#2e7d32",
    "no_bg": "#fdecea", "no_color": "#c62828",
}

# 「实用小技」暖橙专属配色（第三栏目，与 AI 蓝/技术蓝灰形成差异；暖橙主强调 + 正文克制）
ORANGE_PALETTE = {
    "primary": "#d35400",
    "primary_dark": "#b34400",
    "lead_border": "#e67e22",
    "lead_bg": "#fff3e6",
    "lead_color": "#5c3d1a",
    "sub_blue": "#8a5a20",
    "sub_orange": "#e67e22",
    "text": "#333333",
    "muted": "#888888",
    "border": "#ecd9c2",
    "emph_red": "#c0392b",
    "gartner_bg": "#fff3e6",
    "point_bg": "#fff3e6", "point_border": "#e67e22", "point_strong": "#b35400",
    "ok_bg": "#e8f5e9", "ok_color": "#2e7d32",
    "no_bg": "#fdecea", "no_color": "#c62828",
}

# 「现代修仙」玄幻专属配色（古风水墨 x 墨金玄色；正文克制、主强调玄金/仙青，营造修仙气韵）
XIUXIAN_PALETTE = {
    "primary": "#8a5a1e",
    "primary_dark": "#6e4617",
    "lead_border": "#b8860b",
    "lead_bg": "#f7f1e4",
    "lead_color": "#3e3427",
    "sub_blue": "#3f5c54",
    "sub_orange": "#c78b2c",
    "text": "#333333",
    "muted": "#888888",
    "border": "#e2d7bd",
    "emph_red": "#9a3b2a",
    "gartner_bg": "#f0ece0",
    "point_bg": "#fdf6e3", "point_border": "#c9a84c", "point_strong": "#8a5a1e",
    "ok_bg": "#eef3e6", "ok_color": "#4d6b3a",
    "no_bg": "#fbeae4", "no_color": "#9a3b2a",
}

# 当前生效配色（默认科技蓝；渲染 practical 主题时切换到 ORANGE_PALETTE、xiuxian 主题时切换到 XIUXIAN_PALETTE）
ACTIVE_PALETTE = _PALETTE


def _set_active_palette(theme):
    global ACTIVE_PALETTE
    if theme == "practical":
        ACTIVE_PALETTE = ORANGE_PALETTE
    elif theme == "xiuxian":
        ACTIVE_PALETTE = XIUXIAN_PALETTE
    else:
        ACTIVE_PALETTE = _PALETTE





def _resolve_style_preset(theme):
    return STYLE_PRESETS.get(theme) or STYLE_PRESETS["default"]


def _normalize_article_text(md_text):
    text = md_text.replace("\r\n", "\n")
    text = text.replace(" / ", "/").replace(" /", "/").replace("/ ", "/")
    return text


def _extract_plain_text(md_text):
    import re
    text = md_text
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'!\[.*?\]\((.*?)\)', ' ', text)
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)
    text = re.sub(r'[#>*`\-_=|]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def inspect_article_package(md_text, title, theme="default"):
    preset = _resolve_style_preset(theme)
    normalized_md = _normalize_article_text(md_text)
    plain = _extract_plain_text(normalized_md)
    plain_length = len(plain)
    checks = {
        "title_not_empty": bool(title.strip()),
        "plain_text_ge_1200": plain_length >= 1200,
        "no_spaced_slash": " / " not in normalized_md,
        "no_markdown_strong_residue": "****" not in normalized_md,
        "footer_rule_declared": ("关于本文" in normalized_md) or ("资料来源" in normalized_md),
    }
    return {
        "workflow": DEFAULT_WORKFLOW,
        "theme": theme,
        "style_name": preset["name"],
        "plain_text_length": plain_length,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _post_json(url, payload):
    headers = {"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, data=data, headers=headers, timeout=30)
    resp.encoding = "utf-8"
    return resp.json()


def _post_form(url, files):
    resp = requests.post(url, files=files, timeout=30)
    return resp.json()


def _get_json(url, params=None):
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()


def _load_credentials():
    """读取公众号凭证：环境变量优先（WX_MP_APP_ID / WX_MP_APP_SECRET），
    其次凭证文件（WX_MP_CREDS_FILE，默认 ./wechat_mp.json）。
    凭证文件可为明文 JSON，也可以是 Fernet 密文（同目录需有 .fernet_key）。
    """
    app_id = os.environ.get("WX_MP_APP_ID")
    app_secret = os.environ.get("WX_MP_APP_SECRET")
    if app_id and app_secret:
        return {"app_id": app_id, "app_secret": app_secret}

    creds_file = _creds_file_path()
    if not creds_file.exists():
        raise FileNotFoundError(
            "未找到公众号凭证。请任选一种方式：\n"
            "  1) 设置环境变量 WX_MP_APP_ID / WX_MP_APP_SECRET\n"
            f"  2) 提供凭证文件并设置 WX_MP_CREDS_FILE（默认路径 {creds_file}）"
        )

    raw = creds_file.read_bytes()
    key_file = creds_file.parent / ".fernet_key"
    try:
        plain = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        # 不是明文 JSON，按 Fernet 密文处理
        from cryptography.fernet import Fernet, InvalidToken

        if not key_file.exists():
            raise ValueError(
                f"凭证文件 {creds_file} 不是明文 JSON，且缺少 Fernet 密钥 {key_file}"
            )
        fernet = Fernet(key_file.read_bytes())
        try:
            plain = json.loads(fernet.decrypt(raw).decode("utf-8"))
        except InvalidToken:
            raise ValueError(f"凭证文件 {creds_file} 解密失败：Fernet 密钥不匹配")

    app_id = plain.get("app_id") or (plain.get("wechat") or {}).get("app_id")
    app_secret = plain.get("app_secret") or (plain.get("wechat") or {}).get("app_secret")
    if not app_id or not app_secret:
        raise ValueError(f"凭证文件 {creds_file} 缺少 app_id / app_secret")
    return {"app_id": app_id, "app_secret": app_secret}


def _get_access_token(force_refresh=False):
    if not force_refresh and TOKEN_CACHE.get("access_token") and TOKEN_CACHE.get("expires_at", 0) > time.time():
        return TOKEN_CACHE["access_token"]
    creds = _load_credentials()
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": creds["app_id"], "secret": creds["app_secret"]}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if "access_token" in data:
        TOKEN_CACHE["access_token"] = data["access_token"]
        TOKEN_CACHE["expires_at"] = time.time() + data.get("expires_in", 7200) - 300
        return data["access_token"]
    raise Exception(f"获取AccessToken失败: {data}")


def upload_image(image_path):
    token = _get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    with open(image_path, 'rb') as f:
        files = {'media': (os.path.basename(image_path), f, 'image/png')}
        data = _post_form(url, files)
    if "url" in data:
        return data["url"]
    raise Exception(f"上传图片失败: {data}")


def upload_cover(image_path):
    token = _get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(image_path, 'rb') as f:
        files = {'media': (os.path.basename(image_path), f, 'image/png')}
        data = _post_form(url, files)
    if "media_id" in data:
        return data["media_id"]
    raise Exception(f"上传封面失败: {data}")


def _h_style(level):
    if level >= 4:
        return (f'font-size:16px;font-weight:700;color:{ACTIVE_PALETTE["sub_blue"]};'
                f'border-left:3px solid {ACTIVE_PALETTE["sub_orange"]};padding-left:8px;'
                f'margin:16px 0 6px 0;line-height:1.5;')
    return (f'font-size:{19 if level == 3 else 20}px;font-weight:700;color:{ACTIVE_PALETTE["primary"]};'
            f'border-left:4px solid {ACTIVE_PALETTE["primary"]};padding-left:10px;'
            f'margin:22px 0 10px 0;line-height:1.5;')


def _render_strong_anchor(text):
    import re
    text = re.sub(r'\*\*(.+?)\*\*：', r'<strong>\1：</strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return text


def _escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _inline_markdown(text):
    import re
    text = re.sub(r'`([^`]+)`', r'<code style="background:#f2f4f7;color:#c7254e;padding:2px 5px;border-radius:3px;font-family:Menlo,Consolas,monospace;font-size:14px;">\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*：', rf'<strong style="color:{ACTIVE_PALETTE["primary"]};">\1：</strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', rf'<strong style="color:{ACTIVE_PALETTE["primary"]};">\1</strong>', text)
    text = re.sub(r'==(.+?)==', rf'<strong style="color:{ACTIVE_PALETTE["emph_red"]};">\1</strong>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', rf'<a href="\2" style="color:{ACTIVE_PALETTE["primary"]};text-decoration:underline;">\1</a>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    return text


def _paragraph(text, style_preset=None):
    paragraph = (style_preset or STYLE_PRESETS["default"])["paragraph"]
    return (f'<p style="font-size:{paragraph["font_size"]}px;line-height:{paragraph["line_height"]};margin:{paragraph["margin"]};color:{ACTIVE_PALETTE["text"]};">{text}</p>')


def _render_table(header, rows, style_preset=None):
    table_mode = (style_preset or STYLE_PRESETS["default"]).get("table_mode", "rich")
    head_bg = '#1a4e8a' if table_mode == 'rich' else '#eef4fb'
    head_color = '#ffffff' if table_mode == 'rich' else ACTIVE_PALETTE["primary"]
    row_alt = '#f5f8fc' if table_mode == 'rich' else '#fafbfd'

    def cell_tag(text, tag, extra_style=""):
        base = 'padding:9px 12px;font-size:14px;line-height:1.6;vertical-align:middle;border:1px solid #dbe2ec;'
        return f'<{tag} style="word-break:break-all;{base}{extra_style}">{_inline_markdown(text)}</{tag}>'

    ths = ''.join(cell_tag(c, 'th', f'background:{head_bg};color:{head_color};font-weight:700;text-align:center;') for c in header)
    tds = ''
    for ri, row in enumerate(rows):
        bg = '#ffffff' if ri % 2 == 0 else row_alt
        cells = ''.join(cell_tag(c, 'td', (f'color:{ACTIVE_PALETTE["primary"]};font-weight:700;' if ci == 0 else f'color:{ACTIVE_PALETTE["text"]};') + f'background:{bg};') for ci, c in enumerate(row))
        tds += f'<tr>{cells}</tr>'
    return f'<table border="0" cellspacing="0" cellpadding="0" style="width:100%;margin:14px 0;border-collapse:collapse;max-width:677px;"><thead><tr>{ths}</tr></thead><tbody>{tds}</tbody></table>'


def _callout(title, body, kind):
    kind = kind or "quote"
    if kind == "lead":
        lead_text = body or title
        return (f'<p style="font-size:17px;line-height:1.9;margin:16px 0;padding:14px 18px 14px 22px;background:{ACTIVE_PALETTE["lead_bg"]};border-left:6px solid {ACTIVE_PALETTE["lead_border"]};color:{ACTIVE_PALETTE["lead_color"]};font-weight:600;border-radius:0 6px 6px 0">{lead_text}</p>')
    if kind == "gartner":
        return (f'<p style="font-size:15px;line-height:1.8;margin:14px 0;padding:12px 16px;background:{ACTIVE_PALETTE["gartner_bg"]};border-left:4px solid {ACTIVE_PALETTE["primary"]};color:#333"><strong style="color:{ACTIVE_PALETTE["primary"]};">{title}</strong> {body}</p>')
    if kind == "point":
        return (f'<p style="font-size:15px;line-height:1.8;margin:14px 0;padding:12px 16px;background:{ACTIVE_PALETTE["point_bg"]};border:1px solid {ACTIVE_PALETTE["point_border"]};border-radius:6px;color:#7a5a00"><strong style="color:{ACTIVE_PALETTE["point_strong"]};">{title}</strong> {body}</p>')
    if kind in ("ok", "no"):
        is_ok = kind == "ok"
        bg = ACTIVE_PALETTE["ok_bg"] if is_ok else ACTIVE_PALETTE["no_bg"]
        ac = ACTIVE_PALETTE["ok_color"] if is_ok else ACTIVE_PALETTE["no_color"]
        color = "#1b5e20" if is_ok else "#7a1f1f"
        return (f'<p style="font-size:15px;line-height:1.8;margin:4px 0;padding:10px 14px;background:{bg};border-left:4px solid {ac};color:{color}"><strong style="color:{ac};">{title}</strong> {body}</p>')
    if kind in ("tip", "note", "warn"):
        spec = {"tip": ("#e8f5e9", "#2e7d32", "#1b5e20"), "note": ("#eef4fb", "#2f6bd8", "#2c3e50"), "warn": ("#fff3e0", "#e67e22", "#7a4a00")}[kind]
        return (f'<p style="font-size:15px;line-height:1.8;margin:14px 0;padding:12px 16px;background:{spec[0]};border-left:4px solid {spec[1]};border-radius:0 6px 6px 0;color:{spec[2]}"><strong style="color:{spec[1]};">{title}</strong> {body}</p>')
    return f'<p style="font-size:15px;line-height:1.8;margin:16px 22px;padding:8px 14px;border-left:1px dashed #99a3b0;color:#5d6b7a;font-style:italic">{body}</p>'


def markdown_to_wechat_html(md_text, theme="default"):
    import re
    _set_active_palette(theme)
    md_text = _normalize_article_text(md_text)
    style_preset = _resolve_style_preset(theme)
    lines = md_text.split('\n')
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if line.startswith('```'):
            code_lang = line[3:].strip()
            j = i + 1
            buf = []
            while j < n and not lines[j].startswith('```'):
                buf.append(lines[j])
                j += 1
            blocks.append(f'<pre style="background:#282c34;color:#abb2bf;padding:14px;border-radius:8px;overflow-x:auto;font-family:Menlo,Consolas,monospace;font-size:13px;line-height:1.7;margin:12px 0;"><code class="{_escape_html(code_lang)}">{_escape_html(chr(10).join(buf))}</code></pre>')
            i = j + 1
            continue
        if line.strip() in ('---', '***', '___'):
            blocks.append(f'<hr style="border:none;border-top:1px solid {ACTIVE_PALETTE["border"]};margin:18px 0;">')
            i += 1
            continue
        # 彩色卡片：支持两种写法 —— 规范 `> [!note] 内容` 与宽松 `[!note] 内容`（行首）
        # 2026-10-20 修复：以 `> [!x]` 开头的卡片必须在这里优先匹配，
        # 否则会被下方 line.startswith('>') 的普通引用分支吞掉、渲染成虚线斜体（样式丢失）。
        callout_match = re.match(r'^>\s*\[!(lead|gartner|point|ok|no|tip|note|warn)\]\s*(.*)', line.rstrip())
        if callout_match:
            blocks.append(_callout(_inline_markdown(callout_match.group(2)), '', callout_match.group(1)))
            i += 1
            continue
        callout_match = re.match(r'^\s*\[!(lead|gartner|point|ok|no|tip|note|warn)\]\s*(.*)', line.rstrip())
        if callout_match:
            kind = callout_match.group(1)
            head = callout_match.group(2)
            blocks.append(_callout(_inline_markdown(head), '', kind))
            i += 1
            continue
        if line.startswith('>'):
            quote_lines = []
            while i < n and lines[i].startswith('>'):
                quote_lines.append(lines[i][1:].strip())
                i += 1
            blocks.append(_callout('', _inline_markdown(' '.join(quote_lines)), 'quote'))
            continue
        if not line.strip():
            i += 1
            continue
        if re.match(r'^!\[.*?\]\(.*?\)$', line.strip()):
            alt = re.search(r'\[(.*?)\]', line).group(1)
            src = re.search(r'\((.*?)\)', line).group(1)
            blocks.append(f'<img src="{src}" alt="{alt}" style="max-width:100%;border-radius:6px;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,.08);">')
            i += 1
            continue
        if line.startswith('#### '):
            blocks.append(f'<h4 style="{_h_style(4)}">{_render_strong_anchor(line[5:])}</h4>')
            i += 1
            continue
        if line.startswith('### '):
            blocks.append(f'<h3 style="{_h_style(3)}">{_render_strong_anchor(line[4:])}</h3>')
            i += 1
            continue
        if line.startswith('## '):
            blocks.append(f'<h2 style="{_h_style(2)}">{_render_strong_anchor(line[3:])}</h2>')
            i += 1
            continue
        if line.startswith('# '):
            blocks.append(f'<h1 style="{_h_style(1)}">{_render_strong_anchor(line[2:])}</h1>')
            i += 1
            continue
        if line.strip().startswith('|') and i + 1 < n and re.match(r'^\s*\|[\s:|\-]+\|?\s*$', lines[i + 1].strip()):
            def split_row(txt):
                return [c.strip() for c in txt.strip().rstrip('|').lstrip('|').split('|')]
            header = split_row(line)
            j = i + 2
            rows = []
            while j < n and lines[j].strip().startswith('|') and not re.match(r'^\s*\|[\s:|\-]+\|?\s*$', lines[j].strip()):
                rows.append(split_row(lines[j]))
                j += 1
            blocks.append(_render_table(header, rows, style_preset=style_preset))
            i = j
            continue
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            items = []
            while i < n and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                items.append(lines[i].strip()[2:])
                i += 1
            body = ''.join(f'<p style="margin:4px 0;line-height:1.85;font-size:15px;color:{ACTIVE_PALETTE["text"]};"><span style="color:{ACTIVE_PALETTE["primary"]};font-weight:700;margin-right:6px;">&#9679;</span>{_inline_markdown(it)}</p>' for it in items)
            blocks.append(f'<section style="margin:8px 0;">{body}</section>')
            continue
        if re.match(r'^\d+[\.、]\s', line.strip()):
            items = []
            while i < n and re.match(r'^\d+[\.、]\s', lines[i].strip()):
                items.append(lines[i].strip())
                i += 1
            body = ''
            for idx, it in enumerate(items, 1):
                content = re.sub(r'^\d+[\.、]\s', '', it)
                body += f'<p style="margin:4px 0;line-height:1.85;font-size:15px;color:{ACTIVE_PALETTE["text"]};"><span style="color:{ACTIVE_PALETTE["primary"]};font-weight:700;margin-right:6px;">&#9679;</span><strong style="color:{ACTIVE_PALETTE["primary"]};margin-right:6px;">{idx}.</strong>{_inline_markdown(content)}</p>'
            blocks.append(f'<section style="margin:8px 0;">{body}</section>')
            continue
        stripped = line.strip()
        if stripped.startswith("关于本文") or stripped.startswith("资料来源"):
            footer = style_preset["footer"]
            blocks.append(f'<p style="font-size:{footer["font_size"]}px;line-height:1.75;margin:18px 0 6px 0;color:{footer["color"]};font-weight:{footer["font_weight"]};">{_inline_markdown(line)}</p>')
        else:
            blocks.append(_paragraph(_inline_markdown(line), style_preset=style_preset))
        i += 1

    html = '\n'.join(blocks)
    return (f'<section style="padding:6px 0;max-width:677px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;-webkit-font-smoothing:antialiased;">\n{html}\n</section>')


def make_digest(html_content, max_len=120):
    """从正文 HTML 派生一段纯文字摘要（≤ max_len 字），避免微信默认抓取正文开头。

    做法：去标签 → 去多余空白 → 优先取第一句完整话（。！？结尾），
    若过长则在 max_len 内按标点回退截断，末尾补「…」。
    """
    import re as _re
    text = _re.sub(r"<[^>]+>", "", html_content or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = _re.sub(r"\s+", "", text).strip()
    if not text:
        return ""
    # 先按句号切，取第一句（完整句优先）
    m = _re.match(r"^(.+?[。！？])", text)
    if m and len(m.group(1)) <= max_len:
        return m.group(1)
    # 否则在 max_len 内找最后一个标点截断
    window = text[:max_len]
    best = max((window.rfind(p) for p in "。！？；，、"), default=-1)
    if best >= max_len * 0.6:
        return window[:best + 1]
    return window + ("…" if len(text) > max_len else "")


def create_draft(title, html_content, cover_media_id=None, author="", source_url="", need_open_comment=True, only_fans_can_comment=False, digest=None):
    token = _get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    clean_title = title.replace('\u3010', '').replace('\u3011', '').replace('【', '').replace('】', '')
    article = {"title": clean_title, "content": html_content, "need_open_comment": 1 if need_open_comment else 0, "only_fans_can_comment": 1 if only_fans_can_comment else 0}
    # 摘要：显式传入优先，否则从正文自动派生（≤120 字），避免微信抓正文开头
    article["digest"] = (digest or make_digest(html_content))[:120]
    if cover_media_id:
        article["thumb_media_id"] = cover_media_id
    if author:
        article["author"] = author
    if source_url:
        article["content_source_url"] = source_url
    data = _post_json(url, {"articles": [article]})
    if "media_id" in data:
        return data["media_id"]
    raise Exception(f"创建草稿失败: {data}")


def create_bundled_draft(articles):
    """创建一条包含多篇图文的草稿（打包内多篇，最多 8 篇）。

    articles: list[dict]，每个元素含：
        title, html_content, cover_media_id=None, author="",
        source_url="", need_open_comment=True, only_fans_can_comment=False
    返回 draft media_id。
    """
    token = _get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload_articles = []
    for a in articles:
        clean_title = (a.get("title") or "").replace('\u3010', '').replace('\u3011', '').replace('【', '').replace('】', '')
        item = {
            "title": clean_title,
            "content": a.get("html_content", ""),
            "need_open_comment": 1 if a.get("need_open_comment", True) else 0,
            "only_fans_can_comment": 1 if a.get("only_fans_can_comment") else 0,
        }
        # 摘要：显式传入优先，否则自动派生（≤120 字）
        item["digest"] = (a.get("digest") or make_digest(a.get("html_content", "")))[:120]
        if a.get("cover_media_id"):
            item["thumb_media_id"] = a["cover_media_id"]
        if a.get("author"):
            item["author"] = a["author"]
        if a.get("source_url"):
            item["content_source_url"] = a["source_url"]
        payload_articles.append(item)
    data = _post_json(url, {"articles": payload_articles})
    if "media_id" in data:
        return data["media_id"]
    raise Exception(f"创建批量图文草稿失败: {data}")


def publish_draft(media_id):
    token = _get_access_token()
    data = _post_json(f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}", {"media_id": media_id})
    if "publish_id" in data:
        return data["publish_id"]
    raise Exception(f"发布草稿失败: {data}")


def get_publish_status(publish_id):
    token = _get_access_token()
    return _post_json(f"https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token={token}", {"publish_id": publish_id})


def get_draft_list(offset=0, count=20, no_content=False):
    token = _get_access_token()
    data = _post_json(f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}", {"offset": offset, "count": min(count, 20), "no_content": no_content})
    if "item" in data:
        return data["item"]
    raise Exception(f"获取草稿列表失败: {data}")


def verify_draft(title=None, media_id=None, min_plain_text_length=1200, count=20):
    drafts = get_draft_list(offset=0, count=count, no_content=False)
    matched = None
    for item in drafts:
        content = ((item.get("content") or {})
                   .get("news_item") or [{}])[0]
        draft_title = content.get("title", "")
        draft_media_id = item.get("media_id", "")
        if media_id and draft_media_id == media_id:
            matched = (item, content)
            break
        if title and draft_title == title:
            matched = (item, content)
            break
    if not matched:
        raise Exception(f"未在草稿箱中找到目标草稿: title={title} media_id={media_id}")
    item, content = matched
    plain = _extract_plain_text(content.get("content", ""))
    return {
        "ok": len(plain) >= min_plain_text_length,
        "media_id": item.get("media_id", ""),
        "title": content.get("title", ""),
        "author": content.get("author", ""),
        "plain_text_length": len(plain),
        "checks": {
            "title_match": (not title) or content.get("title", "") == title,
            "plain_text_ge_threshold": len(plain) >= min_plain_text_length,
            "author_present": bool(content.get("author", "")),
        }
    }


def publish_prestyled_html(html_content, title, author="", cover_path=None, min_plain_text_length=1200, need_open_comment=True, only_fans_can_comment=False, source_url="", publish=True):
    """直接推送已排版完成的 HTML 到草稿箱（跳过 Markdown 二次渲染）。

    适用场景：调用方已用自身模板产出最终公众号 HTML，
    只需复用本 skill 的封面上传、草稿创建与回读验证能力。
    """
    result = {"status": "ok"}
    try:
        import re
        # 取正文纯文本做字数自查
        plain = re.sub(r"<[^>]+>", "", html_content)
        plain = plain.replace("&nbsp;", " ").replace("&amp;", "&")
        plain = re.sub(r"\s+", " ", plain).strip()
        plain_length = len(plain)
        section_closed = html_content.strip().rstrip("</section>").count("<section") >= 1 and html_content.strip().endswith("</section>")
        checks = {
            "title_not_empty": bool(title.strip()),
            "plain_text_ge_threshold": plain_length >= min_plain_text_length,
            "html_section_closed": section_closed,
            "author_present": bool(author.strip()),
        }
        inspection = {
            "mode": "prestyled_html",
            "plain_text_length": plain_length,
            "checks": checks,
            "ok": all(checks.values()),
        }
        result["inspection"] = inspection
        if not inspection["ok"]:
            result["status"] = "error"
            result["error"] = f"预排版 HTML 自查未通过: {inspection['checks']}"
            return result

        cover_media_id = None
        if cover_path and os.path.exists(cover_path):
            cover_media_id = upload_cover(cover_path)
            result["cover_media_id"] = cover_media_id

        media_id = create_draft(title=title, html_content=html_content, cover_media_id=cover_media_id, author=author, source_url=source_url, need_open_comment=need_open_comment, only_fans_can_comment=only_fans_can_comment)
        result["media_id"] = media_id
        result["mode"] = "prestyled_html"
        result["draft_verification"] = verify_draft(title=title, media_id=media_id, min_plain_text_length=min_plain_text_length)
        if publish:
            publish_id = publish_draft(media_id)
            result["publish_id"] = publish_id
            result["message"] = f"文章《{title}》已发布成功！"
        else:
            result["message"] = f"文章《{title}》已保存为草稿"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result


def publish_article(md_text, title, author="", cover_path=None, theme="default", need_open_comment=True, only_fans_can_comment=False, source_url="", publish=True):
    result = {"status": "ok"}
    try:
        normalized_md = _normalize_article_text(md_text)
        inspection = inspect_article_package(normalized_md, title=title, theme=theme)
        result["inspection"] = inspection
        result["workflow"] = DEFAULT_WORKFLOW
        if not inspection["ok"]:
            result["status"] = "error"
            result["error"] = f"推送前自查未通过: {inspection['checks']}"
            return result
        cover_media_id = None
        if cover_path and os.path.exists(cover_path):
            cover_media_id = upload_cover(cover_path)
            result["cover_media_id"] = cover_media_id
        import re
        processed_md = normalized_md
        local_images = re.findall(r'!\[.*?\]\(([^)]+)\)', normalized_md)
        for img_path in local_images:
            if os.path.exists(img_path):
                try:
                    url = upload_image(img_path)
                    processed_md = processed_md.replace(f'({img_path})', f'({url})')
                except Exception as e:
                    print(f"  上传图片失败 {img_path}: {e}")
        html_content = markdown_to_wechat_html(processed_md, theme=theme)
        media_id = create_draft(title=title, html_content=html_content, cover_media_id=cover_media_id, author=author, source_url=source_url, need_open_comment=need_open_comment, only_fans_can_comment=only_fans_can_comment)
        result["media_id"] = media_id
        result["draft_verification"] = verify_draft(title=title, media_id=media_id, min_plain_text_length=1200)
        if publish:
            publish_id = publish_draft(media_id)
            result["publish_id"] = publish_id
            result["message"] = f"文章《{title}》已发布成功！"
        else:
            result["message"] = f"文章《{title}》已保存为草稿"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result


if __name__ == "__main__":
    try:
        token = _get_access_token()
        print(f"[OK] AccessToken: {token[:8]}...{token[-4:]}")
        drafts = get_draft_list(count=5)
        print(f"[OK] 草稿列表: {len(drafts)} 篇")
        for d in drafts[:3]:
            print(f"  - {d.get('title', '无标题')}")
    except Exception as e:
        print(f"[ERROR] {e}")

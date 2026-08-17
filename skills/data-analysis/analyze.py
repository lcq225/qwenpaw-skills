#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
analyze.py — 通用数据分析工具（data-analysis skill）

对任意数据源（本地文件 / 数据库 / 粘贴文本 / 剪贴板）做一通自动分析：
  1. 数据接入   loading     (CSV/Excel/TSV/SQL/粘贴/clipboard, 自动猜分隔符/编码/类型)
  2. 数据诊断   diagnose    (缺失/重复/唯一/异常值/质量问题)
  3. EDA        eda         (描述统计/分布/趋势/相关矩阵/Top 排行)
  4. 多维下钻   drilldown   (按一列或多列维度组合 groupby 聚合)
  5. 同环比     momyoy      (时间序列同比/环比, 自动识别日期列)
  6. 洞察报告   report      (Markdown + HTML(带图表) 输出)

零公司绑定、通用：任何用户传自己公司/部门/业务的数据即可用。
默认输出 Markdown + HTML。
"""
import sys
import io
import os
import re
import json
import argparse
import datetime as _dt
import traceback
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

_TS_COL_CACHE = {}


# ---------------------------------------------------------------- 路径工具
def _out_path(args):
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    return Path(os.getcwd()) / "analysis_report"


def _split_extension(out_root: Path, ext: str):
    """给输出路径加扩展名；若用户已带同名扩展名则不去重（直接追加）。"""
    return Path(str(out_root) + ext)


# ---------------------------------------------------------------- 1. 数据接入
def load_table(args):
    """返回 (df, meta)"""
    if args.sql:
        return _load_sql(args)
    if not sys.stdin.isatty() and args.data is None and not args.file and not args.sql:
        return _load_paste(sys.stdin.read()), {"source": "stdin"}
    if args.data:
        return _load_paste(args.data), {"source": "inline"}
    if args.clipboard:
        try:
            import subprocess

            if sys.platform.startswith("win"):
                out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                      "Get-Clipboard -Raw"], capture_output=True, text=True)
                text = out.stdout
            else:
                out = subprocess.run(["pbpaste"], capture_output=True, text=True)
                text = out.stdout
        except Exception as e:
            raise SystemExit(f"[-] 读取剪贴板失败: {e}")
        return _load_paste(text), {"source": "clipboard"}
    if args.file:
        return _load_file(args.file), {"source": Path(args.file).name}
    raise SystemExit("[-] 未指定数据源：请用 --file / --sql / --data / --clipboard 或 stdin")


def _load_file(fp):
    p = Path(fp)
    if not p.exists():
        raise SystemExit(f"[-] 文件不存在: {fp}")
    low_memory = False
    suffix = p.suffix.lower()
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb18030", "latin1"]
    try:
        if suffix in (".xlsx", ".xlsm"):
            return pd.read_excel(p)
        if suffix in (".xls",):
            return pd.read_excel(p, engine="xlrd") if False else pd.read_excel(p)
        if suffix == ".json":
            return pd.read_json(p)
        if suffix == ".parquet":
            return pd.read_parquet(p)
        if suffix == ".tsv":
            return pd.read_csv(p, sep="\t", encoding="utf-8-sig")
        # csv / txt / dat / log ...
        for enc in _try_encodings(p, encodings):
            try:
                df = pd.read_csv(p, encoding=enc, low_memory=low_memory)
                return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        # 回退: 尝试其他分隔符
        for enc in encodings:
            try:
                df = pd.read_csv(p, sep=None, engine="python", encoding=enc)
                return df
            except Exception:
                continue
        raise ValueError("无法解析文件")
    except Exception as e:
        raise SystemExit(f"[-] 读取 {fp} 失败: {e}")


def _try_encodings(p, encodings):
    raw = p.read_bytes()[:4000]
    for enc in encodings:
        try:
            raw.decode(enc)
            yield enc
            return
        except UnicodeDecodeError:
            continue
    yield "utf-8"


def _load_paste(text):
    if not text or not text.strip():
        raise SystemExit("[-] 粘贴文本为空")
    text = text.strip()
    try:
        return pd.read_csv(io.StringIO(text))
    except Exception:
        try:
            return pd.read_csv(io.StringIO(text), sep="\t")
        except Exception:
            try:
                return pd.read_csv(io.StringIO(text), sep=",", engine="python")
            except Exception as e:
                raise SystemExit(f"[-] 无法解析粘贴文本: {e}")


def _load_sql(args):
    if not args.dsn:
        # 尝试常见默认
        if args.sql.lstrip().lower().startswith("postgres"):
            args.dsn = "postgresql://"
        else:
            raise SystemExit("[-] --sql 需要配合 --dsn 数据库连接串")
    try:
        import sqlalchemy
    except ImportError:
        raise SystemExit("[-] 连数据库需 sqlalchemy：pip install sqlalchemy")
    # 按协议补驱动提示
    scheme = args.dsn.split(":", 1)[0].lower()
    need_map = {
        "postgresql": "psycopg2-binary",
        "mysql": "pymysql",
        "mssql": "pymssql",
        "sqlite": "",  # 内置
    }
    if scheme in need_map and need_map[scheme]:
        try:
            __import__({
                "postgresql": "psycopg2",
                "mysql": "pymysql",
                "mssql": "pymssql",
            }[scheme])
        except ImportError:
            raise SystemExit(
                f"[-] {scheme} 需要驱动 {need_map[scheme]}："
                f"pip install {need_map[scheme]}"
            )
    try:
        eng = sqlalchemy.create_engine(args.dsn)
        with eng.connect() as conn:
            df = pd.read_sql(args.sql, conn)
        return df, {"source": f"sql:{args.dsn.split(':', 1)[0]}"}
    except Exception as e:
        raise SystemExit(f"[-] SQL 查询失败: {e}")


# ---------------------------------------------------------------- 类型规整
def _coerce_types(df):
    """把"看起来是数值/日期"的 object 列转成正确类型，返回转换统计。"""
    changed = {}
    df = df.copy()
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            continue
        if pd.api.types.is_datetime64_any_dtype(s):
            continue
        non_null = s.dropna()
        if non_null.empty:
            continue
        # 布尔
        low = non_null.astype(str).str.strip().str.lower()
        if low.isin(["true", "false", "是", "否", "yes", "no", "0", "1"]).all():
            # 避免把 0/1 数值转 bool，仅在字符串真值时
            if low.isin(["true", "false", "是", "否", "yes", "no"]).any():
                df[col] = low.map({"true": True, "是": True, "yes": True,
                                   "false": False, "否": False, "no": False})
                changed[col] = "bool"
                continue
        # 数值（除去空串）
        cleaned = non_null.astype(str).str.replace(",", "").str.replace(" ", "")
        try:
            num = pd.to_numeric(cleaned, errors="coerce")
            if num.notna().sum() / max(len(num), 1) >= 0.8:
                # 检查原始是否混有非数值
                df[col] = pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")
                changed[col] = "numeric"
                continue
        except Exception:
            pass
        # 日期
        try:
            dt_ser = pd.to_datetime(non_null, errors="coerce")
            ratio = dt_ser.notna().sum() / max(len(non_null), 1)
            if ratio >= 0.8:
                df[col] = pd.to_datetime(s, errors="coerce")
                changed[col] = "datetime"
                continue
        except Exception:
            pass
    return df, changed


def _pick_date_col(df):
    """返回最像日期的那一列名；没有则 None（缓存避免重复探测）。"""
    cols = tuple(df.columns)
    if cols in _TS_COL_CACHE:
        return _TS_COL_CACHE[cols]
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            _TS_COL_CACHE[cols] = col
            return col
    best = None
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        non_null = df[col].dropna()
        if non_null.empty:
            continue
        try:
            ratio = pd.to_datetime(non_null, errors="coerce").notna().mean()
            if ratio >= 0.9:
                best = col
                break
        except Exception:
            pass
    _TS_COL_CACHE[cols] = best
    return best


# ---------------------------------------------------------------- 2. 数据诊断
def diagnose(df):
    total = len(df)
    rows = {
        "总行数": int(total),
        "总列数": int(df.shape[1]),
        "重复行": int(df.duplicated().sum()),
        "缺失单元格": int(df.isna().sum().sum()),
        "唯一行占比": f"{(1 - df.duplicated().sum()/total)*100:.1f}%" if total else "n/a",
    }
    col_quality = []
    for col in df.columns:
        na = int(df[col].isna().sum())
        nunique = int(df[col].nunique(dropna=True))
        col_quality.append({
            "列": str(col),
            "类型": str(df[col].dtype),
            "缺失": na,
            "缺失率%": round(na / total * 100, 1) if total else 0,
            "唯一值": nunique,
            "非空": int(total - na),
        })
    return rows, pd.DataFrame(col_quality)


def _detect_outliers(series):
    s = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    if len(s) < 4:
        return None
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return None
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (s < lo) | (s > hi)
    if mask.sum() == 0:
        return None
    return {
        "异常值数": int(mask.sum()),
        "异常率%": round(mask.sum() / len(s) * 100, 1),
        "下界": round(float(lo), 2),
        "上界": round(float(hi), 2),
    }


# ---------------------------------------------------------------- 3. EDA
def describe_numeric(df):
    nums = df.select_dtypes(include=[np.number])
    if nums.empty:
        return pd.DataFrame()
    d = nums.describe().T
    d["缺失率%"] = (nums.isna().mean() * 100).round(1)
    d = d.round(2)
    return d


def top_values(df, col, n=10):
    s = df[col].dropna()
    vc = s.value_counts().head(n)
    total = len(s)
    out = pd.DataFrame({"值": vc.index, "数量": vc.values,
                        "占比%": (vc.values / total * 100).round(1)} if total else {})
    return out


def correlation(df):
    nums = df.select_dtypes(include=[np.number])
    if nums.shape[1] < 2:
        return pd.DataFrame()
    try:
        return nums.corr(numeric_only=True).round(2)
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------- 4. 多维下钻
def drilldown(df, dims, measures=None, agg="sum"):
    dims = [d for d in dims if d in df.columns]
    if not dims:
        # 自动选: 用分类列（排除日期）
        date_col = _pick_date_col(df)
        cands = []
        for col in df.columns:
            if col and col == date_col:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                if 1 < df[col].nunique(dropna=True) <= 50:
                    cands.append(col)
        if not cands:
            return None, "未找到可下钻维度（需有低基数分类列）"
        dims = cands[:2]
    # 度量列
    nums = df.select_dtypes(include=[np.number]).columns.tolist()
    if measures is None:
        measures = nums
    if not measures:
        measures = [df.columns[0]]
    g = df.groupby(dims, dropna=False)[measures].agg(agg).reset_index()
    return g, None


def auto_drill_candidates(df, max_cols=4):
    """推荐多维下钻维度组合（低基数字段；两两组合，仅 1 个分类字段时用单维度）"""
    date_col = _pick_date_col(df)
    cat = []
    for col in df.columns:
        if col and col == date_col:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            if 1 < df[col].nunique(dropna=True) <= 30:
                cat.append(col)
    combos = []
    if len(cat) == 1:
        combos.append([cat[0]])
    else:
        for i in range(len(cat)):
            for j in range(i + 1, len(cat)):
                combos.append([cat[i], cat[j]])
    return combos[:max_cols]


# ---------------------------------------------------------------- 5. 同环比
def momyoy(df, date_col, value_col, period="M"):
    """
    period: Y 年 / M 月 / D 日 / Q 季。返回带同比(YoY)/环比(MoM)的汇总表。
    同比 = 本期 vs 去年同期；环比 = 本期 vs 上一期。
    """
    d = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(d[date_col]):
        d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    if d.empty:
        return None
    if not pd.api.types.is_numeric_dtype(d[value_col]):
        d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    key = {
        "Y": d[date_col].dt.year,
        "M": d[date_col].dt.to_period("M"),
        "Q": d[date_col].dt.to_period("Q"),
        "D": d[date_col].dt.date,
    }[period.upper()]
    g = d.groupby(key)[value_col].sum().reset_index()
    g = g.sort_values(g.columns[0])
    vals = g[value_col]
    g["环比(MoM)%"] = (vals.pct_change() * 100).round(2)
    # 同比（统一用字符串键比较）
    if period.upper() == "M":
        g["日期"] = g[g.columns[0]].apply(lambda x: str(x))
        g["年"] = g["日期"].str.split("-").str[0].astype("int")
        g["月"] = g["日期"].str.split("-").str[1].astype("int")
        key_str = g["日期"]
        prev_key = lambda k: f"{int(k.split('-')[0]) - 1}-{k.split('-')[1]}"
    elif period.upper() == "Q":
        key_str = g[g.columns[0]].apply(lambda x: str(x))
        def pkq(k):
            m = re.match(r"(\d{4})[Qq](\d)", k)
            return f"{int(m.group(1)) - 1}Q{m.group(2)}" if m else None
        prev_key = pkq
    elif period.upper() == "Y":
        key_str = g[g.columns[0]].astype(str)
        prev_key = lambda k: str(int(k) - 1)
    else:
        key_str = g[g.columns[0]].astype(str)
        prev_key = lambda k: None
    ref = {k: v for k, v in zip(key_str, vals)}
    yoy = []
    for k in key_str:
        pk = prev_key(k)
        yoy.append(ref.get(pk, np.nan))
    g["去年同期值"] = yoy
    g["同比(YoY)%"] = ((vals - pd.Series(yoy, index=g.index)) / pd.Series(yoy, index=g.index) * 100).round(2)
    return g


# ---------------------------------------------------------------- 图表 & 报告
def render_charts(df, num_cols, out_root):
    """生成常见的几张图，返回 (markdown 段落, 生成的图片文件名列表)"""
    assets = []
    md = []
    charts_dir = out_root.parent / f"{Path(str(out_root)).name}_assets"
    charts_dir.mkdir(parents=True, exist_ok=True)
    n = min(len(num_cols), 4)

    # 1) 数值分布直方图
    if n:
        try:
            fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 3.4))
            if n == 1:
                axes = [axes]
            for ax, c in zip(axes, num_cols[:n]):
                s = pd.to_numeric(df[c], errors="coerce").dropna()
                ax.hist(s, bins=30, color="#4C78A8", alpha=0.85)
                ax.set_title(str(c), fontsize=10)
                ax.tick_params(labelsize=8)
            fig.tight_layout()
            fn = f"distribution.png"
            fig.savefig(charts_dir / fn, dpi=110, bbox_inches="tight")
            plt.close(fig)
            assets.append(fn)
            rel = f"{charts_dir.name}/{fn}"
            md.append(f"### 数值分布\n![分布]({rel})\n")
        except Exception:
            pass

    return md, assets, charts_dir


# ---------------------------------------------------------------- 报告生成
def build_report(args, df, meta, df_wide=None):
    df, changed = _coerce_types(df)
    L = []
    L.append("# 数据分析报告\n")
    L.append(f"- **数据源**: {meta.get('source', '未知')}")
    L.append(f"- **生成时间**: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if args.title:
        L = [f"# {args.title}\n"] + L[1:]
    L.append("")

    # 概览
    L.append("## 1. 数据概览\n")
    rows, qual_df = diagnose(df)
    L.append("| 指标 | 值 |\n|---|---|")
    for k, v in rows.items():
        L.append(f"| {k} | {v} |")
    L.append("")
    if changed:
        conv = ", ".join(f"{k}→{v}" for k, v in changed.items())
        L.append(f"> 🔧 自动类型转换：{conv}\n")

    # 列质量
    L.append("### 列质量\n")
    L.append(qual_df.to_markdown(index=False))
    L.append("")

    # 描述统计
    L.append("## 2. 描述统计\n")
    desc = describe_numeric(df)
    if not desc.empty:
        L.append(desc.to_markdown())
    else:
        L.append("无数值列。")
    L.append("")

    # 异常
    L.append("### 异常值检测 (IQR 1.5×)\n")
    any_out = False
    for col in df.select_dtypes(include=[np.number]).columns:
        o = _detect_outliers(df[col])
        if o:
            any_out = True
            L.append(f"- **{col}**: {o['异常值数']} 个异常（{o['异常率%']}%），正常区间 [{o['下界']}, {o['上界']}]")
    if not any_out:
        L.append("未检出明显异常值。")
    L.append("")

    # 相关性
    L.append("## 3. 相关矩阵\n")
    corr = correlation(df)
    if not corr.empty:
        L.append(corr.to_markdown())
    else:
        L.append("数值列不足 2 列，跳过相关性。")
    L.append("")

    # 分类列 Top
    L.append("## 4. 关键字段分布 (Top)\n")
    date_col = _pick_date_col(df)
    for col in df.columns:
        if col and col == date_col:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique(dropna=True) <= 20:
            L.append(f"### {col}\n")
            L.append(top_values(df, col).to_markdown(index=False))
            L.append("")
    L.append("")

    # 图表
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    out_root = _out_path(args)
    md_charts, assets, charts_dir = render_charts(df, num_cols, out_root)
    if md_charts:
        L.append("## 5. 可视化\n")
        L.extend(md_charts)
        L.append("")

    # 多维下钻
    L.append("## 6. 多维下钻\n")
    combos = auto_drill_candidates(df)
    if combos:
        L.append("| 维度组合 | 说明 |\n|---|---|")
        for c in combos:
            g, err = drilldown(df, c)
            if err is None and g is not None:
                L.append(f"| {', '.join(c)} | {g.shape[0]} 个分组 |")
        L.append("\n> 完整明细见下钻附表 (`--drill '维度1,维度2'` 可自定义组合)。\n")
    else:
        L.append("无低基数字段，跳过下钻。")
    L.append("")

    # 同环比
    L.append("## 7. 同环比\n")
    date_col = _pick_date_col(df)
    if date_col:
        L.append(f"> 检测到日期列 **{date_col}**。")
        period = args.period.upper()
        # 找一个数值列做同环比
        vcols = df.select_dtypes(include=[np.number]).columns.tolist()
        vcol = args.value if args.value and args.value in df.columns else (vcols[0] if vcols else None)
        if vcol:
            L.append(f"> 度量列 **{vcol}**，周期 **{period}**。\n")
            m = momyoy(df, date_col, vcol, period)
            if m is not None:
                L.append(m.to_markdown(index=False))
            else:
                L.append("同环比计算失败（数据过少）。")
        else:
            L.append("无数值度量列，跳过同环比。")
    else:
        L.append("未检测到日期列。可用 `--period` 指定；或先确保数据含日期字段。")
    L.append("")

    # 简单洞察（固定规则，不依赖 LLM）
    L.append("## 8. 初步洞察与建议\n")
    insights = []
    if isinstance(rows, dict):
        if rows.get("缺失单元格", 0) > 0:
            insights.append(f"数据存在 {rows['缺失单元格']} 个缺失单元格（集中在列质量表），建议先清洗或说明缺失原因。")
        if rows.get("重复行", 0) > 0:
            insights.append(f"存在 {rows['重复行']} 行完全重复，建议去重后再做汇总。")
    # 趋势方向
    date_col2 = _pick_date_col(df)
    if date_col2 and vcols:
        try:
            d = df.copy()
            d[date_col2] = pd.to_datetime(d[date_col2], errors="coerce")
            d = d.dropna(subset=[date_col2]).sort_values(date_col2)
            v = pd.to_numeric(d[vcols[0]], errors="coerce")
            if len(v) >= 3:
                first, last = v.iloc[0], v.iloc[-1]
                if last > first:
                    insights.append(f"{vcols[0]} 呈上升趋势（{first:.2f} → {last:.2f}），可关注增长驱动因素。")
                elif last < first:
                    insights.append(f"{vcols[0]} 呈下降趋势（{first:.2f} → {last:.2f}），建议排查回落原因。")
                else:
                    insights.append(f"{vcols[0]} 整体平稳（{first:.2f}）。")
        except Exception:
            pass
    if not insights:
        insights.append("数据整体较干净。建议结合业务上下文做进一步归因。")
    L.extend(f"- {x}" for x in insights)
    L.append("")
    L.append("---\n*由 data-analysis skill 自动生成。*")

    md_text = "\n".join(L)
    out_root = _out_path(args)
    md_file = _split_extension(out_root, ".md")
    md_file.write_text(md_text, encoding="utf-8")

    # HTML
    html = _md_to_html(md_text, out_root)
    html_file = Path(str(out_root) + ".html")
    html_file.write_text(html, encoding="utf-8")
    return md_file, html_file, assets


def _md_to_html(md_text, out_root):
    """极简 Markdown→HTML（够用即可，不引入额外依赖）。"""
    import html as _h
    lines = []
    in_table = False
    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if in_table:
                lines.append("</table>")
                in_table = False
            lines.append("")
            continue
        if line.startswith("|"):
            if not in_table:
                lines.append("<table>")
                in_table = True
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            tag = "th" if in_table and line.strip("|").split("|")[0].strip().startswith(("列", "值", "指标")) else "td"
            lines.append("<tr>" + "".join(f"<{tag}>{_h.escape(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            lines.append("</table>")
            in_table = False
        if line.startswith("### "):
            lines.append(f"<h3>{_h.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            lines.append(f"<h2>{_h.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            lines.append(f"<h1>{_h.escape(line[2:])}</h1>")
        elif line.startswith("- "):
            lines.append(f"<li>{_h.escape(line[2:])}</li>")
        elif line.startswith("> "):
            lines.append(f"<blockquote>{_h.escape(line[2:])}</blockquote>")
        else:
            lines.append(f"<p>{_h.escape(line)}</p>")
    if in_table:
        lines.append("</table>")
    body = "\n".join(lines)
    title = re.search(r"<h1>(.*?)</h1>", body)
    title = title.group(1) if title else "数据分析报告"
    return f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>{_h.escape(title)}</title>
<style>body{{font-family:'Microsoft YaHei',sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#222;line-height:1.6}}
h1{{border-bottom:3px solid #4C78A8;padding-bottom:6px}}h2{{color:#4C78A8;margin-top:28px;border-left:4px solid #4C78A8;padding-left:8px}}
table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}}th,td{{border:1px solid #ddd;padding:6px 10px;text-align:left}}
th{{background:#4C78A8;color:#fff}}tr:nth-child(even){{background:#f6f8fb}}img{{max-width:100%}}
blockquote{{background:#f0f4f8;border-left:4px solid #4C78A8;margin:8px 0;padding:8px 12px;color:#555}}
li{{margin:4px 0}}</style></head><body>
{body}
</body></html>"""


def print_md(md_file):
    text = md_file.read_text(encoding="utf-8")
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


# ---------------------------------------------------------------- CLI
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="通用数据分析工具 (data-analysis)")
    src = p.add_argument_group("数据源 (四选一)")
    src.add_argument("--file", help="本地文件: CSV/Excel/TSV/JSON/Parquet")
    src.add_argument("--sql", help="SQL 查询语句")
    src.add_argument("--dsn", help="数据库连接串，如 postgresql://USER:PASSWORD@host/db, mysql+pymysql://...")
    src.add_argument("--data", help="直接粘贴的表格文本")
    src.add_argument("--clipboard", action="store_true", help="从剪贴板读表格")
    p.add_argument("--out", default="analysis_report", help="输出路径(无扩展名, 生成 md+html)")
    p.add_argument("--title", help="报告标题")
    p.add_argument("--drill", help="自定义下钻维度(逗号分隔)")
    p.add_argument("--period", choices=["Y", "Q", "M", "D"], default="M", help="同环比周期 Y年/Q季/M月/D日")
    p.add_argument("--value", help="同环比度量列(默认第一个数值列)")
    p.add_argument("--print", dest="print_report", action="store_true", help="同时打印报告到终端")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    df, meta = load_table(args)
    md_file, html_file, assets = build_report(args, df, meta)
    print(f"[+] Markdown: {md_file}")
    print(f"[+] HTML: {html_file}")
    if assets:
        print(f"[+] 图表: {Path(str(md_file)).parent / (Path(str(md_file)).stem + '_assets')}")
    if args.print_report:
        print_md(md_file)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"[-] 出错: {e}")
        traceback.print_exc()
        sys.exit(1)

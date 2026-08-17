---
name: data-analysis
description: "通用数据分析工具 — 对任意数据源(本地文件/数据库/粘贴文本/剪贴板)一条命令生成洞察报告。Use when the user needs to analyze a dataset: 分析数据、数据分析、出数据报告、看数据情况、统计、趋势、同环比、同比环比、多维下钻、数据洞察、Explore data, EDA, descriptive stats. Loads CSV/Excel/TSV/JSON/Parquet or SQL databases, diagnostics (missing/duplicates/outliers), EDA (distributions/correlation/top), multi-dimension drill-down, year-over-year & month-over-month, outputs Markdown + HTML with charts. 零公司绑定，任何用户可分析自己公司的数据."
---

# data-analysis — 通用数据分析

对**任意数据源**一条命令出洞察报告（诊断 → EDA → 下钻 → 同环比 → 洞察建议），默认输出 **Markdown + HTML（含图表）**。不绑定任何公司，任何用户传自己公司/部门/业务的数据即可用。

## When to Use

- 手头有一份数据（表格文件/数据库/粘贴内容），想要**自动化洞察**而不是手动算
- 查**缺失/重复/异常值**、看**分布/趋势/相关性**
- 要做**多维下钻**（按部门/区域/产品等维度组合汇总）
- 要看**同比/环比**（本期 vs 上一期/去年同期）
- 快速出一份**可视化分析报告**（Markdown + HTML）

## 用法

```bash
python analyze.py --file sales.csv [--out 报告名] [--title "标题"]
python analyze.py --sql "select * from orders" --dsn "postgresql://USER:PASSWORD@host/db"
python analyze.py --data "列1,列2\n值1,值2"          # 直接粘贴
python analyze.py --clipboard                            # 从剪贴板读
echo "a,b" | python analyze.py                          # stdin 管道
```

### 主要参数

| 参数 | 说明 |
|:--|:--|
| `--file` | 本地文件：CSV/Excel/TSV/JSON/Parquet（自动猜编码/类型）|
| `--sql` + `--dsn` | 连数据库查询（sqlalchemy；sqlite 内置，其他需装驱动）|
| `--data` | 直接粘贴的表格文本（逗号/空格/制表符分隔均可）|
| `--clipboard` | 从系统剪贴板读表格 |
| `--out` | 输出路径（无扩展名，自动生成 `.md` + `.html` + `_assets/` 图表）|
| `--title` | 报告标题 |
| `--drill '维度1,维度2'` | 自定义下钻维度（默认自动推荐分类维度组合）|
| `--period Y\|Q\|M\|D` | 同环比周期：年/季/月/日（默认月）|
| `--value` | 同环比度量列（默认第一个数值列）|
| `--print` | 同时把报告打印到终端 |

## 报告包含什么

1. **数据概览** — 行/列/重复/缺失/唯一占比 + 列质量（类型/缺失率/唯一值）+ 自动类型转换
2. **描述统计** — 均值/标准差/分位数 + 异常值检测（IQR 1.5×）
3. **相关矩阵** — 数值列两两相关
4. **关键字段分布** — 分类列 Top 排行
5. **可视化** — 数值分布直方图（SVG/PNG 图表，HTML 内嵌）
6. **多维下钻** — 自动推荐分类型维度组合，或多列交叉汇总
7. **同环比** — 自动识别日期列，计算同比(YoY)/环比(MoM)
8. **初步洞察与建议** — 数据质量 + 趋势方向 + 可执行提示

## 数据库支持

`--sql` + `--dsn` 走 sqlalchemy，连接串示例：

```bash
# SQLite（内置，无需驱动）
--dsn "sqlite:///data.db"

# PostgreSQL（需 psycopg2-binary）
--dsn "postgresql://USER:PASSWORD@host:5432/db"

# MySQL（需 pymysql）
--dsn "mysql+pymysql://USER:PASSWORD@host:3306/db"

# SQL Server（需 pymssql）
--dsn "mssql+pymssql://USER:PASSWORD@host:1433/db"
```

缺驱动时脚本会提示装哪个包。

## Python API

```python
import sys; sys.path.insert(0, r'<skills>/data-analysis')
from analyze import load_table, build_report, drilldown, momyoy

# 加载
df, meta = load_table(args)          # args = parse_args(["--file", "x.csv"])
# 下钻
g, err = drilldown(df, ["区域", "产品"])
# 同环比（自动识别日期列）
from analyze import _pick_date_col, _coerce_types
df, _ = _coerce_types(df)
m = momyoy(df, _pick_date_col(df), "销售额", "M")
```

## 依赖

`pandas` `numpy` `matplotlib` `tabulate` `sqlalchemy`（`--file` 基础可用前三者；`tabulate` 用于 Markdown 表格；`sqlalchemy` 仅连库时需要）。

```bash
pip install pandas numpy matplotlib tabulate sqlalchemy
# 国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pandas numpy matplotlib tabulate sqlalchemy
```

## Common Mistakes

- **日期列没被识别** → 同环比/趋势会缺失。把数据里的日期字段用 `YYYY-MM-DD` / `YYYY/MM/DD` / `YYYYMMDD` 等常见格式，脚本会自动 `to_datetime`。
- **无日期列时 `--period` 无效** → 同环比需先有一列可解析的日期。
- **数据库驱动缺失** → 看报错提示补装对应驱动（psycopg2-binary/pymysql/pymssql）。
- **数值列被当文本**（因为混入了 `,` 千分位或 `￥` 符号）→ 脚本尝试剥离 `,`；特殊符号可先清洗数据。

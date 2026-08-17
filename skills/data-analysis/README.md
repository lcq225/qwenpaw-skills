# data-analysis — 通用数据分析技能

对**任意数据源**一条命令生成洞察报告：诊断 → EDA → 多维下钻 → 同环比 → 洞察建议，输出 **Markdown + HTML（含图表）**。

零公司绑定、完全通用：任何用户传自己公司/部门/业务的数据（表格文件、数据库、粘贴文本、剪贴板）即可用。

## 特性

- 🔌 **多数据源**：CSV / Excel / TSV / JSON / Parquet / 数据库(SQL) / 粘贴文本 / 剪贴板 / stdin，自动猜编码与类型
- 🔍 **数据诊断**：缺失 / 重复 / 唯一占比 / 列质量 / 异常值(IQR 1.5×) / 自动类型转换
- 📊 **EDA**：描述统计 / 分布 / 相关矩阵 / 分类 Top 排行 / 可视化直方图
- 🧩 **多维下钻**：按多列维度组合交叉汇总（自动推荐或 `--drill` 自定义）
- 📈 **同环比**：自动识别日期列，计算同比(YoY) / 环比(MoM)，支持年/季/月/日周期
- 💡 **洞察建议**：数据质量 + 趋势方向 + 可执行提示
- 📄 **双格式输出**：Markdown + 带样式的 HTML（内嵌图表）

## 安装

```bash
pip install pandas numpy matplotlib tabulate sqlalchemy
# 国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pandas numpy matplotlib tabulate sqlalchemy
```

## 快速开始

```bash
# 本地 CSV
python analyze.py --file 2024销售.csv --out 销售分析 --title "2024销售分析"

# 连数据库
python analyze.py --sql "select 日期,部门,金额 from orders" \
    --dsn "postgresql://USER:PASSWORD@host:5432/db" --out 订单分析

# 直接粘贴表格
python analyze.py --data $'月份,销量\n1,100\n2,120'

# 从剪贴板
python analyze.py --clipboard

# 多维下钻 + 年度同环比
python analyze.py --file sales.csv --drill '区域,产品' --period Y
```

运行后在工作目录生成：`<out>.md`（报告）+ `<out>.html`（带样式，浏览器打开）+ `<out>_assets/`（图表）。

## 示例报告目录

1. 数据概览（行/列/重复/缺失/列质量）
2. 描述统计（均值/分位数 + 异常检测）
3. 相关矩阵
4. 关键字段分布（分类 Top）
5. 可视化（数值分布）
6. 多维下钻
7. 同环比（同比/环比）
8. 初步洞察与建议

## 数据库连接串示例

| 数据库 | --dsn | 驱动 |
|:--|:--|:--|
| SQLite | `sqlite:///data.db` | 内置 |
| PostgreSQL | `postgresql://USER:PASSWORD@host/db` | psycopg2-binary |
| MySQL | `mysql+pymysql://USER:PASSWORD@host/db` | pymysql |
| SQL Server | `mssql+pymssql://USER:PASSWORD@host/db` | pymssql |

缺驱动时脚本会提示装哪个包。

## Python API

```python
import sys; sys.path.insert(0, '/path/to/data-analysis')
from analyze import load_table, drilldown, momyoy, parse_args, _coerce_types, _pick_date_col

df, meta = load_table(parse_args(["--file", "x.csv"]))
df, _ = _coerce_types(df)
g, err = drilldown(df, ["区域", "产品"])            # 多维下钻
m = momyoy(df, _pick_date_col(df), "销售额", "M")    # 同环比
```

## 版本

v1.0.0 — 首个通用版本

## License

Apache-2.0

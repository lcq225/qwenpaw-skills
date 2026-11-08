---
name: evidence-ledger
description: Use when writing reports, plans, research, policy applications, due diligence, or business analysis that need traceable claims; when facts, sources, assumptions, and pending verification must be separated; or when the same metric/topic may have conflicting statements.
metadata:
  requires: {}
version: 0.1.0
---

# Evidence Ledger — 证据台账

将每条结论登记为「主张—证据—来源—状态」，让任何人能追问：**这句话依据是什么？**

## 何时使用

- 写报告、方案、经营分析、研究、申报材料前后
- 需要区分：**已核实 / 推断 / 待核定 / 未查询**
- 同一指标出现多个口径，需并置而非凭直觉选一个
- 需要导出「主张—证据—来源」附表供复核

**不做什么**：不联网检索、不替用户验证来源、不自动判定矛盾；只把证据链结构化，矛盾由人核对。

## 核心原则

1. **没有来源，不标「已核实」**。
2. **推断不是事实**：必须标「推断」，并保留推导依据。
3. **同主题不同主张先并置，不自动选边**。
4. **空白与未查询分开**：未查的事标「未查询」，不要写成「不存在」。

## 快速开始

```bash
# 登记一条已核实事实
python evidence.py add --topic "Q3产品毛利率" --claim "Q3毛利率18%" --evidence "财务报表第12页" --source "2026Q3财务报表" --status 已核实

# 登记一条待确认口径
python evidence.py add --topic "Q3产品毛利率" --claim "Q3毛利率22%" --evidence "业务初步测算" --source "业务部门台账" --status 待核定

# 列出主题、并置同主题不同主张、导出 Markdown 附表
python evidence.py list --topic "Q3产品毛利率"
python evidence.py conflicts
python evidence.py export --out evidence-appendix.md
```

默认在当前目录读写 `evidence.json`。可用 `--db path/to/evidence.json` 指定项目台账。

## 命令参考

| 命令 | 作用 |
|:---|:---|
| `add` | 登记主题、主张、证据、来源、状态、日期 |
| `list` | 按主题或状态列出台账 |
| `conflicts` | 并置同一主题下的不同主张，提示人工核对 |
| `export` | 导出 Markdown「主张—证据—来源—状态」附表 |

### 状态口径

| 状态 | 含义 |
|:---|:---|
| `已核实` | 有一手/权威来源，且已核对 |
| `推断` | 根据证据推导，未独立核实 |
| `待核定` | 有值或说法，但口径待确认 |
| `未查询` | 尚未查，不能写成「不存在」 |

## 验收标准

1. 任何导出表中的主张都有证据、来源、状态。
2. `conflicts` 不判谁对，只把同主题不同主张并置。
3. 写入后 JSON 可被 `json.load` 读取。
4. 仅使用 Python 标准库，无网络、无凭据、无外部依赖。

---
name: connector-kit
description: Use when building or using read-only connectors for document libraries, enterprise knowledge systems, Confluence, Jira, SharePoint, OA, or similar sources; when multiple sources need one list/search/fetch interface with explicit limits, pagination, credentials, and audit boundaries.
metadata:
  requires: {}
version: 0.1.0
---

# Connector Kit — 统一只读连接器底座

将不同数据源收敛为三个只读接口：`connector_list`、`connector_search`、`connector_fetch`。MVP 内置本地文档库适配器，作为未来企业系统适配器的安全参考。

## 安全边界（第一版写死）

- **只读**：没有 create/update/delete 接口。
- **一连接器一适配器**：不做万能 HTTP 请求器。
- **凭据不进源码或配置明文**：未来网络连接器只允许 `${ENV_VAR}` 或 secret store 引用。
- **限流与截断**：每个连接器设置搜索条数、内容字符数上限。
- **失败显式可见**：鉴权、限流、分页不完整必须返回错误，不静默空数据。
- **企业系统连接器需逐个授权**：本 MVP 不接企业系统。

## 三个统一接口

| 接口 | 作用 |
|:---|:---|
| `connector_list` | 列出已配置连接器及状态，不返回凭据 |
| `connector_search` | 统一搜索，返回标准化资源 ID、分数、长度 |
| `connector_fetch` | 按资源 ID 读取单个资源内容，受长度限制 |

## 内置适配器：local_docs

只读搜索用户指定目录中的 `.md`、`.txt` 文件。配置文件 `connectors.yaml` 使用 JSON 语法（也是合法 YAML），因此**不依赖 PyYAML**。

```bash
# 在技能目录准备 docs/，或修改 connectors.yaml 的 root
python connector_kit.py --config connectors.yaml list
python connector_kit.py --config connectors.yaml search local_docs --query "smart factory" --limit 10
python connector_kit.py --config connectors.yaml fetch local_docs path/to/file.md
```

## 未来扩展原则

新增 Confluence、Jira、SharePoint、飞书、OA 等适配器前，必须分别确认：

1. 来源系统、读取范围、负责人；
2. 凭据存储与授权范围；
3. 分页、限流、字段映射、脱敏规则；
4. 是否仅只读；
5. 日志记录什么、不记录什么。

不满足以上五项，不接入企业系统。

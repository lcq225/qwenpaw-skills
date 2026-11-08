---
name: skill-publish-auditor
description: Use when preparing a QwenPaw skill for GitHub, a skill marketplace, URL hosting, or any other public distribution; when checking whether a skill is original, attributable, licensed, privacy-safe, and correctly packaged before release.
metadata:
  requires: {}
version: 0.1.0
---

# Skill Publish Auditor — 技能公开发布前审计器

公开发布前，先回答：**是不是我方原创？许可是否完整？有没有敏感信息？安装包能不能被正确安装？**

## 何时使用

- 要把 skill 发布到 GitHub、Release、市场或任何公开 URL
- 要判断一个现有 skill 能否作为「我方贡献」发布
- 要检查 zip 是否扁平（`SKILL.md` 必须在根）
- 要避免把第三方 MIT 项目误包装为我方原创

**边界**：本工具只审计，不发布、不提交、不推送；发现风险只阻断并报告，不替人决定是否发布。

## 快速开始

```bash
# 审计技能目录：来源/许可/隐私/frontmatter/依赖
python audit.py --skill-path path/to/skill

# 审计待发布 zip：完整性 + SKILL.md 是否在根目录
python audit.py --zip releases/My-Skill-v1.0.0.zip
```

## 检查项

| 检查 | 阻断条件 |
|:---|:---|
| 来源与署名 | 检测到作者、版权、上游、GitHub 来源等信号，未确认原创或未保留署名/许可 |
| 许可 | 缺 LICENSE/COPYING 文件，需补齐或确认归属 |
| 公开敏感信息 | 本机路径、公司名、个人身份、凭据关键词、连接串 |
| Frontmatter | 缺 `name` / `description`，或 YAML 可能无效 |
| 依赖 | 列出非标准库 import，供 README/requirements 审阅 |
| Zip 结构 | `SKILL.md` 不在 zip 根目录，阻断安装包发布 |

## 审计结论口径

- `✅ PASS`：此项未发现问题
- `⚠️ WARN`：待补项，人工补齐后重审
- `🔴 BLOCK`：不得直接发布，先处理红色项

## 发布纪律

1. 审计通过≠授权发布。
2. Git commit、push、创建 Release、改公开 README 是**不同的外发动作**，须逐项授权。
3. 动手前说明什么会永久公开、能否撤回。
4. 关联打包与端到端安装流程：[[digest/procedure/skill-packaging-and-distribution.md]]。

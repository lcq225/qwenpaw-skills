# Skill Publish Auditor

A local, zero-dependency pre-publication auditor for QwenPaw skills.

It does not publish anything. It checks whether a skill is ready for human release review and surfaces risks before a file becomes public.

## Why

A skill can be privacy-clean yet still be unsuitable to publish as an original contribution. For example, it may be a third-party project with an attribution or license obligation. A release package can also look valid while failing installation because `SKILL.md` is nested inside a wrapper directory.

## Checks

- Provenance and attribution signals: author fields, copyright, upstream/source markers, GitHub links
- License file presence
- Public sensitive-information signals: local paths, company names, personal identifiers, credential words, connection strings
- `SKILL.md` frontmatter: `name` and `description`
- Non-standard-library Python imports
- Zip integrity and flat layout: `SKILL.md` must be at the archive root

## Requirements

- Python 3.8+
- No external Python packages

## Usage

```bash
# Audit a skill directory
python audit.py --skill-path path/to/skill

# Audit a release zip
python audit.py --zip releases/My-Skill-v1.0.0.zip
```

## Verdicts

| Verdict | Meaning |
|---|---|
| `可进入人工发布审阅` | The auditor found no blocking signal; human release approval is still required |
| `待补项` | Resolve warning items and review again |
| `阻断直接发布` | Resolve red items first; do not publish |

## Important boundary

Audit success is **not** authorization to commit, push, create a Release, or change public documentation. Those are separate external actions and require explicit approval.

## Platform compatibility

- **Windows:** runtime verified locally with Python 3.11.
- **Linux/macOS:** statically reviewed for Python 3.8+ compatibility: standard library only, LF line endings, UTF-8 I/O, and platform-neutral path APIs. Run the audit command on the target OS before production use.

## License

MIT. See [LICENSE](LICENSE).

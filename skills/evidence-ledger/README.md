# Evidence Ledger

A local, zero-dependency evidence ledger for AI-assisted reports, research, plans, due diligence, and business analysis.

It records every claim as **topic / claim / evidence / source / status**, so a reviewer can ask: **What is the basis for this sentence?**

## Why

Writing failures often happen when verified facts, inferences, pending confirmations, and unqueried questions are mixed together. Evidence Ledger keeps them separate and exports a traceable appendix.

## Features

- Four evidence states: `已核实` (verified), `推断` (inferred), `待核定` (pending), `未查询` (not queried)
- Local JSON storage; Python standard library only
- Lists records by topic or state
- Surfaces different claims under the same topic for human review; it does **not** choose a side
- Exports a Markdown claim–evidence–source appendix

## Requirements

- Python 3.8+
- No external Python packages

## Usage

```bash
# Add a verified claim
python evidence.py add --topic "Q3 product gross margin" --claim "Q3 gross margin was 18%" --evidence "Financial report, page 12" --source "2026 Q3 financial report" --status 已核实

# Add a pending claim under the same topic
python evidence.py add --topic "Q3 product gross margin" --claim "Q3 gross margin was 22%" --evidence "Preliminary business calculation" --source "Business unit workbook" --status 待核定

# List, review differing claims, and export an appendix
python evidence.py list --topic "Q3 product gross margin"
python evidence.py conflicts
python evidence.py export --out evidence-appendix.md
```

Use `--db path/to/evidence.json` to store the ledger in a project-specific location.

## Status semantics

| Status | Meaning |
|---|---|
| `已核实` | Backed by a primary or authoritative source and checked |
| `推断` | Derived from evidence but not independently verified |
| `待核定` | A value or statement exists but its definition needs confirmation |
| `未查询` | Not yet queried; do not turn this into a claim of absence |

## Platform compatibility

- **Windows:** runtime verified locally with Python 3.11.
- **Linux/macOS:** statically reviewed for Python 3.8+ compatibility: standard library only, LF line endings, UTF-8 I/O, and platform-neutral file APIs. Run the included commands on the target OS before production use.

## License

MIT. See [LICENSE](LICENSE).

# Connector Kit

A small, read-only connector foundation for QwenPaw skills and plugins.

It provides three consistent operations across data sources:

- `list`: show configured connectors without exposing credentials
- `search`: return bounded, normalized search results
- `fetch`: read one bounded resource by ID

The first built-in adapter is `local_docs`, a local Markdown/text document library. It is intentionally offline and credential-free, so it can serve as a safe reference adapter before connecting enterprise systems.

## Security model

- Read-only: no create, update, or delete operations
- One adapter per source: no generic HTTP request passthrough
- Future credentials must use environment-variable or secret-store references, never source code or plaintext config
- Bounded search result count and fetched content length
- Explicit errors; no silent empty result on authentication, pagination, or limit failures

## Requirements

- Python 3.8+
- No external Python packages

## Quick start

`connectors.yaml` uses JSON syntax, which is also valid YAML:

```json
{
  "connectors": {
    "local_docs": {
      "type": "local_docs",
      "enabled": true,
      "read_only": true,
      "root": "./docs",
      "extensions": [".md", ".txt"],
      "max_content_chars": 12000,
      "search_limit": 20
    }
  }
}
```

```bash
python connector_kit.py --config connectors.yaml list
python connector_kit.py --config connectors.yaml search local_docs --query "smart factory" --limit 10
python connector_kit.py --config connectors.yaml fetch local_docs path/to/file.md
```

## Adding an enterprise adapter

Before adding Confluence, Jira, SharePoint, Feishu, OA, or another enterprise source, explicitly define:

1. source system, read scope, and business owner;
2. credential storage and permission scope;
3. pagination, rate limits, field mapping, and redaction rules;
4. read-only boundary;
5. audit logging fields, excluding credential values.

Do not connect an enterprise system until all five are approved.

## Platform compatibility

- **Windows:** runtime verified locally with Python 3.11.
- **Linux/macOS:** statically reviewed for Python 3.8+ compatibility: standard library only, LF line endings, UTF-8 I/O, and `os.path` handling for file boundaries. Run local adapter tests on the target OS before production use.

## License

MIT. See [LICENSE](LICENSE).

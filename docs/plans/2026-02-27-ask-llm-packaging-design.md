# Design: Finalize `ask-llm` as Installable Python CLI Package

**Date:** 2026-02-27
**Status:** Approved

## Summary

Restructure the flat `ask_help/` script collection into a proper pip-installable Python package named `ask-llm`, with CLI entry points (`ask-gemini`, `ask-claude`, `ask-openai`, `ask-qwen`) and publish to a public GitHub repository at `pmdusso/ask-llm`.

## Naming

| Context | Value |
|---------|-------|
| PyPI package name | `ask-llm` |
| Python import | `ask_llm` |
| GitHub repo | `pmdusso/ask-llm` |
| CLI commands | `ask-gemini`, `ask-claude`, `ask-openai`, `ask-qwen` |

## Target Directory Structure

```
tool-ask-help/              (repo root)
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── .env.example
├── .gitignore
├── ask_llm/
│   ├── __init__.py
│   ├── _common.py
│   ├── ask_gemini.py
│   ├── ask_claude.py
│   ├── ask_openai.py
│   └── ask_qwen.py
└── tests/
    └── test_all.py
```

## Changes Required

### Rename: `ask_help` -> `ask_llm`

All internal references change from `ask_help` to `ask_llm`:
- Directory name
- `pyproject.toml` entry points and package config
- `__init__.py` module docstring
- `test_all.py` imports

### Move files to proper locations

- `pyproject.toml`, `README.md`, `CHANGELOG.md`, `requirements.txt` stay at repo root (already there once `ask_llm/` becomes a subdirectory)
- Python source files move into `ask_llm/` subdirectory
- `test_all.py` moves into `tests/`

### Update `pyproject.toml`

- Change `name = "ask-llm"`
- Entry points: `ask_llm.ask_gemini:main`, etc.
- `packages.find.where = ["."]`, `include = ["ask_llm*"]`
- `package-data` key: `ask_llm`

### Update `tests/test_all.py`

- Remove `sys.path.insert(0, ...)` hack
- Change imports from `ask_help.*` to `ask_llm.*`

### Update `README.md`

- Rename references from `ask_help` to `ask_llm`
- Add installation section (`pip install -e .`)
- Update CLI usage to show `ask-gemini` etc. as global commands

### New files

- `.env.example`: API key placeholders for all 4 providers
- `.gitignore`: Standard Python project ignores

### Source files (`_common.py`, `ask_*.py`)

- No code changes needed. Relative imports (`from ._common import ...`) work regardless of package name.

## GitHub Repository

- Public repo: `pmdusso/ask-llm`
- Initial commit with full restructured layout
- Push to `main`

## Verification Criteria

1. `pip install -e .` succeeds without errors
2. All 4 CLI commands respond: `ask-gemini "test"`, `ask-claude "test"`, `ask-openai "test"`, `ask-qwen "test"`
3. `python tests/test_all.py` passes 17/17

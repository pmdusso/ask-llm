# ask-llm Changelog

## [0.3.0] - 2026-02-27

### Changed
- Renamed package from `ask_help` to `ask_llm`.
- Restructured to standard Python package layout (`ask_llm/` subdirectory).
- Moved tests into `tests/` directory.

### Added
- `.env.example` with placeholder API keys.
- `.gitignore` for Python projects.
- `pip install -e .` editable install support.

## [0.2.0] - 2026-02-26

### Fixed
- `ask_gemini.py`: API key moved from URL query string to `x-goog-api-key` header (security).
- `ask_gemini.py`: Removed unused `Dict, Any` imports.
- `ask_gemini.py`: Fixed stale docstring and default model fallback (`gemini-3-pro-preview` → `gemini-2.5-pro-preview`).
- `ask_gemini.py`: Added `timeout=60` to HTTP request.
- `ask_claude.py`: Added `timeout=60` to HTTP request.
- `ask_openai.py`: Added `timeout=60` to HTTP request.
- `ask_qwen.py`: Added `logging` (consistent with other scripts); replaced bare `print` errors with `logger.error`.
- `ask_qwen.py`: `ask_qwen_text` — removed `**kwargs` (silently swallowed unknown args), set `enable_thinking=False` by default (thinking tokens were billed but never returned to caller), added `timeout=60`.
- `ask_qwen.py`: `ask_qwen` (streaming) — added `system_instruction` parameter; replaced `sys.exit(1)` with `return` so it is safe to import as a library; added `timeout=120`.

### Added
- `requirements.txt`: Explicit dependency manifest (`openai`, `requests`, `python-dotenv`).
- `README.md`: Setup instructions, CLI usage, import usage, and function signature reference.

## [2026-01-22]

### Added
- Created `ask_openai.py` for interacting with OpenAI API.
- Created `ask_claude.py` for interacting with Anthropic Claude API.
- Created `ask_gemini.py` (renamed from `ask_llm_feedback.py`) for interacting with Google Gemini API.
- Implemented environment variable configuration for model selection in `.env` (`OPENAI_MODEL`, `CLAUDE_MODEL`, `GEMINI_MODEL`).
- Added `python-dotenv` dependency to `requirements.txt`.

# ask-llm — LLM CLI Wrappers

A collection of lightweight Python wrappers for calling different LLM providers from the command line or from other scripts.

## Providers

| CLI Command | Provider | API Key env var | Model env var |
|---|---|---|---|
| `ask-gemini` | Google Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` |
| `ask-claude` | Anthropic Claude | `ANTHROPIC_API_KEY` | `CLAUDE_MODEL` |
| `ask-openai` | OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| `ask-qwen` | Alibaba Qwen (DashScope) | `DASHSCOPE_API_KEY` | — |

## Installation

```bash
pip install -e .
```

## Configuration

Copy the example env file and fill in your API keys:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

## CLI Usage

```bash
ask-gemini "Explain photosynthesis" --system "You are a biology teacher"
ask-claude "Explain photosynthesis" --temp 0.3
ask-openai "Explain photosynthesis" --model gpt-4o
ask-qwen "Explain photosynthesis"
```

All CLI commands accept `--system`, `--model`, and `--temp` flags (except `ask-qwen` which uses positional args).

## Import Usage

```python
from ask_llm.ask_gemini import ask_gemini
from ask_llm.ask_claude import ask_claude
from ask_llm.ask_openai import ask_openai
from ask_llm.ask_qwen import ask_qwen_text  # non-streaming, returns str | None

result = ask_gemini("Summarise this text", system_instruction="Be concise.")
result = ask_qwen_text("Summarise this text", enable_thinking=True)  # thinking off by default
```

### Shared function signature (Gemini, Claude, OpenAI)

```python
ask_<provider>(
    prompt: str,
    system_instruction: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096–8192,
    json_mode: bool = False,       # not available on Claude
) -> str | None
```

### Qwen — two functions

- **`ask_qwen_text(...)`** — non-streaming, returns `str | None`. Use in scripts. `enable_thinking` defaults to `False` to avoid billing thinking tokens that are never returned.
- **`ask_qwen(...)`** — streaming, prints to stdout. Use from CLI. `enable_thinking` defaults to `True` to show reasoning.

## Notes

- All wrappers return `None` on failure and log errors via the standard `logging` module.
- HTTP requests have a `timeout=60s` (120s for Qwen streaming).
- Gemini passes the API key as an `x-goog-api-key` header (not in the URL) for security.

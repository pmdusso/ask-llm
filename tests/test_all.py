#!/usr/bin/env python3
"""Quick smoke-test for all 4 LLM wrappers and their main options."""

import sys
import json as _json
from ask_llm.ask_gemini import ask_gemini
from ask_llm.ask_claude import ask_claude
from ask_llm.ask_openai import ask_openai
from ask_llm.ask_qwen import ask_qwen_text

PROMPT = "Reply with exactly one sentence: what is 2+2 and why?"
SYSTEM = "You are a concise assistant. Always reply in English."

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"

def run(label, fn, *args, assert_json: bool = False, **kwargs):
    try:
        result = fn(*args, **kwargs)
        ok = isinstance(result, str) and len(result) > 0
        if ok and assert_json:
            try:
                _json.loads(result)
            except _json.JSONDecodeError as e:
                ok = False
                print(f"{FAIL}  {label}\n       → JSON parse failed: {e}\n       Raw: {result[:120]}\n")
                return False
        status = PASS if ok else FAIL
        preview = result[:120].replace("\n", " ") if result else repr(result)
        print(f"{status}  {label}\n       → {preview}\n")
        return ok
    except Exception as e:
        print(f"{FAIL}  {label}\n       → Exception: {e}\n")
        return False

results = []

print("=" * 60)
print("GEMINI")
print("=" * 60)
results.append(run("basic prompt",              ask_gemini, PROMPT))
results.append(run("with system_instruction",   ask_gemini, PROMPT, system_instruction=SYSTEM))
results.append(run("json_mode=True",            ask_gemini, '{"question":"what is 2+2?"}', system_instruction="Reply in JSON with key 'answer'.", json_mode=True, assert_json=True))
results.append(run("low temperature (0.0)",     ask_gemini, PROMPT, temperature=0.0))
results.append(run("high temperature (1.0)",    ask_gemini, PROMPT, temperature=1.0))

print("=" * 60)
print("CLAUDE")
print("=" * 60)
results.append(run("basic prompt",              ask_claude, PROMPT))
results.append(run("with system_instruction",   ask_claude, PROMPT, system_instruction=SYSTEM))
results.append(run("json_mode=True",            ask_claude, '{"question":"what is 2+2?"}', system_instruction="Reply in JSON with key 'answer'.", json_mode=True, assert_json=True))
results.append(run("low temperature (0.0)",     ask_claude, PROMPT, temperature=0.0))

print("=" * 60)
print("OPENAI")
print("=" * 60)
results.append(run("basic prompt",              ask_openai, PROMPT))
results.append(run("with system_instruction",   ask_openai, PROMPT, system_instruction=SYSTEM))
results.append(run("json_mode=True",            ask_openai, '{"question":"what is 2+2?"}', system_instruction="Reply in JSON with key 'answer'.", json_mode=True, assert_json=True))
results.append(run("low temperature (0.0)",     ask_openai, PROMPT, temperature=0.0))

print("=" * 60)
print("QWEN (ask_qwen_text — non-streaming)")
print("=" * 60)
results.append(run("basic prompt",              ask_qwen_text, PROMPT))
results.append(run("with system_instruction",   ask_qwen_text, PROMPT, system_instruction=SYSTEM))
results.append(run("enable_thinking=True",      ask_qwen_text, PROMPT, enable_thinking=True))
results.append(run("low temperature (0.0)",     ask_qwen_text, PROMPT, temperature=0.0))

passed = sum(results)
total  = len(results)
print("=" * 60)
print(f"Results: {passed}/{total} passed")
print("=" * 60)
sys.exit(0 if passed == total else 1)

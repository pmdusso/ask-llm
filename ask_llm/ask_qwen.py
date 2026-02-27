#!/usr/bin/env python3
"""
Script to interact with Alibaba's Qwen LLM via DashScope API.

Usage:
    python ask_qwen.py "Your question here"
    python ask_qwen.py  # Interactive mode

Requires:
    - DASHSCOPE_API_KEY environment variable (or in .env file)
    - pip install openai python-dotenv
"""

import os
import sys
import time
import logging
from openai import OpenAI
from ._common import is_retryable_status

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


def ask_qwen_text(
    prompt: str,
    system_instruction: str | None = None,
    model: str = "qwen3-max-2026-01-23",
    temperature: float = 0.7,
    max_tokens: int = 8192,
    enable_thinking: bool = False,
) -> str | None:
    """Non-streaming wrapper that returns response text (for use in scripts)."""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("DASHSCOPE_API_KEY not found in environment variables.")
        return None

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        timeout=60,
    )

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    _MAX_RETRIES = 3
    _backoff = 2.0
    for _attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_body={"enable_thinking": enable_thinking},
            )
            if response.choices:
                return response.choices[0].message.content
            return None
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status and is_retryable_status(status) and _attempt < _MAX_RETRIES:
                logger.warning("Qwen HTTP %d — attempt %d/%d, retrying in %.1fs…",
                               status, _attempt, _MAX_RETRIES, _backoff)
                time.sleep(_backoff); _backoff *= 2; continue
            logger.error(f"Error calling Qwen: {e}")
            return None
    return None


def ask_qwen(
    prompt: str,
    system_instruction: str | None = None,
    model: str = "qwen3-max-2026-01-23",
    enable_thinking: bool = True,
) -> None:
    """
    Send a prompt to Qwen and stream the response to stdout.
    
    Args:
        prompt: The user's question or prompt
        system_instruction: Optional system context/persona
        model: The Qwen model to use
        enable_thinking: Whether to enable and display the thinking process
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("DASHSCOPE_API_KEY not found in environment variables.")
        return

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        timeout=120,
    )

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            extra_body={"enable_thinking": enable_thinking},
            stream=True
        )
    except Exception as e:
        logger.error(f"Error starting Qwen stream: {e}")
        return

    is_answering = False

    if enable_thinking:
        print("\n" + "=" * 20 + " Thinking process " + "=" * 20)

    try:
        for chunk in completion:
            delta = chunk.choices[0].delta

            # Handle thinking/reasoning content
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                if not is_answering and enable_thinking:
                    print(delta.reasoning_content, end="", flush=True)

            # Handle actual response content
            if hasattr(delta, "content") and delta.content:
                if not is_answering:
                    print("\n" + "=" * 20 + " Response " + "=" * 20)
                    is_answering = True
                print(delta.content, end="", flush=True)
    except Exception as e:
        logger.error(f"Error during Qwen stream: {e}")

    print("\n")  # Final newline


def main():
    if len(sys.argv) > 1:
        # Use command line argument as prompt
        prompt = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        print("Qwen Interactive Mode (Ctrl+C to exit)")
        print("-" * 40)
        try:
            prompt = input("Your question: ").strip()
            if not prompt:
                print("No prompt provided. Exiting.")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit(0)

    ask_qwen(prompt)


if __name__ == "__main__":
    main()


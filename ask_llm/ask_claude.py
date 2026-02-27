import os
import requests
import json
import logging
from typing import Optional
from ._common import is_retryable_status, validate_json_response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ask_claude(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    json_mode: bool = False
) -> Optional[str]:
    """
    Generic wrapper to call Anthropic's Claude LLM via REST API.
    
    Args:
        prompt (str): The user's input/query.
        system_instruction (str, optional): System context/persona.
        model (str, optional): Model name (e.g., "claude-4.5-sonnet"). 
                               Defaults to ANTHROPIC_MODEL env var or "claude-4.5-sonnet-20260215".
        temperature (float): Creativity control (0.0 to 1.0).
        max_tokens (int): Max output tokens.
        json_mode (bool): If True, requests JSON response (if supported by model/prompt).
        
    Returns:
        Optional[str]: The text response from the LLM, or None if call fails.
    """
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables.")
        return None

    # Using the specific ID provided by user
    target_model = model or os.getenv("CLAUDE_MODEL", "claude-opus-4-5-20251101") 
    
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Construct payload
    payload = {
        "model": target_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    if system_instruction:
        payload["system"] = system_instruction

    if json_mode:
        # Claude doesn't have a strict "json_mode" flag like OpenAI in the same way, 
        # but we can prompt for it or use tool use if needed. 
        # For text generation, we usually just ensure the prompt asks for JSON.
        pass

    _MAX_RETRIES = 3
    _backoff = 2.0
    for _attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if is_retryable_status(response.status_code) and _attempt < _MAX_RETRIES:
                logger.warning("Claude HTTP %d — attempt %d/%d, retrying in %.1fs…",
                               response.status_code, _attempt, _MAX_RETRIES, _backoff)
                import time; time.sleep(_backoff); _backoff *= 2; continue
            response.raise_for_status()

            data = response.json()

            try:
                content_blocks = data.get("content", [])
                if content_blocks:
                    text = content_blocks[0].get("text", "")
                    return validate_json_response(text, "Claude") if json_mode else text
                else:
                    logger.warning("No content blocks found in Claude response.")
                    return None
            except (KeyError, IndexError) as e:
                logger.error(f"Error parsing Claude response: {e}. Response: {data}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            if e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            if _attempt < _MAX_RETRIES and e.response is not None and is_retryable_status(e.response.status_code):
                import time; time.sleep(_backoff); _backoff *= 2; continue
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
    return None

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Ask Claude a question via command line.")
    parser.add_argument("prompt", type=str, help="The prompt to send to Claude.")
    parser.add_argument("--system", type=str, help="System instruction.", default=None)
    parser.add_argument("--model", type=str, help="Model to use.", default=None)
    parser.add_argument("--temp", type=float, help="Temperature.", default=0.7)
    parser.add_argument("--json", action="store_true", help="Request JSON response.", dest="json_mode")

    args = parser.parse_args()

    model_used = args.model or os.getenv("CLAUDE_MODEL", "claude-opus-4-5-20251101")
    print(f"Asking Claude ({model_used})...")
    response = ask_claude(
        prompt=args.prompt,
        system_instruction=args.system,
        model=args.model,
        temperature=args.temp,
        json_mode=args.json_mode
    )

    if response:
        print("\n--- Response ---\n")
        print(response)
        print("\n----------------\n")
    else:
        print("Failed to get response.")
        sys.exit(1)


if __name__ == "__main__":
    main()

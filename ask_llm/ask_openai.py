import os
import requests
import json
import logging
from typing import Optional
from ._common import is_retryable_status, validate_json_response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ask_openai(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    json_mode: bool = False
) -> Optional[str]:
    """
    Generic wrapper to call OpenAI's GPT LLM via REST API.
    
    Args:
        prompt (str): The user's input/query.
        system_instruction (str, optional): System context/persona.
        model (str, optional): Model name (e.g., "gpt-5.2"). 
                               Defaults to OPENAI_MODEL env var or "gpt-5.2".
        temperature (float): Creativity control (0.0 to 2.0).
        max_tokens (int): Max completion tokens.
        json_mode (bool): If True, requests JSON object response.
        
    Returns:
        Optional[str]: The text response from the LLM, or None if call fails.
    """
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables.")
        return None

    target_model = model or os.getenv("OPENAI_MODEL", "gpt-5.2-2025-12-11")
    
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    
    messages.append({"role": "user", "content": prompt})
    
    # Construct payload
    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
        # Ensure system prompt instructs JSON if json_mode is on, 
        # but usually user handles that in prompt/system.

    _MAX_RETRIES = 3
    _backoff = 2.0
    for _attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if is_retryable_status(response.status_code) and _attempt < _MAX_RETRIES:
                logger.warning("OpenAI HTTP %d — attempt %d/%d, retrying in %.1fs…",
                               response.status_code, _attempt, _MAX_RETRIES, _backoff)
                import time; time.sleep(_backoff); _backoff *= 2; continue
            response.raise_for_status()

            data = response.json()

            try:
                text = data["choices"][0]["message"]["content"]
                return validate_json_response(text, "OpenAI") if json_mode else text
            except (KeyError, IndexError) as e:
                logger.error(f"Error parsing OpenAI response: {e}. Response: {data}")
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

    parser = argparse.ArgumentParser(description="Ask OpenAI a question via command line.")
    parser.add_argument("prompt", type=str, help="The prompt to send to OpenAI.")
    parser.add_argument("--system", type=str, help="System instruction.", default=None)
    parser.add_argument("--model", type=str, help="Model to use.", default=None)
    parser.add_argument("--temp", type=float, help="Temperature.", default=0.7)
    parser.add_argument("--json", action="store_true", help="Request JSON response.", dest="json_mode")

    args = parser.parse_args()

    model_used = args.model or os.getenv("OPENAI_MODEL", "gpt-5.2-2025-12-11")
    print(f"Asking OpenAI ({model_used})...")
    response = ask_openai(
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

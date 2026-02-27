import os
import requests
import json
import logging
from typing import Optional
from ._common import is_retryable_status, validate_json_response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ask_gemini(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    json_mode: bool = False
) -> Optional[str]:
    """
    Generic wrapper to call Google's Gemini LLM via REST API.
    
    Args:
        prompt (str): The user's input/query.
        system_instruction (str, optional): System context/persona.
        model (str, optional): Model name (e.g., "gemini-2.5-pro-preview"). 
                               Defaults to GEMINI_MODEL env var or "gemini-2.5-pro-preview".
        temperature (float): Creativity control (0.0 to 1.0).
        max_tokens (int): Max output tokens.
        json_mode (bool): If True, requests JSON response (if supported by model).
        
    Returns:
        Optional[str]: The text response from the LLM, or None if call fails.
    """
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables.")
        return None

    target_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-pro-preview")
    
    # Ensure model name doesn't have 'models/' prefix for the URL construction if user provided it raw
    # But usually the API expects 'models/gemini-1.5-flash' or just 'gemini-1.5-flash'
    # The endpoint format is .../models/{model}:generateContent
    # If the user provides "gemini-1.5-flash", strictly it works. 
    
    if target_model.startswith("models/"):
        model_id = target_model.split("/")[-1]
    else:
        model_id = target_model

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    # Construct payload
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [
                {"text": system_instruction}
            ]
        }

    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    _MAX_RETRIES = 3
    _backoff = 2.0
    for _attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if is_retryable_status(response.status_code) and _attempt < _MAX_RETRIES:
                logger.warning("Gemini HTTP %d — attempt %d/%d, retrying in %.1fs…",
                               response.status_code, _attempt, _MAX_RETRIES, _backoff)
                import time; time.sleep(_backoff); _backoff *= 2; continue
            response.raise_for_status()

            data = response.json()

            # Extract text — candidates[0].content.parts[0].text
            try:
                candidate = data["candidates"][0]
                content_parts = candidate.get("content", {}).get("parts", [])
                if content_parts:
                    text = content_parts[0].get("text", "")
                    return validate_json_response(text, "Gemini") if json_mode else text
                else:
                    logger.warning("No content parts found in Gemini response.")
                    return None
            except (KeyError, IndexError) as e:
                logger.error(f"Error parsing Gemini response: {e}. Response: {data}")
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

    parser = argparse.ArgumentParser(description="Ask Gemini a question via command line.")
    parser.add_argument("prompt", type=str, help="The prompt to send to Gemini.")
    parser.add_argument("--system", type=str, help="System instruction.", default=None)
    parser.add_argument("--model", type=str, help="Model to use.", default=None)
    parser.add_argument("--temp", type=float, help="Temperature.", default=0.7)
    parser.add_argument("--json", action="store_true", help="Request JSON response.", dest="json_mode")

    args = parser.parse_args()

    model_used = args.model or os.getenv("GEMINI_MODEL", "gemini-2.5-pro-preview")
    print(f"Asking Gemini ({model_used})...")
    response = ask_gemini(
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

import os
import sys
from typing import Any

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
import dashscope

def test_dashscope_stream():
    api_key = settings.tongyi.dashscope_api_key
    if not api_key or "YOUR" in api_key:
        print("Please set DASHSCOPE_API_KEY")
        return

    dashscope.api_key = api_key
    model = settings.tongyi.tongyi_model_name

    prompt = "What is FastAPI?"
    
    print(f"Testing DashScope SDK with model: {model}")

    # Scenario 1: Minimal params
    print("\n--- Scenario 1: Minimal params ---")
    try:
        responses = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            stream=True,
            result_format="message"
        )
        for response in responses:
            pass # consume
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")

    # Scenario 2: With max_tokens
    print("\n--- Scenario 2: With max_tokens ---")
    try:
        responses = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            stream=True,
            result_format="message",
            max_tokens=100
        )
        for response in responses:
            pass
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")

    # Scenario 3: With output_tokens (deprecated/alias?)
    print("\n--- Scenario 3: With output_tokens ---")
    try:
        responses = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            stream=True,
            result_format="message",
            output_tokens=100
        )
        for response in responses:
            pass
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")

    # Scenario 4: Both max_tokens and output_tokens (Conflict?)
    print("\n--- Scenario 4: Both max_tokens and output_tokens ---")
    try:
        responses = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            stream=True,
            result_format="message",
            max_tokens=100,
            output_tokens=100
        )
        for response in responses:
            pass
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_dashscope_stream()

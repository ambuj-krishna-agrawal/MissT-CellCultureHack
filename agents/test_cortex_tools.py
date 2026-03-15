"""
Standalone test: Cortex REST API tool calling via OpenAI SDK.

Uses the snowhouse_sales_jwt connection from ~/.snowflake/connections.toml
and the OpenAI-compatible Chat Completions API at Snowflake's Cortex endpoint.
"""

import json
import configparser
import os
from openai import OpenAI


def load_connection(name: str = "snowhouse_sales_jwt") -> dict:
    """Load connection config from ~/.snowflake/connections.toml."""
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.snowflake/connections.toml"))
    if name not in config:
        raise ValueError(f"Connection '{name}' not found. Available: {list(config.sections())}")
    sec = config[name]
    return {
        "host": sec.get("host", "").strip('"'),
        "token": sec.get("token", "").strip('"'),
        "account": sec.get("account", "").strip('"'),
    }


def main():
    conn = load_connection("snowhouse_sales_jwt")
    host = conn["host"]
    token = conn["token"]

    base_url = f"https://{host}/api/v2/cortex/v1"
    print(f"Base URL: {base_url}")
    print(f"Token prefix: {token[:30]}...")

    client = OpenAI(
        api_key=token,
        base_url=base_url,
    )

    # Define a simple tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        }
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    messages = [
        {"role": "user", "content": "What is the weather like in San Francisco?"}
    ]

    model = "claude-sonnet-4-6"
    print(f"\n--- Test 1: Tool calling with model={model} ---")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )
        print(f"Response ID: {response.id}")
        print(f"Model: {response.model}")
        message = response.choices[0].message
        print(f"Role: {message.role}")
        print(f"Content: {message.content}")
        print(f"Tool calls: {message.tool_calls}")

        if message.tool_calls:
            tc = message.tool_calls[0]
            print(f"\n  Tool call ID: {tc.id}")
            print(f"  Function name: {tc.function.name}")
            print(f"  Arguments: {tc.function.arguments}")

            # Step 2: Send tool result back
            fake_result = json.dumps({"temperature": "65°F", "condition": "foggy"})
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": fake_result,
            })

            print("\n--- Test 2: Sending tool result back ---")
            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
            )
            final_msg = final_response.choices[0].message
            print(f"Final response: {final_msg.content}")
            print("\nSUCCESS: Full tool-calling round trip works!")
        else:
            print("\nWARNING: Model did not return tool calls. Response was text only.")

    except Exception as e:
        print(f"\nERROR with {model}: {e}")
        print(f"Type: {type(e).__name__}")

        # Fallback: try claude-3-5-sonnet
        fallback_model = "claude-3-5-sonnet"
        print(f"\n--- Fallback: Trying {fallback_model} ---")
        try:
            response = client.chat.completions.create(
                model=fallback_model,
                messages=[{"role": "user", "content": "What is the weather like in San Francisco?"}],
                tools=tools,
            )
            message = response.choices[0].message
            print(f"Tool calls: {message.tool_calls}")
            if message.tool_calls:
                print(f"SUCCESS with fallback model {fallback_model}!")
            else:
                print(f"No tool calls with {fallback_model} either.")
        except Exception as e2:
            print(f"ERROR with fallback: {e2}")


if __name__ == "__main__":
    main()

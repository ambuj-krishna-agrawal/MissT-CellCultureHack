"""Test script for robot streaming protocol execution.

Usage:
    python scripts/test_robot_stream.py [--url URL]

Calls /robot/init then streams the response from /protocol/2.
"""

import argparse
import json
import sys
import time

import requests

DEFAULT_URL = "http://localhost:5050"


def init_robot(session: requests.Session, base_url: str) -> bool:
    print("=" * 60)
    print("Step 1: POST /robot/init")
    print("=" * 60)
    try:
        resp = session.post(
            f"{base_url}/robot/init",
            headers={"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"},
            timeout=30,
        )
        data = resp.json()
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {json.dumps(data, indent=2)}")
        if resp.cookies:
            print(f"  Cookies: {dict(resp.cookies)}")

        if data.get("ok"):
            print("  ✓ Robot initialized successfully")
            return True
        else:
            print(f"  ✗ Init failed: {data.get('error', 'unknown')}")
            return False
    except Exception as e:
        print(f"  ✗ Request failed: {e}")
        return False


def run_protocol_stream(session: requests.Session, base_url: str) -> None:
    print()
    print("=" * 60)
    print("Step 2: POST /protocol/2 (streaming)")
    print("=" * 60)
    print()

    try:
        resp = session.post(
            f"{base_url}/protocol/2",
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "ngrok-skip-browser-warning": "true",
            },
            stream=True,
            timeout=300,
        )

        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type', '?')}")
        print(f"  Transfer-Encoding: {resp.headers.get('Transfer-Encoding', 'n/a')}")
        print()
        print("-" * 60)
        print("STREAMING OUTPUT:")
        print("-" * 60)

        content_type = resp.headers.get("Content-Type", "")
        step_count = 0
        start = time.time()

        if "text/event-stream" in content_type:
            for line in resp.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                line_str = line if isinstance(line, str) else line.decode("utf-8")

                if line_str.startswith("data:"):
                    payload = line_str[5:].strip()
                    if payload == "[DONE]":
                        print("\n[DONE]")
                        break
                    try:
                        event = json.loads(payload)
                        step_count += 1
                        print(f"\n  [{step_count}] {json.dumps(event, indent=4)}")
                    except json.JSONDecodeError:
                        print(f"  >> {payload}")
                elif line_str.strip():
                    print(f"  {line_str}")

        elif "application/json" in content_type:
            data = resp.json()
            print(f"  (non-streaming JSON response)")
            print(f"  {json.dumps(data, indent=2)}")

        else:
            for chunk in resp.iter_content(chunk_size=256, decode_unicode=True):
                if chunk:
                    chunk_str = chunk if isinstance(chunk, str) else chunk.decode("utf-8")
                    # Try to parse as JSON lines
                    for line in chunk_str.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                            step_count += 1
                            print(f"\n  [{step_count}] {json.dumps(event, indent=4)}")
                        except json.JSONDecodeError:
                            print(f"  {line}")

        elapsed = time.time() - start
        print()
        print("-" * 60)
        print(f"  Done. {step_count} events in {elapsed:.1f}s")
        print("-" * 60)

    except requests.exceptions.Timeout:
        print("  ✗ Request timed out (300s)")
    except requests.exceptions.ConnectionError as e:
        print(f"  ✗ Connection error: {e}")
    except KeyboardInterrupt:
        print("\n  Interrupted by user")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test robot streaming protocol")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL of the robot server")
    parser.add_argument("--skip-init", action="store_true", help="Skip robot init")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print(f"Target: {base_url}")
    print()

    session = requests.Session()

    if not args.skip_init:
        ok = init_robot(session, base_url)
        if not ok:
            print("\nRobot init failed. Use --skip-init to proceed anyway.")
            proceed = input("Continue to protocol/2 anyway? [y/N] ").strip().lower()
            if proceed != "y":
                sys.exit(1)

    run_protocol_stream(session, base_url)


if __name__ == "__main__":
    main()

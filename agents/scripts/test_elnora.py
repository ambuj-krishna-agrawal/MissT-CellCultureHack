#!/usr/bin/env python3
"""Test Elnora AI integration — mock or live.

Usage:
  python scripts/test_elnora.py              # mock mode (default)
  python scripts/test_elnora.py --live       # call real Elnora API
  python scripts/test_elnora.py --live -q "Your custom question here"

Saves the question + response to scripts/elnora_test_result.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_FILE = PROJECT_ROOT / "scripts" / "elnora_test_result.json"

DEFAULT_QUERY = (
    "Generate a complete iPSC maintenance, feeding, and passaging protocol "
    "for our automated robotic workcell. "
    "Cell line: iPSC-fast (16hr doubling time). "
    "Media: Media A. Dissociation reagent: TrypLE Express. "
    "Labware: T75 flask (75 cm2 surface area). "
    "Seeding density: 12,000 cells/cm2 (900K total cells). "
    "Feeding: full media change every 24 hours with 15mL Media A at room temperature. "
    "Passage threshold: 70% confluency. Harvest confluency: 80%. "
    "Handling: fast (firm shaking after 5-7min TrypLE incubation at 37C). "
    "Delivery: collect into 50mL Falcon tube. "
    "Re-seed: yes, seed new T75 at same density. "
    "Include step-by-step instructions for feeding cycle, confluency monitoring, "
    "TrypLE dissociation protocol, cell collection, and re-seeding. "
    "Note any critical warnings or timing constraints. "
    "IMPORTANT: Please provide your response in markdown format with proper headers, "
    "tables, numbered lists, and bold emphasis for key values."
)

DEFAULT_CONTEXT = (
    "Robot: UR12e with Robotiq gripper. "
    "Incubator: 37C, 5% CO2, humidified. "
    "Sterile work in BSC. "
    "Automated pipette station for liquid handling. "
    "Zebra camera for confluence imaging. "
    "iPSC colonies should be tightly packed with clean edges. "
    "Culture must not exceed 4 days in flask. "
    "Always image BEFORE feeding to check contamination and viability."
)


async def test_mock(query: str, context: str) -> dict:
    """Run consult_elnora in mock mode."""
    from agent.tools.elnora import _mock_consult

    print("[MOCK] Using cached real Elnora response...")
    start = time.time()
    result = _mock_consult()
    elapsed = round((time.time() - start) * 1000, 1)
    result["elapsed_ms"] = elapsed
    result["mode"] = "mock"
    return result


async def test_live(query: str, context: str) -> dict:
    """Run consult_elnora against real Elnora API."""
    from agent.tools.elnora import _live_consult, _find_elnora_bin

    binary = _find_elnora_bin()
    if not binary:
        print("[LIVE] ERROR: elnora CLI not found on PATH.")
        print("       Install with: pip install elnora")
        return {"source": "elnora", "status": "error", "error": "CLI not found", "mode": "live"}

    print(f"[LIVE] Elnora binary: {binary}")
    print(f"[LIVE] Sending query to Elnora API...")
    print(f"[LIVE] Query: {query[:80]}{'...' if len(query) > 80 else ''}")
    print(f"[LIVE] Waiting for AI response (polling up to 20s)...\n")

    start = time.time()
    result = await _live_consult(query, context)
    elapsed = round((time.time() - start) * 1000, 1)
    result["elapsed_ms"] = elapsed
    result["mode"] = "live"
    return result


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test Elnora AI integration")
    parser.add_argument("--live", action="store_true", help="Call real Elnora API (default: mock)")
    parser.add_argument("-q", "--query", type=str, default=DEFAULT_QUERY, help="Custom query")
    parser.add_argument("-c", "--context", type=str, default=DEFAULT_CONTEXT, help="Custom context")
    args = parser.parse_args()

    mode = "live" if args.live else "mock"
    print(f"═══ Elnora Test ({mode.upper()} mode) ═══\n")

    if mode == "live":
        result = await test_live(args.query, args.context)
    else:
        result = await test_mock(args.query, args.context)

    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mode": mode,
        "query": args.query,
        "context": args.context,
        "result": result,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    status = result.get("status", "unknown")
    elapsed = result.get("elapsed_ms", "?")

    print(f"Status:  {status}")
    print(f"Elapsed: {elapsed} ms")
    print(f"Source:  {result.get('source', '?')}")

    if result.get("task_id"):
        print(f"Task ID: {result['task_id']}")

    protocol = result.get("protocol_text", "")
    if protocol:
        print(f"\n{'─' * 60}")
        print("PROTOCOL RESPONSE:")
        print(f"{'─' * 60}")
        print(protocol[:2000])
        if len(protocol) > 2000:
            print(f"\n... ({len(protocol) - 2000} more chars)")
    elif result.get("error"):
        print(f"\nERROR: {result['error']}")

    print(f"\n{'─' * 60}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

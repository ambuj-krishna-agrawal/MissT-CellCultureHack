"""Fast e2e test: start server for each scenario, run it, verify completion."""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time

import websockets
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "agent_config.yaml")
WS_URL = "ws://localhost:8000/ws"
QUERY = "Set up and maintain iPSC-fast culture in T75"
TIMEOUT_S = 60
SCENARIOS = ["premature_harvest", "contamination", "slow_growth"]


def patch_config(scenario: str) -> None:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    cfg["tools"]["mock_scenario"] = scenario
    cfg["tools"]["mock_delay"] = 0
    cfg["llm"]["active_provider"] = "test"
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)


def kill_port(port: int) -> None:
    subprocess.run(f"lsof -ti :{port} | xargs kill -9 2>/dev/null", shell=True, capture_output=True)


def start_server() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "agent"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


async def wait_for_server(max_wait: float = 15.0) -> bool:
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            async with websockets.connect(WS_URL):
                return True
        except Exception:
            await asyncio.sleep(0.3)
    return False


async def run_scenario(scenario: str) -> dict:
    step_count = 0
    human_count = 0
    errors = []
    tools_seen = []
    start = time.time()

    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"action": "start", "query": QUERY}))

        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT_S)
                msg = json.loads(raw)
                evt = msg.get("type", "")

                if evt == "step_start":
                    step_count += 1
                    tool = msg.get("data", {}).get("tool_name", "?")
                    tools_seen.append(tool)

                elif evt == "human_input_requested":
                    human_count += 1
                    fields = msg.get("data", {}).get("input_fields", [])
                    resp = _auto_respond(fields)
                    await ws.send(json.dumps({"action": "human_response", "response": resp}))

                elif evt == "error":
                    errors.append(msg.get("data", {}).get("error", "?"))

                elif evt == "run_complete":
                    break

                elif evt == "run_error":
                    errors.append(msg.get("data", {}).get("error", "run_error"))
                    break

        except asyncio.TimeoutError:
            errors.append(f"timeout after {TIMEOUT_S}s at step {step_count}")

    return {
        "scenario": scenario,
        "steps": step_count,
        "human_prompts": human_count,
        "errors": errors,
        "elapsed_s": round(time.time() - start, 1),
        "last_tool": tools_seen[-1] if tools_seen else "none",
        "tools": tools_seen,
    }


def _auto_respond(fields: list[dict]) -> dict:
    response = {}
    for f in fields:
        fid = f.get("id", "")
        ftype = f.get("type", "text")
        if ftype == "confirm":
            response[fid] = True
        elif ftype == "select":
            opts = f.get("options", [])
            default = f.get("default")
            if default:
                response[fid] = default
            elif opts:
                response[fid] = opts[0].get("value", opts[0].get("id", ""))
        elif ftype == "number":
            response[fid] = f.get("default", 0)
        else:
            response[fid] = f.get("default", "")
    return response


async def test_one_scenario(scenario: str) -> dict:
    print(f"\n{'━'*60}")
    print(f"▶ SCENARIO: {scenario}")
    print(f"{'━'*60}")

    patch_config(scenario)
    kill_port(8000)
    await asyncio.sleep(0.5)

    proc = start_server()
    try:
        print("  Starting server...", end=" ", flush=True)
        ready = await wait_for_server()
        if not ready:
            return {"scenario": scenario, "steps": 0, "human_prompts": 0,
                    "errors": ["server failed to start"], "elapsed_s": 0,
                    "last_tool": "none", "tools": []}
        print("ready!")

        result = await run_scenario(scenario)

        ok = len(result["errors"]) == 0
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} — {result['steps']} steps, {result['human_prompts']} human, {result['elapsed_s']}s")
        if result["errors"]:
            for e in result["errors"]:
                print(f"    ERROR: {e}")

        tool_summary = result["tools"]
        for i in range(0, len(tool_summary), 10):
            chunk = tool_summary[i:i+10]
            prefix = "  Tools: " if i == 0 else "         "
            print(f"{prefix}{' → '.join(chunk)}")

        return result
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        kill_port(8000)


async def main():
    print(f"Testing {len(SCENARIOS)} scenarios sequentially (server restart per scenario)")
    print(f"mock_delay=0, provider=test (pure mock)\n")

    results = []
    for scenario in SCENARIOS:
        r = await test_one_scenario(scenario)
        results.append(r)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    all_ok = True
    for r in results:
        ok = len(r["errors"]) == 0
        if not ok:
            all_ok = False
        icon = "✅" if ok else "❌"
        print(f"  {icon} {r['scenario']:<22} {r['steps']:>3} steps  {r['human_prompts']} human  {r['elapsed_s']:>5.1f}s  last={r['last_tool']}")

    print()
    if all_ok:
        print("✅ ALL SCENARIOS PASSED")
    else:
        print("❌ SOME SCENARIOS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

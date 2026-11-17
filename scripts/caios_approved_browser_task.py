#!/usr/bin/env python3
"""CAIOS approved browser task: prepare once; execute immediately on consent.

Task plan comes from a previously authorized operation. This runner grants no
browser permissions, never selects an unapproved tab, and does not use tokens.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import queue
import re
import subprocess
import sys
import threading
import time


def emit(event: str, **details):
    print(json.dumps({"event": event, **details}, sort_keys=True), flush=True)


def read_plan(path: pathlib.Path):
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("contract_version") != "1":
        raise ValueError("Unsupported task plan version")
    for key in ("machine", "profile", "extension_id", "expected_title", "expected_url_prefix"):
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            raise ValueError(f"Missing {key}; never infer a browser target")
    for field in ("steps", "finally_steps"):
        steps = plan.get(field, [])
        if not isinstance(steps, list) or (field == "steps" and not steps):
            raise ValueError(f"{field} must be a nonempty list for primary steps")
        for step in steps:
            if not isinstance(step, dict) or not isinstance(step.get("name"), str):
                raise ValueError(f"{field} must contain named steps")
            if not isinstance(step.get("tool"), str) or not step["tool"].startswith("browser_"):
                raise ValueError(f"{field} step must name a browser tool")
            if not isinstance(step.get("arguments"), dict):
                raise ValueError(f"{field} step needs object arguments")
    return plan


class MCP:
    def __init__(self, argv, environment, stderr_path):
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        self.log = stderr_path.open("ab")
        self.proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
            env=environment, bufsize=0,
        )
        self.queue = queue.Queue()
        self.next_id = 0
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            for raw in self.proc.stdout:
                try:
                    self.queue.put(json.loads(raw))
                except ValueError:
                    continue
        finally:
            self.queue.put(None)

    def request(self, method, params, deadline_seconds, phase, status_interval):
        self.next_id += 1
        request_id = self.next_id
        self.proc.stdin.write((json.dumps({
            "jsonrpc": "2.0", "id": request_id, "method": method, "params": params,
        }) + "\n").encode("utf-8"))
        self.proc.stdin.flush()
        start = time.monotonic()
        next_status = start + status_interval
        deadline = start + deadline_seconds
        while True:
            now = time.monotonic()
            if now >= deadline:
                raise TimeoutError(f"{phase} timed out after {deadline_seconds}s; approval not confirmed")
            try:
                msg = self.queue.get(timeout=min(deadline - now, max(0.05, next_status - now)))
            except queue.Empty:
                if time.monotonic() >= next_status:
                    emit("WAITING", phase=phase, elapsed_seconds=round(time.monotonic() - start, 1))
                    next_status = time.monotonic() + status_interval
                continue
            if msg is None:
                raise RuntimeError(f"MCP exited during {phase}; consult task-local stderr")
            if msg.get("id") != request_id:
                continue
            if "error" in msg:
                raise RuntimeError(f"{phase} failed: {str(msg['error'])[:250]}")
            result = msg.get("result", {})
            if result.get("isError"):
                content = str(result.get("content", []))
                raise RuntimeError(f"{phase} returned error: {content[:240]}")
            return result

    def notify_initialized(self):
        self.proc.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        self.proc.stdin.flush()

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=4)
        for stream in (self.proc.stdin, self.proc.stdout):
            if stream and not stream.closed:
                stream.close()
        self.log.close()


def run(args):
    plan = read_plan(pathlib.Path(args.plan))
    actual_host = platform.node().split(".")[0].lower()
    if actual_host != plan["machine"].split(".")[0].lower():
        raise ValueError(f"Wrong machine: expected {plan['machine']}, actual {actual_host}")

    node = pathlib.Path(args.node)
    entry = pathlib.Path(args.mcp_entry)
    browser = pathlib.Path(args.browser_executable)
    for path in (node, entry, browser):
        if not path.is_file():
            raise FileNotFoundError(f"Required executable/source not found: {path}")

    environment = os.environ.copy()
    # Do not silently bypass the normal tab-by-tab Chrome consent UI.
    environment.pop("PLAYWRIGHT_MCP_EXTENSION_TOKEN", None)
    environment["CAIOS_PLAYWRIGHT_EXTENSION_ID"] = plan["extension_id"]
    command = [
        str(node), str(entry), "--extension",
        f"--profile-dir-name={plan['profile']}", "--no-tab-group",
        f"--executable-path={browser}",
    ]
    if args.user_data_dir:
        command.append(f"--user-data-dir={args.user_data_dir}")
    emit("PLAN_PREPARED", machine=plan["machine"], profile=plan["profile"],
         steps=len(plan["steps"]), approval_timeout_seconds=args.approval_timeout)
    client = None
    completed = False
    approved = False
    timings = []
    try:
        client = MCP(command, environment, pathlib.Path(args.stderr_log))
        client.request("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "CAIOS Approved Browser Task", "version": "1"},
        }, 30, "initialize", args.status_interval)
        client.notify_initialized()
        tool_list = client.request("tools/list", {}, 30, "tools-list", args.status_interval)
        available = {tool["name"] for tool in tool_list.get("tools", [])}
        required = {"browser_tabs"} | {step["tool"] for step in plan["steps"] + plan.get("finally_steps", [])}
        if required - available:
            raise RuntimeError(f"MCP missing tools: {sorted(required - available)}")
        emit("READY_FOR_CONSENT", profile=plan["profile"])
        tab_result = client.request("tools/call", {
            "name": "browser_tabs", "arguments": {"action": "list"},
        }, args.approval_timeout, "approval-and-tab-attachment", args.status_interval)
        visible = "\n".join(str(x.get("text", "")) for x in tab_result.get("content", []))
        matches = [
            line for line in visible.splitlines()
            if plan["expected_url_prefix"] in line and plan["expected_title"] in line
        ]
        if len(matches) != 1:
            raise RuntimeError("Approved tab mismatch: expected one exact title/URL entry; no action executed")
        approved = True
        emit("APPROVED_TARGET_VERIFIED", profile=plan["profile"])

        def execute(step, cleanup=False):
            name = step["name"]
            emit("ACTION_START", name=name, cleanup=cleanup)
            start = time.monotonic()
            result = client.request(
                "tools/call", {"name": step["tool"], "arguments": step["arguments"]},
                args.step_timeout, "action-" + name, args.status_interval,
            )
            elapsed = round(time.monotonic() - start, 3)
            timings.append({"step": name, "seconds": elapsed, "cleanup": cleanup})
            emit("ACTION_DONE", name=name, duration_seconds=elapsed, cleanup=cleanup)
            # Results are not echoed: browser pages can include private user data.
            return result

        try:
            for step in plan["steps"]:
                execute(step)
            completed = True
        finally:
            for step in plan.get("finally_steps", []):
                try:
                    execute(step, cleanup=True)
                except Exception as exc:
                    completed = False
                    emit("CLEANUP_FAILED", name=step["name"], error=str(exc)[:250])
        emit("TASK_COMPLETED" if completed else "TASK_INCOMPLETE",
             steps_completed=len(timings), durations=timings)
        return 0 if completed else 1
    except Exception as exc:
        emit("TASK_FAILED", error=str(exc)[:260],
             approved_target_confirmed=approved, steps_completed=len(timings))
        return 1
    finally:
        if client:
            client.close()
        emit("TASK_SESSION_RELEASED")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True)
    p.add_argument("--node", required=True)
    p.add_argument("--mcp-entry", required=True)
    p.add_argument("--browser-executable", required=True)
    p.add_argument("--user-data-dir", default="")
    p.add_argument("--stderr-log", required=True)
    p.add_argument("--approval-timeout", type=int, default=900)
    p.add_argument("--step-timeout", type=int, default=60)
    p.add_argument("--status-interval", type=float, default=15)
    args = p.parse_args()
    if args.approval_timeout < 60 or args.status_interval <= 0:
        p.error("Approval timeout must be at least 60 seconds; status interval must be positive")
    try:
        return run(args)
    except Exception as exc:
        emit("PREFLIGHT_FAILED", error=str(exc)[:260])
        return 2


if __name__ == "__main__":
    sys.exit(main())

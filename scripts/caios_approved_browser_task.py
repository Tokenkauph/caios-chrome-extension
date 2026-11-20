#!/usr/bin/env python3
"""CAIOS approved browser task: prepare once, act on exactly the approved tab.

This runner does not grant consent, open unrelated tabs, or change Chrome
profiles. Unanswered MCP calls are never retried with conflicting actions.
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


TAB_LINE = re.compile(r"^\s*-\s*(\d+):\s*(\(current\)\s*)?\[(.*?)\]\((https?://[^)]*|about:blank)\)(?:\s+\[crashed\])?(?:\s+\[isolatedContext:.*?\])?\s*$")


def emit(event: str, **details):
    print(json.dumps({"event": event, **details}, sort_keys=True), flush=True)


class MCPFault(RuntimeError):
    """Public error contains a stable code only; raw browser/MCP data stays in local logs."""

    def __init__(self, code: str, phase: str):
        super().__init__(code)
        self.code = code
        self.phase = phase


class UnknownOutcome(MCPFault):
    """A request did not answer. Do not send further browser commands."""


def read_plan(path: pathlib.Path):
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("contract_version") != "1":
        raise ValueError("Unsupported task plan version")
    for key in ("machine", "profile", "extension_id"):
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            raise ValueError(f"Missing {key}; never infer the browser host/profile")
    # The Chrome consent picker is authoritative for ordinary user-selected
    # tabs. Preserve explicit title/URL pinning for legacy scripted fixtures.
    mode = plan.get("tab_selection")
    if mode is None:
        mode = ("pinned" if "expected_title" in plan or "expected_url_prefix" in plan
                else "user_selected")
    if mode not in ("pinned", "user_selected"):
        raise ValueError("tab_selection must be pinned or user_selected")
    if mode == "pinned":
        for key in ("expected_title", "expected_url_prefix"):
            if not isinstance(plan.get(key), str) or not plan[key].strip():
                raise ValueError(f"Missing {key} for a pinned tab")
    plan["tab_selection"] = mode
    if "restore_original_url" in plan and not isinstance(plan["restore_original_url"], bool):
        raise ValueError("restore_original_url must be boolean")
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


def tabs_from_result(result):
    lines = "\n".join(str(x.get("text", "")) for x in result.get("content", []))
    tabs = []
    for line in lines.splitlines():
        match = TAB_LINE.match(line)
        if match:
            tabs.append({
                "index": int(match[1]), "current": bool(match[2]),
                "title": match[3].strip(), "url": match[4].strip(),
                "crashed": " [crashed]" in line,
            })
    return tabs


def exact_target(tabs, title, url_prefix):
    matches = [t for t in tabs if not t["crashed"] and t["title"] == title
               and t["url"].startswith(url_prefix)]
    if len(matches) != 1:
        raise MCPFault("approved_tab_missing_or_ambiguous", "tab-identification")
    return matches[0]


def approved_target(tabs, plan):
    if plan["tab_selection"] == "pinned":
        return exact_target(tabs, plan["expected_title"], plan["expected_url_prefix"])
    # Only one non-crashed tab may be attached to this one-tab task. Never
    # guess among several tabs or silently choose a different Chrome tab.
    available = [tab for tab in tabs if not tab["crashed"]]
    if len(available) != 1:
        raise MCPFault("approved_tab_missing_or_ambiguous", "tab-identification")
    return available[0]


class MCP:
    def __init__(self, argv, environment, stderr_path):
        self.stderr_path = stderr_path
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        self.log = stderr_path.open("ab")
        self.log.flush()
        self.stderr_offset = stderr_path.stat().st_size
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

    def _observed_failure(self):
        """Classify only known log signals, never print raw URLs or relay tokens."""
        try:
            with self.stderr_path.open("rb") as stream:
                stream.seek(0, os.SEEK_END)
                stream.seek(max(self.stderr_offset, stream.tell() - 8192))
                tail = stream.read().decode("utf-8", "replace").lower()
        except OSError:
            return None
        if "failed to connect to mcp relay" in tail or "websocket error" in tail:
            return "relay_websocket_failure"
        if "econnrefused" in tail or "extension disconnected" in tail:
            return "relay_disconnected"
        return None

    def request(self, method, params, deadline_seconds, phase, status_interval):
        self.next_id += 1
        request_id = self.next_id
        if self.proc.poll() is not None:
            raise MCPFault("mcp_process_exited", phase)
        try:
            self.proc.stdin.write((json.dumps({
                "jsonrpc": "2.0", "id": request_id, "method": method, "params": params,
            }) + "\n").encode("utf-8"))
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            raise MCPFault("mcp_input_closed", phase) from None
        start = time.monotonic()
        next_status = start + status_interval
        deadline = start + deadline_seconds
        while True:
            now = time.monotonic()
            if self.proc.poll() is not None and self.queue.empty():
                raise MCPFault("mcp_process_exited", phase)
            if now >= deadline:
                raise UnknownOutcome("mcp_reply_timeout", phase)
            try:
                msg = self.queue.get(timeout=min(deadline - now, max(0.05, next_status - now)))
            except queue.Empty:
                failure = self._observed_failure()
                if failure:
                    raise MCPFault(failure, phase)
                if time.monotonic() >= next_status:
                    emit("WAITING", phase=phase, elapsed_seconds=round(time.monotonic() - start, 1),
                         attachment_state="unconfirmed" if phase == "approval-and-tab-attachment" else "pending",
                         human_consent_state="unknown" if phase == "approval-and-tab-attachment" else "not_applicable")
                    next_status = time.monotonic() + status_interval
                continue
            if msg is None:
                raise MCPFault("mcp_output_closed", phase)
            if msg.get("id") != request_id:
                continue
            if "error" in msg:
                raise MCPFault("mcp_reply_error", phase)
            result = msg.get("result") or {}
            if result.get("isError"):
                raise MCPFault("tool_returned_error", phase)
            return result

    def notify_initialized(self):
        try:
            self.proc.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            raise MCPFault("mcp_input_closed", "initialize") from None

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


def safe_failure(exc):
    if isinstance(exc, MCPFault):
        return {"error_code": exc.code, "phase": exc.phase}
    # Do not echo exceptions containing browser content, profile secrets or relay URLs.
    return {"error_code": type(exc).__name__, "phase": "runner"}


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
    # Always preserve the normal Chrome approval picker.
    environment.pop("PLAYWRIGHT_MCP_EXTENSION_TOKEN", None)
    environment["CAIOS_PLAYWRIGHT_EXTENSION_ID"] = plan["extension_id"]
    command = [str(node), str(entry), "--extension",
               f"--profile-dir-name={plan['profile']}", "--no-tab-group",
               f"--executable-path={browser}"]
    if args.user_data_dir:
        command.append(f"--user-data-dir={args.user_data_dir}")
    emit("PLAN_PREPARED", machine=plan["machine"], profile=plan["profile"],
         steps=len(plan["steps"]), approval_timeout_seconds=args.approval_timeout)
    client = None
    approved = False
    primary_completed = 0
    cleanup_completed = 0
    durations = []
    primary_error = None
    cleanup_errors = []
    unknown = False
    current_stage = "preflight"
    original_url = None
    stage_start = time.monotonic()
    try:
        client = MCP(command, environment, pathlib.Path(args.stderr_log))

        def call(tool, arguments, phase, timeout=None):
            return client.request("tools/call", {"name": tool, "arguments": arguments},
                                  timeout or args.step_timeout, phase, args.status_interval)

        current_stage = "initialize"
        phase_started = time.monotonic()
        client.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "CAIOS Approved Browser Task", "version": "1"}},
                       30, current_stage, args.status_interval)
        client.notify_initialized()
        emit("STAGE_DONE", phase="initialize", duration_seconds=round(time.monotonic() - phase_started, 3))
        current_stage = "tools-list"
        phase_started = time.monotonic()
        tool_list = client.request("tools/list", {}, 30, current_stage, args.status_interval)
        emit("STAGE_DONE", phase="tools-list", duration_seconds=round(time.monotonic() - phase_started, 3))
        available = {tool["name"] for tool in tool_list.get("tools", [])}
        required = {"browser_tabs"} | {step["tool"] for step in plan["steps"] + plan.get("finally_steps", [])}
        history_restore = bool(plan.get("restore_original_url")) and (
            sum(step["tool"] == "browser_navigate" for step in plan["steps"]) == 1
            and not any(step["tool"] in ("browser_navigate_back", "browser_navigate_forward")
                        for step in plan["steps"]))
        if plan.get("restore_original_url"):
            required.add("browser_navigate_back" if history_restore else "browser_navigate")
        if plan.get("restore_original_url") or any(x["tool"] == "browser_navigate" for x in plan["steps"]):
            required.add("browser_evaluate")
        if required - available:
            raise MCPFault("required_tool_unavailable", current_stage)

        emit("READY_FOR_CONSENT", profile=plan["profile"],
             selection_mode=plan["tab_selection"], attachment_state="unconfirmed")
        current_stage = "approval-and-tab-attachment"
        consent_start = time.monotonic()
        first_tabs = tabs_from_result(call("browser_tabs", {"action": "list"}, current_stage,
                                           args.approval_timeout))
        target = approved_target(first_tabs, plan)
        emit("MCP_TAB_ATTACHED", elapsed_seconds=round(time.monotonic() - consent_start, 3))
        current_stage = "approved-tab-select"
        select_started = time.monotonic()
        call("browser_tabs", {"action": "select", "index": target["index"]}, current_stage)
        current_stage = "approved-tab-verify"
        current_tabs = tabs_from_result(call("browser_tabs", {"action": "list"}, current_stage))
        selected = approved_target(current_tabs, plan)
        if selected["index"] != target["index"]:
            raise MCPFault("approved_tab_changed", current_stage)
        if not selected["current"]:
            raise MCPFault("approved_tab_not_active", current_stage)
        def scalar_results(result):
            """Read only Playwright's actual Result, never the echoed JS Code."""
            rendered = []
            for item in result.get("content", []):
                body = str(item.get("text", ""))
                if "### Result\n" in body:
                    rendered.append(body.split("### Result\n", 1)[1].split("\n### ", 1)[0])
                else:
                    try:
                        json_response = json.loads(body)
                    except (ValueError, TypeError):
                        continue
                    if isinstance(json_response, dict) and isinstance(json_response.get("result"), str):
                        rendered.append(json.dumps(json_response["result"]))
            return rendered

        def capture_live_original_url():
            result = call("browser_evaluate", {"function": "() => location.href"},
                          "capture-original-url", timeout=min(args.step_timeout, 5.0))
            values = scalar_results(result)
            if len(values) != 1:
                raise MCPFault("original_url_unavailable", "capture-original-url")
            try:
                live_url = json.loads(values[0].strip())
            except (ValueError, TypeError):
                raise MCPFault("original_url_unavailable", "capture-original-url") from None
            allowed_blank = (plan["tab_selection"] == "user_selected"
                             and not plan.get("restore_original_url")
                             and live_url == "about:blank")
            if not isinstance(live_url, str) or not (live_url.startswith(("https://", "http://")) or allowed_blank):
                raise MCPFault("original_url_unavailable", "capture-original-url")
            if (plan["tab_selection"] == "pinned"
                    and not live_url.startswith(plan["expected_url_prefix"])):
                raise MCPFault("original_url_not_approved", "capture-original-url")
            emit("ORIGINAL_URL_CAPTURED", source="live_document",
                 tab_list_comparison="exact" if live_url == selected["url"] else "different")
            return live_url

        original_url = capture_live_original_url()
        emit("STAGE_DONE", phase="approved-tab-select-and-verify", duration_seconds=round(time.monotonic() - select_started, 3))
        approved = True
        emit("APPROVED_TARGET_VERIFIED", profile=plan["profile"],
             index=selected["index"], stage_seconds=round(time.monotonic() - stage_start, 3))

        def restore_url_status(expected, phase):
            """Only an allowlisted state is emitted; no browser URL is logged."""
            function = ("() => {const e=" + json.dumps(expected) + ";"
                        "const a=location.href;"
                        "if(document.readyState==='loading'||!document.body)"
                        "return 'CAIOS_R1_STATUS_LOADING';"
                        "if(a===e)return 'CAIOS_R1_STATUS_EXACT_READY';"
                        "try{return new URL(a).origin===new URL(e).origin"
                        "?'CAIOS_R1_STATUS_SAME_ORIGIN_MISMATCH'"
                        ":'CAIOS_R1_STATUS_OTHER_ORIGIN';}"
                        "catch{return 'CAIOS_R1_STATUS_UNREADABLE';}}")
            try:
                result = call("browser_evaluate", {"function": function},
                              phase + "-redacted-status", timeout=min(args.step_timeout, 3.0))
            except MCPFault as exc:
                if isinstance(exc, UnknownOutcome):
                    raise
                emit("RESTORE_URL_STATE", category="evaluation_error")
                return "evaluation_error"
            content = "\n".join(scalar_results(result))
            categories = ("EXACT_READY", "LOADING", "SAME_ORIGIN_MISMATCH",
                          "OTHER_ORIGIN", "UNREADABLE")
            matched = [name for name in categories if "CAIOS_R1_STATUS_" + name in content]
            category = matched[0] if len(matched) == 1 else "unavailable"
            emit("RESTORE_URL_STATE", category=category)
            return category

        def verify_url(expected, phase, *, exact=False, precheck=False, attempts_override=None):
            # Only returned MCP errors are safe to recheck; no retry of
            # unanswered or ambiguous mutation calls.
            comparison = ("location.href !== " + json.dumps(expected) if exact
                          else "!location.href.startsWith(" + json.dumps(expected) + ")")
            function = ("() => {if (" + comparison +
                        ") throw new Error('Wrong destination'); " +
                        "if (document.readyState === 'loading' || !document.body) " +
                        "throw new Error('Document not ready'); return {ready:true};}")
            # One cheap precheck determines whether to restore. Actual
            # restoration gets bounded additional time for DOM to settle.
            attempts = attempts_override if attempts_override is not None else (1 if precheck else (6 if exact else 3))
            for attempt in range(attempts):
                probe_timeout = min(args.step_timeout, 3.0) if exact else None
                tabs = tabs_from_result(call("browser_tabs", {"action": "list"}, phase,
                                             timeout=probe_timeout))
                current = [tab for tab in tabs if tab["current"]]
                if (len(current) != 1 or current[0]["crashed"]
                        or current[0]["index"] != selected["index"]):
                    raise MCPFault("approved_tab_changed", phase)
                try:
                    call("browser_evaluate", {"function": function}, phase + "-readiness",
                         timeout=probe_timeout)
                    return expected
                except MCPFault as exc:
                    if isinstance(exc, UnknownOutcome) or exc.code != "tool_returned_error":
                        raise
                    if attempt == attempts - 1:
                        if exact and not precheck:
                            if restore_url_status(expected, phase) == "EXACT_READY":
                                return expected
                        raise MCPFault("destination_not_confirmed", phase) from None
                    time.sleep(0.35 if exact else 0.2)

        def execute(step, cleanup=False):
            nonlocal unknown
            name = step["name"]
            phase = ("cleanup-" if cleanup else "action-") + name
            emit("ACTION_START", name=name, cleanup=cleanup)
            start = time.monotonic()
            recovered = False
            try:
                call(step["tool"], step["arguments"], phase)
            except MCPFault as exc:
                if exc.code == "tool_returned_error" and step["tool"] in ("browser_navigate", "browser_navigate_back"):
                    # Explicit intermediate Back navigation can target a page
                    # reached after the approved starting tab. Do not mistake
                    # the user's initial URL for that intermediate destination.
                    back_prefix = step.get("expected_url_prefix")
                    target_url = (back_prefix or original_url if step["tool"] == "browser_navigate_back"
                                  else step["arguments"].get("url"))
                    if not isinstance(target_url, str) or not target_url.startswith(("https://", "http://")):
                        raise
                    verify_url(target_url, phase + "-verify-after-error",
                               exact=step["tool"] == "browser_navigate_back" and not back_prefix)
                    recovered = True
                    emit("NAVIGATION_ARRIVAL_CONFIRMED", name=name)
                else:
                    if isinstance(exc, UnknownOutcome) or exc.code in (
                        "mcp_process_exited", "mcp_output_closed", "mcp_input_closed",
                        "relay_websocket_failure", "relay_disconnected"):
                        unknown = True
                    raise
            if (step["tool"] == "browser_navigate_back"
                    and step.get("expected_url_prefix") and not recovered):
                # Browser Back can return before the destination page is ready.
                # Only poll read-only readiness on the same approved tab; never repeat Back.
                verify_url(step["expected_url_prefix"], phase + "-confirm-ready",
                           attempts_override=12)
                emit("NAVIGATION_ARRIVAL_CONFIRMED", name=name)
            elapsed = round(time.monotonic() - start, 3)
            durations.append({"step": name, "seconds": elapsed, "cleanup": cleanup,
                              "arrival_confirmed_after_error": recovered})
            emit("ACTION_DONE", name=name, duration_seconds=elapsed,
                 cleanup=cleanup, arrival_confirmed_after_error=recovered)
            return True

        try:
            for step in plan["steps"]:
                execute(step)
                primary_completed += 1
        except Exception as exc:
            primary_error = exc
            if isinstance(exc, UnknownOutcome):
                unknown = True
        finally:
            if unknown:
                emit("RECOVERY_SKIPPED", reason="unanswered_mcp_call_state_unknown")
            else:
                if plan.get("restore_original_url") and original_url:
                    try:
                        current_stage = "restore-original-url"
                        tabs = tabs_from_result(call("browser_tabs", {"action": "list"}, current_stage))
                        current = [t for t in tabs if t["current"]]
                        if (len(current) != 1 or current[0]["crashed"]
                                or current[0]["index"] != selected["index"]):
                            raise MCPFault("approved_tab_changed", current_stage)
                        if current[0]["url"] != original_url:
                            # Before sending a restore navigation, check whether the DOM
                            # has already arrived and only the tab header is stale.
                            try:
                                verify_url(original_url, "restore-original-url-precheck",
                                           exact=True, precheck=True)
                            except MCPFault as exc:
                                if isinstance(exc, UnknownOutcome) or exc.code != "destination_not_confirmed":
                                    raise
                                restore = {
                                    "name": "restore_original_url",
                                    "tool": "browser_navigate_back" if history_restore else "browser_navigate",
                                    "arguments": {} if history_restore else {"url": original_url},
                                }
                                execute(restore, cleanup=True)
                        verify_url(original_url, "restore-original-url-verify", exact=True)
                        emit("ORIGINAL_URL_RESTORED")
                    except Exception as exc:
                        cleanup_errors.append(exc)
                        emit("RESTORE_FAILED", **safe_failure(exc))
                        if isinstance(exc, UnknownOutcome):
                            unknown = True
                if not unknown:
                    for step in plan.get("finally_steps", []):
                        try:
                            execute(step, cleanup=True)
                            cleanup_completed += 1
                        except Exception as exc:
                            cleanup_errors.append(exc)
                            emit("CLEANUP_FAILED", name=step["name"], **safe_failure(exc))
                            if isinstance(exc, UnknownOutcome):
                                break

        completed = primary_error is None and not cleanup_errors
        emit("TASK_COMPLETED" if completed else "TASK_FAILED",
             primary_steps_completed=primary_completed,
             primary_steps_total=len(plan["steps"]), cleanup_steps_completed=cleanup_completed,
             cleanup_failures=len(cleanup_errors), durations=durations,
             **(safe_failure(primary_error or cleanup_errors[0]) if not completed else {}))
        return 0 if completed else 1
    except Exception as exc:
        emit("TASK_FAILED", approved_target_confirmed=approved,
             primary_steps_completed=primary_completed,
             primary_steps_total=len(plan["steps"]), cleanup_steps_completed=cleanup_completed,
             **safe_failure(exc))
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
    p.add_argument("--step-timeout", type=float, default=60)
    p.add_argument("--status-interval", type=float, default=15)
    args = p.parse_args()
    if args.approval_timeout < 60 or args.status_interval <= 0 or args.step_timeout <= 0:
        p.error("Approval timeout must be at least 60 seconds; status interval must be positive")
    try:
        return run(args)
    except Exception as exc:
        emit("PREFLIGHT_FAILED", **safe_failure(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())

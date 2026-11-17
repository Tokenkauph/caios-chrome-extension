"""Hermetic behavior tests for the CAIOS approval-first browser runner."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "caios_approved_browser_task.py"
SPEC = importlib.util.spec_from_file_location("caios_approved_browser_task", RUNNER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

FAKE_MCP = r'''
import json, os, sys, time
mode = os.environ.get("FAKE_MODE", "")
trace = os.environ["FAKE_TRACE"]
current = 0
urls = {0: "https://other.invalid/", 1: "https://www.google.com/"}
titles = {0: "Other account", 1: "Google"}
def record(value):
    with open(trace, "a") as out:
        out.write(value + "\n")
def reply(req, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": result}) + "\n")
    sys.stdout.flush()
def tab_list():
    lines = []
    for i in sorted(urls):
        lines.append("- %d:%s [%s](%s)" % (
            i, "(current) " if current == i else "", titles[i], urls[i]))
    if mode == "ambiguous":
        lines.append("- 2: [Google](https://www.google.com/)")
    if mode == "crashed":
        lines = [value + " [crashed]" if "[Google]" in value else value for value in lines]
    return "\n".join(lines)
for line in sys.stdin:
    req = json.loads(line)
    if "id" not in req:
        continue
    method = req["method"]
    if method == "initialize":
        reply(req, {"serverInfo": {"name": "Fake CAIOS MCP"}})
    elif method == "tools/list":
        reply(req, {"tools": [{"name": n} for n in ("browser_tabs", "browser_evaluate", "browser_navigate")]})
    elif method == "tools/call":
        tool = req["params"]["name"]
        args = req["params"]["arguments"]
        if tool == "browser_tabs":
            action = args["action"]
            if action == "list":
                record("tabs_list")
                if mode == "exit_during_approval":
                    sys.exit(2)
                if mode == "relay_error_during_approval":
                    sys.stderr.write("Failed to connect to MCP relay: WebSocket error\n")
                    sys.stderr.flush()
                    time.sleep(3)
                reply(req, {"content": [{"type": "text", "text": tab_list()}]})
            elif action == "select":
                record("tabs_select_" + str(args["index"]))
                if mode == "closed_during_select":
                    reply(req, {"isError": True, "content": [{"type": "text", "text": "Tab closed"}]})
                else:
                    if args["index"] not in urls:
                        reply(req, {"isError": True})
                    else:
                        current = args["index"]
                        reply(req, {"content": [{"type": "text", "text": tab_list()}]})
        elif tool == "browser_navigate":
            target = args["url"]
            record("navigate_" + target)
            if mode == "nav_timeout" and "wikipedia" in target:
                time.sleep(3)
                continue
            if mode == "restore_fail" and "google" in target:
                reply(req, {"isError": True, "content": [{"type": "text", "text": "Load failed"}]})
                continue
            if mode != "nav_failed" or "wikipedia" not in target:
                urls[current] = target
                titles[current] = "European badger - Wikipedia" if "wikipedia" in target else "Google"
            if mode in ("nav_arrived_error", "nav_failed") and "wikipedia" in target:
                reply(req, {"isError": True, "content": [{"type": "text", "text": "Navigation timeout"}]})
            else:
                reply(req, {"content": [{"type": "text", "text": "Done"}]})
        elif tool == "browser_evaluate":
            record("evaluate")
            reply(req, {"content": [{"type": "text", "text": "Done"}]})
        else:
            reply(req, {"isError": True})
'''

class ApprovedTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.mock = self.directory / "mock_mcp.py"
        self.mock.write_text(FAKE_MCP)
        self.browser = self.directory / "dummy-browser"
        self.browser.write_text("mock only")
        self.trace = self.directory / "trace"
        self.plan = self.directory / "plan.json"
        self.task = {
            "contract_version": "1",
            "machine": platform.node(),
            "profile": "Default",
            "extension_id": "kanpfbepfgcpmjoeaaihigjkcdjejbld",
            "expected_title": "Google",
            "expected_url_prefix": "https://www.google.com/",
            "restore_original_url": True,
            "steps": [
                {"name": "read", "tool": "browser_evaluate", "arguments": {"function": "read"}},
                {"name": "navigate", "tool": "browser_navigate",
                 "arguments": {"url": "https://en.wikipedia.org/wiki/European_badger"}},
                {"name": "read_article", "tool": "browser_evaluate", "arguments": {"function": "read"}},
            ],
            "finally_steps": [
                {"name": "verify_home", "tool": "browser_evaluate",
                 "arguments": {"function": "verify_google"}},
            ],
        }

    def run_task(self, changes=None, mode="", step_timeout=1):
        task = dict(self.task)
        if changes:
            task.update(changes)
        self.plan.write_text(json.dumps(task))
        env = dict(os.environ, FAKE_TRACE=str(self.trace), FAKE_MODE=mode)
        env.pop("PLAYWRIGHT_MCP_EXTENSION_TOKEN", None)
        r = subprocess.run(
            [sys.executable, str(RUNNER), "--plan", str(self.plan),
             "--node", sys.executable, "--mcp-entry", str(self.mock),
             "--browser-executable", str(self.browser),
             "--stderr-log", str(self.directory / "stderr.log"),
             "--approval-timeout", "60", "--step-timeout", str(step_timeout),
             "--status-interval", "0.05"],
            env=env, capture_output=True, text=True, timeout=12,
        )
        events = [json.loads(x) for x in r.stdout.splitlines() if x.startswith("{")]
        return r, events, self.trace.read_text().splitlines() if self.trace.exists() else []

    def test_selects_exact_approved_tab_before_actions(self):
        r, ev, trace = self.run_task()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(trace[:4], ["tabs_list", "tabs_select_1", "tabs_list", "evaluate"])
        self.assertEqual(len([e for e in ev if e["event"] == "ACTION_DONE" and not e["cleanup"]]), 3)
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))
        done = [e for e in ev if e["event"] == "TASK_COMPLETED"][0]
        self.assertEqual(done["primary_steps_completed"], 3)
        self.assertEqual(done["cleanup_steps_completed"], 1)
        self.assertEqual(ev[-1]["event"], "TASK_SESSION_RELEASED")

    def test_wrong_title_blocks_before_selection(self):
        r, ev, trace = self.run_task({"expected_title": "Private account"})
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("tabs_select_1", trace)
        self.assertEqual([e for e in ev if e["event"] == "TASK_FAILED"][0]["error_code"],
                         "approved_tab_missing_or_ambiguous")

    def test_ambiguous_tabs_block_before_selection(self):
        r, _, trace = self.run_task(mode="ambiguous")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("tabs_select_1", trace)

    def test_crashed_approved_tab_is_not_executed(self):
        r, _, trace = self.run_task(mode="crashed")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("tabs_select_1", trace)

    def test_closed_tab_selection_blocks_actions(self):
        r, _, trace = self.run_task(mode="closed_during_select")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("evaluate", trace)

    def test_navigation_arrived_despite_completed_error_is_verified(self):
        r, ev, trace = self.run_task(mode="nav_arrived_error")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("navigate_https://en.wikipedia.org/wiki/European_badger", trace)
        self.assertTrue(any(e["event"] == "NAVIGATION_ARRIVAL_CONFIRMED" for e in ev))
        self.assertEqual([e for e in ev if e["event"] == "TASK_COMPLETED"][0]["primary_steps_completed"], 3)

    def test_navigation_not_arrived_is_failure_and_restores(self):
        r, ev, _ = self.run_task(mode="nav_failed")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))
        fail = [e for e in ev if e["event"] == "TASK_FAILED"][0]
        self.assertEqual(fail["primary_steps_completed"], 1)

    def test_unanswered_navigation_never_sends_conflicting_cleanup(self):
        r, ev, trace = self.run_task(mode="nav_timeout", step_timeout=0.2)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("navigate_https://en.wikipedia.org/wiki/European_badger", trace)
        self.assertNotIn("navigate_https://www.google.com/", trace)
        self.assertTrue(any(e["event"] == "RECOVERY_SKIPPED" for e in ev))
        self.assertEqual([e for e in ev if e["event"] == "TASK_FAILED"][0]["error_code"],
                         "mcp_reply_timeout")

    def test_restore_failure_reported_separately(self):
        r, ev, _ = self.run_task(mode="restore_fail")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(any(e["event"] == "RESTORE_FAILED" for e in ev))
        self.assertEqual([e for e in ev if e["event"] == "TASK_FAILED"][0]["primary_steps_completed"], 3)

    def test_no_restore_requested_leaves_new_page(self):
        r, ev, trace = self.run_task({"restore_original_url": False, "finally_steps": []})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("navigate_https://www.google.com/", trace)
        self.assertFalse(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))

    def test_process_exit_during_attachment_reported_without_user_blame(self):
        r, ev, _ = self.run_task(mode="exit_during_approval")
        self.assertEqual(r.returncode, 1)
        fail = [e for e in ev if e["event"] == "TASK_FAILED"][0]
        self.assertIn(fail["error_code"], ("mcp_output_closed", "mcp_process_exited"))
        self.assertFalse(fail["approved_target_confirmed"])

    def test_relay_error_reported_promptly_without_private_url(self):
        r, ev, _ = self.run_task(mode="relay_error_during_approval")
        self.assertEqual(r.returncode, 1, r.stdout)
        fail = [e for e in ev if e["event"] == "TASK_FAILED"][0]
        self.assertEqual(fail["error_code"], "relay_websocket_failure")
        self.assertNotIn("ws://", r.stdout)

    def test_wrong_machine_is_preflight_failure(self):
        r, ev, trace = self.run_task({"machine": "different-host"})
        self.assertEqual(r.returncode, 2)
        self.assertEqual(ev[0]["event"], "PREFLIGHT_FAILED")
        self.assertEqual(trace, [])

    def test_no_approval_is_an_unknown_outcome_with_status(self):
        fake = self.directory / "wait.py"
        fake.write_text("import sys,time\nfor line in sys.stdin:\n time.sleep(1)\n")
        c = MODULE.MCP([sys.executable, str(fake)], os.environ.copy(), self.directory / "wait.log")
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                with self.assertRaises(MODULE.UnknownOutcome):
                    c.request("tools/call", {"name": "browser_tabs"}, 0.18, "approval", 0.05)
        finally:
            c.close()
        self.assertIn('"event": "WAITING"', output.getvalue())

if __name__ == "__main__":
    unittest.main()

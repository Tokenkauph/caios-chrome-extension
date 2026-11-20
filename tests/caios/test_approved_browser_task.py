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
import json, os, re, sys, time
mode = os.environ.get("FAKE_MODE", "")
trace = os.environ["FAKE_TRACE"]
current = 0
urls = {0: "https://other.invalid/", 1: "https://www.google.com/"}
if mode == "restore_prefix_collision":
    urls[1] = "https://www.google.com/page?item=123"
titles = {0: "Other account", 1: "Google"}
history = {0: [], 1: []}
if mode == "user_selected_arbitrary":
    urls = {0: "https://user-chosen.example/path"}
    titles = {0: "User-selected site"}
    history = {0: []}
elif mode == "user_selected_crashed":
    urls = {0: "https://user-chosen.example/path"}
    titles = {0: "User-selected site"}
    history = {0: []}
stale_restore_listing = 0
readiness_lag = 0
after_navigation = False
def record(value):
    with open(trace, "a") as out:
        out.write(value + "\n")
def reply(req, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": result}) + "\n")
    sys.stdout.flush()
def tab_list():
    global stale_restore_listing
    lines = []
    for i in sorted(urls):
        shown_url = urls[i]
        if i == 1 and mode == "stale_initial_tab_url" and not after_navigation:
            shown_url = "https://www.google.com/?tab-list-stale=1"
        if i == 1 and stale_restore_listing:
            shown_url = "https://en.wikipedia.org/wiki/European_badger"
            stale_restore_listing -= 1
        shown_current = current == i or (mode == "ambiguous_current_after_navigation" and after_navigation)
        lines.append("- %d:%s [%s](%s)" % (
            i, "(current) " if shown_current else "", titles[i], shown_url))
    if mode == "ambiguous":
        lines.append("- 2: [Google](https://www.google.com/)")
    if mode == "crashed":
        lines = [value + " [crashed]" if "[Google]" in value else value for value in lines]
    if mode == "user_selected_crashed":
        lines = [value + " [crashed]" for value in lines]
    return "\n".join(lines)
for line in sys.stdin:
    req = json.loads(line)
    if "id" not in req:
        continue
    method = req["method"]
    if method == "initialize":
        reply(req, {"serverInfo": {"name": "Fake CAIOS MCP"}})
    elif method == "tools/list":
        reply(req, {"tools": [{"name": n} for n in ("browser_tabs", "browser_evaluate", "browser_navigate", "browser_navigate_back")]})
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
                history[current].append(urls[current])
                urls[current] = target
                titles[current] = "European badger - Wikipedia" if "wikipedia" in target else "Google"
                if "wikipedia" in target:
                    after_navigation = True
                    if mode == "switch_current_after_navigation":
                        current = 0
                else:
                    if mode == "stale_restore_listing":
                        stale_restore_listing = 2
                    if mode == "readiness_lag":
                        readiness_lag = 1
                    if mode == "diagnostic_late_ready":
                        readiness_lag = 6
                    if mode == "restore_same_origin_redirect":
                        urls[current] = "https://www.google.com/?redirect=1"
                    if mode == "restore_wrong_page":
                        urls[current] = "https://www.google.com/wrong"
                    if mode == "restore_prefix_collision":
                        urls[current] = target + "4"
            if mode in ("nav_arrived_error", "nav_failed") and "wikipedia" in target:
                reply(req, {"isError": True, "content": [{"type": "text", "text": "Navigation timeout"}]})
            else:
                reply(req, {"content": [{"type": "text", "text": "Done"}]})
        elif tool == "browser_navigate_back":
            record("navigate_back")
            if mode == "back_timeout":
                time.sleep(3)
                continue
            if mode == "restore_fail":
                reply(req, {"isError": True, "content": [{"type": "text", "text": "Back failed"}]})
                continue
            if not history[current]:
                reply(req, {"isError": True, "content": [{"type": "text", "text": "No history"}]})
                continue
            urls[current] = history[current].pop()
            titles[current] = "Google" if "google" in urls[current] else "European badger - Wikipedia"
            if mode == "restore_wrong_page":
                urls[current] = "https://www.google.com/wrong"
            if mode == "restore_prefix_collision":
                urls[current] += "4"
            if mode == "back_same_origin_redirect":
                urls[current] = "https://www.google.com/?redirect=1"
            if mode == "stale_restore_listing":
                stale_restore_listing = 2
            if mode == "readiness_lag":
                readiness_lag = 1
            if mode == "diagnostic_late_ready":
                readiness_lag = 6
            if mode == "back_arrived_error":
                reply(req, {"isError": True, "content": [{"type": "text", "text": "Navigation error"}]})
                continue
            reply(req, {"content": [{"type": "text", "text": "Done"}]})
        elif tool == "browser_evaluate":
            record("evaluate")
            expression = args.get("function", "")
            if expression.strip() == "() => location.href":
                value = urls[current]
                response_text = ("### Result\n" + json.dumps(value) +
                                 "\n\n### Ran Playwright code\n" + expression)
                reply(req, {"content": [{"type": "text", "text": response_text}]})
                continue
            if "CAIOS_R1_STATUS_" in expression:
                found = re.search(r'const e=("[^"]+")', expression)
                expected = json.loads(found.group(1)) if found else ""
                actual = urls[current]
                if actual == expected:
                    category = "EXACT_READY"
                elif actual.split("/")[2] == expected.split("/")[2]:
                    category = "SAME_ORIGIN_MISMATCH"
                else:
                    category = "OTHER_ORIGIN"
                # Real Playwright includes both the scalar Result and echoed JS Code.
                response_text = ("### Result" + chr(10) + chr(34) +
                                 "CAIOS_R1_STATUS_" + category + chr(34) +
                                 chr(10) + chr(10) + "### Ran Playwright code" +
                                 chr(10) + expression)
                reply(req, {"content": [{"type": "text", "text": response_text}]})
                continue
            exact = re.search(r'location\.href !== ("[^"]+")', expression)
            prefix = re.search(r'location\.href\.startsWith\(("[^"]+")\)', expression)
            if exact or prefix:
                expected = json.loads((exact or prefix).group(1))
                actual = urls[current]
                correct = actual == expected if exact else actual.startswith(expected)
                if readiness_lag and actual.startswith("https://www.google.com/"):
                    readiness_lag -= 1
                    correct = False
                if not correct:
                    reply(req, {"isError": True, "content": [{"type": "text", "text": "Not at destination"}]})
                    continue
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

    def test_user_selected_tab_accepts_arbitrary_title_and_url(self):
        r, ev, trace = self.run_task({
            "tab_selection": "user_selected",
            "expected_title": "A different test-only title",
            "expected_url_prefix": "https://example.com/",
            "finally_steps": [],
        }, mode="user_selected_arbitrary")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("tabs_select_0", trace)
        self.assertTrue(any(e["event"] == "APPROVED_TARGET_VERIFIED" for e in ev))
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))
        self.assertNotIn("https://user-chosen.example/path", r.stdout)

    def test_user_selected_tab_without_title_or_prefix_defaults_to_picker(self):
        changes = {"finally_steps": [], "restore_original_url": False}
        changes["expected_title"] = None
        changes["expected_url_prefix"] = None
        task = dict(self.task)
        task.update(changes)
        task.pop("expected_title")
        task.pop("expected_url_prefix")
        self.plan.write_text(json.dumps(task))
        env = dict(os.environ, FAKE_TRACE=str(self.trace), FAKE_MODE="user_selected_arbitrary")
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--plan", str(self.plan),
             "--node", sys.executable, "--mcp-entry", str(self.mock),
             "--browser-executable", str(self.browser),
             "--stderr-log", str(self.directory / "stderr.log"),
             "--approval-timeout", "60", "--step-timeout", "1",
             "--status-interval", "0.05"],
            env=env, capture_output=True, text=True, timeout=12,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("tabs_select_0", self.trace.read_text())

    def test_user_selected_multiple_attached_tabs_does_not_guess(self):
        r, ev, trace = self.run_task({"tab_selection": "user_selected"})
        self.assertEqual(r.returncode, 1)
        self.assertFalse(any(line.startswith("tabs_select") for line in trace))
        self.assertEqual([e for e in ev if e["event"] == "TASK_FAILED"][0]["error_code"],
                         "approved_tab_missing_or_ambiguous")

    def test_user_selected_crashed_tab_not_accepted(self):
        r, _, trace = self.run_task({"tab_selection": "user_selected"}, mode="user_selected_crashed")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(any(line.startswith("tabs_select") for line in trace))

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

    def test_delayed_tab_listing_accepts_correct_document(self):
        r, ev, trace = self.run_task(mode="stale_restore_listing")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))
        self.assertEqual(trace.count("navigate_back"), 1)

    def test_wrong_restored_page_is_not_accepted(self):
        r, ev, _ = self.run_task(mode="restore_wrong_page")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any(e["event"] == "RESTORE_FAILED" for e in ev))
        self.assertFalse(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))

    def test_exact_original_query_not_prefix_collision(self):
        r, ev, _ = self.run_task(mode="restore_prefix_collision")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any(e["event"] == "RESTORE_FAILED" for e in ev))

    def test_switched_current_tab_never_receives_restore_navigation(self):
        r, ev, trace = self.run_task(mode="switch_current_after_navigation")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse(any("navigate_https://www.google.com/" in x for x in trace))
        self.assertTrue(any(e["event"] == "RESTORE_FAILED" for e in ev))

    def test_ambiguous_current_tab_never_receives_restore_navigation(self):
        r, ev, trace = self.run_task(mode="ambiguous_current_after_navigation")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse(any("navigate_https://www.google.com/" in x for x in trace))
        self.assertTrue(any(e["event"] == "RESTORE_FAILED" for e in ev))

    def test_brief_loading_delay_settles_without_duplicate_navigation(self):
        r, ev, trace = self.run_task(mode="readiness_lag")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))
        self.assertEqual(trace.count("navigate_back"), 1)

    def test_redacted_final_probe_accepts_exact_ready_document(self):
        r, ev, trace = self.run_task(mode="diagnostic_late_ready")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(any(e["event"] == "RESTORE_URL_STATE" and
                            e["category"] == "EXACT_READY" for e in ev))
        self.assertEqual(trace.count("navigate_back"), 1)
        self.assertNotIn("https://www.google.com/", r.stdout)

    def test_same_origin_redirect_does_not_pass_exact_restore(self):
        r, ev, _ = self.run_task(mode="back_same_origin_redirect")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any(e["event"] == "RESTORE_URL_STATE" and
                            e["category"] == "SAME_ORIGIN_MISMATCH" for e in ev))
        self.assertFalse(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))
        self.assertNotIn("https://www.google.com/?redirect=1", r.stdout)

    def test_history_back_avoids_redirect_on_reopening_google(self):
        r, ev, trace = self.run_task(mode="restore_same_origin_redirect")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(trace.count("navigate_back"), 1)
        self.assertNotIn("navigate_https://www.google.com/", trace)
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))

    def test_capture_live_document_url_not_stale_tab_header(self):
        r, ev, trace = self.run_task(mode="stale_initial_tab_url")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_CAPTURED" and
                            e["tab_list_comparison"] == "different" for e in ev))
        self.assertEqual(trace.count("navigate_back"), 1)
        self.assertNotIn("https://www.google.com/?tab-list-stale=1", r.stdout)

    def test_back_error_after_arrival_is_verified_without_duplicate_navigation(self):
        r, ev, trace = self.run_task(mode="back_arrived_error")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(trace.count("navigate_back"), 1)
        self.assertTrue(any(e["event"] == "NAVIGATION_ARRIVAL_CONFIRMED" and
                            e["name"] == "restore_original_url" for e in ev))

    def test_multiple_navigation_task_keeps_existing_restoration(self):
        steps = list(self.task["steps"])
        steps.append({"name": "second_navigation", "tool": "browser_navigate",
                      "arguments": {"url": "https://en.wikipedia.org/wiki/European_badger?view=1"}})
        r, ev, trace = self.run_task({"steps": steps})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("navigate_back", trace)
        self.assertEqual(trace.count("navigate_https://www.google.com/"), 1)
        self.assertTrue(any(e["event"] == "ORIGINAL_URL_RESTORED" for e in ev))

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

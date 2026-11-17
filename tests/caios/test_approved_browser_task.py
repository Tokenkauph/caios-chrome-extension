"""Hermetic acceptance tests for the reusable CAIOS approval-first task runner."""
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
def reply(req, data):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": data})+"\n")
    sys.stdout.flush()
for line in sys.stdin:
    req = json.loads(line)
    if "id" not in req: continue
    method = req["method"]
    if method == "initialize":
        reply(req, {"serverInfo": {"name": "Fake CAIOS Playwright MCP"}})
    elif method == "tools/list":
        reply(req, {"tools": [{"name": x} for x in ["browser_tabs","browser_evaluate","browser_navigate"]]})
    elif method == "tools/call":
        tool = req["params"]["name"]
        if tool == "browser_tabs":
            time.sleep(0.06)
            title = os.environ.get("FAKE_TITLE", "Google")
            reply(req, {"content": [{"type": "text", "text": "- 0: (current) "+title+" (https://www.google.com/)"}]})
        else:
            with open(os.environ["FAKE_TRACE"], "a") as f:
                f.write(req["params"]["arguments"].get("function", "navigation") + "\n")
            reply(req, {"content": [{"type": "text", "text": "Done"}]})
'''


class ApprovedTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.mock = self.directory / "mock_mcp.py"
        self.mock.write_text(FAKE_MCP)
        self.browser = self.directory / "dummy-browser"
        self.browser.write_text("browser is never executed in mock")
        self.trace = self.directory / "trace"
        self.plan = self.directory / "plan.json"
        self.task = {
            "contract_version": "1",
            "machine": platform.node(),
            "profile": "Default",
            "extension_id": "kanpfbepfgcpmjoeaaihigjkcdjejbld",
            "expected_title": "Google",
            "expected_url_prefix": "https://www.google.com/",
            "steps": [
                {"name": "read", "tool": "browser_evaluate", "arguments": {"function": "read"}},
                {"name": "scroll", "tool": "browser_evaluate", "arguments": {"function": "scroll"}},
            ],
            "finally_steps": [
                {"name": "restore", "tool": "browser_navigate", "arguments": {"url": "https://www.google.com/"}},
            ],
        }

    def run_task(self, changed=None):
        task = dict(self.task)
        if changed:
            task.update(changed)
        self.plan.write_text(json.dumps(task))
        env = dict(os.environ, FAKE_TRACE=str(self.trace))
        env.pop("PLAYWRIGHT_MCP_EXTENSION_TOKEN", None)
        r = subprocess.run(
            [
                sys.executable, str(RUNNER), "--plan", str(self.plan),
                "--node", sys.executable, "--mcp-entry", str(self.mock),
                "--browser-executable", str(self.browser),
                "--stderr-log", str(self.directory / "stderr.log"),
                "--approval-timeout", "60", "--status-interval", "0.05",
            ], env=env, capture_output=True, text=True, timeout=8,
        )
        events = [json.loads(x) for x in r.stdout.splitlines() if x.startswith("{")]
        return r, events

    def test_approval_automatically_runs_every_prepared_step_without_new_command(self):
        r, events = self.run_task()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([e["event"] for e in events if e["event"] in
                          ("APPROVED_TARGET_VERIFIED","ACTION_START","TASK_COMPLETED")],
                         ["APPROVED_TARGET_VERIFIED","ACTION_START","ACTION_START",
                          "ACTION_START","TASK_COMPLETED"])
        self.assertEqual(self.trace.read_text().splitlines(), ["read", "scroll", "navigation"])
        self.assertEqual(events[-1]["event"], "TASK_SESSION_RELEASED")

    def test_wrong_tab_does_not_execute_actions(self):
        r, events = self.run_task({"expected_title": "Private account"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(self.trace.exists())
        self.assertTrue(any(e["event"] == "TASK_FAILED" for e in events))

    def test_wrong_machine_is_rejected_before_spawning(self):
        r, events = self.run_task({"machine": "different-host"})
        self.assertEqual(r.returncode, 2)
        self.assertFalse(self.trace.exists())
        self.assertEqual(events[0]["event"], "PREFLIGHT_FAILED")

    def test_no_approval_reports_waiting_and_timeout(self):
        fake = self.directory / "wait.py"
        fake.write_text("import sys,time\nfor line in sys.stdin:\n time.sleep(1)\n")
        env = os.environ.copy()
        c = MODULE.MCP([sys.executable, str(fake)], env, self.directory / "wait.log")
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                with self.assertRaises(TimeoutError):
                    c.request("tools/call", {"name": "browser_tabs"},
                              0.18, "approval", 0.05)
        finally:
            c.close()
        self.assertIn('"event": "WAITING"', out.getvalue())


if __name__ == "__main__":
    unittest.main()

"""Static contract checks for the mandatory real-world browser install acceptance.

These checks validate the reusable plan and package source. They do not claim
real Chrome consent or a successful live browser submission.
"""
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
WIN = SCRIPTS / "windows-smoke"
PLAN = WIN / "caios-install-acceptance.template.json"
UPLOAD_NAME = "caios-install-acceptance-upload.txt"


class StandardInstallAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN.read_text(encoding="utf-8"))
        cls.steps = cls.plan["steps"]
        cls.names = [step["name"] for step in cls.steps]

    def test_new_install_uses_only_user_selected_tab(self):
        self.assertEqual(self.plan["contract_version"], "1")
        self.assertEqual(self.plan["tab_selection"], "user_selected")
        self.assertNotIn("expected_title", self.plan)
        self.assertNotIn("expected_url_prefix", self.plan)
        self.assertFalse(self.plan["restore_original_url"])
        self.assertEqual(self.plan["finally_steps"], [])
        self.assertEqual(len(self.steps), 39)
        self.assertEqual(len(set(self.names)), 39)

    def test_real_navigation_and_back_precede_form(self):
        prefix = self.steps[:7]
        self.assertEqual([step["tool"] for step in prefix], [
            "browser_navigate", "browser_evaluate",
            "browser_navigate", "browser_evaluate",
            "browser_navigate_back", "browser_evaluate",
            "browser_navigate",
        ])
        self.assertEqual(prefix[0]["arguments"]["url"], "https://www.msn.com/")
        self.assertEqual(prefix[2]["arguments"]["url"], "https://en.wikipedia.org/wiki/European_badger")
        self.assertEqual(prefix[4]["expected_url_prefix"], "https://www.msn.com/")
        self.assertIn("BACK_DID_NOT_RETURN_TO_MSN", prefix[5]["arguments"]["function"])
        self.assertEqual(prefix[6]["arguments"]["url"], "https://www.selenium.dev/selenium/web/web-form.html")

    def test_all_editable_control_families_and_protected_fields(self):
        tools = {step["tool"] for step in self.steps}
        self.assertTrue({
            "browser_type", "browser_fill_form", "browser_select_option",
            "browser_file_upload", "browser_press_key", "browser_evaluate",
            "browser_click", "browser_snapshot",
        }.issubset(tools))
        for fragment in (
            "text", "password", "textarea", "dropdown", "datalist",
            "checkboxes", "radio", "date", "color", "slider",
            "uploaded_file", "protected_fields",
        ):
            self.assertTrue(any(fragment in name for name in self.names), fragment)
        self.assertEqual(self.steps[-2]["name"], "38_submit_form")
        self.assertEqual(self.steps[-1]["name"], "39_verify_received")
        self.assertEqual(self.steps[-2]["tool"], "browser_click")
        self.assertIn("Received!", self.steps[-1]["arguments"]["function"])
        self.assertIn("submitted-form.html", self.steps[-1]["arguments"]["function"])

    def test_upload_is_harmless_and_within_runner_working_directory(self):
        upload = [step for step in self.steps if step["tool"] == "browser_file_upload"]
        self.assertEqual(len(upload), 1)
        self.assertEqual(upload[0]["arguments"]["paths"], [UPLOAD_NAME])
        payload = (WIN / UPLOAD_NAME).read_text(encoding="utf-8")
        self.assertIn("harmless dummy file", payload)
        self.assertNotIn("password", payload.lower())

    def test_install_date_is_rendered_per_run(self):
        raw = PLAN.read_text(encoding="utf-8")
        self.assertGreaterEqual(raw.count("__TEST_DATE__"), 4)
        script = (WIN / "run-acceptance.ps1").read_text(encoding="utf-8")
        self.assertIn("Replace('__TEST_DATE__', $today)", script)
        self.assertIn("Set-Location -LiteralPath $PSScriptRoot", script)
        self.assertIn("CAIOS_ACCEPTANCE_EXIT_CODE", script)
        self.assertNotIn("Start-Process", script)
        self.assertNotIn("expected_url_prefix", raw)

    def test_bundle_includes_mandatory_acceptance_tools(self):
        package = SCRIPTS / "package_caios_windows.py"
        spec = importlib.util.spec_from_file_location("package_caios_windows", package)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for member in (
            "smoke/caios-install-acceptance.template.json",
            "smoke/caios-install-acceptance-upload.txt",
            "smoke/run-acceptance.ps1",
            "smoke/caios_approved_browser_task.py",
        ):
            self.assertIn(member, module.SMOKE_FILES)
            self.assertTrue((SCRIPTS / module.SMOKE_FILES[member]).is_file())


if __name__ == "__main__":
    unittest.main()

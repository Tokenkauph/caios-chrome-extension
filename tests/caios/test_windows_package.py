"""Regression tests for reuse of the already-approved CAIOS Windows release and browser runner."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "package_caios_windows.py"
spec = importlib.util.spec_from_file_location("caios_windows_package", SCRIPT)
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


class WindowsReleaseSmokePackageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "complete.zip"
        self.out = Path(self.tmp.name) / "complete-with-smoke.zip"

    def fixture(self, *, extension_id=pack.EXTENSION_ID, version="0.5.0.3", extra=None):
        contents = {
            "extension/manifest.json": json.dumps(
                {"name": "CAIOS Chrome Extension", "version": version}
            ).encode(),
            "CAIOS-RELEASE.json": json.dumps(
                {"extension_version": version, "extension_id": extension_id}
            ).encode(),
            "playwright-core/lib/entry/mcp.js": b"// fake MCP entry, no runtime execution\n",
            "runtime/node.exe": b"fake test bytes only",
        }
        contents.update(extra or {})
        with zipfile.ZipFile(self.base, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, value in contents.items():
                z.writestr(name, value)
        return pack.sha256_file(self.base)

    def build(self, sha):
        return pack.build_bundle(
            self.base, self.out, sha, "0.5.0.3", script_root=REPO / "scripts"
        )

    def test_includes_identical_canonical_runner_and_plan(self):
        sha = self.fixture()
        report = self.build(sha)
        self.assertTrue(self.out.is_file())
        self.assertEqual(report["base_archive_sha256"], sha)
        self.assertEqual(report["smoke_files"], 5)
        with zipfile.ZipFile(self.out) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(
                z.read("smoke/caios_approved_browser_task.py"),
                (REPO / "scripts" / "caios_approved_browser_task.py").read_bytes(),
            )
            self.assertIn(b"MCP_TAB_ATTACHED", z.read("smoke/caios_approved_browser_task.py"))
            self.assertIn(b"READY_FOR_CONSENT", z.read("smoke/caios_approved_browser_task.py"))
            plan = json.loads(z.read("smoke/caios-example-domain-smoke.template.json"))
            self.assertEqual(plan["machine"], "__TARGET_HOST__")
            self.assertEqual(plan["profile"], "__CHROME_PROFILE__")
            self.assertEqual(plan["extension_id"], pack.EXTENSION_ID)
            self.assertEqual(plan["expected_title"], "Example Domain")
            self.assertEqual(plan["expected_url_prefix"], "https://example.com/")
            self.assertEqual(plan["steps"][2]["tool"], "browser_navigate")
            self.assertTrue(plan["restore_original_url"])
            self.assertIn(b"WriteAllText", z.read("smoke/run-smoke.ps1"))
            self.assertIn(b"UTF8Encoding($false)", z.read("smoke/run-smoke.ps1"))
            meta = json.loads(z.read("smoke/CAIOS-SMOKE-RELEASE.json"))
            self.assertEqual(meta["base_archive_sha256"], sha)
            self.assertEqual(meta["extension_id"], pack.EXTENSION_ID)
            self.assertEqual(meta["embedded_sha256"]["smoke/caios_approved_browser_task.py"], hashlib.sha256(
                (REPO / "scripts" / "caios_approved_browser_task.py").read_bytes()).hexdigest())
            self.assertEqual(z.read("runtime/node.exe"), b"fake test bytes only")

    def test_wrong_sha_fails_without_output(self):
        self.fixture()
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            self.build("0" * 64)
        self.assertFalse(self.out.exists())

    def test_wrong_extension_identity_fails_closed(self):
        sha = self.fixture(extension_id="mmlmfjhmonkocbjadbfplnigmagldckm")
        with self.assertRaisesRegex(ValueError, "identity mismatch|version, name or CAIOS extension ID mismatch"):
            self.build(sha)
        self.assertFalse(self.out.exists())

    def test_incomplete_release_refused(self):
        sha = self.fixture()
        with zipfile.ZipFile(self.base, "w") as z:
            z.writestr("extension/manifest.json", b"{}")
        with self.assertRaisesRegex(ValueError, "missing"):
            self.build(pack.sha256_file(self.base))
        self.assertFalse(self.out.exists())

    def test_unsafe_zip_member_refused(self):
        self.fixture(extra={"../outside.txt": b"must not extract"})
        with self.assertRaisesRegex(ValueError, "Unsafe ZIP member"):
            self.build(pack.sha256_file(self.base))
        self.assertFalse(self.out.exists())

    def test_existing_smoke_refused(self):
        self.fixture(extra={"smoke/caios_approved_browser_task.py": b"old"})
        with self.assertRaisesRegex(ValueError, "already has smoke tooling"):
            self.build(pack.sha256_file(self.base))
        self.assertFalse(self.out.exists())

    def test_refuses_to_replace_preexisting_output(self):
        sha = self.fixture()
        self.out.write_bytes(b"untouched")
        with self.assertRaises(FileExistsError):
            self.build(sha)
        self.assertEqual(self.out.read_bytes(), b"untouched")

    def test_refuses_in_place_repackage(self):
        sha = self.fixture()
        with self.assertRaisesRegex(ValueError, "in-place"):
            pack.build_bundle(self.base, self.base, sha, "0.5.0.3",
                              script_root=REPO / "scripts")


if __name__ == "__main__":
    unittest.main()

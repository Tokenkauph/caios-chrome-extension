#!/usr/bin/env python3
"""Add the canonical CAIOS approved browser runner and Windows smoke test to a reviewed complete ZIP.

Only consumes an already-built, SHA-256-verified complete Windows release.
Does not build Playwright, install software, start Chrome, or change user profiles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile


EXTENSION_ID = "kanpfbepfgcpmjoeaaihigjkcdjejbld"
REQUIRED = {
    "CAIOS-RELEASE.json",
    "extension/manifest.json",
    "playwright-core/lib/entry/mcp.js",
    "runtime/node.exe",
}
SMOKE_FILES = {
    "smoke/caios_approved_browser_task.py": "caios_approved_browser_task.py",
    "smoke/caios-example-domain-smoke.template.json": "windows-smoke/caios-example-domain-smoke.template.json",
    "smoke/run-smoke.ps1": "windows-smoke/run-smoke.ps1",
    "smoke/README.md": "windows-smoke/README.md",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while part := stream.read(1024 * 1024):
            digest.update(part)
    return digest.hexdigest()


def checked_members(archive: zipfile.ZipFile) -> set[str]:
    names: set[str] = set()
    for item in archive.infolist():
        name = item.filename
        pieces = PurePosixPath(name).parts
        if (not name or name.startswith("/") or "\\" in name or
                any(part in ("..", ".") for part in pieces) or
                (pieces and ":" in pieces[0])):
            raise ValueError("Unsafe ZIP member")
        if name in names:
            raise ValueError("Duplicate ZIP member: " + name)
        if name.startswith("smoke/"):
            raise ValueError("Complete bundle already has smoke tooling; refusing to replace it")
        names.add(name)
    if missing := REQUIRED - names:
        raise ValueError("Incomplete Windows bundle; missing: " + ", ".join(sorted(missing)))
    bad = archive.testzip()
    if bad is not None:
        raise ValueError("Corrupt archive member")
    return names


def validate_release(archive: zipfile.ZipFile, expected_version: str) -> None:
    manifest = json.loads(archive.read("extension/manifest.json"))
    release = json.loads(archive.read("CAIOS-RELEASE.json"))
    if (manifest.get("name") != "CAIOS Chrome Extension" or
            manifest.get("version") != expected_version or
            release.get("extension_version") != expected_version or
            release.get("extension_id") != EXTENSION_ID):
        raise ValueError("Release version, name or CAIOS extension ID mismatch")


def build_bundle(
    original: Path, target: Path, expected_sha256: str, expected_version: str,
    script_root: Path | None = None,
) -> dict:
    original, target = original.resolve(), target.resolve()
    if original == target:
        raise ValueError("Refusing in-place replacement of original release")
    if target.exists():
        raise FileExistsError("Output already exists; preserve existing immutable releases")
    if not original.is_file():
        raise FileNotFoundError("Reviewed complete release ZIP not found")
    actual = sha256_file(original)
    if actual.lower() != expected_sha256.lower():
        raise ValueError("Input complete-release SHA-256 mismatch; refusing to package")
    scripts = script_root or Path(__file__).resolve().parent
    extras: dict[str, bytes] = {}
    for archive_name, relative in SMOKE_FILES.items():
        content = (scripts / relative).read_bytes()
        if not content:
            raise ValueError("Empty smoke source: " + relative)
        extras[archive_name] = content
    # No host secrets, approvals, tokens, private URLs or machine names in package metadata.
    smoke_meta = {
        "format": 1,
        "extension_version": expected_version,
        "extension_id": EXTENSION_ID,
        "base_archive_sha256": actual,
        "embedded_sha256": {name: sha256_bytes(data) for name, data in sorted(extras.items())},
    }
    extras["smoke/CAIOS-SMOKE-RELEASE.json"] = (json.dumps(smoke_meta, indent=2, sort_keys=True) + "\n").encode()
    target.parent.mkdir(parents=True, exist_ok=True)
    # Use a task-owned temporary file and only publish it after independent readback.
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".caios-release-", suffix=".zip", delete=False) as f:
            tmp = Path(f.name)
        with zipfile.ZipFile(original, "r") as src, zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as dst:
            checked_members(src)
            validate_release(src, expected_version)
            for info in src.infolist():
                dst.writestr(info, src.read(info.filename))
            for name, data in sorted(extras.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                dst.writestr(info, data)
        with zipfile.ZipFile(tmp, "r") as built:
            members = set(built.namelist())
            if built.testzip() is not None or not REQUIRED.issubset(members):
                raise ValueError("Output archive integrity check failed")
            validate_release(built, expected_version)
            for name, data in extras.items():
                if built.read(name) != data:
                    raise ValueError("Output smoke payload mismatch: " + name)
            if len(members) != len(set(members)):
                raise ValueError("Output duplicate members")
        tmp.replace(target)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()
    return {
        "output": str(target),
        "sha256": sha256_file(target),
        "bytes": target.stat().st_size,
        "extension_version": expected_version,
        "runner_sha256": smoke_meta["embedded_sha256"]["smoke/caios_approved_browser_task.py"],
        "base_archive_sha256": actual,
        "smoke_files": len(extras),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-zip", type=Path, required=True)
    parser.add_argument("--base-sha256", required=True, help="approved digest of exact complete release ZIP")
    parser.add_argument("--version", required=True, help="approved CAIOS extension version")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (len(args.base_sha256) == 64 and all(c in "0123456789abcdefABCDEF" for c in args.base_sha256)):
        parser.error("--base-sha256 must be a 64-character hexadecimal digest")
    print(json.dumps(build_bundle(args.base_zip, args.output, args.base_sha256, args.version), indent=2))


if __name__ == "__main__":
    main()

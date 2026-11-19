# CAIOS Chrome extension: low-cost development and validation

This CAIOS fork retains normal GitHub source control: edit code, commit, push, open/merge pull requests, and release the extension. The inherited upstream Playwright GitHub Actions workflows were removed after excessive usage. Their source remains available in history, but must not be restored without an explicit runner/trigger/cost review.

## Current GitHub Actions policy

Repository-level GitHub Actions is **enabled** only after the five obsolete queued Playwright runs were cancelled. On the main branch, the single executable workflow is [`CAIOS R1 focused regression`](../.github/workflows/caios-r1.yml). A prior temporary R1 workflow is explicitly disabled. The retained workflow:

- Uses **one standard `ubuntu-latest` runner** on this **public** repository, with a **3-minute job timeout**; standard GitHub-hosted runners are free for public repositories.
- Runs only syntax checks and the existing CAIOS R1 Python regression (`tests/caios/test_approved_browser_task.py`).
- Automatically triggers on changes to that workflow, the approved browser task script, or `tests/caios/**` on main and pull requests to main; it also supports deliberate manual dispatch.
- Has no cross-platform matrices, large/xlarge runners, publishing, schedules, artifacts, or inherited Playwright test suites.

**Verification boundary:** The five old queued jobs were individually cancelled and the queue was read back empty before GitHub Actions was re-enabled. Both workflow enabled/disabled states were read back. A manual R1 test dispatch was blocked by the execution tool's safety checks, so **no fresh R1 test result is claimed**. Do not attempt an alternate tool route around an explicit execution denial.

## Local extension build and validation on Forge

The local script is independent of GitHub Actions:

```bash
bash scripts/caios_extension_validate.sh
```

It uses the existing npm install/build/extension-test commands. The current Forge terminal session did not have Node/npm on its PATH, so local build execution remains unverified; inspect the correct development environment and prerequisites before claiming it works. A focused browser-extension installation and interaction check is still needed for release acceptance.

## Mandatory protections for future imports

Apply the ACTIVE CAIOS Creation & Change Playbook mandatory cost preflight before copying/syncing another repository or enabling inherited workflows. Inventory all automated triggers, reusable workflows, runner labels and matrices, budget exposure, publishing, and old queued runs. Disable a newly imported repository's Actions **before** any inherited automation can run. For this already-reviewed repository, keep only the focused R1 workflow; do not restore upstream workflows, add paid runners, switch to a paid fallback, or raise budgets without explicit informed approval. Re-audit after any upstream sync. An unverified imported workflow is a stop condition for actions that might trigger it, **not** a ban on normal code editing and local development.

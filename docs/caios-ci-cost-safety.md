# CAIOS Chrome extension: cost-safe validation

The copied Playwright repository's inherited GitHub Actions workflows were removed from this CAIOS fork after they consumed the account's GitHub Actions overage allowance. The repository's GitHub Actions permission is also disabled at the repository setting level. **Do not re-enable it or restore an inherited workflow without explicit approval of the runner, trigger and estimated cost.**

## Normal validation (no GitHub-hosted runners)

Use the existing Nexus Forge Ubuntu environment, after checking that the task can run there and has the expected Node/npm and browser dependencies:

```bash
bash scripts/caios_extension_validate.sh
```

The script runs the repository's existing `npm ci`, `npm run build`, and `npm run test-extension` commands on that machine, not on GitHub Actions. Install browser prerequisites through the existing documented development setup if required, with no automated paid cloud fallback. For a small change, prefer the smallest focused existing test before a full suite. Browser-extension acceptance still requires an actual installation and focused interaction check; source-only validation is not proof of deployment.

## Restoring any automation

The original upstream workflows remain in Git history and may be reviewed individually. First inventory *all* incoming `.github/workflows` files and reusable workflows; inspect `push`, `pull_request`, `pull_request_target`, `workflow_run`, `schedule`, `workflow_dispatch`, matrix size, runner labels, large/macOS/Windows pricing, upload/publish actions, and duplicate events. Apply the current mandatory CAIOS Creation & Change Playbook source-import preflight. Keep GitHub Actions disabled by default. Re-enable only an explicitly approved narrowly scoped workflow after proving its runner availability, actual no-cost or approved cost route, and maximum spend. No automatic hosted-runner fallback.

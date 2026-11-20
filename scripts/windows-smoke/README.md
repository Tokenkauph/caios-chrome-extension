# CAIOS Chrome Extension — Windows acceptance tests

This folder is bundled by [package_caios_windows.py](../../scripts/package_caios_windows.py). It uses the **single canonical Python browser runner** and the matching forked Node/Playwright MCP from the installed CAIOS release. Do not invent a per-host controller.

## Required for every new extension installation: real-world acceptance

After verifying the extension is installed, enabled and paired with the exact Chrome profile and matching controller, use **run-acceptance.ps1**. It must run in the interactive session of the installed user's Chrome profile. Prepare scripts, dependencies and diagnostic logging **before** any browser tab consent or visible desktop interruption. Do not unexpectedly launch or focus windows on an occupied desktop.

The user is free to approve **any one website tab** in the CAIOS Chrome picker. The tab's original title or URL is not a constraint; **never require Example Domain, MSN or Google as the starting tab**. One tab only is required for this test. Nothing is approved by merely running the script.

From normal PowerShell on the target Windows user session:

```powershell
& "$env:LOCALAPPDATA\CAIOS\ChromeExtension\v0.5.0.3\smoke\run-acceptance.ps1" -Profile Default
```

Change the versioned installation path and `-Profile` to the actual installed release and Chrome profile. Python 3 is a prerequisite; the ZIP bundles the matching Node/MCP but not Python. The launcher checks release identity, prefers the actual user-local Python installation over Windows Store aliases, generates a task-owned plan with the **actual** computer name and current form date, switches the MCP working directory to the bundled harmless upload fixture, and starts exactly one canonical runner. It does **not** open Chrome, select a tab automatically, bypass consent, or create a background service.

Once the user chooses one tab and clicks **Connect selected tabs**, this single process immediately:

1. Opens **https://www.msn.com/** and verifies the first website.
2. Opens **https://en.wikipedia.org/wiki/European_badger** and verifies the second website.
3. Uses the real browser **Back** action, and verifies that the first MSN website is visible again.
4. Navigates to the public [Selenium web form](https://www.selenium.dev/selenium/web/web-form.html), inspects its controls and takes a snapshot.
5. Fills all editable control families with **dummy data**: text, dummy password, textarea, select dropdown, datalist, both checkboxes, alternate radio, date picker, color input, range slider, and bundled harmless file upload. It verifies each field/group independently and confirms disabled, read-only and hidden inputs were not altered.
6. Clicks **Submit** and independently verifies the real submitted-form page displays **Received!**.

This 39-step plan exercises navigation across sites, Back/history, interactive input, upload and submission in an ordinary user-authorized tab. The successful submission page remains visible; this suite deliberately has `restore_original_url: false`. A task that is specifically meant to restore the starting URL should use a different explicitly authorized plan. The runner always releases its own MCP client after success or failure; it does not close Chrome.

**PASS criteria:** An actual approved tab is attached and verified; both distinct sites load; browser Back returns to the first; all 39 primary actions emit `ACTION_DONE`, including all form checks and the submission confirmation; `TASK_COMPLETED` reports 39/39 with zero cleanup failures; `TASK_SESSION_RELEASED` occurs; runner exit code is 0. A launch, browser picker, mock-unit-test PASS or partial form fill **does not count**. Record precise failures and keep any connection/error logs local, without publishing private starting URLs or credentials.

## Optional troubleshooting only: simple public-page smoke

`run-smoke.ps1` and `caios-example-domain-smoke.template.json` remain for targeted diagnostics and historical comparison, **not as the installation acceptance gate**. That legacy test intentionally requires a disposable `https://example.com/` tab. The restriction is specific to that legacy fixture, not the normal browser controller or standard full acceptance.

The November 19, 2026 Quantum Haze historical receipt recorded a successful 3-step host-local smoke (with two local corrections). The old published `v0.5.0.3-smoke.1` ZIP predates the new mandatory suite, even if it is still present on a host. A newly built bundle from the reviewed source will have the full suite; do not treat source publication as installed/working on any machine.

**Owners:** [CAIOS Engineering #201](https://github.com/Tokenkauph/caios/issues/201), [complete Windows install guide](../../docs/windows-host-install-and-acceptance.md), and [canonical runner instructions](../../scripts/README.md).

# CAIOS browser approval-priority task runner

**Scope:** All CAIOS Chrome Extension tasks routed by CAIOS Engineering, in every conversation and on any specifically authorized machine/profile. This is not a conversation-specific benchmark workaround. It reuses existing Chrome/MCP consent; it does not grant access, register a native ChatGPT Tool, or bypass approval.

## Mandatory new-install live acceptance (not the old 3-step smoke)

Every **new CAIOS Chrome extension installation**, including new Windows VM/desktop hosts and supported Linux hosts, requires a real-user-tab full browser acceptance before its status is called **working**. The same canonical runner, not a separate per-host implementation, must:

1. Accept **one tab actually selected in Chrome's picker**, regardless of starting website/title.
2. Navigate to **MSN**, verify it, navigate to **Wikipedia**, verify it, then perform a real browser **Back** and verify the first MSN page.
3. Open the public **Selenium Web Form**, fill and independently verify text, dummy password, multiline, dropdown, datalist, checkboxes, radio, date, color, slider and dummy-file upload; confirm disabled/read-only fields were preserved.
4. **Submit the form** and verify the submitted page says **Received!**, then release the task-owned browser client.

The standardized, packaged Windows implementation is [`windows-smoke/run-acceptance.ps1`](windows-smoke/run-acceptance.ps1) with the [39-action cross-site test plan](windows-smoke/caios-install-acceptance.template.json) and harmless bundled upload. The real user's approved starting tab is never pinned to `example.com`; the final confirmation page remains visible (no automatic starting-URL restore). Source tests and a bundle build alone are not proof of live acceptance. Record approved-tab attachment, 39/39 actions, submission confirmation, zero cleanup failures, client release and runner exit code 0. For Linux, reuse the same plan and canonical runner with the actual host/profile and local upload path; do not fork the acceptance semantics.

The old `run-smoke.ps1` Example Domain test is **optional troubleshooting**, retained for historical comparison, not the new-install acceptance gate. New bundles include both, and only the full acceptance counts as a complete new-host browser validation.

**Updated blank-tab source behavior (not yet live accepted):** After the user selects the built-in Chrome New Tab, the extension converts that **same** approved tab to `about:blank`. The shared runner parses the blank URL and permits it only when original-URL restoration is disabled. Chrome settings and other internal pages remain excluded; tab consent and unique identity checks are unchanged. This does not retroactively change previously installed packages.

## Windows onboarding: use the same tested runner

**Verified QUANTUMHAZE Windows acceptance — November 19, 2026 (22:03 ET):** Existing CAIOS v0.5.0.3 / Chrome `Default` profile completed **MCP tab attachment, approved Example Domain (`https://example.com/`) snapshot, navigation to `https://example.org/`, destination snapshot, original URL restore and task-client release (3/3 steps, exit 0, zero cleanup failures)**. [Verified receipt](https://github.com/Tokenkauph/caios/issues/201#issuecomment-7029072376). This does **not** establish a native ChatGPT Tool, unattended startup, or Plex acceptance.

**Source vs deployed state:** The verified Quantum Haze `smoke/run-smoke.ps1` was locally adjusted to select the installed user Python 3.14 binary before Windows Store aliases and save a preflight transcript (`smoke/run-smoke-latest.log`). Its local test JSON was simplified to **snapshot → navigate → snapshot** because a redundant `browser_evaluate` assertion returned an error. **Those locally proven changes are not yet part of the published `v0.5.0.3-smoke.1` ZIP nor this repo's packaged launcher/plan source.** Sync and verify changes before a new release; do not claim the old ZIP was end-to-end accepted. [Windows guide](../docs/windows-host-install-and-acceptance.md).

**Coordination during live use:** Prepare source, task and exact host/profile off-screen. The user chooses which Chrome tab to approve. An Example Domain requirement is only for a separately agreed public smoke test, never a default for normal browsing. Immediately before any approved visible desktop focus interruption, identify the exact host/window. Execute the prepared launch immediately and verify foreground handle/PID before every typing/Enter action; stop if focus shifted. A desktop-control lease is not consent to surprise the user while they are working or playing. The same controller automatically runs the already-prepared steps after Chrome approval, and releases only the owned session.


For each additional Windows computer, follow the [single repeatable Windows install and live acceptance guide](../docs/windows-host-install-and-acceptance.md). It covers the versioned complete ZIP, checksum and correct Chrome profile, the CAIOS-specific extension ID, the existing shared runner, public test-tab consent, exact pass markers, cleanup and failure diagnosis. **Do not write a new one-off browser test script for each host.** A host-local Playwright PASS is not evidence that a native ChatGPT browser-control Tool was registered.

## Build the reusable Windows release (same runner on every host)

The previously created complete Windows ZIP contains the extension and forked Node/MCP only. The reviewed packager in [package_caios_windows.py](package_caios_windows.py) adds **the exact current canonical Python runner**, the required cross-site and full-form acceptance plan/launcher/dummy upload, the optional historical Example Domain quick smoke, their instructions, and checksummed package metadata, preserving the original complete ZIP unmodified. It **does not** create a new extension implementation, install Python, automatically start Chrome, or register a remote ChatGPT Tool.

After separately verifying the input complete release and its approved SHA-256, run the same packager on the build host (example for the Nov 19 v0.5.0.3 bundle; adjust paths to the actual release):

~~~bash
python3 scripts/package_caios_windows.py \
  --base-zip /path/to/verified/caios-chrome-windows-v0.5.0.3-complete.zip \
  --base-sha256 21b2fa235e4d833bc04a25e1f6382810ca2b75e95c832cd30cbb5040bfb25c3f \
  --version 0.5.0.3 \
  --output /path/to/release/caios-chrome-windows-v0.5.0.3-with-smoke.zip
~~~

The packager rejects a bad digest, incomplete or mismatched CAIOS release, unsafe/duplicate archive paths, already-bundled smoke tooling, and an existing output path. It re-verifies its own ZIP after creation, compares the embedded files byte-for-byte with this repository's canonical sources, and outputs its **new SHA-256** for subsequent host transfer verification. Do not use the **old input archive checksum** to validate the enhanced output ZIP.

**Windows use:** the enhanced ZIP has a smoke/ directory; after registering and verifying the unpacked extension in the intended Chrome profile, open **any website tab of the user's choice** and run `smoke/run-acceptance.ps1` with the real `-Profile` name for the mandatory 39-step end-to-end acceptance. It selects Python 3 already installed on that host, prepares a temporary plan containing the actual computer name/profile, and launches the bundled exact canonical runner. User consent still selects one tab. See the [complete Windows procedure](../docs/windows-host-install-and-acceptance.md). Python 3 is a declared Windows runtime prerequisite; do not invent a second Node browser runner to hide it.

## Just-in-time control on a shared, actively used desktop

**The Chrome tab approval and the Windows foreground-console interruption are different events.** Complete host/script/package/version checks before asking to focus or open PowerShell. When a visible launch is truly necessary, tell Ryan the exact target computer/window and that they may choose any one website tab in Chrome's consent picker **immediately before** the prepared launch; aim to initiate within 10 seconds of the ready signal (not a guaranteed platform timer). Never return several minutes later and unexpectedly open a window or type under an earlier broad task approval. If delayed, abort that foreground attempt and coordinate another brief interruption when actually ready; do not repeat approval for the whole task. Before typing or Enter, independently check the foreground target. If the user switched to another application, stop rather than auto-refocus or send blind input. Release task-owned desktop control promptly. Prefer a supported non-foreground host execution route when it achieves the same authorized purpose.

After the single task-owned MCP client is already waiting, the user's **actual choice of the specific Chrome tab** is the browser consent event; do not substitute a preselected website. Once the matching client returns that approved tab, the existing prepared runner immediately acts and releases its own session. The 900-second browser attachment wait is **not** permission to queue delayed Windows foreground input or to leave a live window takeover open. Preserve selected-tab consent and the current owner/host boundaries.

## Mandatory order for every approved browser operation

1. **Before requesting consent**, prepare exact host, Chrome profile, CAIOS extension and matching forked client; do not require a predetermined tab website for ordinary tasks, complete authorized operation, and cleanup/recovery steps. Finish all unrelated GitHub/docs/Neon checks **before** opening the consent picker.
2. **One task-owned MCP client and one approval:** start the shared runner with a prebuilt plan; it initiates browser_tabs(action=list) and waits for the selected tab. The extension picker may refresh tabs opened later; it never grants access automatically.
3. **Approval has exclusive priority:** when MCP returns the approved tab, verify its unique attached-tab identity/current index (and validate a specified URL/title only in an explicitly pinned test), then **immediately execute the prepared actions in the same process**, without another chat message or terminal instruction. No unrelated work between consent and operation.
4. **Status/timeout:** default 900 seconds for task-side approval and attachment, replacing the temporary test harness's 180 seconds. Print a progress event every 15 seconds. A timeout means **MCP did not confirm tab attachment**; never assert the user failed to approve. Do not start an unrequested second approval or bypass tab consent.
5. **After the task:** release only the task-owned client, verify results, then reconcile documentation. Existing Chrome tabs/profiles and Microsoft's independent extension remain intact.

This runner is a shared implementation for deterministic, preplanned operations. Interactive exploratory tasks needing decisions after a page read must **keep the approved connection** and immediately perform the next authorized step before any other work. Do not claim a source commit is installed on every endpoint; deploy a reviewed runner separately to each host.

## Plan and command

Plan JSON, authored for a **specific already authorized** task:

~~~json
{
  "contract_version": "1",
  "machine": "nexus-forge",
  "profile": "Default",
  "extension_id": "kanpfbepfgcpmjoeaaihigjkcdjejbld",
  "tab_selection": "user_selected",
  "restore_original_url": false,
  "steps": [
    {"name": "inspect", "tool": "browser_evaluate",
     "arguments": {"function": "() => ({title:document.title,url:location.href})"}}
  ],
  "finally_steps": []
}
~~~

The example does **not** grant access to any account. The user's actual browser-picker selection, task authorization and exact machine/profile control. For ordinary tasks, omit `expected_title` and `expected_url_prefix`: the default is `user_selected`. The runner accepts the **one approved tab** regardless of its title, starting URL or site. If zero, multiple, or crashed tabs are returned, it stops rather than guessing. Legacy plans that explicitly supply expected title/URL retain `pinned` matching, and a plan may explicitly set `tab_selection: pinned`. Use title/URL pinning only when the **user's task itself** requires that starting website, such as a designated public smoke fixture. The user's selected tab may be on any supported HTTP(S) site; don't print or store its private starting URL in public receipts. Plan steps must be prepared and validated before consent.

Run with OS-local paths and exact task-owned files:

~~~bash
python3 scripts/caios_approved_browser_task.py \
  --plan /path/to/approved-task-plan.json \
  --node /path/to/node \
  --mcp-entry /path/to/CAIOS-fork/playwright-core/lib/entry/mcp.js \
  --browser-executable /path/to/chrome \
  --stderr-log /path/to/task-owned-stderr.log
~~~

The runner requires the **forked CAIOS MCP** and exact extension ID, not the official Microsoft MCP. It clears the shortcut approval token from its child environment; no stored token or cross-profile bypass. It verifies the machine, chooses exactly one approved tab index, explicitly selects that tab, and independently verifies it is active before executing any primary action. Set `restore_original_url: true` only for a task that explicitly authorizes restoring the starting tab URL; the runner captures the URL and conditionally restores it after known outcomes, then runs any `finally_steps` checks. If an MCP call never answers, the page state is unknown and conflicting restoration is skipped. On a returned navigation error the runner checks the actual destination and DOM readiness before deciding whether the action succeeded. Separate primary/cleanup counts, phase timings, stable redacted connection errors and accurate failure events are reported without echoing private page content. Keep task-owned stderr logs private, because they can contain connection details.

**Timeout distinction:** the 900-second setting is a **task-side** waiting budget and does not change Chrome consent expiration or OpenAI's tool lifetimes. Progress every 15 seconds is not an event delivered independently to ChatGPT; the host-side runner proceeds immediately on actual MCP tab return. No standing daemon or background scheduler is installed.

**Tests:** `python3 -m unittest discover -s tests/caios -p test_approved_browser_task.py -v` verifies prearmed execution, actual Playwright tab-list format, unique explicit selection, known versus unanswered navigation, conditional restore, failure reporting and process/relay exit. `node --test tests/caios/*.test.mjs` includes the existing ten CAIOS tests and the bounded broker retry tests. Browser/extension full integration and signed-in six-step acceptance are separate later checks. The production v0.5.0.2 CAIOS extension and original Microsoft extension remain installed until an authorized replacement is independently verified.

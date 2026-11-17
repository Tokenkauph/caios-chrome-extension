# CAIOS browser approval-priority task runner

**Scope:** All CAIOS Chrome Extension tasks routed by CAIOS Engineering, in every conversation and on any specifically authorized machine/profile. This is not a conversation-specific benchmark workaround. It reuses existing Chrome/MCP consent; it does not grant access, register a native ChatGPT Tool, or bypass approval.

## Mandatory order for every approved browser operation

1. **Before requesting consent**, prepare exact host, Chrome profile, pre-opened target tab, CAIOS extension and matching forked client, complete authorized operation, and cleanup/recovery steps. Finish all unrelated GitHub/docs/Neon checks **before** opening the consent picker.
2. **One task-owned MCP client and one approval:** start the shared runner with a prebuilt plan; it initiates browser_tabs(action=list) and waits for the selected tab. The extension picker may refresh tabs opened later; it never grants access automatically.
3. **Approval has exclusive priority:** when MCP returns the approved tab, validate its exact title/URL and **immediately execute the prepared actions in the same process**, without another chat message or terminal instruction. No unrelated work between consent and operation.
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
  "expected_title": "Google",
  "expected_url_prefix": "https://www.google.com/",
  "restore_original_url": false,
  "steps": [
    {"name": "inspect", "tool": "browser_evaluate",
     "arguments": {"function": "() => ({title:document.title,url:location.href})"}}
  ],
  "finally_steps": []
}
~~~

The example is **not** blanket approval to access Google or any account. User authorization, exact machine/profile and selected tab still control. Plan steps must be prepared and validated before consent.

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

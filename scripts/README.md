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

The runner requires the **forked CAIOS MCP** and exact extension ID, not the official Microsoft MCP. It clears the shortcut approval token from its child environment; no stored token or cross-profile bypass. It verifies the machine, profile selection and exactly one matching returned title/URL before any action. All actions are preapproved, and optional finally_steps handle in-scope recovery if a step fails. Console events report steps and timings but not page contents. Keep task-owned stderr logs private, because they can contain connection details.

**Timeout distinction:** the 900-second setting is a **task-side** waiting budget and does not change Chrome consent expiration or OpenAI's tool lifetimes. Progress every 15 seconds is not an event delivered independently to ChatGPT; the host-side runner proceeds immediately on actual MCP tab return. No standing daemon or background scheduler is installed.

**Tests:** python3 -m unittest discover -s tests/caios -p test_approved_browser_task.py -v tests immediate preloaded action after fake consent, host/tab rejection, and periodic wait/timeout. This does not prove a new production signed-in browser acceptance or measured speed gain. Preserve the accepted v0.5.0.2 extension and Microsoft extension as installed.

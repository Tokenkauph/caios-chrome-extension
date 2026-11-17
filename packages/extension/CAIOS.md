# CAIOS Chrome Extension — build and controlled acceptance

**Owner:** [CAIOS Engineering #201](https://github.com/Tokenkauph/caios/issues/201), Remote Management & Endpoint Agent → shared Chromium browser integration. This fork is based on Microsoft Playwright's open-source extension; preserve Microsoft source copyrights and Apache-2.0 notices. Development baseline: merged fork PRs #1 and #2; current GitHub main contains the independent CAIOS extension ID and companion client source.

## Why this fork exists

The official Microsoft extension is already verified on the physical Nexus Forge Ubuntu machine for independently chosen Chrome profiles: Ryan/RStires = `Default` and Tokenkauph = `Profile 1`. The official extension successfully controlled existing tabs for Wikipedia, MSN, a public Selenium form, Instagram, and a Gemini conversation including one authorized story continuation. However, multiple attempts to select the original `chatgpt.com` story tab stalled before `browser_tabs` returned its contents. **Cause still unknown**; do not claim ChatGPT blocks the extension, or that this fork fixes the issue without a real acceptance test.

## Prototype changes

- CAIOS development identity and clearer connection phases in the extension's consent window: request registration → available tab choices → user approval → local relay/tab attach; an **informational** notice after 12 seconds when approval is accepted but connection remains pending. Genuine errors are displayed with the phase that failed. No browser data, tabs, relay URLs, auth tokens or messages are logged to a new store.
- Companion Playwright core change: best-effort `browser_tabs list` has bounded waits (4 seconds for initializing the current tab; 3 seconds per title/console header), returning a URL with a visible missing-title label instead of indefinitely blocking the whole tab list. This is a **candidate workaround** for stalled CDP title/initialization calls, related to upstream [Playwright issue #43842](https://github.com/microsoft/playwright/issues/43842); it is **not proof** that the specific ChatGPT outage was caused by that issue.
- Seven dependency-free tests: three bounded tab-initialization/title cases and four extension-ID/default/override/invalid-ID cases. The fallback and selectable ID apply only to **CAIOS forked Playwright core**, not the installed stock `@playwright/mcp`.

## Build and tests

Use the local Node.js >=20 toolchain (on Forge, the existing `~/Caios/Tools/node/24.22.3/bin`). A normal checkout with workspaces may use the upstream root `npm ci` first, then:

```bash
cd packages/extension
npm run build
```

The Vite build emits `packages/extension/dist/` containing the extension manifest, `connect.html`, `manage.html`, UI bundles and background worker. For isolated helper tests from the repository root with Node 24:

```bash
node --test tests/caios/bounded-tab.test.mjs
```

On the verified Forge P0 task, dependencies were installed in a disposable **task-local** directory instead of modifying global Node/npm or unrelated CAIOS installations; the extension Vite build and both extension TypeScript projects passed. Build success is not browser acceptance.

## Extension identity / stock compatibility boundary

**Development extension ID:** `kanpfbepfgcpmjoeaaihigjkcdjejbld`. The CAIOS manifest now contains a distinct **public** RSA key, so an unpacked CAIOS build has a stable ID **different** from Microsoft's Web Store extension `mmlmfjhmonkocbjadbfplnigmagldckm`. The development public key was generated locally; its private test key was intentionally **discarded without storage**, so no CRX signing/release key is established. For future packaging or Web Store publishing, choose a durable independently managed release identity. **This ID does not authorize installation or browser control.**

The stock installed `@playwright/mcp` still targets Microsoft's extension by default. A **built CAIOS companion client from this fork** must use `CAIOS_PLAYWRIGHT_EXTENSION_ID=kanpfbepfgcpmjoeaaihigjkcdjejbld` (and the required explicit `--extension --profile-dir-name=...`) to target the CAIOS fork; the upstream/default ID remains intact when the env var is absent. The forked MCP client has now been **compiled and accepted against this extension in a disposable, unsigned-in test Chromium profile** (details below). The installed stock client remains unchanged. Merely setting the environment variable on stock `@playwright/mcp` **does not add support**; neither the CAIOS extension nor its client is installed as a native ChatGPT browser Tool.

The CAIOS and Microsoft extensions can have separate IDs in a single Chrome profile, but the candidate is **not yet installed or verified** in Ryan's `Default` or Tokenkauph's `Profile 1`. Only the user should approve Chrome installation and the exact selected tab; preserve the official working extension. Chrome authentication tokens are still distinct per **Chrome profile and extension**. Never publish private authentication material in GitHub.

## Verified companion-client acceptance — Nexus Forge, November 17, 2026 ET

**PASS — CAIOS forked MCP ↔ CAIOS extension ↔ approved disposable test tab.** This is real integration evidence, beyond a source compile or unit-test result. It is **not** an acceptance of signed-in `chatgpt.com` or of production installation.

1. From the separate CAIOS GitHub fork, installed npm workspace dependencies only into the task-local checkout and ran `node utils/build/build.js --disable-install`. The upstream monorepo build later stopped on an unrelated web-dashboard `codemirror` dependency, but **the forked `packages/playwright-core/lib/coreBundle.js`, `utilsBundle.js`, `tools/utils/extension.js`, and `entry/mcp.js` had already compiled**. The generated client started, replied to MCP JSON-RPC `initialize` with `Playwright 1.66.0-next`, and advertised the expected browser tools.
2. Used a **disposable, unsigned-in Chromium** profile on physical Nexus Forge Ubuntu and loaded the unpacked CAIOS `packages/extension/dist/`. Chrome's developer tools confirmed the exact CAIOS extension service worker at `chrome-extension://kanpfbepfgcpmjoeaaihigjkcdjejbld/lib/background.mjs`. Microsoft's and Ryan's already-installed Chrome extensions/profiles were not modified. Branded Chrome 157 would not load an unpacked extension from the deprecated `--load-extension` switch; per [Playwright's official extension-testing guidance](https://playwright.dev/docs/chrome-extensions) the test instead used bundled Chromium.
3. Spawned the **forked** `packages/playwright-core/lib/entry/mcp.js` with `CAIOS_PLAYWRIGHT_EXTENSION_ID=kanpfbepfgcpmjoeaaihigjkcdjejbld`, an explicit disposable `--user-data-dir`, `--profile-dir-name=Default`, and the disposable Chromium executable. The test launcher had to preserve a process-local Chromium `--no-sandbox` flag because this Ubuntu host does not allow the downloaded test Chromium to initialize its sandbox. That setting was **restricted to offline, unsigned-in, task-owned test Chromium**; do not carry it into the production browser configuration. No permanent browser service or extension token was configured.
4. In the isolated test browser, the CAIOS connection page listed the **exact** `CAIOS Disposable Chromium` dummy `data:` tab. The test harness programmatically checked **only that tab** and clicked the test approval button. The first synthetic relay URL had an erroneous trailing period copied from a diagnostic log and returned a WebSocket error; after correcting the harness URL, the approval succeeded and the test consent page closed. That punctuation error is a **test-harness defect**, not evidence of an extension or ChatGPT bug. Do not use synthetic approval in real signed-in profiles; **the actual user must approve each intended tab**.
5. The actual forked MCP returned `browser_tabs(action=list)` with the **approved dummy tab title/URL**; `browser_snapshot` read the heading `CAIOS disposable profile`; `browser_evaluate` confirmed title, URL and body content; it created a harmless input; `browser_type` filled `CAIOS handshake pass`; an independent `browser_evaluate` read back that exact input value. **Tab discovery, DOM read, input interaction and readback PASS.**
6. Closed the test-owned MCP client and confirmed there were no active task-owned MCP processes. Stopped both disposable browser instances; verified no process remained attached to either test profile. The task-local source and compiled bundles were preserved for later authorized tests, while the user's signed-in Chrome data, windows and the official Microsoft Playwright extension remained untouched.

**Boundaries:** There is **no measured end-to-end latency improvement**, and the `browser_tabs` fallback is **not yet verified against a deliberately stalled real tab**. The original ChatGPT conversation has **not** been read, scrolled or modified by this CAIOS fork. No durable CAIOS Tool/connector has been registered with ChatGPT; Microsoft Playwright remains the accepted human-browser operating route until explicit installation and actual signed-in tab acceptance.

**Test-only operational note:** The upstream full-workspace build failing on unrelated `codemirror` does **not** invalidate the compiled core client that was actually exercised, but a reproducible targeted build/package command and clean whole-workspace CI remain future release tasks. Do not mistake a successful local executable for a deployed/updatable package.

## Next end-to-end acceptance

1. Keep the **working Microsoft extension and both Chrome profiles** unchanged. If Ryan explicitly approves an installation into a specified profile, use Chrome Developer Mode → Load unpacked for the verified CAIOS development build (different extension ID), and connect with the matching compiled CAIOS MCP client using the correct machine/profile/tab. Do not silently install it into `Default` or `Profile 1`.
2. With specific approval for the original throwaway `chatgpt.com` wizard-story tab, reproduce the connection there, distinguish extension consent/relay from `browser_tabs` title/initialization, and verify real read, scroll, prompt submission and generated response. Only declare the ChatGPT problem fixed on actual evidence.
3. Measure connection start, consent, tab listing and first action; simplify the tested launcher and package only after observing real bottlenecks. Test simultaneous profile clients separately and preserve per-profile, per-tab authorization.
4. For a distributable release, provide a repeatable targeted forked MCP build, independently maintained extension signing/update identity if packaging CRX, version compatibility tests and rollback. Do not activate a standing controller, copy site tokens or register a native ChatGPT Tool without its own approval.
**Source publication != installed extension != working ChatGPT tab != registered ChatGPT Tool.** Existing [Engineering Playwright operating guide](https://github.com/Tokenkauph/caios/blob/183afcdde496b52421527093c92b42af0380f4eb/docs/ops/playwright-human-chrome.md) remains the current verified host route until this fork is installed/accepted and Core routing is reconciled.

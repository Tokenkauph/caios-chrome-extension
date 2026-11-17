# CAIOS Chrome Extension — build and controlled acceptance

**Owner:** [CAIOS Engineering #201](https://github.com/Tokenkauph/caios/issues/201), Remote Management & Endpoint Agent → shared Chromium browser integration. This fork is based on Microsoft Playwright's open-source extension; preserve Microsoft source copyrights and Apache-2.0 notices. Current branch: `caios/p0-chatgpt-connection-diagnostics`.

## Why this fork exists

The official Microsoft extension is already verified on the physical Nexus Forge Ubuntu machine for independently chosen Chrome profiles: Ryan/RStires = `Default` and Tokenkauph = `Profile 1`. The official extension successfully controlled existing tabs for Wikipedia, MSN, a public Selenium form, Instagram, and a Gemini conversation including one authorized story continuation. However, multiple attempts to select the original `chatgpt.com` story tab stalled before `browser_tabs` returned its contents. **Cause still unknown**; do not claim ChatGPT blocks the extension, or that this fork fixes the issue without a real acceptance test.

## Prototype changes

- CAIOS development identity and clearer connection phases in the extension's consent window: request registration → available tab choices → user approval → local relay/tab attach; an **informational** notice after 12 seconds when approval is accepted but connection remains pending. Genuine errors are displayed with the phase that failed. No browser data, tabs, relay URLs, auth tokens or messages are logged to a new store.
- Companion Playwright core change: best-effort `browser_tabs list` has bounded waits (4 seconds for initializing the current tab; 3 seconds per title/console header), returning a URL with a visible missing-title label instead of indefinitely blocking the whole tab list. This is a **candidate workaround** for stalled CDP title/initialization calls, related to upstream [Playwright issue #43842](https://github.com/microsoft/playwright/issues/43842); it is **not proof** that the specific ChatGPT outage was caused by that issue.
- Three dependency-free tests: resolved title, indefinitely pending title, rejected title. This fallback is only in the **forked Playwright core source** and **does not affect the separately installed stock @playwright/mcp** until a compatible CAIOS client is built and admitted.

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

**Important:** The fork currently retains Microsoft's original public `manifest.key` to remain compatible with upstream Playwright MCP, which hardcodes extension ID `mmlmfjhmonkocbjadbfplnigmagldckm` in `packages/playwright-core/src/tools/utils/extension.ts`. **Do not load this prototype into the same Chrome profile as the official Web Store extension: their IDs conflict.** For tests, use only an isolated disposable Chrome profile/browser, not Ryan's `Default` or Tokenkauph's `Profile 1`.

Before the independent CAIOS extension can coexist with the official one, create and retain a **distinct CAIOS extension signing identity**, and update/build the corresponding CAIOS MCP/client launcher to target that exact new ID. Verify separate installation, explicit host → profile → user-selected tab consent, version compatibility, and uninstall/rollback. Never publish a secret private signing key in GitHub. Do **not** remove or replace the working official extension without a separate user-approved browser installation/replacement decision. Chrome UI permission remains Ryan's action.

## Next end-to-end acceptance

1. With the actual user's permission, reproduce original ChatGPT web-tab selection on Forge's exact intended Chrome profile. Inspect the extension approval page and Manage clients, relay handshake and `browser_tabs` response; differentiate failure before connection vs a tab header request that stalls afterward.
2. Build a compatible CAIOS MCP client with the forked core fallback and **run it against an isolated test Chrome profile** before any user-profile install. Use an authorized existing tab with a deliberately unresolved title in tests if feasible. Check fallback returns URL without waiting indefinitely and never changes another profile or unselected tab.
3. Obtain Chrome's explicit permission for a candidate side-by-side CAIOS extension after its unique ID is established. Repeat the actual signed-in ChatGPT story read/scroll/submit test; preserve the official extension until real acceptance and rollback are verified.
4. Measure connection latency (MCP start, approval, tab list, first action). Reuse an authorized session for multiple actions. Do not quietly enable per-profile tokens or a persistent cross-account service.

**Source publication != installed extension != working ChatGPT tab != registered ChatGPT Tool.** Existing [Engineering Playwright operating guide](https://github.com/Tokenkauph/caios/blob/183afcdde496b52421527093c92b42af0380f4eb/docs/ops/playwright-human-chrome.md) remains the current verified host route until this fork is installed/accepted and Core routing is reconciled.

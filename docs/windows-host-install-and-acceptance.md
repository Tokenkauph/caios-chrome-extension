# CAIOS Chrome Extension — repeatable Windows install and acceptance

## CURRENT — accepted reusable Windows package (November 20, 2026)

**Preferred for future Windows hosts:** [CAIOS Chrome Windows v0.5.0.3 full 39-step acceptance bundle (`acceptance.1`)](https://github.com/Tokenkauph/caios-chrome-extension/releases/tag/caios-chrome-windows-v0.5.0.3-acceptance.1). [Direct verified ZIP asset](https://github.com/Tokenkauph/caios-chrome-extension/releases/download/caios-chrome-windows-v0.5.0.3-acceptance.1/caios-chrome-windows-v0.5.0.3-blank-tab-backready-642a9de-acceptance.zip).

- **Asset:** `caios-chrome-windows-v0.5.0.3-blank-tab-backready-642a9de-acceptance.zip`; **37,329,059 bytes**, 83 members, independently downloaded and hash-checked against the reviewed build.
- **SHA-256:** `b0bdddf55735016d7131ffb693d94cbbd4e548077c120be3b8bab66d8a2d4b01`.
- **Stable CAIOS ID:** `kanpfbepfgcpmjoeaaihigjkcdjejbld`, version `0.5.0.3`; extension source commit `7c21a135554f55c27a9b5adf08c0a2e0d322ba50` (PR #22); **canonical runner** source `642a9decdc649177e23cbd0e4fd66741fa2a85b6` (PR #23), installed runner SHA-256 `e8ae308c0f143115974db88ce2c3f37ccde018550ba315b125ec197393935063`.
- **Included:** `extension/`, matching `playwright-core/lib/entry/mcp.js`, Windows `runtime/node.exe` v24.22.3, bundled `smoke/run-acceptance.ps1`, 39-action plan, shared Python runner, dummy-file test fixture, optional earlier 3-action diagnostic, SHA/checksum metadata. **Host prerequisite:** installed Python 3 and Chrome; the ZIP does not silently install those, enable Chrome, bypass tab approval, register a new ChatGPT Tool or create an unattended service.
- **Live evidence:** [Nexus Forge Windows Development VM (`NEXUS-FORGE-DEV`, user `nexus`, Chrome `Default`) completed 39/39, public Selenium `Received!`, `TASK_COMPLETED`, `TASK_SESSION_RELEASED`, exit 0, Windows Task Scheduler result 0 at 12:03:28 ET](https://github.com/Tokenkauph/caios/issues/201#issuecomment-7045621864). The previous 5/39 Back-readiness failure was corrected by runner PR #23. Other hosts are **not** automatically accepted. The successful summary receipt verifies one approved tab but does **not** independently record whether that user's starting tab was blank; blank-tab handling is supported by source and needs no pinned starting website.

### Repeatable future Windows host install — actual supported route

1. **Preflight:** Identify the actual Windows hostname, logged-in user and Chrome profile directory (`chrome://version` → Profile Path). Confirm approved machine/Tool or manual transfer route, Chrome, Python 3 (`py -3 --version` or `python --version`), and whether Chrome is already using another CAIOS installation. Do not infer a Windows Desktop agent from a working Forge SSH guest.
2. **Acquire the whole package** from the release above, rather than copying only `extension/`, an old `smoke.1` ZIP, or task scratch. Verify **this exact archive's SHA-256**. Use a fresh user-local version folder, retaining prior versions for rollback:

   ~~~powershell
   $zip = Join-Path $env:USERPROFILE 'Downloads\caios-chrome-windows-v0.5.0.3-blank-tab-backready-642a9de-acceptance.zip'
   $expected = 'B0BDDDF55735016D7131FFB693D94CBBD4E548077C120BE3B8BAB66D8A2D4B01'
   if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $expected) { throw 'Wrong full Windows ZIP' }
   $root = Join-Path $env:LOCALAPPDATA 'CAIOS\ChromeExtension\v0.5.0.3-acceptance.1'
   if (Test-Path -LiteralPath $root) { throw 'Version exists: inspect it, do not overwrite' }
   Expand-Archive -LiteralPath $zip -DestinationPath $root
   $release = Get-Content (Join-Path $root 'CAIOS-RELEASE.json') -Raw | ConvertFrom-Json
   if ($release.extension_id -ne 'kanpfbepfgcpmjoeaaihigjkcdjejbld' -or
       $release.extension_fork_commit -ne '7c21a135554f55c27a9b5adf08c0a2e0d322ba50' -or
       $release.acceptance_runner_fork_commit -ne '642a9decdc649177e23cbd0e4fd66741fa2a85b6') { throw 'Wrong package provenance' }
   if ((Get-FileHash (Join-Path $root 'smoke\caios_approved_browser_task.py') -Algorithm SHA256).Hash -ne 'E8AE308C0F143115974DB88CE2C3F37CCDE018550BA315B125EC197393935063') { throw 'Wrong runner' }
   & (Join-Path $root 'runtime\node.exe') --version
   ~~~

3. **Register user-selected extension only:** In the correct user's actual Chrome profile open `chrome://extensions`, enable Developer mode and **Load unpacked** from `$root\extension`; confirm **CAIOS Chrome Extension** v0.5.0.3, exact stable ID, enabled. If the same CAIOS extension is already registered to an older folder, replace **only its prior CAIOS Chrome registration** with the new folder while preserving the previous files; do **not** remove the unrelated Microsoft Playwright extension or other profiles. Chrome registration for an unpacked extension can live in `Default\Secure Preferences`; absence under Chrome's packed `Extensions` folder is not a failure.
4. **Test the real browser locally:** Prepare off-screen and coordinate any visible desktop focus immediately before launch. Run the packaged 39-step acceptance in the intended user's interactive session (not a detached background process or wrong console account). Use the **actual** Chrome profile directory name:

   ~~~powershell
   & (Join-Path $root 'smoke\run-acceptance.ps1') -Profile Default
   ~~~

   When CAIOS's Chrome picker appears, approve **exactly one tab** (an ordinary website or the built-in New Tab). It will navigate MSN → Wikipedia European badger → real browser Back to MSN → Selenium Web Form, fill and verify the controls including harmless file upload, submit and confirm **`Received!`**. The runner leaves the final confirmation page open (`restore_original_url=false`).
5. **Acceptance and cleanup:** Host is accepted only after chosen-tab attachment and identity, **39/39**, `Received!`, zero cleanup failures, `TASK_COMPLETED`, `TASK_SESSION_RELEASED`, exit code **0** and verification of actual host/profile. Stop/diagnose failures by step; do not replay unexpected foreground interaction. Keep prior folder for rollback; to roll back, re-register the old CAIOS unpacked `extension/` in that same Chrome profile and restore the prior matching Node/MCP/runner folder. Never mix a new extension with an unrelated old MCP/runner or silently change a user's chosen tab.

**Exact accepted VM deployment:** Windows guest `NEXUS-FORGE-DEV\nexus`; active installed folder `C:\Users\nexus\AppData\Local\CAIOS\ChromeExtension\v0.5.0.3-blanktab-7c21a135`, `Default` Chrome profile; previous version and runner backups retained. That guest is reached **via the existing physical Nexus Forge Ubuntu terminal and its independently verified Forge → VM SSH destination**, not via a separately installed Windows Desktop agent. The VM's previously prepared one-shot acceptance task `CAIOS-ChromeBlankTabAcceptance-Once-20261120` was host-specific and **is not a prerequisite or a portable installer**. Current actual working connection and task authorization must be reverified before new use; user-selected tab consent is still mandatory. [Engineering operator routing](https://github.com/Tokenkauph/caios/blob/main/docs/ops/operator-routing.md) · [Forge host record](https://github.com/Tokenkauph/caios/blob/main/docs/resources/nexus-forge.md).

**Tool directory migration:** [Personal AI System #53](https://github.com/Tokenkauph/personal-ai-system/issues/53) and [draft PR #54](https://github.com/Tokenkauph/personal-ai-system/pull/54) classify the CAIOS Chrome extension as a host-local browser capability, **not a separate native connected Tool**. Its current Windows guest is distinct from the proposed Linux test guest; do not reuse Linux guest metadata to claim Windows deployment. Production Neon cutover is not active until separately accepted by its owner.

### Source build / future package updates

Keep the **single current CAIOS Chrome fork**, its matching forked MCP and canonical runner. For an updated Windows version, build the reviewed extension and matching complete base ZIP from the correct source versions, record **both** actual extension and runner source commits in `CAIOS-RELEASE.json`, and run [`scripts/package_caios_windows.py`](../scripts/package_caios_windows.py) with the exact matching **base archive SHA**. Verify the produced output ZIP's **new** SHA-256, all expected members and embedded runner byte match; separately run repository tests and a new real consented 39-step Windows acceptance before declaring that version or additional host accepted. Publish one versioned asset/checksum/release note, preserve rollback, and update the Engineering #201 installed-host evidence. Do not republish the earlier `smoke.1` ZIP as current or generate an unreviewed host-specific alternative harness.


**Owner:** [CAIOS Engineering #201](https://github.com/Tokenkauph/caios/issues/201), Remote Management & Endpoint Agent / shared Chromium browser integration.  
**Authoritative implementations:** [CAIOS extension fork](../packages/extension/CAIOS.md), [single canonical browser runner](../scripts/caios_approved_browser_task.py), and [runner instructions](../scripts/README.md).  
**Historical Quantum Haze checkpoint:** November 19, 2026, **22:03 ET**. This is reusable operating guidance, not a new permission grant. **QUANTUMHAZE / Chrome `Default` / installed CAIOS v0.5.0.3 user-approved tab access now PASSED** a real snapshot → `https://example.org/` navigation → destination snapshot → original URL restore → controller release (**3/3, `TASK_COMPLETED`, exit 0**; [verified host acceptance](https://github.com/Tokenkauph/caios/issues/201#issuecomment-7029072376)). **Plex and direct native ChatGPT Tool remain separately unverified.**

## In-use Windows desktop coordination and stale takeovers

When ChatGPT is about to launch PowerShell, Chrome or another visible application on an occupied Windows desktop, complete every package/hash/Python/version/profile/script preflight **off-screen before requesting immediate availability**. Prefer an already-authorized background execution route over opening and typing into a visible console. If a visible console is required, tell the user which computer, window and disposable tab will be affected, execute the prepared invocation at once (10-second start target, not a guaranteed timer), and verify the actual focused target before each input and Enter. If delayed or focus changes, **do not** unexpectedly resume the queued launch or type later; stop and coordinate a fresh short interruption while preserving the original task approval. The browser's own selected-tab consent and 900-second attachment wait are separate, and must not be shortened to 10 seconds. Never treat a Windows controller lease, a launch acknowledgement, or an earlier general "go ahead" as just-in-time availability.

The verified Quantum Haze host-local Python selection and simplified public Example Domain smoke plan are still distinguished from the older published ZIP. Keep this distinction until a reviewed source package and independent acceptance establish a successor; do not silently regenerate a different launcher during a desktop session. See [CAIOS SNAFU incident #131](https://github.com/Tokenkauph/caios-core/issues/131) and [Engineering Chrome owner #201](https://github.com/Tokenkauph/caios/issues/201).

## Rule: Never reinvent the installation or test on a new machine

Every Windows host uses **one reviewed versioned extension, its matching forked Playwright MCP and the same canonical Python runner**. Host-specific input changes only: machine identity, approved Chrome profile, file paths, and explicitly selected test tab. Do not create another Node/Python one-off MCP client, substitute stock Playwright, or invent another service/transport.

**Normal browser tasks — user chooses the tab:** The Chrome picker, not an assistant-assumed website, determines the allowed tab. The canonical runner now supports `tab_selection: user_selected`: accept exactly one non-crashed attached tab, explicitly select and verify its current identity, then run the authorized task regardless of its starting title/URL. Do not require `example.com`, Google, MSN or any other page for ordinary use. A dedicated **Example Domain smoke test** may intentionally pin that public fixture, but that is **test-specific only**, not a restriction on user browsing. Legacy pinned plans remain supported. If several tabs are attached to a single-tab task, stop and request a unique selection rather than guessing. This source change is not evidence of installation on each host; verify its exact runner before claiming generic-tab acceptance.

**Blank-tab source correction (accepted package above; per-host verification still required):** An explicitly selected Chrome New Tab (`chrome://newtab/` or `chrome://new-tab-page/`) is eligible in the updated source picker and is navigated **in the same approved tab ID** to `about:blank` before attachment. An ordinary `about:blank` tab is also selectable. The runner allows that starting URL only for user-selected tasks without original-page restoration (including the 39-action installation acceptance). Other Chrome-internal pages remain excluded, and multiple selections are not silently converted. **Older Windows packages remain unchanged. The newer `acceptance.1` release has completed the full live 39-step user-selected-tab acceptance on the Windows Dev VM; that pass does not establish the starting tab was blank or that other hosts are accepted.** No special starting domain is required.

Four distinct checkpoints: **machine identity → actual Chrome profile → compatible host-local MCP → explicitly approved tab**. Installed files, Chrome Sync, a debugging banner, successful initialize/tools-list, or user approval reported in chat do not by themselves prove the final page action. A **direct registered ChatGPT remote browser-control Tool** is also separate from this temporary host-local runner.

CAIOS extension ID: **kanpfbepfgcpmjoeaaihigjkcdjejbld**. Existing independent Microsoft extension ID: **mmlmfjhmonkocbjadbfplnigmagldckm**. Keep Microsoft's extension. The canonical runner explicitly targets the CAIOS extension and removes optional token-based approval bypass.

## Windows release format and reuse

**Historical earlier Windows bundle (built and inspected on physical Nexus Forge, Nov 19; superseded for new installs by `acceptance.1` above):** caios-chrome-windows-v0.5.0.3-with-smoke-final.zip, **37,321,806 bytes**, SHA-256 **6c0808d3d4f7fb5515e6effa6dfa4fd0748107a29465a431b9feccb3d7eb8a98**. This bundle is now a **published GitHub prerelease** ([release page](https://github.com/Tokenkauph/caios-chrome-extension/releases/tag/caios-chrome-windows-v0.5.0.3-smoke.1); [verified ZIP](https://github.com/Tokenkauph/caios-chrome-extension/releases/download/caios-chrome-windows-v0.5.0.3-smoke.1/caios-chrome-windows-v0.5.0.3-with-smoke-final.zip)). The published asset was independently downloaded and compared byte-for-byte to the merged-source build, **not** installed or given live Windows acceptance. Its five added smoke/ entries contain the exact unchanged canonical Python runner, a public-page test plan, a PowerShell launcher, a README and checksummed smoke metadata. All **75 entries of the original package remain unchanged**; archive integrity and exact runner byte match were independently verified. **Important release distinction:** the successful Quantum Haze test used the existing installed 0.5.0.3 extension/Node/MCP with the canonical runner staged alongside it, and two **host-local** fixes (Python selection/preflight transcript and simplified 3-step plan). The published `smoke.1` ZIP predates those fixes and must not be described as the same fully accepted corrected package; synchronize them into the canonical Windows package sources before publishing a successor.

**Older base ZIP:** caios-chrome-windows-v0.5.0.3-complete.zip, SHA-256 **21b2fa235e4d833bc04a25e1f6382810ca2b75e95c832cd30cbb5040bfb25c3f**, contains Node/MCP/extension but **no** smoke runner/plan. Do not apply the older base ZIP's hash to the enhanced ZIP. When making later Windows releases, use the same **[release packager](../scripts/package_caios_windows.py)** with the correct reviewed source ZIP/digest and source version. The packager refuses mixed versions, bad input SHA, unsafe members, duplicate smoke tools and output overwrite.

On an approved host receiving an **enhanced** ZIP, after loading its unpacked extension and verifying its ID, run **smoke/run-acceptance.ps1** with the real `-Profile` name to perform the **mandatory full real-world acceptance** using whichever website tab the user selects. The older **smoke/run-smoke.ps1** with an Example Domain-only page is optional troubleshooting. Only a normal local Python 3 interpreter is needed in addition to the included Node/MCP; the launcher creates a per-host task plan and invokes the canonical runner. It does not install Python, bypass Chrome's selected-tab approval, or create a service. Actual host-local acceptance and a native direct ChatGPT Tool are separate gates.

## A. One-time Windows installation

1. **Resolve and verify the approved host.** Read exact hostname, logged-in Windows user, existing Chrome profile and allowed host Tool route. The physical Nexus Forge Ubuntu, Quantum Haze Windows, Plex Windows and Forge Windows VM are distinct. Do not use retired Windows-Dev1 or administrator recovery SSH as fallback. A Windows Desktop controller lease is not GUI consent.
2. **Deliver the entire approved Windows package** via an authorized, verified transfer path. The Nov 19 complete v0.5.0.3 archive is named caios-chrome-windows-v0.5.0.3-complete.zip; **37,310,541 bytes**, SHA-256 **21b2fa235e4d833bc04a25e1f6382810ca2b75e95c832cd30cbb5040bfb25c3f**. It contains **extension/**, **playwright-core/**, **runtime/node.exe**, and **CAIOS-RELEASE.json**. Release manifest records fork commit **397ab1585f24c9ed89d4806c8eec50704126321f**. Do NOT substitute the separate extension-only ZIP. These identifiers apply only to this exact release. The Nov 19 private Forge port 18882 and Forge Temp/Tasks paths were **temporary task staging**, not a maintained installation service. Future builds need their own reviewed manifest/checksum/source.
3. **Verify archive SHA and extract to a version-specific user-local directory**, not over the prior version. PowerShell on the exact host, replacing the placeholder with the actual approved archive file:

   ~~~powershell
   $zip = '<approved-full-release-zip-path>'
   $sha = '<approved-digest-of-the-actual-delivered-zip>'
   if (-not (Test-Path -LiteralPath $zip -PathType Leaf)) { throw 'Full release ZIP missing' }
   if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $sha) { throw 'Release checksum mismatch' }
   $root = Join-Path $env:LOCALAPPDATA 'CAIOS\ChromeExtension\v0.5.0.3'
   if (Test-Path -LiteralPath $root) {
       Write-Host 'Version already present. Inspect existing files; do not overwrite blindly.'
   } else {
       New-Item -ItemType Directory -Path $root | Out-Null
       Expand-Archive -LiteralPath $zip -DestinationPath $root
   }
   ~~~

4. **Verify manifest, Node and matching MCP**, in the same local PowerShell:

   ~~~powershell
   $root = Join-Path $env:LOCALAPPDATA 'CAIOS\ChromeExtension\v0.5.0.3'
   $manifest = Get-Content (Join-Path $root 'extension\manifest.json') -Raw | ConvertFrom-Json
   $release = Get-Content (Join-Path $root 'CAIOS-RELEASE.json') -Raw | ConvertFrom-Json
   if ($manifest.name -ne 'CAIOS Chrome Extension' -or $manifest.version -ne '0.5.0.3') { throw 'Unexpected extension' }
   if ($release.extension_id -ne 'kanpfbepfgcpmjoeaaihigjkcdjejbld') { throw 'Unexpected extension ID' }
   $node = Join-Path $root 'runtime\node.exe'
   $mcp = Join-Path $root 'playwright-core\lib\entry\mcp.js'
   if (-not ((Test-Path $node -PathType Leaf) -and (Test-Path $mcp -PathType Leaf))) { throw 'Missing matching Node or MCP' }
   & $node --version
   & $node $mcp --version
   ~~~

   Nov 19 Quantum Haze verified **Node v24.22.3**, **Playwright MCP Version 1.66.0-next**, **extension 0.5.0.3**. Keep previous release folders for rollback.
5. **Register the unpacked extension in the correct *user* Chrome profile.** In Chrome inspect **chrome://version → Profile Path** (Quantum Haze RStires used Default). Then **chrome://extensions → Developer mode → Load unpacked**. Select the **extension** folder under the version folder, e.g. C:\Users\rstires\AppData\Local\CAIOS\ChromeExtension\v0.5.0.3\extension. Confirm visible **CAIOS Chrome Extension** card, correct version and **ID kanpfbepfgcpmjoeaaihigjkcdjejbld**, and **enabled**. Keep the Microsoft extension and all other Chrome profiles. **Important:** an unpacked extension may not appear in the on-disk Default\Extensions directory; its absence from that directory is NOT an installation failure. Use the real Chrome extension-management card.
6. **Use the existing host-local controller/runner.** The **enhanced Windows ZIP** includes the exact canonical runner, plan and PowerShell launcher; the **older base ZIP** contains Node/MCP but not the runner. Neither includes Python 3. Resolve Python 3 and use the existing reviewed repository runner below through an authorized host-local execution route. Do not assume Windows Desktop launch_app executes PowerShell scripts: a previous compound launch did not produce an execution receipt and a different VBScript launcher was explicitly denied. A denied tool is not permission for an alternative credential, privileged SSH or GUI trick.

## B. REQUIRED: standard end-to-end acceptance for each new installation

The old three-step Example Domain demo is **not sufficient** to mark a new extension installation working. Every new Windows installation must run the packaged [standard 39-step test](../scripts/windows-smoke/caios-install-acceptance.template.json) using [run-acceptance.ps1](../scripts/windows-smoke/run-acceptance.ps1) and the existing canonical runner. Existing Linux/new-platform hosts must perform the same real-world steps with their authorized matching runner and task-local dummy file, not a separately invented browser controller.

1. **Verify and preflight off-screen.** Confirm exact machine, actual user Chrome profile, enabled matching CAIOS extension, bundled Node/MCP, Python 3, packaged `smoke/run-acceptance.ps1`, task plan and harmless upload fixture. If using an **older published package such as v0.5.0.3-smoke.1**, those new suite files are absent; do not claim acceptance by running the old smoke. Update through a separately reviewed and verified release before applying the new standard. Never overwrite an installed version blindly.
2. **Choose any ordinary website tab.** The user's Chrome tab picker is the only tab-selection authority. There is **no required starting title or URL**, including Example Domain, Google or MSN; the runner's `tab_selection: user_selected` accepts exactly one distinct non-crashed consented tab. The consent authorizes only that selected tab and the requested test sequence. Prepare all launch/preflight details before asking for consent, and warn just before any actual visible desktop-control operation.
3. **Run the approved local launcher** in the installed Chrome user's interactive Windows session. The normal invocation for a versioned user-local installation is:

   ~~~powershell
   & "$env:LOCALAPPDATA\CAIOS\ChromeExtension\v0.5.0.3\smoke\run-acceptance.ps1" -Profile Default
   ~~~

   Replace the version directory and `-Profile` with actual installed values. The script will not start Chrome or select a tab for the user, will not bypass consent, and will not install software. It sets the MCP working directory to the packaged dummy upload so the form's file chooser can read it without extra permissions; it inserts the current date in the form fields and checks, not a fixed installation date.
4. **Perform and independently verify the complete browser sequence:** navigate to **MSN**, verify; navigate to the **Wikipedia European badger article**, verify; use the real browser **Back** tool and verify the first MSN page again; navigate to Selenium's **Web Form**; exercise and separately verify text, dummy password, multiline text, dropdown, datalist, checkboxes, radio, date, color, slider, file upload; verify disabled/read-only/hidden inputs remain intact; **submit** and confirm **Received!**.
5. **Require the real pass receipts.** The same attached consented tab must produce `MCP_TAB_ATTACHED`, `APPROVED_TARGET_VERIFIED`, **39/39 `ACTION_DONE`**, `TASK_COMPLETED`, `TASK_SESSION_RELEASED`, zero cleanup failures, runner **exit 0**, and confirmation that the submitted Selenium page says **Received!**. Leave that submission confirmation visible; this full suite deliberately does not restore the initial tab URL. A partial navigation, test file creation, unit tests, or browser picker alone is **NOT PASS**. Any failure blocks *new-install end-to-end acceptance*, but preserve the working installed release and document the failing step without silently switching machine, profile or privilege.

The newer suite is incorporated into the standard Windows packager together with the prior optional diagnostic. Source publication and a passing CI simulation do **not** retroactively establish live acceptance on already installed machines. Keep one [Engineering #201](https://github.com/Tokenkauph/caios/issues/201) owner record and record each host's actual deployed version and acceptance receipt.

## C. OPTIONAL legacy Example Domain smoke for targeted diagnostics

1. Open a disposable, public **https://example.com/** tab in the exact intended Chrome profile **before** starting the controller. Do not select personal account tabs for this test.
2. Create an approved task plan JSON, here named **caios-example-domain-smoke.json**. On another Windows host change only the verified machine/profile and task-scoped paths. The plan deliberately limits operations to the selected public test tab:

   ~~~json
   {
     "contract_version": "1",
     "machine": "QUANTUMHAZE",
     "profile": "Default",
     "extension_id": "kanpfbepfgcpmjoeaaihigjkcdjejbld",
     "expected_title": "Example Domain",
     "expected_url_prefix": "https://example.com/",
     "restore_original_url": true,
     "steps": [
       {"name": "read_public", "tool": "browser_snapshot", "arguments": {}},
       {"name": "navigate_public", "tool": "browser_navigate", "arguments": {"url": "https://example.org/"}},
       {"name": "read_destination", "tool": "browser_snapshot", "arguments": {}}
     ],
     "finally_steps": []
   }
   ~~~

3. **Start the canonical runner.** **Preferred on a host with the enhanced ZIP:** run the bundled smoke/run-smoke.ps1 -Profile <verified Chrome directory name>; it generates the plan for the verified host/profile and calls the same embedded canonical Python runner. The manual repository-checkout command below applies **only to older packages without the bundled smoke directory**; require Python 3 in either case. In Windows PowerShell:

   ~~~powershell
   $repo = '<verified-local-caios-chrome-extension-checkout>'
   $plan = '<absolute-path-to-caios-example-domain-smoke.json>'
   $root = Join-Path $env:LOCALAPPDATA 'CAIOS\ChromeExtension\v0.5.0.3'
   $chrome = Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'
   $runner = Join-Path $repo 'scripts\caios_approved_browser_task.py'
   $node = Join-Path $root 'runtime\node.exe'
   $mcp = Join-Path $root 'playwright-core\lib\entry\mcp.js'
   $log = Join-Path $env:TEMP 'caios-browser-smoke-stderr.log'
   python $runner --plan $plan --node $node --mcp-entry $mcp --browser-executable $chrome --stderr-log $log
   ~~~

   If Python 3 is unavailable, resolve that prerequisite in the legitimate approved route; do NOT recreate the runner using another language. The shared runner launches one matching local forked MCP client and requires ordinary Chrome consent. It is not a daemon or native registered ChatGPT Tool.
4. **User consents to only the Example Domain tab (`https://example.com/`)** in the CAIOS picker. **Before** starting, explicitly tell the user this is the tab they must select, not the active ChatGPT conversation or the `Connect CAIOS to Chrome` page. On an in-use desktop, complete source/plan/runtime checks off-screen first, warn **immediately** before any approved brief takeover, execute promptly with the exact foreground handle/PID checked before typing and before Enter, and stop input if focus changes. Do not unexpectedly open PowerShell during active work. A desktop lease is not consent. This verified three-step plan uses the canonical runner's built-in selected-tab identity, navigation and restoration checks; an additional JavaScript `browser_evaluate` assertion had failed after genuine tab read and was unnecessary. The same process must then immediately receive the attached tab, parse Playwright's actual list format, select its real index, confirm exact title/URL and run the planned read/navigation/return. Do not stop for another chat confirmation between approval and execution; no repeat consent unless the session genuinely ended and a new request is authorized.
5. **True acceptance requires** emitted **MCP_TAB_ATTACHED**, **APPROVED_TARGET_VERIFIED**, individual **ACTION_DONE** for every planned step, **ORIGINAL_URL_RESTORED** for this restore-enabled plan, **TASK_COMPLETED** and **TASK_SESSION_RELEASED**; also verify that actual page content was read, destination https://example.org/ was reached, and original public tab returned. Close only the task-owned controller, leave unrelated tabs, Chrome sign-ins and Microsoft extension intact. Initial MCP initialize/tools-list is **not** a pass.

### Troubleshooting without rebuilding

| Observation | Interpretation and next action |
| --- | --- |
| ZIP hash and package versions PASS | Only proves extraction. Check Chrome card and real tab access next; no reinstall. |
| No unpacked CAIOS directory under Default\Extensions | Not a valid registration test. Check chrome://extensions in verified profile. |
| CONTROLLER_STARTED, CONTROLLER_INITIALIZED and PLAYWRIGHT_TOOLS_PRESENT | Controller started, not proof of tab attachment or page read. Continue the same authorized session. |
| User says consent clicked but MCP tab is missing | Verify real MCP attachment / picker state, not user blame. No bypass token, profile swap or arbitrary retry. |
| Tab-list mismatch in a custom script | **Do not fix the custom script.** Use scripts/caios_approved_browser_task.py, which already parses the actual Playwright tab syntax and checks unique title/URL/index. |
| Tab attached but DOM/navigation fails | Diagnose only that returned page action; no claim of full acceptance until independent page evidence. |
| Windows Desktop focus fails during user activity | Desktop GUI focus and MCP tab consent are separate. Never type into an unverified foreground. Prepare all work off-screen, warn immediately before the brief authorized takeover, recheck handle/PID before each input, abort if focus changed, and release lease promptly. |
| Local browser runner PASS but ChatGPT cannot call Quantum Haze Chrome directly | Separate native registered ChatGPT/host controller integration, owned by #201; not an extension-install success. |
| Explicit tool/safety denial | Stop that route; do not use admin recovery SSH or an unauthorized shell/credential workaround. |

## Actual November 19 status, distinguishing evidence from claims

- **Physical Nexus Forge Ubuntu:** CAIOS fork + matching MCP previously connected to an explicitly approved already-open ChatGPT conversation; read and scrolled its content, submitted one authorized continuation and read back the reply. The canonical runner was created afterward with test-covered tab parsing and controlled cleanup; separate R1 URL restore reliability findings remain under #201. Does **not** prove native direct registered ChatGPT browser Tool.
- **Quantum Haze Windows — ACCEPTED November 19, 22:03 ET:** Installed existing CAIOS extension **0.5.0.3** and matching Node **v24.22.3**/forked MCP in Chrome `Default`; user-local Python **3.14.10**; canonical runner staged in `%LOCALAPPDATA%\\CAIOS\\ChromeExtension\\v0.5.0.3\\smoke`. After selecting **Example Domain `https://example.com/`** in CAIOS Chrome's picker, the corrected local three-step plan completed **read original → navigate to `https://example.org/` → read destination**, restored original URL and released session. **`MCP_TAB_ATTACHED`, `APPROVED_TARGET_VERIFIED`, 3/3 `ACTION_DONE`, `ORIGINAL_URL_RESTORED`, `TASK_COMPLETED`, `TASK_SESSION_RELEASED`, exit 0**, cleanup failures 0. Independently reread `smoke\\run-smoke-latest.log`; [Engineering receipt](https://github.com/Tokenkauph/caios/issues/201#issuecomment-7029072376). Earlier one-off test and consent-tab mismatch are **historical failed attempts** superseded by this live acceptance. **The published enhanced ZIP has not been independently live-accepted with the two newer host-local fixes.**
- **Other hosts including Plex:** Do not assume installation or control based on Forge/Quantum Haze; check each requested actual host, profile, tool route and one user-selected tab.

## Single owner and rollout improvement

Record each verified host once in existing [Engineering #201](https://github.com/Tokenkauph/caios/issues/201) and applicable host record: approved target/profile, exact package hash/version/ID, matching forked MCP, canonical runner source revision, Chrome card enabled state, approved tab/title/URL, actual read/navigation/restore/cleanup results, native Tool connectivity and blockers. No new tracker, additional fork, or one-off browser harness for each computer.

**Release packaging improvement published:** the packager and standard smoke tools are in this repository's Windows release workflow; the Nov 19 enhanced ZIP was built and independently inspected on physical Forge, as above. It has been published as a **GitHub prerelease with a verified asset**, but is **not automatically installed on Quantum Haze**. Python 3 remains a host prerequisite; a native ChatGPT-to-Quantum-Haze browser Tool remains separate. After source integration, use the enhanced release artifact and exact SHA for future approved Windows installations, not the old extension-only or base ZIP.

# CAIOS Chrome Extension — repeatable Windows install and acceptance

**Owner:** [CAIOS Engineering #201](https://github.com/Tokenkauph/caios/issues/201), Remote Management & Endpoint Agent / shared Chromium browser integration.  
**Authoritative implementations:** [CAIOS extension fork](../packages/extension/CAIOS.md), [single canonical browser runner](../scripts/caios_approved_browser_task.py), and [runner instructions](../scripts/README.md).  
**Evidence checkpoint:** November 19, 2026. This is reusable operating guidance, not a new permission grant or proof that Quantum Haze has passed end-to-end.

## Rule: Never reinvent the installation or test on a new machine

Every Windows host uses **one reviewed versioned extension, its matching forked Playwright MCP and the same canonical Python runner**. Host-specific input changes only: machine identity, approved Chrome profile, file paths, and explicitly selected test tab. Do not create another Node/Python one-off MCP client, substitute stock Playwright, or invent another service/transport.

Four distinct checkpoints: **machine identity → actual Chrome profile → compatible host-local MCP → explicitly approved tab**. Installed files, Chrome Sync, a debugging banner, successful initialize/tools-list, or user approval reported in chat do not by themselves prove the final page action. A **direct registered ChatGPT remote browser-control Tool** is also separate from this temporary host-local runner.

CAIOS extension ID: **kanpfbepfgcpmjoeaaihigjkcdjejbld**. Existing independent Microsoft extension ID: **mmlmfjhmonkocbjadbfplnigmagldckm**. Keep Microsoft's extension. The canonical runner explicitly targets the CAIOS extension and removes optional token-based approval bypass.

## A. One-time Windows installation

1. **Resolve and verify the approved host.** Read exact hostname, logged-in Windows user, existing Chrome profile and allowed host Tool route. The physical Nexus Forge Ubuntu, Quantum Haze Windows, Plex Windows and Forge Windows VM are distinct. Do not use retired Windows-Dev1 or administrator recovery SSH as fallback. A Windows Desktop controller lease is not GUI consent.
2. **Deliver the entire approved Windows package** via an authorized, verified transfer path. The Nov 19 complete v0.5.0.3 archive is named caios-chrome-windows-v0.5.0.3-complete.zip; **37,310,541 bytes**, SHA-256 **21b2fa235e4d833bc04a25e1f6382810ca2b75e95c832cd30cbb5040bfb25c3f**. It contains **extension/**, **playwright-core/**, **runtime/node.exe**, and **CAIOS-RELEASE.json**. Release manifest records fork commit **397ab1585f24c9ed89d4806c8eec50704126321f**. Do NOT substitute the separate extension-only ZIP. These identifiers apply only to this exact release. The Nov 19 private Forge port 18882 and Forge Temp/Tasks paths were **temporary task staging**, not a maintained installation service. Future builds need their own reviewed manifest/checksum/source.
3. **Verify archive SHA and extract to a version-specific user-local directory**, not over the prior version. PowerShell on the exact host, replacing the placeholder with the actual approved archive file:

   ~~~powershell
   $zip = '<approved-full-release-zip-path>'
   $sha = '21b2fa235e4d833bc04a25e1f6382810ca2b75e95c832cd30cbb5040bfb25c3f'
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
6. **Use the existing host-local controller/runner.** The 0.5.0.3 complete ZIP includes bundled Node and forked MCP, **not a verified local Python runner or Python 3 interpreter**. Resolve Python 3 and use the existing reviewed repository runner below through an authorized host-local execution route. Do not assume Windows Desktop launch_app executes PowerShell scripts: a previous compound launch did not produce an execution receipt and a different VBScript launcher was explicitly denied. A denied tool is not permission for an alternative credential, privileged SSH or GUI trick.

## B. Same smoke test on every new approved host

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
       {"name": "read", "tool": "browser_snapshot", "arguments": {}},
       {"name": "inspect", "tool": "browser_evaluate",
         "arguments": {"function": "() => ({title:document.title,url:location.href,heading:document.querySelector('h1')?.textContent})"}},
       {"name": "navigate_public", "tool": "browser_navigate", "arguments": {"url": "https://example.org/"}},
       {"name": "inspect_public", "tool": "browser_evaluate",
         "arguments": {"function": "() => ({title:document.title,url:location.href})"}}
     ],
     "finally_steps": []
   }
   ~~~

3. **Start the canonical runner** from the verified CAIOS repo checkout; require a real Python 3 executable and one pre-verified approved file path for the JSON plan. In Windows PowerShell:

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
4. **User consents to only the Example Domain tab** in the CAIOS picker. The same process must then immediately receive the attached tab, parse Playwright's actual list format, select its real index, confirm exact title/URL and run the planned read/navigation/return. Do not stop for another chat confirmation between approval and execution; no repeat consent unless the session genuinely ended and a new request is authorized.
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
| Windows Desktop focus fails during user activity | Desktop GUI focus and MCP tab consent are separate. Do not take over active user work. |
| Local browser runner PASS but ChatGPT cannot call Quantum Haze Chrome directly | Separate native registered ChatGPT/host controller integration, owned by #201; not an extension-install success. |
| Explicit tool/safety denial | Stop that route; do not use admin recovery SSH or an unauthorized shell/credential workaround. |

## Actual November 19 status, distinguishing evidence from claims

- **Physical Nexus Forge Ubuntu:** CAIOS fork + matching MCP previously connected to an explicitly approved already-open ChatGPT conversation; read and scrolled its content, submitted one authorized continuation and read back the reply. The canonical runner was created afterward with test-covered tab parsing and controlled cleanup; separate R1 URL restore reliability findings remain under #201. Does **not** prove native direct registered ChatGPT browser Tool.
- **Quantum Haze Windows:** Full v0.5.0.3 bundle checksum/install receipt passed; manifest, Node and MCP were independently read back. User reports unpacked Chrome extension installed. The Nov 19 **hand-built** quantumhaze-extension-smoke.cjs received **CONTROLLER_STARTED, CONTROLLER_INITIALIZED, PLAYWRIGHT_TOOLS_PRESENT**, then failed with **Selected tab mismatch or more than one tab selected; no page accessed**. It exited before reading or navigating the public test page. This likely reflects the one-off parser assumptions, **not a proven extension failure or an end-to-end PASS**. Do **not** reuse that custom test. Canonical runner acceptance still remains.
- **Other hosts including Plex:** Do not assume installation or control based on Forge/Quantum Haze; check each requested actual host, profile, tool route and one user-selected tab.

## Single owner and rollout improvement

Record each verified host once in existing [Engineering #201](https://github.com/Tokenkauph/caios/issues/201) and applicable host record: approved target/profile, exact package hash/version/ID, matching forked MCP, canonical runner source revision, Chrome card enabled state, approved tab/title/URL, actual read/navigation/restore/cleanup results, native Tool connectivity and blockers. No new tracker, additional fork, or one-off browser harness for each computer.

**Future implementation, NOT delivered by this document:** package the already-reviewed canonical runner and one reusable public smoke-test plan with every Windows release, or provide an equivalent approved native host-local launch interface. The current Windows bundle does not include Python/the runner; this is the remaining setup friction to eliminate under #201. Publishing documentation does not install a service, activate a direct ChatGPT Tool or qualify an untested machine.

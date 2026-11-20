# CAIOS Chrome Extension Windows smoke test

This directory is **bundled by** [scripts/package_caios_windows.py](../../scripts/package_caios_windows.py) into each verified complete Windows release. It includes the **unmodified canonical Python runner** from scripts/caios_approved_browser_task.py and its public Example Domain test plan. Do **not** write a new per-host runner.

**November 19 Quantum Haze receipt:** The installed CAIOS v0.5.0.3 Chrome `Default` human-profile controller **PASSED** an approved Example Domain snapshot → navigate to `https://example.org/` → destination snapshot → original URL restoration → controller release (**3/3**, exit **0**, no cleanup errors). [Engineering #201 verified evidence](https://github.com/Tokenkauph/caios/issues/201#issuecomment-7029072376). The host had locally corrected its Python 3.14 selection and transcript logging; the local plan uses the three simple canonical steps. **The already-published `v0.5.0.3-smoke.1` ZIP predates those changes.** Do not represent it as containing the exact accepted corrected launcher/plan until source and new asset are synchronized and verified.

1. Extract the complete approved Windows release, check its recorded release checksum, and load **extension/** into the intended user's Chrome profile using chrome://extensions → Developer mode → Load unpacked. Verify the enabled CAIOS extension ID **kanpfbepfgcpmjoeaaihigjkcdjejbld**; keep Microsoft's separate extension.
2. Verify Python **3** is already available via Windows py.exe or python.exe; the v0.5.0.3 full ZIP bundles Node but does **not** bundle Python. The launcher will **not** install Python or register a service.
3. Open **https://example.com/** in a disposable tab in the exact intended profile; do not select a signed-in tab.
4. In regular PowerShell on that exact machine, run:

   ~~~powershell
   & "$env:LOCALAPPDATA\CAIOS\ChromeExtension\v0.5.0.3\smoke\run-smoke.ps1" -Profile Default
   ~~~

   Change the path to the version actually installed and **-Profile** to the actual directory name shown in chrome://version. The script generates a task-owned plan from the bundled template with your verified hostname and explicit Chrome profile, then launches the **same canonical runner** with the matching bundled Node and Playwright MCP. No Chrome credential or approval token is read.
5. **Before requesting Chrome consent**, explicitly tell the user the exact disposable tab to select: **Example Domain (`https://example.com/`)**, not their ChatGPT conversation or the CAIOS connection page. If the user is working on the machine, prepare everything off-screen, announce the short separately approved desktop interruption immediately before it, verify actual PowerShell foreground handle/PID before typing and Enter, and stop if focus changed. Then select **only** the Example Domain tab and approve. The corrected host-local three-step runner performs original page snapshot → navigate to `https://example.org/` → destination snapshot, and restores the original URL. No additional browser-evaluate assertion was necessary for verified acceptance.
6. A true PASS requires **MCP_TAB_ATTACHED**, **APPROVED_TARGET_VERIFIED**, **ACTION_DONE** for all intended steps, **ORIGINAL_URL_RESTORED**, **TASK_COMPLETED** and **TASK_SESSION_RELEASED**, along with actual positive public-page content/navigation evidence. A successful MCP initialize or tab picker alone is not acceptance.

A task-local stderr log is left in %TEMP% for genuine errors; it may contain connection details, so do not paste it into public issue reports. The proven Quantum Haze host-local launcher additionally writes `smoke/run-smoke-latest.log` from PowerShell preflight, but the current published ZIP does **not** yet include that change. The generated plan is removed. Chrome remains running and the runner terminates only its task-owned MCP. The native ChatGPT-to-host browser Tool remains a separate capability and is **not** installed by this package.

Owner/diagnosis: [Engineering #201](https://github.com/Tokenkauph/caios/issues/201); [full repeatable Windows install and test guide](../../docs/windows-host-install-and-acceptance.md).

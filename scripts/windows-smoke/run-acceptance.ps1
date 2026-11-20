# Standard interactive CAIOS Chrome install acceptance: user chooses one tab.
# Run on the intended Windows machine, in its normal signed-in Chrome session.
# No Chrome process, profile, approved tab, or site is chosen by this script.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateNotNullOrEmpty()]
    [string]$Profile
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$node = Join-Path $root 'runtime\node.exe'
$mcp = Join-Path $root 'playwright-core\lib\entry\mcp.js'
$runner = Join-Path $PSScriptRoot 'caios_approved_browser_task.py'
$template = Join-Path $PSScriptRoot 'caios-install-acceptance.template.json'
$upload = Join-Path $PSScriptRoot 'caios-install-acceptance-upload.txt'
$chrome = Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'
foreach ($file in @($node,$mcp,$runner,$template,$upload,$chrome)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing acceptance dependency: $file" }
}
if ($Profile -match '[\\/]' -or $Profile -in @('.', '..')) {
    throw 'Pass only the installed Chrome profile directory name, from chrome://version'
}
$manifest = Get-Content -LiteralPath (Join-Path $root 'extension\manifest.json') -Raw | ConvertFrom-Json
$release = Get-Content -LiteralPath (Join-Path $root 'CAIOS-RELEASE.json') -Raw | ConvertFrom-Json
if ($manifest.name -ne 'CAIOS Chrome Extension' -or
    $manifest.version -ne $release.extension_version -or
    $release.extension_id -ne 'kanpfbepfgcpmjoeaaihigjkcdjejbld') {
    throw 'CAIOS Chrome Extension and forked controller release mismatch'
}
# Prefer a real installed user-local Python before PATH's Microsoft Store aliases.
$executable = $null
$prefix = @()
$pythonRoot = Join-Path $env:LOCALAPPDATA 'Programs\Python'
if (Test-Path -LiteralPath $pythonRoot -PathType Container) {
    $dirs = @(Get-ChildItem -LiteralPath $pythonRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'Python3*' } | Sort-Object Name -Descending)
    foreach ($dir in $dirs) {
        $candidate = Join-Path $dir.FullName 'python.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $executable = $candidate
            break
        }
    }
}
if (-not $executable) {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($py) { $executable = $py.Source; $prefix = @('-3') }
    elseif ($python) { $executable = $python.Source }
    else { throw 'Install Python 3 for the existing CAIOS browser runner; no installation was attempted' }
}
$version = & $executable @prefix --version
if ($LASTEXITCODE -ne 0 -or $version -notmatch '^Python 3\.') {
    throw 'The selected Python command is not a functional Python 3 runtime'
}
$today = (Get-Date).ToString('MM/dd/yyyy', [System.Globalization.CultureInfo]::InvariantCulture)
$rawTemplate = Get-Content -LiteralPath $template -Raw
if (-not $rawTemplate.Contains('__TEST_DATE__')) { throw 'Acceptance template date placeholder missing' }
$task = $rawTemplate.Replace('__TEST_DATE__', $today) | ConvertFrom-Json
if ($task.tab_selection -ne 'user_selected' -or
    $task.steps.Count -ne 39 -or
    $task.restore_original_url -or
    ($task.PSObject.Properties.Name -contains 'expected_title') -or
    ($task.PSObject.Properties.Name -contains 'expected_url_prefix')) {
    throw 'Unexpected standard acceptance plan; a fixed starting website is prohibited'
}
$task.machine = $env:COMPUTERNAME
$task.profile = $Profile
$plan = Join-Path $env:TEMP ('caios-install-acceptance-' + [guid]::NewGuid().ToString('N') + '.json')
$log = Join-Path $env:TEMP ('caios-install-acceptance-' + [guid]::NewGuid().ToString('N') + '.stderr.log')
$previous = Get-Location
try {
    $json = $task | ConvertTo-Json -Depth 30
    [System.IO.File]::WriteAllText($plan, $json, (New-Object System.Text.UTF8Encoding($false)))
    # The Playwright MCP limits local file reads to its workspace; this directory
    # contains the bundled harmless upload and becomes the child process cwd.
    Set-Location -LiteralPath $PSScriptRoot
    Write-Host 'CAIOS standard install acceptance: pick ANY ONE website tab in the Chrome approval picker.'
    Write-Host 'The approved tab will visit MSN, Wikipedia, go Back to MSN, complete the Selenium form and submit.'
    Write-Host 'The successful Received! confirmation remains open; the starting page is not restored.'
    & $executable @prefix $runner --plan $plan --node $node --mcp-entry $mcp --browser-executable $chrome --stderr-log $log
    $code = $LASTEXITCODE
    Write-Host "CAIOS_ACCEPTANCE_EXIT_CODE=$code"
    Write-Host "Task-owned diagnostic log (local only): $log"
    if ($code -ne 0) { throw "CAIOS standard install acceptance failed; runner exit code $code" }
} finally {
    Set-Location -LiteralPath $previous.Path
    if (Test-Path -LiteralPath $plan -PathType Leaf) { Remove-Item -LiteralPath $plan -Force }
}

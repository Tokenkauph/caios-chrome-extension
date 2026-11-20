# One task-owned, explicit-user-consent smoke test for the matching CAIOS fork.
# Run ONLY on the intended Windows host, in its normal user session.
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
$template = Join-Path $PSScriptRoot 'caios-example-domain-smoke.template.json'
$chrome = Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'
foreach ($file in @($node,$mcp,$runner,$template,$chrome)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required release file missing: $file" }
}
if ($Profile -match '[\\/]' -or $Profile -in @('.', '..')) {
    throw 'Supply the exact Chrome profile directory name from chrome://version'
}
$pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($pyLauncher) {
    $executable = $pyLauncher.Source
    $prefix = @('-3')
} elseif ($python) {
    $executable = $python.Source
    $prefix = @()
} else {
    throw 'Python 3 is needed to run the already-approved CAIOS Python runner. No installation performed.'
}
$pythonVersion = & $executable @prefix --version
if ($LASTEXITCODE -ne 0 -or $pythonVersion -notmatch '^Python 3\.') {
    throw 'Python 3 is not available through the selected launcher'
}
$manifest = Get-Content -LiteralPath (Join-Path $root 'extension\manifest.json') -Raw | ConvertFrom-Json
$release = Get-Content -LiteralPath (Join-Path $root 'CAIOS-RELEASE.json') -Raw | ConvertFrom-Json
if ($manifest.name -ne 'CAIOS Chrome Extension' -or $manifest.version -ne $release.extension_version -or
    $release.extension_id -ne 'kanpfbepfgcpmjoeaaihigjkcdjejbld') {
    throw 'Mismatched CAIOS extension release'
}
$task = Get-Content -LiteralPath $template -Raw | ConvertFrom-Json
$task.machine = $env:COMPUTERNAME
$task.profile = $Profile
if ($task.expected_title -ne 'Example Domain' -or $task.expected_url_prefix -ne 'https://example.com/') {
    throw 'Unexpected public smoke-test target'
}
$plan = Join-Path $env:TEMP ('caios-chrome-smoke-' + [guid]::NewGuid().ToString('N') + '.json')
$log = Join-Path $env:TEMP ('caios-chrome-smoke-' + [guid]::NewGuid().ToString('N') + '.stderr.log')
try {
    $task | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $plan -Encoding UTF8
    Write-Host 'CAIOS public smoke test: ensure the Example Domain tab is already open in the selected Chrome profile.'
    Write-Host 'When prompted, select ONLY that Example Domain tab and approve it.'
    & $executable @prefix $runner --plan $plan --node $node --mcp-entry $mcp --browser-executable $chrome --stderr-log $log
    $code = $LASTEXITCODE
    Write-Host "CAIOS_RUNNER_EXIT_CODE=$code"
    Write-Host "Task-owned diagnostic log (local only): $log"
    if ($code -ne 0) { throw "CAIOS smoke test failed; runner exit code $code" }
} finally {
    if (Test-Path -LiteralPath $plan -PathType Leaf) { Remove-Item -LiteralPath $plan -Force }
}

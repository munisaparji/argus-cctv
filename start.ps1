$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run .\setup.ps1 first' }
& '.\.venv\Scripts\python.exe' -m argus.cli demo
if ($LASTEXITCODE -ne 0) { throw 'Sample pipeline failed' }
if (-not (Test-Path -LiteralPath 'apps\console\dist\index.html')) {
    Push-Location 'apps\console'
    try { npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw 'Console build failed' } } finally { Pop-Location }
}
Write-Host 'Open http://127.0.0.1:8000 in your browser. Press Ctrl+C to stop.'
& '.\.venv\Scripts\python.exe' -m argus.cli serve


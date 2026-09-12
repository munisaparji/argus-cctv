$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { python -m venv .venv }
& '.\.venv\Scripts\python.exe' -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Python setup failed' }
Push-Location 'apps\console'
try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Frontend setup failed' } } finally { Pop-Location }
& '.\.venv\Scripts\python.exe' -m argus.cli schema
Push-Location 'apps\console'
try { npm.cmd run types; if ($LASTEXITCODE -ne 0) { throw 'Type generation failed' } } finally { Pop-Location }
Write-Host 'Setup complete. Run .\start.ps1'


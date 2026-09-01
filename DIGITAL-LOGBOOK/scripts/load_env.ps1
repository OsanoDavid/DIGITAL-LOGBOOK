<#
PowerShell helper to load variables from a local .env file into the current session.
Usage (dot-source so variables are set in your shell):
. .\scripts\load_env.ps1

This script reads the top-level `.env` file and sets matching environment variables
for the current PowerShell session. It ignores blank lines and lines starting with #.
#>

$scriptParent = Split-Path -Parent $MyInvocation.MyCommand.Definition
# .env is expected at the project root (one level above the scripts folder)
$envFile = Join-Path -Path $scriptParent -ChildPath "..\.env"
$envFile = (Resolve-Path -Path $envFile -ErrorAction SilentlyContinue).Path
if (-not $envFile) {
    Write-Host "No .env file found at workspace root. Create one from .env.example and paste your secrets there." -ForegroundColor Yellow
    return
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ([string]::IsNullOrWhiteSpace($line)) { return }
    if ($line.StartsWith('#')) { return }
    if ($line -notmatch '=') { return }
    $parts = $line -split '=', 2
    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    # Remove surrounding quotes if present
    if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }
    if ($value.StartsWith("'") -and $value.EndsWith("'")) { $value = $value.Trim("'") }
    Set-Item -Path Env:$name -Value $value
    Write-Host "Set env: $name" -ForegroundColor Green
}

Write-Host "Loaded .env into session. Run 'python scripts/send_test_email.py' in this shell to test." -ForegroundColor Cyan

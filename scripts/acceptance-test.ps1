[CmdletBinding()]
param(
    [switch]$Offline,
    [switch]$Extended,
    [string]$CodexBin = "codex",
    [string]$Report = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$Python = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
}
else {
    Write-Error "Python was not found. Install Python 3 and ensure 'py' or 'python' is on PATH."
    exit 2
}

$ArgsList = @((Join-Path $RepoRoot "scripts\acceptance_test_codex.py"))

if ($Offline) {
    $ArgsList += "--offline"
}
else {
    $ArgsList += "--live"
}

if ($Extended) {
    if ($Offline) {
        Write-Error "-Extended cannot be used with -Offline."
        exit 2
    }
    $ArgsList += "--extended"
}

$ArgsList += @("--codex-bin", $CodexBin)
if ($Report -ne "") {
    $ArgsList += @("--report", $Report)
}

Write-Host "Engineering Agent Stack - Windows acceptance"
Write-Host "Repository: $RepoRoot"
Write-Host "Mode: $(if ($Offline) { 'offline' } elseif ($Extended) { 'live-extended' } else { 'live' })"
Write-Host ""

& $Python @ArgsList
$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "Acceptance completed without blocking failures." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Acceptance found blocking failures. Review the generated report." -ForegroundColor Red
}

exit $ExitCode

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
    Write-Error "Python was not found. Install Python 3.10+ and ensure 'py' or 'python' is on PATH."
    exit 2
}

$PythonVersion = & $Python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Unable to execute Python through '$Python'."
    exit 2
}

$VersionParts = $PythonVersion.Trim().Split('.')
if ([int]$VersionParts[0] -lt 3 -or ([int]$VersionParts[0] -eq 3 -and [int]$VersionParts[1] -lt 10)) {
    Write-Error "Python $PythonVersion is too old. Engineering Agent Stack requires Python 3.10 or newer."
    exit 2
}

if (-not $Offline) {
    $CodexCommand = Get-Command $CodexBin -ErrorAction SilentlyContinue
    if (-not $CodexCommand) {
        Write-Host "Codex CLI was not found on PATH." -ForegroundColor Red
        Write-Host "Requested command: $CodexBin"
        Write-Host "Check with: Get-Command codex"
        Write-Host "If Codex exists at a custom path, run:"
        Write-Host ".\scripts\acceptance-test.ps1 -CodexBin 'C:\path\to\codex.exe'"
        Write-Host "You can still run the non-model acceptance with:"
        Write-Host ".\scripts\acceptance-test.ps1 -Offline"
        exit 2
    }
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
Write-Host "Python: $PythonVersion"
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

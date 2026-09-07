[CmdletBinding()]
param(
    [switch]$Offline,
    [switch]$Extended,
    [switch]$StrictDelegation,
    [string]$CodexBin = "codex",
    [string]$Report = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$PythonExe = $null
$PythonPrefix = @()
$PythonVersion = $null

function Test-PythonCandidate {
    param(
        [string]$Exe,
        [string[]]$Prefix
    )
    try {
        $version = & $Exe @Prefix -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $version) {
            return $null
        }
        $parts = $version.Trim().Split('.')
        if ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 9)) {
            return $version.Trim()
        }
    }
    catch {
        return $null
    }
    return $null
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    $candidateVersion = Test-PythonCandidate -Exe "python" -Prefix @()
    if ($candidateVersion) {
        $PythonExe = "python"
        $PythonVersion = $candidateVersion
    }
}

if (-not $PythonExe -and (Get-Command py -ErrorAction SilentlyContinue)) {
    foreach ($minor in 13, 12, 11, 10, 9) {
        $candidatePrefix = @("-3.$minor")
        $candidateVersion = Test-PythonCandidate -Exe "py" -Prefix $candidatePrefix
        if ($candidateVersion) {
            $PythonExe = "py"
            $PythonPrefix = $candidatePrefix
            $PythonVersion = $candidateVersion
            break
        }
    }
}

if (-not $PythonExe) {
    Write-Host "A supported Python interpreter was not found." -ForegroundColor Red
    Write-Host "Engineering Agent Stack requires Python 3.9 or newer; Python 3.11/3.12 is recommended."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        Write-Host "Installed Python versions:"
        & py -0p
    }
    exit 2
}

if ($Extended -or $StrictDelegation) {
    Write-Host "Provider delegation tests were moved out of the release gate." -ForegroundColor Yellow
    Write-Host "Use: .\scripts\provider-probe.ps1$(if ($Extended) { ' -Extended' } else { '' })"
    exit 2
}

if (-not $Offline -and -not (Get-Command $CodexBin -ErrorAction SilentlyContinue)) {
    Write-Host "Codex CLI was not found on PATH." -ForegroundColor Red
    Write-Host "Requested command: $CodexBin"
    Write-Host "Use -Offline for stack/install validation without model calls, or pass -CodexBin with the exact launcher path."
    exit 2
}

$ArgsList = @((Join-Path $RepoRoot "scripts\acceptance_core.py"))
if ($Offline) {
    $ArgsList += "--offline"
}
else {
    $ArgsList += "--live"
}
$ArgsList += @("--codex-bin", $CodexBin)
if ($Report -ne "") {
    $ArgsList += @("--report", $Report)
}

Write-Host "Engineering Agent Stack - Windows acceptance"
Write-Host "Repository: $RepoRoot"
Write-Host "Python: $PythonVersion ($PythonExe $($PythonPrefix -join ' '))"
Write-Host "Python text mode: UTF-8 (wrapper + explicit subprocess decoding)"
Write-Host "Scope: stack-owned release gate; provider child spawning/model routing excluded"
Write-Host "Mode: $(if ($Offline) { 'offline' } else { 'live' })"
Write-Host ""

$PythonArgs = @()
$PythonArgs += $PythonPrefix
$PythonArgs += @("-X", "utf8")
$PythonArgs += $ArgsList

& $PythonExe @PythonArgs
$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "Acceptance completed without blocking failures." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Acceptance found blocking stack-owned failures. Review the generated report." -ForegroundColor Red
}

exit $ExitCode

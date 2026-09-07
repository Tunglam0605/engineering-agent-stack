[CmdletBinding()]
param(
    [switch]$Extended,
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
    exit 2
}

if (-not (Get-Command $CodexBin -ErrorAction SilentlyContinue)) {
    Write-Host "Codex CLI was not found on PATH." -ForegroundColor Red
    Write-Host "Requested command: $CodexBin"
    exit 2
}

$ArgsList = @((Join-Path $RepoRoot "scripts\provider_probe_codex.py"))
$ArgsList += @("--codex-bin", $CodexBin)
if ($Extended) {
    $ArgsList += "--extended"
}
if ($Report -ne "") {
    $ArgsList += @("--report", $Report)
}

Write-Host "Engineering Agent Stack - Codex provider probe"
Write-Host "Repository: $RepoRoot"
Write-Host "Python: $PythonVersion ($PythonExe $($PythonPrefix -join ' '))"
Write-Host "Python text mode: UTF-8 (wrapper + explicit subprocess decoding)"
Write-Host "Scope: provider/runtime diagnostic only; this does NOT gate stack release"
Write-Host "Mode: $(if ($Extended) { 'extended' } else { 'basic' })"
Write-Host ""

$PythonArgs = @()
$PythonArgs += $PythonPrefix
$PythonArgs += @("-X", "utf8")
$PythonArgs += $ArgsList

& $PythonExe @PythonArgs
$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "Provider probe passed on this Codex runtime." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Provider probe found Codex runtime/delegation gaps. Stack release status is unchanged." -ForegroundColor Yellow
}

exit $ExitCode

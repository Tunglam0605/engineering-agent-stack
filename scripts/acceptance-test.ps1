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
$ResolvedCodexBin = $CodexBin
$ActualCodexBin = $CodexBin
$AcceptanceCodexWrapper = $null

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

# Prefer the active `python` on PATH first. This preserves virtualenv/setup-python
# environments where dependencies were installed into that interpreter.
if (Get-Command python -ErrorAction SilentlyContinue) {
    $candidateVersion = Test-PythonCandidate -Exe "python" -Prefix @()
    if ($candidateVersion) {
        $PythonExe = "python"
        $PythonVersion = $candidateVersion
    }
}

# If PATH's Python is old/missing, use the newest supported Windows py-launcher
# interpreter. Python 3.9 is intentionally supported because the repository
# uses a conditional `tomli` compatibility dependency for pre-3.11 runtimes.
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
    Write-Host "Engineering Agent Stack requires Python 3.9 or newer; Python 3.11/3.12 is recommended for new installations."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        Write-Host "Installed Python versions:"
        & py -0p
    }
    Write-Host "Recommended Windows install command for a new interpreter:"
    Write-Host "winget install -e --id Python.Python.3.12"
    exit 2
}

if ($Offline -and $StrictDelegation) {
    Write-Error "-StrictDelegation requires live Codex execution and cannot be combined with -Offline."
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
    if ($CodexCommand.Source) {
        $ResolvedCodexBin = $CodexCommand.Source

        # npm installs sibling .ps1 and .cmd launchers. PowerShell normally
        # resolves the .ps1 first, but `codex exec ... -` uses a lone '-' stdin
        # marker that is fragile when a shim is re-entered via powershell -File.
        # Prefer the .cmd sibling so the complete argv reaches Codex unchanged.
        if ([System.IO.Path]::GetExtension($ResolvedCodexBin).ToLowerInvariant() -eq ".ps1") {
            $CmdSibling = [System.IO.Path]::ChangeExtension($ResolvedCodexBin, ".cmd")
            if (Test-Path -LiteralPath $CmdSibling) {
                $ResolvedCodexBin = $CmdSibling
            }
        }
    }

    $ActualCodexBin = $ResolvedCodexBin

    # Live acceptance is executed in a fresh temporary repository. Current Codex
    # deliberately loads project-local .codex/config.toml as disabled until that
    # project is trusted. Session flags therefore enable V2 and, when the harness
    # is running inside its installed sandbox, explicitly register all seven role
    # files by absolute path. This keeps the test isolated from personal trust/config.
    $AcceptanceCodexWrapper = Join-Path ([System.IO.Path]::GetTempPath()) ("engineering-agent-stack-codex-" + [guid]::NewGuid().ToString("N") + ".cmd")

    # IMPORTANT: this text is embedded inside a Windows .cmd quoted argument.
    # Do not put literal double quotes in the instruction value: cmd.exe does
    # not use backslash as a quote escape and would split the -c argument.
    $AcceptanceDeveloperInstructions = 'Engineering Agent Stack acceptance policy. The disposable acceptance sandbox changes requested by this harness are already authorized, so do not ask the user for confirmation. If and only if the user prompt begins with the literal prefix Acceptance test., the requested named custom agent is mandatory. Call spawn_agent exactly once for that role, set agent_type to the requested custom role, set fork_turns to none, put the complete assignment in the child message, wait for the child result, and never perform the requested child task directly in the parent. If spawn_agent fails, report that failure instead of falling back. For prompts without that literal prefix, follow the normal repository orchestration policy and direct-first rule.'
    $BaseInvocation = ('"' + $ActualCodexBin + '" -c "approval_policy=''never''" -c "agents.enabled=true" -c "features.multi_agent_v2.enabled=true" -c "features.multi_agent_v2.wait_agent_enabled=true" -c "features.multi_agent_v2.non_code_mode_only=true" -c "features.multi_agent_v2.hide_spawn_agent_metadata=false" -c "features.multi_agent_v2.expose_spawn_agent_model_overrides=true" -c "developer_instructions=''' + $AcceptanceDeveloperInstructions + '''"')
    $RoleOverrides = '-c "agents.scout.config_file=''%CD%\.codex\agents\scout.toml''" -c "agents.researcher.config_file=''%CD%\.codex\agents\researcher.toml''" -c "agents.implementer.config_file=''%CD%\.codex\agents\implementer.toml''" -c "agents.debugger.config_file=''%CD%\.codex\agents\debugger.toml''" -c "agents.test-engineer.config_file=''%CD%\.codex\agents\test-engineer.toml''" -c "agents.reviewer.config_file=''%CD%\.codex\agents\reviewer.toml''" -c "agents.architect.config_file=''%CD%\.codex\agents\architect.toml''"'
    $WrapperLines = @(
        '@echo off',
        'if exist "%CD%\.codex\agents\scout.toml" goto with_roles',
        ($BaseInvocation + ' %*'),
        'exit /b %ERRORLEVEL%',
        ':with_roles',
        ($BaseInvocation + ' ' + $RoleOverrides + ' %*'),
        'exit /b %ERRORLEVEL%'
    )
    Set-Content -LiteralPath $AcceptanceCodexWrapper -Value $WrapperLines -Encoding ASCII
    $ResolvedCodexBin = $AcceptanceCodexWrapper
}

$ArgsList = @((Join-Path $RepoRoot "scripts\acceptance_gate.py"))

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

if ($StrictDelegation) {
    $ArgsList += "--strict-delegation"
}

$ArgsList += @("--codex-bin", $ResolvedCodexBin)
if ($Report -ne "") {
    $ArgsList += @("--report", $Report)
}

Write-Host "Engineering Agent Stack - Windows acceptance"
Write-Host "Repository: $RepoRoot"
Write-Host "Python: $PythonVersion ($PythonExe $($PythonPrefix -join ' '))"
Write-Host "Python text mode: UTF-8"
if (-not $Offline) {
    Write-Host "Codex launcher: $ActualCodexBin"
    Write-Host "Acceptance runtime: non-interactive approval + forced Multi-Agent V2 + explicit session role registration"
    if ($StrictDelegation) {
        Write-Host "Delegation gate: strict (provider child-spawn failures are blocking)"
    }
    else {
        Write-Host "Delegation gate: provider-observational (provider child-spawn failures are warnings)"
    }
}
Write-Host "Mode: $(if ($Offline) { 'offline' } elseif ($Extended) { 'live-extended' } else { 'live' })"
Write-Host ""

# Windows developer environments often inherit a legacy ANSI code page such as
# cp1252. Codex JSONL is UTF-8 and may contain Unicode characters, so force
# Python UTF-8 mode for the entire acceptance process and all text-mode child
# subprocess pipes. This prevents locale-dependent UnicodeDecodeError failures.
$PythonArgs = @()
$PythonArgs += $PythonPrefix
$PythonArgs += @("-X", "utf8")
$PythonArgs += $ArgsList

try {
    & $PythonExe @PythonArgs
    $ExitCode = $LASTEXITCODE
}
finally {
    if ($AcceptanceCodexWrapper -and (Test-Path -LiteralPath $AcceptanceCodexWrapper)) {
        Remove-Item -LiteralPath $AcceptanceCodexWrapper -Force -ErrorAction SilentlyContinue
    }
}

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "Acceptance completed without blocking failures." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Acceptance found blocking failures. Review the generated report." -ForegroundColor Red
}

exit $ExitCode

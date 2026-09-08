param(
    [ValidateSet("main")]
    [string]$Ref = "main",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/Tunglam0605/engineering-agent-stack.git"
$CodexHome = Join-Path $HOME ".codex"
$Checkout = Join-Path $CodexHome "engineering-agent-stack"
$VenvDir = Join-Path $Checkout ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$BinDir = Join-Path $HOME ".local\bin"

function Find-Python {
    $candidates = @(
        @("py", "-3.9"),
        @("python", ""),
        @("python3", "")
    )
    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate[0] -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $prefix = @()
        if ($candidate[1]) { $prefix += $candidate[1] }
        & $candidate[0] @prefix -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return @($candidate[0]) + $prefix }
    }
    throw "Python 3.9+ is required."
}

function Invoke-BootstrapPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $exe = $BootstrapPython[0]
    $prefix = @()
    if ($BootstrapPython.Length -gt 1) {
        $prefix = $BootstrapPython[1..($BootstrapPython.Length - 1)]
    }
    $output = & $exe @prefix @Arguments
    $code = $LASTEXITCODE
    if ($output) { $output | ForEach-Object { Write-Host $_ } }
    return $code
}

function Invoke-RuntimePython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $output = & $VenvPython @Arguments
    $code = $LASTEXITCODE
    if ($output) { $output | ForEach-Object { Write-Host $_ } }
    return $code
}

function Ensure-Runtime {
    if (-not (Test-Path $VenvPython)) {
        $code = Invoke-BootstrapPython -m venv $VenvDir
        if ($code -ne 0) { throw "Unable to create managed Python virtual environment: $VenvDir" }
    }
    & $VenvPython -c "import importlib.util,sys; ok_yaml=importlib.util.find_spec('yaml') is not None; ok_toml=sys.version_info >= (3,11) or importlib.util.find_spec('tomli') is not None; raise SystemExit(0 if ok_yaml and ok_toml else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        & $VenvPython -m pip install --disable-pip-version-check "PyYAML>=6.0.2,<7" "tomli>=2.0.1,<3; python_version < '3.11'"
        if ($LASTEXITCODE -ne 0) { throw "Unable to install EAS runtime dependencies (PyYAML and Python 3.9/3.10 tomli)." }
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required."
}

$BootstrapPython = @(Find-Python)
New-Item -ItemType Directory -Force -Path $CodexHome | Out-Null

if (Test-Path (Join-Path $Checkout ".git")) {
    $dirty = git -C $Checkout status --porcelain --untracked-files=all
    if ($dirty) { throw "Managed checkout is dirty: $Checkout" }

    Ensure-Runtime
    $ExistingCli = Join-Path $Checkout "scripts\eas.py"
    if (Test-Path $ExistingCli) {
        $code = Invoke-RuntimePython (Join-Path $Checkout "scripts\install_codex.py") --personal --check
        if ($code -ne 0) {
            throw "Existing EAS installation is not clean; refusing to update the managed checkout."
        }
        $code = Invoke-RuntimePython $ExistingCli update
        if ($code -ne 0) { exit $code }
    } else {
        # Upgrade path from pre-v0.3. The managed venv supplies tomli on Python
        # 3.9/3.10 so the old installer can validate before source mutation.
        $code = Invoke-RuntimePython (Join-Path $Checkout "scripts\install_codex.py") --personal --check
        if ($code -ne 0) {
            throw "Existing pre-v0.3 EAS installation is not clean; refusing source update."
        }
        git -C $Checkout fetch origin $Ref
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        git -C $Checkout checkout $Ref
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        git -C $Checkout merge --ff-only "origin/$Ref"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
} elseif (Test-Path $Checkout) {
    throw "Target exists but is not a Git checkout: $Checkout"
} else {
    git clone --branch $Ref --single-branch $RepoUrl $Checkout
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Ensure-Runtime
& $VenvPython -m pip install --disable-pip-version-check --upgrade $Checkout
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$InstallScript = Join-Path $Checkout "scripts\install_codex.py"
$code = Invoke-RuntimePython $InstallScript --personal --dry-run
if ($code -ne 0) { exit $code }

$InstallArgs = @($InstallScript, "--personal")
if ($Force) { $InstallArgs += "--force" }
$code = Invoke-RuntimePython @InstallArgs
if ($code -ne 0) { exit $code }

$code = Invoke-RuntimePython $InstallScript --personal --check
if ($code -ne 0) { exit $code }

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
$Launcher = Join-Path $BinDir "eas.cmd"
@"
@echo off
"$VenvPython" "$Checkout\scripts\eas.py" %*
"@ | Set-Content -LiteralPath $Launcher -Encoding ASCII

Write-Host "Engineering Agent Stack installed."
Write-Host "Managed runtime: $VenvDir"
Write-Host "Launcher: $Launcher"
Write-Host "PATH was not modified. Add $BinDir to PATH yourself if needed."
Write-Host "Run: $Launcher doctor"

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repoRoot

function Stop-WithPrerequisiteHelp([string]$message, [string]$help) {
    Write-Error "$message`n$help"
    exit 1
}

Write-Host "ARTERIA setup on $([System.Runtime.InteropServices.RuntimeInformation]::OSDescription) ($([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture))"

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm -ErrorAction SilentlyContinue
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if (-not $nodeCommand) {
    Stop-WithPrerequisiteHelp 'Node.js was not found.' 'Install Node.js 24 LTS from https://nodejs.org/en/download/ and reopen PowerShell.'
}
if (-not $npmCommand) {
    Stop-WithPrerequisiteHelp 'npm was not found.' 'Install Node.js 24 LTS from https://nodejs.org/en/download/; npm is included with Node.js.'
}
if (-not $uvCommand) {
    Stop-WithPrerequisiteHelp 'uv was not found.' 'Install uv for your user with: winget install --id=astral-sh.uv -e. Or follow https://docs.astral.sh/uv/getting-started/installation/, then reopen PowerShell.'
}

$nodeVersion = (& node --version).Trim()
if ($nodeVersion -notmatch '^v?24\.') {
    Stop-WithPrerequisiteHelp "Node.js 24.x is required; found $nodeVersion." 'Install Node.js 24 LTS from https://nodejs.org/en/download/ and select it in your terminal.'
}
Write-Host "Node.js $nodeVersion; npm $(& npm --version)"
Write-Host "uv $(& uv --version)"

$pythonInstallDir = Join-Path $repoRoot '.uv-python'
$env:UV_PYTHON_INSTALL_DIR = $pythonInstallDir
$python312 = & uv python find --managed-python 3.12 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Acquiring a project-local Python 3.12 runtime with uv in $pythonInstallDir..."
    & uv python install 3.12 --install-dir $pythonInstallDir --no-bin
    if ($LASTEXITCODE -ne 0) { throw 'uv could not acquire Python 3.12. Check uv installation permissions and its Python download output.' }
    $python312 = & uv python find --managed-python 3.12
    if ($LASTEXITCODE -ne 0) { throw 'uv installed Python 3.12 but could not find the managed interpreter.' }
} else {
    Write-Host "Using uv-managed Python 3.12 at $($python312.Trim())"
}

Write-Host 'Installing the locked Python environment...'
& uv sync --locked
if ($LASTEXITCODE -ne 0) { throw 'uv sync --locked failed. Check the Python version and package installation output.' }

Write-Host 'Installing locked frontend dependencies...'
Push-Location -LiteralPath (Join-Path $repoRoot 'frontend')
try {
    & npm ci
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed. Check the Node.js 24 and npm output.' }
} finally {
    Pop-Location
}

Write-Host 'Checking optional SUMO availability and Python integration...'
& uv run --locked python -m sim.sumo_support --smoke
if ($LASTEXITCODE -ne 0) {
    Write-Warning 'SUMO was detected but its optional smoke test did not pass. Basic frontend/backend startup remains available; see the SUMO status above.'
}

Write-Host 'Running project validation...'
& (Join-Path $PSScriptRoot 'check.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Project validation failed. See the preceding check output.' }
Write-Host 'ARTERIA setup completed.'

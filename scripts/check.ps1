$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repoRoot

foreach ($commandName in @('uv', 'npm', 'node')) {
    if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "$commandName was not found. Install prerequisites and run scripts/setup.ps1 first."
    }
}
$nodeVersion = (& node --version).Trim()
if ($nodeVersion -notmatch '^v?24\.') { throw "Node.js 24.x is required; found $nodeVersion." }

Write-Host 'Running Python backend and spatial smoke tests...'
& uv run --locked pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Python tests failed.' }
& uv run --locked python scripts/health_smoke.py
if ($LASTEXITCODE -ne 0) { throw 'Backend HTTP health smoke test failed.' }

Write-Host 'Running frontend TypeScript and production build checks...'
Push-Location -LiteralPath (Join-Path $repoRoot 'frontend')
try {
    & npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw 'Frontend TypeScript check failed.' }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend production build failed.' }
} finally {
    Pop-Location
}

Write-Host 'Checking optional SUMO installation and running its real smoke test when available...'
& uv run --locked python -m sim.sumo_support --smoke
if ($LASTEXITCODE -ne 0) { Write-Warning 'Optional SUMO smoke test failed. Basic frontend/backend checks passed; SUMO is not marked ready.' }
Write-Host 'Project checks completed.'

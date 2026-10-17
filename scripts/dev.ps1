$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

foreach ($commandName in @('uv', 'npm', 'node')) {
    if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "$commandName was not found. Install prerequisites and run scripts/setup.ps1 first."
    }
}
$nodeVersion = (& node --version).Trim()
if ($nodeVersion -notmatch '^v?24\.') { throw "Node.js 24.x is required; found $nodeVersion. Run scripts/setup.ps1 after selecting Node.js 24." }
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'frontend\node_modules'))) {
    throw 'Frontend dependencies are missing. Run scripts/setup.ps1 first.'
}

$backendJob = $null
$frontendJob = $null
try {
    $backendJob = Start-Job -Name 'arteria-backend' -ArgumentList $repoRoot -ScriptBlock {
        param($root)
        Set-Location -LiteralPath $root
        uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
    }
    $frontendJob = Start-Job -Name 'arteria-frontend' -ArgumentList $repoRoot -ScriptBlock {
        param($root)
        Set-Location -LiteralPath (Join-Path $root 'frontend')
        npm run dev -- --host 127.0.0.1
    }

    Write-Host 'ARTERIA development services are starting:'
    Write-Host '  Frontend: http://127.0.0.1:5173'
    Write-Host '  Backend:  http://127.0.0.1:8000/health'
    Write-Host 'Press Ctrl+C to stop both services.'

    while ($true) {
        foreach ($job in @($backendJob, $frontendJob)) {
            Receive-Job -Job $job -ErrorAction Continue
            if ($job.State -in @('Failed', 'Completed', 'Stopped')) {
                throw "Service job '$($job.Name)' stopped with state $($job.State)."
            }
        }
        Start-Sleep -Seconds 1
    }
} finally {
    $jobs = @($backendJob, $frontendJob) | Where-Object { $_ -ne $null }
    if ($jobs.Count -gt 0) {
        Stop-Job -Job $jobs -ErrorAction SilentlyContinue
        Remove-Job -Job $jobs -Force -ErrorAction SilentlyContinue
    }
}

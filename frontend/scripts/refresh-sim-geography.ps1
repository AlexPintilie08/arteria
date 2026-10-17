param(
  [string]$SimWorkspace = (Join-Path $PSScriptRoot '..\..'),
  [string]$PythonPath = ''
)

$ErrorActionPreference = 'Stop'
$resolvedSimWorkspace = (Resolve-Path -LiteralPath $SimWorkspace).Path
$outputDirectory = Join-Path $PSScriptRoot '..\web\public\data'
$exporter = Join-Path $PSScriptRoot 'export_sim_geography.py'

if (-not $PythonPath) {
  $candidate = Join-Path $resolvedSimWorkspace '.venv\Scripts\python.exe'
  if (Test-Path -LiteralPath $candidate) {
    $PythonPath = $candidate
  } else {
    $pythonCommand = Get-Command python -ErrorAction Stop
    $PythonPath = $pythonCommand.Source
  }
}

if (-not (Test-Path -LiteralPath $PythonPath)) {
  throw "Python executable not found: $PythonPath"
}

& $PythonPath $exporter --sim-workspace $resolvedSimWorkspace --output-directory $outputDirectory
if ($LASTEXITCODE -ne 0) {
  throw "SIM geography export failed with exit code $LASTEXITCODE"
}

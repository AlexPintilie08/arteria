param([string]$Python='python')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
& $Python (Join-Path $PSScriptRoot 'build_deck.py')
if ($LASTEXITCODE -ne 0) { throw 'Static build failed' }
& (Join-Path $PSScriptRoot 'apply_motion.ps1')
& (Join-Path $PSScriptRoot 'render_deck.ps1') -InputDeck (Join-Path $root 'reports/.qa/build/animated.pptx') -Pdf
& $Python (Join-Path $PSScriptRoot 'qa_deck.py') --deck (Join-Path $root 'reports/.qa/build/animated.pptx')
if ($LASTEXITCODE -ne 0) { throw 'QA failed; current final preserved' }
& $Python -X utf8 (Join-Path $PSScriptRoot 'validate_package.py') (Join-Path $root 'reports/.qa/build/animated.pptx')
if ($LASTEXITCODE -ne 0) { throw 'Package validation failed; current final preserved' }
Copy-Item -LiteralPath (Join-Path $root 'reports/.qa/build/animated.pptx') -Destination (Join-Path $root 'Template-Pitch-Hackathon.pptx') -Force
Write-Output 'Verified V2 published.'

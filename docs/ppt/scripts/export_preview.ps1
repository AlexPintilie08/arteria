param([string]$InputDeck = 'docs/ppt/ARTERIA.pptx')
& (Join-Path $PSScriptRoot 'render_deck.ps1') -InputDeck $InputDeck -OutputDir 'docs/ppt/preview' -Pdf

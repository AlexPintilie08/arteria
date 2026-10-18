param([string]$InputDeck = 'docs/ppt/Template-Pitch-Hackathon.pptx')
& (Join-Path $PSScriptRoot 'render_deck.ps1') -InputDeck $InputDeck -OutputDir 'docs/ppt/preview' -Pdf

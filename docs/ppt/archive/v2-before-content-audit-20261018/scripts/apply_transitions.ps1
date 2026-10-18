# Compatibility entry point. V2 applies object animations as well as transitions.
param(
    [string]$InputDeck = 'docs/ppt/reports/.qa/build/static.pptx',
    [string]$OutputDeck = 'docs/ppt/reports/.qa/build/animated.pptx'
)
& (Join-Path $PSScriptRoot 'apply_motion.ps1') -InputDeck $InputDeck -OutputDeck $OutputDeck

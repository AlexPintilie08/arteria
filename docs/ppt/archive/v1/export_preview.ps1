$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pptPath = (Resolve-Path "docs\ppt\Template-Pitch-Hackathon.pptx").Path
    $outDir = (Resolve-Path "docs\ppt\preview").Path
    $pres = $ppt.Presentations.Open($pptPath, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    $pres.Export($outDir, "PNG", 1920, 1080)
    $pres.Close()
    Write-Host "Export completed successfully to $outDir"
} finally {
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pptPath = (Resolve-Path "docs\ppt\Template-Pitch-Hackathon.pptx").Path
    $pres = $ppt.Presentations.Open($pptPath, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    
    foreach ($slide in $pres.Slides) {
        $slide.SlideShowTransition.EntryEffect = 1537 # ppEffectFade
        $slide.SlideShowTransition.Duration = 0.5
    }
    
    $pres.Save()
    $pres.Close()
    Write-Host "Applied smooth fade transition (0.5s) to all 16 slides!"
} finally {
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

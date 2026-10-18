param(
    [string]$InputDeck = 'docs/ppt/reports/.qa/build/static.pptx',
    [string]$OutputDeck = 'docs/ppt/reports/.qa/build/animated.pptx'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$sourcePath = (Resolve-Path -LiteralPath $InputDeck).Path
$targetPath = [IO.Path]::GetFullPath($OutputDeck)
$plan = Get-Content -Raw -LiteralPath (Join-Path $root 'reports/motion-plan.json') | ConvertFrom-Json
$ppt = New-Object -ComObject PowerPoint.Application
$initialCount = $ppt.Presentations.Count
$pres = $null
try {
    foreach ($opened in $ppt.Presentations) {
        if ($opened.FullName -eq $sourcePath -or $opened.FullName -eq $targetPath) {
            throw 'A staging deck is already open. Close it before applying motion; no user document will be closed.'
        }
    }
    $pres = $ppt.Presentations.Open($sourcePath, 0, 0, 0)
    if ($pres.Slides.Count -ne 10) { throw "Expected exactly 10 submission slides, found $($pres.Slides.Count)." }
    $result = @()
    foreach ($slide in $pres.Slides) {
        $seq = $slide.TimeLine.MainSequence
        while ($seq.Count -gt 0) { $seq.Item(1).Delete() }
        $slide.SlideShowTransition.EntryEffect = 3849 # ppEffectFadeSmoothly
        $slide.SlideShowTransition.Duration = 0.45
        $slide.SlideShowTransition.AdvanceOnClick = -1
        $slide.SlideShowTransition.AdvanceOnTime = 0
        $slide.SlideShowTransition.AdvanceTime = 0
        $rows = @()
        foreach ($item in @($plan | Where-Object { $_.slide -eq $slide.SlideIndex })) {
            $shape = $slide.Shapes.Item([string]$item.shape)
            $effectId = switch ($item.effect) {
                'fade' { 10 }
                'wipe' { 22 }
                'float' { 30 }
                default { throw "Unsupported native PowerPoint effect '$($item.effect)' on slide $($slide.SlideIndex)." }
            }
            $trigger = switch ($item.trigger) { 'auto' {2}; 'after' {3}; 'click' {1}; default {throw 'Unknown trigger'} }
            $fx = $seq.AddEffect($shape, $effectId, 0, $trigger)
            $fx.Timing.Duration = [single]$item.duration
            $fx.Timing.TriggerDelayTime = [single]$item.delay
            if ($effectId -eq 22) { $fx.EffectParameters.Direction = 4 } # msoAnimDirectionLeft
            $fx.Timing.Duration = [single]$item.duration # Direction can reset Wipe timing.
            $rows += [PSCustomObject]@{
                shape=$fx.Shape.Name; shapeId=$fx.Shape.Id; effectId=$fx.EffectType
                effect=$item.effect
                trigger=$fx.Timing.TriggerType; duration=$fx.Timing.Duration
                delay=$fx.Timing.TriggerDelayTime
            }
        }
        $result += [PSCustomObject]@{
            slide=$slide.SlideIndex; transition=$slide.SlideShowTransition.EntryEffect
            transitionDuration=$slide.SlideShowTransition.Duration
            advanceOnClick=$slide.SlideShowTransition.AdvanceOnClick
            advanceOnTime=$slide.SlideShowTransition.AdvanceOnTime
            effects=$rows
        }
    }
    $pres.SaveAs($targetPath, 24)
    [PSCustomObject]@{powerPointVersion=$ppt.Version; slides=$result; visualPlaybackVerified=$false} |
        ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $root 'reports/motion-com.json')
        Write-Output "Applied native editable animations and 0.45s Fade transitions to 10 slides: $targetPath"
} finally {
    if ($null -ne $pres) { $pres.Close() }
    if ($initialCount -eq 0) { $ppt.Quit() }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ppt)
}

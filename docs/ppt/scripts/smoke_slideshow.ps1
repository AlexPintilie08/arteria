param([string]$Deck='docs/ppt/ARTERIA.pptx')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$deckPath=(Resolve-Path -LiteralPath $Deck).Path
$motion=Get-Content -Raw -LiteralPath (Join-Path $root 'reports/motion-com.json') | ConvertFrom-Json
$ppt=New-Object -ComObject PowerPoint.Application
$initialCount=$ppt.Presentations.Count
$presentation=$null;$show=$null
$steps=[System.Collections.Generic.List[object]]::new()
try{
    foreach($opened in $ppt.Presentations){
        if($opened.FullName -eq $deckPath){throw 'The target deck is already open; slideshow smoke test skipped to protect the open session.'}
    }
    $presentation=$ppt.Presentations.Open($deckPath,-1,0,0)
    if($presentation.Slides.Count -ne 10){throw "Expected 10 slides, found $($presentation.Slides.Count)."}
    $presentation.SlideShowSettings.AdvanceMode=1 # ppSlideShowManualAdvance
    $show=$presentation.SlideShowSettings.Run()
    Start-Sleep -Milliseconds 900
    for($i=1;$i -le 10;$i++){
        $view=$show.View
        if($view.CurrentShowPosition -ne $i){throw "Expected slide $i, slideshow is on $($view.CurrentShowPosition)."}
        $slideData=$motion.slides[$i-1]
        $firstClick=-1
        for($j=0;$j -lt $slideData.effects.Count;$j++){
            if($slideData.effects[$j].trigger -eq 1){$firstClick=$j;break}
        }
        if($firstClick -ge 0){
            $preMs=0
            for($j=0;$j -lt $firstClick;$j++){$preMs += [int](1000*($slideData.effects[$j].duration+$slideData.effects[$j].delay))}
            if($preMs -gt 0){Start-Sleep -Milliseconds ($preMs+100)}
            $view.Next()
            Start-Sleep -Milliseconds 150
            if($view.CurrentShowPosition -ne $i){throw "The reveal click on slide $i advanced the slide unexpectedly."}
            $postMs=0
            for($j=$firstClick;$j -lt $slideData.effects.Count;$j++){$postMs += [int](1000*($slideData.effects[$j].duration+$slideData.effects[$j].delay))}
            if($postMs -gt 0){Start-Sleep -Milliseconds ($postMs+150)}
        }else{
            $autoMs=0
            foreach($effect in $slideData.effects){$autoMs += [int](1000*($effect.duration+$effect.delay))}
            if($autoMs -gt 0){Start-Sleep -Milliseconds ($autoMs+150)}
        }
        $steps.Add([PSCustomObject]@{slide=$i;effects=$slideData.effects.Count;manualReveal=($firstClick -ge 0);revealClickPreservedSlide=($view.CurrentShowPosition -eq $i)})
        if($i -lt 10){
            $view.Next()
            Start-Sleep -Milliseconds 700
            if($view.CurrentShowPosition -ne ($i+1)){throw "Manual slide advance from $i failed."}
        }
    }
    $show.View.Exit()
    $show=$null
    $result=[ordered]@{powerPointVersion=$ppt.Version;slides=10;slidesVisited=$steps;allManualAdvancesWorked=$true;revealClicksStayedOnCurrentSlide=$true;nativeSlideshowStarted=$true;intermediateFramesVisuallyInspected=$false;limitation='COM slideshow was stepped successfully, but no screen capture was available to inspect intermediate animation frames.'}
    $result | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $root 'reports/playback-smoke.json')
    Write-Output 'PowerPoint native slideshow smoke completed across 10 slides.'
}finally{
    if($null -ne $show){try{$show.View.Exit()}catch{}}
    if($null -ne $presentation){try{$presentation.Close()}catch{}}
    if($initialCount -eq 0){$ppt.Quit()}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ppt)
}

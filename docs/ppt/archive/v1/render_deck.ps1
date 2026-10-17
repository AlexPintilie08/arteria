param(
    [string]$InputDeck = 'docs/ppt/Template-Pitch-Hackathon.pptx',
    [string]$OutputDir = 'docs/ppt/preview',
    [switch]$Pdf
)
$ErrorActionPreference = 'Stop'
$deckPath = (Resolve-Path -LiteralPath $InputDeck).Path
$null = New-Item -ItemType Directory -Force -Path $OutputDir
$previewPath = (Resolve-Path -LiteralPath $OutputDir).Path
$ppt = New-Object -ComObject PowerPoint.Application
$presentation = $null
try {
    $presentation = $ppt.Presentations.Open($deckPath, -1, 0, 0)
    $presentation.Export($previewPath, 'PNG', 1920, 1080)
    if ($Pdf) { $presentation.SaveAs((Join-Path $previewPath 'presentation.pdf'), 32) }
    $checks = @()
    foreach ($slide in $presentation.Slides) {
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
                $checks += [PSCustomObject]@{
                    slide=$slide.SlideIndex; name=$shape.Name
                    text=$shape.TextFrame.TextRange.Text
                    height=$shape.Height; boundHeight=$shape.TextFrame2.TextRange.BoundHeight
                    width=$shape.Width; boundWidth=$shape.TextFrame2.TextRange.BoundWidth
                }
            }
        }
    }
    $checks | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $previewPath 'text-bounds.json') -Encoding utf8
    Write-Output "PowerPoint opened and exported $($presentation.Slides.Count) slides to $previewPath"
} finally {
    if ($null -ne $presentation) { $presentation.Close() }
    $ppt.Quit()
    [void][System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt)
}

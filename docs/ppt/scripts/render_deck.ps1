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
$initialCount = $ppt.Presentations.Count
$presentation = $null
try {
    $presentation = $ppt.Presentations.Open($deckPath, -1, 0, 0)
    $presentation.Export($previewPath, 'PNG', 1920, 1080)
    if ($Pdf) { $presentation.SaveAs((Join-Path $previewPath 'presentation.pdf'), 32) }
    $checks = [System.Collections.Generic.List[object]]::new()
    function Inspect-Shapes($shapes, $slideNumber, $prefix) {
        foreach ($shape in $shapes) {
            if ($shape.Type -eq 6) {
                Inspect-Shapes $shape.GroupItems $slideNumber ($prefix + $shape.Name + '/')
            } elseif ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
                $checks.Add([PSCustomObject]@{
                    slide=$slideNumber; name=$prefix + $shape.Name
                    text=$shape.TextFrame.TextRange.Text
                    height=$shape.Height; boundHeight=$shape.TextFrame2.TextRange.BoundHeight
                    width=$shape.Width; boundWidth=$shape.TextFrame2.TextRange.BoundWidth
                })
            } elseif ($shape.HasTable -eq -1) {
                for ($ri=1; $ri -le $shape.Table.Rows.Count; $ri++) {
                    for ($ci=1; $ci -le $shape.Table.Columns.Count; $ci++) {
                        $cell=$shape.Table.Cell($ri,$ci).Shape
                        $checks.Add([PSCustomObject]@{
                            slide=$slideNumber; name=$prefix + $shape.Name + ":$ri/$ci"
                            text=$cell.TextFrame.TextRange.Text
                            height=$cell.Height; boundHeight=$cell.TextFrame2.TextRange.BoundHeight
                            width=$cell.Width; boundWidth=$cell.TextFrame2.TextRange.BoundWidth
                        })
                    }
                }
            }
        }
    }
    foreach ($slide in $presentation.Slides) { Inspect-Shapes $slide.Shapes $slide.SlideIndex '' }
    $checks | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path (Split-Path $PSScriptRoot -Parent) 'reports/text-bounds.json') -Encoding utf8
    Write-Output "PowerPoint opened and exported $($presentation.Slides.Count) slides to $previewPath"
} finally {
    if ($null -ne $presentation) { $presentation.Close() }
    if ($initialCount -eq 0) { $ppt.Quit() }
    [void][System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt)
}

param([string]$Python='python')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$qa=Join-Path $root 'reports/.qa/build'
$fullStatic=Join-Path $qa 'static.pptx'
$submissionStatic=Join-Path $qa 'submission-static.pptx'
$animated=Join-Path $qa 'animated-10-slide.pptx'
$previewBuild=Join-Path $root 'reports/.qa/preview-build'
$canonical=Join-Path $root 'ARTERIA.pptx'
$archive=Join-Path $root 'archive/premium-motion-20261018'
$null=New-Item -ItemType Directory -Force -Path $qa,$archive
foreach($path in @($submissionStatic,$animated)){
    if(Test-Path -LiteralPath $path){Remove-Item -LiteralPath $path -Force}
}
if(Test-Path -LiteralPath $previewBuild){Remove-Item -LiteralPath $previewBuild -Recurse -Force}

& $Python (Join-Path $PSScriptRoot 'build_deck.py')
if($LASTEXITCODE -ne 0){throw 'Full audited source build failed.'}
if(-not(Test-Path -LiteralPath $fullStatic)){throw 'Expected full audited staging deck was not created.'}
& $Python -X utf8 (Join-Path $PSScriptRoot 'audited_content.py') $fullStatic --submission $submissionStatic
if($LASTEXITCODE -ne 0){throw 'Extracting the audited ten-slide submission failed.'}
& (Join-Path $PSScriptRoot 'apply_motion.ps1') -InputDeck $submissionStatic -OutputDeck $animated
if($LASTEXITCODE -ne 0){throw 'PowerPoint motion generation failed.'}
& (Join-Path $PSScriptRoot 'render_deck.ps1') -InputDeck $animated -OutputDir $previewBuild -Pdf
if($LASTEXITCODE -ne 0){throw 'PowerPoint render and PDF export failed.'}
& $Python -X utf8 (Join-Path $PSScriptRoot 'qa_deck.py') --deck $animated --preview $previewBuild
if($LASTEXITCODE -ne 0){throw 'Motion and visual bounds QA failed; current canonical file preserved.'}
& $Python -X utf8 (Join-Path $PSScriptRoot 'validate_package.py') $animated
if($LASTEXITCODE -ne 0){throw 'PowerPoint package validation failed; current canonical file preserved.'}

# Publish only after the ten-slide deck, motion, renders, PDF, and package all pass.
$newHash=(Get-FileHash -LiteralPath $animated -Algorithm SHA256).Hash
$oldFull=Join-Path $root 'ARTERIA-Audited.pptx'
$oldSubmission=Join-Path $root 'ARTERIA-Submission.pptx'
$oldPdf=Join-Path $root 'ARTERIA-Submission.pdf'
$pdfBuild=Join-Path $previewBuild 'presentation.pdf'
if(-not(Test-Path -LiteralPath $pdfBuild)){throw 'Validated PowerPoint PDF export is missing.'}
function Move-ToArchive([string]$source,[string]$leaf){
    if(-not(Test-Path -LiteralPath $source)){return $null}
    $destination=Join-Path $archive $leaf
    if(Test-Path -LiteralPath $destination){
        $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
        $ext=[IO.Path]::GetExtension($leaf);$stem=[IO.Path]::GetFileNameWithoutExtension($leaf)
        $destination=Join-Path $archive ($stem+'-'+$stamp+$ext)
    }
    Move-Item -LiteralPath $source -Destination $destination
    return $destination
}
function Copy-ToArchive([string]$source,[string]$leaf){
    if(-not(Test-Path -LiteralPath $source)){return $null}
    $destination=Join-Path $archive $leaf
    if(Test-Path -LiteralPath $destination){
        $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
        $ext=[IO.Path]::GetExtension($leaf);$stem=[IO.Path]::GetFileNameWithoutExtension($leaf)
        $destination=Join-Path $archive ($stem+'-'+$stamp+$ext)
    }
    Copy-Item -LiteralPath $source -Destination $destination
    return $destination
}
$archived=[System.Collections.Generic.List[string]]::new()
foreach($entry in @(
    @{source=$canonical;leaf='ARTERIA-premium-motion-auto-reveals.pptx'},
    @{source=$oldPdf;leaf='ARTERIA-Submission-premium-motion-click-reveals.pdf'}
)){
    $saved=Copy-ToArchive $entry.source $entry.leaf
    if($saved){$archived.Add($saved)}
}
Copy-Item -LiteralPath $animated -Destination $canonical -Force
Copy-Item -LiteralPath $pdfBuild -Destination $oldPdf -Force
foreach($entry in @(
    @{source=$oldFull;leaf='ARTERIA-Audited-13-slides.pptx'},
    @{source=$oldSubmission;leaf='ARTERIA-Submission-pre-motion-10-slides.pptx'}
)){
    $moved=Move-ToArchive $entry.source $entry.leaf
    if($moved){$archived.Add($moved)}
}
$preview=Join-Path $root 'preview'
$oldPreview=Move-ToArchive $preview 'preview-pre-motion-13-slides'
if($oldPreview){$archived.Add($oldPreview)}
Move-Item -LiteralPath $previewBuild -Destination $preview

$canonicalHash=(Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash
if($canonicalHash -ne $newHash){throw 'Published canonical SHA-256 differs from validated staging deck.'}
$pdfHash=(Get-FileHash -LiteralPath $oldPdf -Algorithm SHA256).Hash
[ordered]@{
    published_at=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')
    authoritative_pptx='docs/ppt/ARTERIA.pptx'
    slides=10
    duration_seconds=180
    sha256=$canonicalHash
    synchronized_pdf='docs/ppt/ARTERIA-Submission.pdf'
    pdf_sha256=$pdfHash
    archived=$archived
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $root 'reports/canonical-publication.json')
Write-Output "Published one authoritative 10-slide animated PowerPoint and synchronized PDF. SHA-256: $canonicalHash"

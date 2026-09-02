function Get-FinalVisualAcceptanceViews {
    return @('roomA', 'npcA', 'doorTransition', 'roomB')
}

function Confirm-RoomReview {
    param($Result, [string] $EvidenceRoot, [string] $Revision, [string] $Fingerprint,
          [string] $View, [string] $Name)

    $ErrorActionPreference = 'Stop'
    if ($Result.revision -ne $Revision -or $Result.fingerprint -ne $Fingerprint -or $Result.stale) {
        throw "$Name review evidence is stale for the current working tree."
    }
    if (-not $Result.$View) { throw "$Name acceptance capture is missing." }
    $screenshotPath = Join-Path $EvidenceRoot $Result.$View.screenshotPath
    $reviewPath = Join-Path $EvidenceRoot $Result.$View.reviewPath
    $review = Get-Content -LiteralPath $reviewPath -Raw | ConvertFrom-Json
    $hash = (Get-FileHash -LiteralPath $screenshotPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $Result.$View.sha256 -or $review.screenshotSha256 -ne $hash) {
        throw "$Name review does not match the current screenshot."
    }
    if ($review.revision -ne $Revision -or $review.fingerprint -ne $Fingerprint) {
        throw "$Name review revision or fingerprint is stale."
    }
    if ($review.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($review.reviewer)) {
        throw "$Name needs an evidenced passing agent visual review."
    }
    if ($View -in @('roomAExterior', 'roomBExterior')) {
        $pairedView = if ($View -eq 'roomAExterior') { 'roomBExterior' } else { 'roomAExterior' }
        if (-not $Result.$pairedView -or $review.pairedScreenshotSha256 -ne $Result.$pairedView.sha256) {
            throw "$Name review is not paired with the current counterpart exterior screenshot."
        }
        $criteria = @('depth', 'scale', 'lightingContinuity', 'seams',
                      'renderingDefects', 'interiorComposition', 'propertyCoherence', 'distinctness')
    } else {
        $criteria = @('composition', 'lighting', 'materials', 'density', 'renderingDefects', 'uiObstruction')
        if ($View -in @('npcA', 'npcB')) { $criteria += @('npcPresentation', 'referenceBaseline') }
    }
    foreach ($criterion in $criteria) {
        $finding = $review.criteria.$criterion
        if ($finding.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($finding.evidence)) {
            throw "$Name visual criterion lacks passing evidence: $criterion"
        }
    }
    return $review
}

# Preserve the T04 caller interface and evidence format.
function Confirm-RoomAReview {
    param($Result, [string] $EvidenceRoot, [string] $Revision, [string] $Fingerprint)
    Confirm-RoomReview $Result $EvidenceRoot $Revision $Fingerprint 'roomA' 'Room A'
}

# The T04-T07 review formats above remain readable. T08 adds one assessment of
# the complete apartment, with all eight criteria evidenced for all four views.
function Confirm-FinalVisualReview {
    param($Result, [string] $EvidenceRoot, [string] $Revision, [string] $Fingerprint)

    $ErrorActionPreference = 'Stop'
    if ($Result.revision -ne $Revision -or $Result.fingerprint -ne $Fingerprint -or $Result.stale) {
        throw 'Final visual acceptance evidence is stale for the current working tree.'
    }
    if ($Result.finalVisualAcceptance.profile -ne 'T08') {
        throw 'Final visual acceptance requires a fresh T08 verification run.'
    }
    $review = Get-Content -LiteralPath (Join-Path $EvidenceRoot $Result.finalVisualAcceptance.reviewPath) -Raw | ConvertFrom-Json
    if ($review.revision -ne $Revision -or $review.fingerprint -ne $Fingerprint) {
        throw 'Final visual review revision or fingerprint is stale.'
    }
    if ($review.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($review.reviewer)) {
        throw 'Final visual acceptance needs an evidenced passing multimodal review; reported defects remain unmet.'
    }
    if ($review.coherence.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($review.coherence.evidence)) {
        throw 'Final visual acceptance requires evidence of a coherent apartment across all four views.'
    }
    $views = @(Get-FinalVisualAcceptanceViews)
    $declaredViews = @($Result.finalVisualAcceptance.views)
    if ($declaredViews.Count -ne $views.Count -or
        @(Compare-Object $views $declaredViews -CaseSensitive).Count -ne 0) {
        throw 'Final visual acceptance result declared an incorrect view set.'
    }
    if (@($review.views.PSObject.Properties).Count -ne $views.Count) {
        throw 'Final visual acceptance requires exactly four reviewed views.'
    }
    foreach ($view in $views) {
        $capture = $Result.$view
        $finding = $review.views.$view
        if (-not $capture -or -not $finding) { throw "Final visual acceptance view is missing: $view" }
        $hash = (Get-FileHash -LiteralPath (Join-Path $EvidenceRoot $capture.screenshotPath) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($capture.sha256 -ne $hash -or $finding.screenshotSha256 -ne $hash) {
            throw "Final visual acceptance screenshot does not match: $view"
        }
        if ($capture.width -ne 2560 -or $capture.height -ne 1440) {
            throw "Final visual acceptance requires 2560 x 1440: $view"
        }
        foreach ($criterion in @('composition', 'lighting', 'materials', 'density', 'renderingDefects', 'npcPresentation', 'uiObstruction', 'referenceBaseline')) {
            $evidence = $finding.criteria.$criterion
            if ($evidence.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($evidence.evidence)) {
                throw "Final visual acceptance has an unmet criterion: $view / $criterion"
            }
        }
    }
    return $review
}

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
    foreach ($criterion in @('composition', 'lighting', 'materials', 'density', 'renderingDefects', 'uiObstruction')) {
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

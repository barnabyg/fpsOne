function Confirm-RoomAReview {
    param($Result, [string] $EvidenceRoot, [string] $Revision, [string] $Fingerprint)

    $ErrorActionPreference = 'Stop'
    if ($Result.revision -ne $Revision -or $Result.fingerprint -ne $Fingerprint -or $Result.stale) {
        throw 'Room A review evidence is stale for the current working tree.'
    }
    $screenshotPath = Join-Path $EvidenceRoot $Result.roomA.screenshotPath
    $reviewPath = Join-Path $EvidenceRoot $Result.roomA.reviewPath
    $review = Get-Content -LiteralPath $reviewPath -Raw | ConvertFrom-Json
    $hash = (Get-FileHash -LiteralPath $screenshotPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $Result.roomA.sha256 -or $review.screenshotSha256 -ne $hash) {
        throw 'Room A review does not match the current screenshot.'
    }
    if ($review.revision -ne $Revision -or $review.fingerprint -ne $Fingerprint) {
        throw 'Room A review revision or fingerprint is stale.'
    }
    if ($review.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($review.reviewer)) {
        throw 'Room A needs an evidenced passing agent visual review.'
    }
    foreach ($criterion in @('composition', 'lighting', 'materials', 'density', 'renderingDefects', 'uiObstruction')) {
        $finding = $review.criteria.$criterion
        if ($finding.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($finding.evidence)) {
            throw "Room A visual criterion lacks passing evidence: $criterion"
        }
    }
    return $review
}

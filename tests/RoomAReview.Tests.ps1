$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'Room A visual evidence linkage' {
    BeforeEach {
        . "$repoRoot\scripts\room-a-review.ps1"
        $captureRoot = Join-Path $TestDrive ([guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $captureRoot -Force | Out-Null
        Set-Content "$captureRoot\room.png" 'current image bytes'
        $currentHash = (Get-FileHash "$captureRoot\room.png" -Algorithm SHA256).Hash.ToLowerInvariant()
        $review = @{ status = 'passed'; reviewer = 'Test reviewer'; revision = 'revision'; fingerprint = 'fingerprint'; screenshotSha256 = $currentHash; criteria = @{} }
        foreach ($criterion in @('composition', 'lighting', 'materials', 'density', 'renderingDefects', 'uiObstruction')) {
            $review.criteria[$criterion] = @{ status = 'passed'; evidence = 'Observed evidence for this criterion.' }
        }
        $result = [pscustomobject]@{
            revision = 'revision'; fingerprint = 'fingerprint'
            roomA = @{ screenshotPath = 'room.png'; sha256 = $currentHash; reviewPath = 'review.json' }
        }
    }
    It 'accepts a complete current review' {
        $review | ConvertTo-Json -Depth 5 | Set-Content "$captureRoot\review.json"
        (Confirm-RoomAReview $result $captureRoot 'revision' 'fingerprint').status | Should Be 'passed'
    }
    It 'rejects a review written for another screenshot' {
        $review.screenshotSha256 = '0' * 64
        $review | ConvertTo-Json -Depth 5 | Set-Content "$captureRoot\review.json"
        { Confirm-RoomAReview $result $captureRoot 'revision' 'fingerprint' } | Should Throw 'screenshot'
    }
    It 'rejects evidence after the working tree changes' {
        $review | ConvertTo-Json -Depth 5 | Set-Content "$captureRoot\review.json"
        { Confirm-RoomAReview $result $captureRoot 'revision' 'changed' } | Should Throw 'stale'
    }
    It 'requires observed evidence for every visual criterion' {
        $review.criteria.lighting.evidence = ''
        $review | ConvertTo-Json -Depth 5 | Set-Content "$captureRoot\review.json"
        { Confirm-RoomAReview $result $captureRoot 'revision' 'fingerprint' } | Should Throw 'lighting'
    }
}

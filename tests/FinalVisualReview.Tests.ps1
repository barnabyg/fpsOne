$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'T08 complete-prototype visual acceptance' {
    BeforeEach {
        . "$repoRoot\scripts\visual-review.ps1"
        $captureRoot = Join-Path $TestDrive ([guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $captureRoot | Out-Null
        $result = [pscustomobject]@{
            revision = 'tested-revision'; fingerprint = 'tested-tree'; stale = $false
            finalVisualAcceptance = @{
                profile = 'T08'; reviewPath = 'final-review.json'
                views = @('roomA', 'npcA', 'doorTransition', 'roomB')
            }
        }
        $review = @{
            status = 'passed'; reviewer = 'Multimodal test reviewer'
            revision = 'tested-revision'; fingerprint = 'tested-tree'
            coherence = @{ status = 'passed'; evidence = 'Oak, sage upholstery and warm practical lighting continue across the Door.' }
            views = @{}
        }
        foreach ($view in @('roomA', 'npcA', 'doorTransition', 'roomB')) {
            Set-Content "$captureRoot\$view.png" "Distinct image bytes for $view"
            $hash = (Get-FileHash "$captureRoot\$view.png" -Algorithm SHA256).Hash.ToLowerInvariant()
            $result | Add-Member -NotePropertyName $view -NotePropertyValue @{
                screenshotPath = "$view.png"; sha256 = $hash; width = 2560; height = 1440
            }
            $review.views[$view] = @{ screenshotSha256 = $hash; criteria = @{} }
            foreach ($criterion in @('composition', 'lighting', 'materials', 'density', 'renderingDefects', 'npcPresentation', 'uiObstruction', 'referenceBaseline')) {
                $review.views[$view].criteria[$criterion] = @{ status = 'passed'; evidence = "Observed $criterion in $view." }
            }
        }
    }

    It 'accepts an evidenced review of the four current acceptance views as one apartment' {
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        (Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree').status | Should Be 'passed'
    }

    It 'rejects a substituted screenshot even when the review still says passed' {
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        Set-Content "$captureRoot\doorTransition.png" 'An older Door image'
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'screenshot'
    }

    It 'rejects a review that belongs to another image or working tree' {
        $review.views.npcA.screenshotSha256 = '0' * 64
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'npcA'
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'changed-tree' } | Should Throw 'stale'
        { Confirm-FinalVisualReview $result $captureRoot 'another-revision' 'tested-tree' } | Should Throw 'stale'
    }

    It 'requires all four views, including Room B with NPC B' {
        $review.views.Remove('roomB')
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'four'
    }

    It 'rejects a result that declares a different final view set' {
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        $result.finalVisualAcceptance.views = @('roomA', 'npcA', 'doorTransition')
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'declared'
    }

    It 'keeps explicitly reported visual defects red' {
        $review.views.npcA.criteria.lighting = @{ status = 'failed'; evidence = 'Sunlit face loses facial detail.' }
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'npcA / lighting'
        $review.status = 'failed'
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'unmet'
    }

    It 'requires benchmark and NPC evidence in the environment views too' {
        $review.views.roomB.criteria.npcPresentation.evidence = ''
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'roomB / npcPresentation'
        $review.views.roomA.criteria.referenceBaseline.status = 'not_applicable'
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'roomA / referenceBaseline'
    }

    It 'requires an evidenced judgement of coherence across the rooms' {
        $review.coherence.evidence = ' '
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'coherent apartment'
    }

    It 'rejects old slice evidence and incorrect capture resolution' {
        $review | ConvertTo-Json -Depth 8 | Set-Content "$captureRoot\final-review.json"
        $result.roomA.width = 1920
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw '2560 x 1440'
        $result.finalVisualAcceptance.profile = 'T07'
        { Confirm-FinalVisualReview $result $captureRoot 'tested-revision' 'tested-tree' } | Should Throw 'fresh T08'
    }
}

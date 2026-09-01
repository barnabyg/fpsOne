$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'Shipping delivery completion' {
    BeforeEach {
        $packageRoot = Join-Path $TestDrive 'Shipping'
        $windowsRoot = Join-Path $packageRoot 'Windows'
        New-Item -ItemType Directory -Path $windowsRoot -Force | Out-Null
        $script:packageExecutable = Join-Path $windowsRoot 'FPSOne.exe'
        Set-Content -LiteralPath $script:packageExecutable -Value 'shipping executable fixture' -Encoding UTF8
        Set-Content -LiteralPath (Join-Path $windowsRoot 'FPSOne.pak') -Value 'shipping content fixture' -Encoding UTF8

        $script:revision = '0123456789abcdef0123456789abcdef01234567'
        $script:fingerprint = 'sha256:' + ('a' * 64)
        $script:acceptancePath = Join-Path $TestDrive 'shipping-acceptance.json'
        $script:deliveryRoot = Join-Path $TestDrive 'Delivery'
        $script:resultPath = Join-Path $TestDrive 'delivery-result.json'
        $executableHash = (Get-FileHash -LiteralPath $script:packageExecutable -Algorithm SHA256).Hash.ToLowerInvariant()
        @{
            schemaVersion = 1
            completedAtUtc = '2026-09-01T12:00:00Z'
            reviewer = 'Fixture reviewer'
            revision = $script:revision
            fingerprint = $script:fingerprint
            packageExecutable = $script:packageExecutable
            packageExecutableSha256 = $executableHash
            resolution = @{ width = 2560; height = 1440 }
            checks = @(
                @{ id = 'room-traversal'; status = 'passed'; evidence = 'Walked through both furnished Rooms.' },
                @{ id = 'npc-dialogues'; status = 'passed'; evidence = 'Completed and replayed both Dialogue Interactions.' },
                @{ id = 'door-cycle'; status = 'passed'; evidence = 'Opened, crossed, closed, and observed collision.' },
                @{ id = 'restored-input'; status = 'passed'; evidence = 'Movement and look returned after both dialogues.' },
                @{ id = 'escape-exit'; status = 'passed'; evidence = 'Escape closed the Shipping build.' },
                @{ id = 'presentation'; status = 'passed'; evidence = 'Inspected the experience at 2560 x 1440.' }
            )
        } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $script:acceptancePath -Encoding UTF8
    }

    It 'validates current manual evidence and creates a versioned ZIP with a hash' {
        & (Join-Path $repoRoot 'scripts\complete-delivery.ps1') `
            -PackageExecutable $script:packageExecutable `
            -AcceptancePath $script:acceptancePath `
            -DeliveryRoot $script:deliveryRoot `
            -Revision $script:revision `
            -Fingerprint $script:fingerprint `
            -ResultPath $script:resultPath

        $result = Get-Content -LiteralPath $script:resultPath -Raw | ConvertFrom-Json
        Test-Path -LiteralPath $result.zipPath -PathType Leaf | Should Be $true
        $result.zipPath | Should Match 'fpsOne-0123456789ab-win64-shipping\.zip$'
        $result.zipSha256 | Should Match '^[0-9a-f]{64}$'
        (Get-FileHash -LiteralPath $result.zipPath -Algorithm SHA256).Hash.ToLowerInvariant() | Should Be $result.zipSha256
        $result.acceptancePath | Should Be $script:acceptancePath
    }

    It 'rejects manual evidence for a different Shipping executable' {
        Add-Content -LiteralPath $script:packageExecutable -Value 'changed'

        {
            & (Join-Path $repoRoot 'scripts\complete-delivery.ps1') `
                -PackageExecutable $script:packageExecutable `
                -AcceptancePath $script:acceptancePath `
                -DeliveryRoot $script:deliveryRoot `
                -Revision $script:revision `
                -Fingerprint $script:fingerprint `
                -ResultPath $script:resultPath
        } | Should Throw 'does not match the current Shipping executable'
    }

    It 'rejects incomplete manual checklist evidence' {
        $acceptance = Get-Content -LiteralPath $script:acceptancePath -Raw | ConvertFrom-Json
        $acceptance.checks = @($acceptance.checks | Where-Object id -ne 'escape-exit')
        $acceptance | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $script:acceptancePath -Encoding UTF8

        {
            & (Join-Path $repoRoot 'scripts\complete-delivery.ps1') `
                -PackageExecutable $script:packageExecutable `
                -AcceptancePath $script:acceptancePath `
                -DeliveryRoot $script:deliveryRoot `
                -Revision $script:revision `
                -Fingerprint $script:fingerprint `
                -ResultPath $script:resultPath
        } | Should Throw 'exactly the required T09 checks'
    }

    It 'rejects delivery from a dirty source repository' {
        $sourceRepository = Join-Path $TestDrive 'source-repository'
        New-Item -ItemType Directory -Path $sourceRepository -Force | Out-Null
        & git -C $sourceRepository init --quiet
        & git -C $sourceRepository config user.name 'Fixture User'
        & git -C $sourceRepository config user.email 'fixture@example.invalid'
        Set-Content -LiteralPath (Join-Path $sourceRepository 'tracked.txt') -Value 'committed' -Encoding UTF8
        & git -C $sourceRepository add tracked.txt
        & git -C $sourceRepository commit --quiet -m 'fixture'
        Set-Content -LiteralPath (Join-Path $sourceRepository 'tracked.txt') -Value 'dirty' -Encoding UTF8

        {
            & (Join-Path $repoRoot 'scripts\complete-delivery.ps1') `
                -PackageExecutable $script:packageExecutable `
                -AcceptancePath $script:acceptancePath `
                -DeliveryRoot $script:deliveryRoot `
                -Revision $script:revision `
                -Fingerprint $script:fingerprint `
                -ResultPath $script:resultPath `
                -RepositoryRoot $sourceRepository
        } | Should Throw 'clean source working tree'
    }
}

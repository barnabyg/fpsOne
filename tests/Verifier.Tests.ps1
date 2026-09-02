$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'canonical verifier' -Tag 'VerifierSelfTest' {
    It 'keeps every generated default beneath the ignored Saved directory' {
        $verifyScript = Join-Path $repoRoot 'scripts\verify.ps1'
        $scriptText = Get-Content -LiteralPath $verifyScript -Raw

        $scriptText | Should Match 'Join-Path \$repoRoot ''Saved'''
        $scriptText | Should Match 'Join-Path \$savedRoot ''Packages\\Development'''
        $scriptText | Should Match 'Join-Path \$savedRoot ''Packages\\Shipping'''
        $scriptText | Should Match 'Join-Path \$savedRoot ''Delivery'''
        $scriptText | Should Match 'Join-Path \$savedRoot ''CleanClone'''
        $cleanCloneScript = Get-Content -LiteralPath (Join-Path $repoRoot 'scripts\test-clean-clone.ps1') -Raw
        $cleanCloneScript | Should Match 'Join-Path \$SourceRepository ''Saved\\CleanClone'''
        (Get-Content -LiteralPath (Join-Path $repoRoot '.gitignore') -Raw) | Should Match '(?m)^Saved/\r?$'
    }

    It 'records actionable current evidence when Unreal Engine is unavailable' {
        $evidenceRoot = Join-Path $TestDrive 'evidence'
        $packageRoot = Join-Path $TestDrive 'package'
        $shippingPackageRoot = Join-Path $TestDrive 'shipping-package'
        $deliveryRoot = Join-Path $TestDrive 'delivery'
        $cleanCloneRoot = Join-Path $TestDrive 'clean-clone'
        $missingEngineRoot = Join-Path $TestDrive 'missing-engine'
        $verifyScript = Join-Path $repoRoot 'scripts\verify.ps1'

        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $verifyScript `
            -EngineRoot $missingEngineRoot `
            -EvidenceRoot $evidenceRoot `
            -PackageRoot $packageRoot `
            -ShippingPackageRoot $shippingPackageRoot `
            -DeliveryRoot $deliveryRoot `
            -CleanCloneRoot $cleanCloneRoot `
            -NoOpenDashboard

        $LASTEXITCODE | Should Be 1

        $resultPath = Join-Path $evidenceRoot 'verification-result.json'
        $dashboardPath = Join-Path $evidenceRoot 'index.html'
        Test-Path -LiteralPath $resultPath | Should Be $true
        Test-Path -LiteralPath $dashboardPath | Should Be $true

        $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
        $result.mode | Should Be 'human-local'
        $result.stale | Should Be $false
        $result.fingerprint | Should Match '^sha256:[0-9a-f]{64}$'
        @($result.gates | Where-Object name -eq 'Project health')[0].status | Should Be 'failed'
        @($result.gates | Where-Object name -eq 'Project health')[0].details | Should Match 'Unreal Engine 5\.8 was not found'
        @($result.gates | Where-Object name -eq 'Repository tests')[0].status | Should Be 'passed'
        @($result.gates | Where-Object name -eq 'Development package')[0].status | Should Be 'skipped'
        @($result.gates | Where-Object name -eq 'Shipping package')[0].status | Should Be 'skipped'
        @($result.gates | Where-Object name -eq 'Shipping manual acceptance')[0].status | Should Be 'skipped'
        @($result.gates | Where-Object name -eq 'Versioned Shipping ZIP')[0].status | Should Be 'skipped'
    }
}

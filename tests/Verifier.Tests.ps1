$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'canonical verifier' -Tag 'VerifierSelfTest' {
    It 'records actionable current evidence when Unreal Engine is unavailable' {
        $evidenceRoot = Join-Path $TestDrive 'evidence'
        $packageRoot = Join-Path $TestDrive 'package'
        $missingEngineRoot = Join-Path $TestDrive 'missing-engine'
        $verifyScript = Join-Path $repoRoot 'scripts\verify.ps1'

        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $verifyScript `
            -EngineRoot $missingEngineRoot `
            -EvidenceRoot $evidenceRoot `
            -PackageRoot $packageRoot `
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
    }
}

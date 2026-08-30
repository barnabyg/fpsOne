$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'verification dashboard renderer' {
    It 'renders provenance, gates, logs, and package evidence from a result file' {
        $resultPath = Join-Path $TestDrive 'verification-result.json'
        $dashboardPath = Join-Path $TestDrive 'index.html'
        @{
            schemaVersion = 1
            generatedAtUtc = '2026-08-29T12:00:00Z'
            mode = 'human-local'
            revision = 'abc1234'
            fingerprint = 'sha256:fixture'
            stale = $false
            tools = @{
                powershell = '5.1.26100.1'
                git = '2.51.0'
                unreal = '5.8.0'
            }
            gates = @(
                @{
                    name = 'Project health'
                    status = 'passed'
                    durationMs = 1200
                    details = 'Blueprint compilation completed with zero warnings.'
                    logPath = 'logs/project-health.log'
                }
            )
            packagePath = 'C:\fpsOne-output\Development\FPSOne.exe'
            screenshots = @()
            visualReview = @{
                status = 'not_applicable'
                details = 'Human-local validation does not use an AI visual gate.'
            }
            warningExceptions = @()
        } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8

        & (Join-Path $repoRoot 'scripts\render-dashboard.ps1') -ResultPath $resultPath -OutputPath $dashboardPath

        Test-Path -LiteralPath $dashboardPath | Should Be $true
        $dashboard = Get-Content -LiteralPath $dashboardPath -Raw
        $dashboard | Should Match 'human-local'
        $dashboard | Should Match 'abc1234'
        $dashboard | Should Match 'Project health'
        $dashboard | Should Match 'logs/project-health\.log'
        $dashboard | Should Match 'C:\\fpsOne-output\\Development\\FPSOne\.exe'
        $dashboard | Should Match 'CURRENT EVIDENCE'
    }
}

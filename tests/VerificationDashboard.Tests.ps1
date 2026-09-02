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
                    reportPaths = @('logs/interaction-functional-report/index.html', 'logs/interaction-functional-report/index.json')
                }
                @{
                    name = 'Legacy gate without reports'
                    status = 'passed'
                    durationMs = 0
                    details = 'Older result files remain readable.'
                    logPath = ''
                }
            )
            packagePath = 'C:\project\fpsOne\Saved\Packages\Development\Windows\FPSOne.exe'
            packages = @{
                development = 'C:\project\fpsOne\Saved\Packages\Development\Windows\FPSOne.exe'
                shipping = 'C:\project\fpsOne\Saved\Packages\Shipping\Windows\FPSOne.exe'
            }
            delivery = @{
                zipPath = 'C:\project\fpsOne\Saved\Delivery\fpsOne-abc1234-win64-shipping.zip'
                zipSha256 = 'fixture-delivery-sha256'
                acceptancePath = 'logs\shipping-acceptance.json'
            }
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
        $dashboard | Should Match 'href="logs/interaction-functional-report/index\.html"'
        $dashboard | Should Match 'href="logs/interaction-functional-report/index\.json"'
        $dashboard | Should Match 'Saved\\Packages\\Development\\Windows\\FPSOne\.exe'
        $dashboard | Should Match 'Saved\\Packages\\Shipping\\Windows\\FPSOne\.exe'
        $dashboard | Should Match 'fpsOne-abc1234-win64-shipping\.zip'
        $dashboard | Should Match 'fixture-delivery-sha256'
        $dashboard | Should Match 'logs\\shipping-acceptance\.json'
        $dashboard | Should Match 'CURRENT EVIDENCE'
        $dashboard | Should Match 'Legacy gate without reports'
    }
}

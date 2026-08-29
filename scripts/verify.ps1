[CmdletBinding()]
param(
    [switch] $RequireVisualReview,

    [string] $EngineRoot,

    [string] $EvidenceRoot,

    [string] $PackageRoot,

    [switch] $NoOpenDashboard
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$projectPath = Join-Path $repoRoot 'FPSOne.uproject'

if (-not $EvidenceRoot) {
    $EvidenceRoot = Join-Path $repoRoot 'Saved\Verification'
}
if (-not $PackageRoot) {
    $PackageRoot = 'C:\fpsOne-output\Development'
}
if (-not $EngineRoot) {
    $environmentPath = Join-Path $repoRoot '.env'
    if (Test-Path -LiteralPath $environmentPath) {
        $engineRootLine = Get-Content -LiteralPath $environmentPath | Where-Object { $_ -match '^FPS_ONE_ENGINE_ROOT=' } | Select-Object -Last 1
        if ($engineRootLine) {
            $EngineRoot = $engineRootLine.Substring('FPS_ONE_ENGINE_ROOT='.Length)
        }
    }
}
if (-not $EngineRoot) {
    $EngineRoot = 'C:\Program Files\Epic Games\UE_5.8'
}

$logsRoot = Join-Path $EvidenceRoot 'logs'
New-Item -ItemType Directory -Path $logsRoot -Force | Out-Null

function Get-GitOutput {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & git -C $repoRoot @Arguments 2>$null
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode."
    }
    return @($output)
}

function Get-WorkingTreeFingerprint {
    $revision = ([string](Get-GitOutput rev-parse HEAD)).Trim()
    $material = [System.Collections.Generic.List[string]]::new()
    $material.Add("revision:$revision")
    foreach ($diffLine in @(Get-GitOutput diff --binary HEAD)) {
        $material.Add([string] $diffLine)
    }

    foreach ($relativePath in @(Get-GitOutput ls-files --others --exclude-standard | Sort-Object)) {
        $absolutePath = Join-Path $repoRoot $relativePath
        if (Test-Path -LiteralPath $absolutePath -PathType Leaf) {
            $hash = (Get-FileHash -LiteralPath $absolutePath -Algorithm SHA256).Hash.ToLowerInvariant()
            $material.Add("untracked:$relativePath`:$hash")
        }
    }

    $bytes = [System.Text.Encoding]::UTF8.GetBytes(($material -join "`n"))
    $hashBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return 'sha256:' + (($hashBytes | ForEach-Object { $_.ToString('x2') }) -join '')
}

function New-Gate {
    param(
        [string] $Name,
        [ValidateSet('passed', 'failed', 'skipped', 'missing', 'not_applicable')]
        [string] $Status,
        [long] $DurationMs,
        [string] $Details,
        [AllowEmptyString()][string] $LogPath = ''
    )

    return [pscustomobject][ordered]@{
        name = $Name
        status = $Status
        durationMs = $DurationMs
        details = $Details
        logPath = $LogPath
    }
}

function Get-RelativeEvidencePath {
    param([string] $Path)

    return $Path.Substring($EvidenceRoot.TrimEnd('\').Length).TrimStart('\')
}

function Invoke-LoggedCommand {
    param(
        [string] $Executable,
        [string[]] $Arguments,
        [string] $LogPath
    )

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Executable @Arguments 2>&1 | Tee-Object -FilePath $LogPath | Out-Null
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    return [int] $exitCode
}

$mode = if ($RequireVisualReview) { 'agent' } else { 'human-local' }
$revision = ([string](Get-GitOutput rev-parse HEAD)).Trim()
$initialFingerprint = Get-WorkingTreeFingerprint
$gates = [System.Collections.Generic.List[object]]::new()
$warningExceptions = @()
$packageExecutable = ''
$editorPath = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$uatPath = Join-Path $EngineRoot 'Engine\Build\BatchFiles\RunUAT.bat'

$assetTimer = [System.Diagnostics.Stopwatch]::StartNew()
$assetManifestPath = Join-Path $repoRoot 'ASSETS.md'
if (Test-Path -LiteralPath $assetManifestPath) {
    $assetDetails = 'ASSETS.md is present; T01 contains no third-party assets.'
    $assetStatus = 'passed'
} else {
    $assetDetails = 'ASSETS.md is missing.'
    $assetStatus = 'failed'
}
$assetTimer.Stop()
$gates.Add((New-Gate 'Asset manifest' $assetStatus $assetTimer.ElapsedMilliseconds $assetDetails))

$testTimer = [System.Diagnostics.Stopwatch]::StartNew()
$testLog = Join-Path $logsRoot 'repository-tests.log'
$testReport = Join-Path $logsRoot 'repository-tests.xml'
$testArguments = @(
    '-NoProfile',
    '-ExecutionPolicy',
    'Bypass',
    '-File',
    (Join-Path $PSScriptRoot 'test.ps1'),
    '-ReportPath',
    $testReport
)
$testExitCode = Invoke-LoggedCommand -Executable 'powershell.exe' -Arguments $testArguments -LogPath $testLog
if ($testExitCode -eq 0 -and (Test-Path -LiteralPath $testReport -PathType Leaf)) {
    $testStatus = 'passed'
    $testDetails = 'Repository tests passed and exported an NUnit report.'
} else {
    $testStatus = 'failed'
    $testDetails = "Repository tests failed or did not export their report (exit code $testExitCode)."
}
$testTimer.Stop()
$gates.Add((New-Gate 'Repository tests' $testStatus $testTimer.ElapsedMilliseconds $testDetails (Get-RelativeEvidencePath $testLog)))

$projectTimer = [System.Diagnostics.Stopwatch]::StartNew()
$projectLog = Join-Path $logsRoot 'project-health.log'
$requiredProjectFiles = @(
    $projectPath,
    (Join-Path $repoRoot 'Config\DefaultEngine.ini'),
    (Join-Path $repoRoot 'Config\DefaultGame.ini'),
    (Join-Path $repoRoot 'Config\DefaultInput.ini'),
    (Join-Path $repoRoot 'Content\Maps\L_Testbed.umap'),
    (Join-Path $repoRoot 'Content\Blueprints\BP_TestbedGameMode.uasset'),
    (Join-Path $repoRoot 'Content\Blueprints\BP_TestbedPlayerController.uasset'),
    (Join-Path $repoRoot 'Content\Blueprints\BP_Player.uasset'),
    (Join-Path $repoRoot 'scripts\validate_player.py')
)
$missingProjectFiles = @($requiredProjectFiles | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })

if (-not (Test-Path -LiteralPath $editorPath -PathType Leaf) -or -not (Test-Path -LiteralPath $uatPath -PathType Leaf)) {
    $projectStatus = 'failed'
    $projectDetails = "Unreal Engine 5.8 was not found at '$EngineRoot'. Run scripts/setup-unreal.sh, or pass -EngineRoot."
    Set-Content -LiteralPath $projectLog -Value $projectDetails -Encoding UTF8
} elseif ($missingProjectFiles.Count -gt 0) {
    $projectStatus = 'failed'
    $projectDetails = 'Required project content is missing: ' + (($missingProjectFiles | ForEach-Object { $_.Substring($repoRoot.Length + 1) }) -join ', ')
    Set-Content -LiteralPath $projectLog -Value $projectDetails -Encoding UTF8
} else {
    $compileArguments = @(
        $projectPath,
        '-run=CompileAllBlueprints',
        '-AllowListFile=Config/BlueprintCompileAllowList.txt',
        '-unattended',
        '-nop4',
        '-nosplash',
        '-NullRHI',
        '-stdout',
        '-FullStdOutLogOutput'
    )
    $compileExitCode = Invoke-LoggedCommand -Executable $editorPath -Arguments $compileArguments -LogPath $projectLog
    $compileSummary = Select-String -LiteralPath $projectLog -Pattern 'Compiling Completed with 0 errors and 0 warnings and 0 blueprints that failed to load\.' -Quiet
    $runSummary = Select-String -LiteralPath $projectLog -Pattern 'Success - 0 error\(s\), 0 warning\(s\)' -Quiet
    if ($compileExitCode -eq 0 -and $compileSummary -and $runSummary) {
        $projectStatus = 'passed'
        $projectDetails = 'Project loaded and every project Blueprint compiled successfully.'
    } else {
        $projectStatus = 'failed'
        $projectDetails = "Blueprint compilation failed or did not report a zero-warning summary (exit code $compileExitCode)."
    }
}
$projectTimer.Stop()
$gates.Add((New-Gate 'Project health' $projectStatus $projectTimer.ElapsedMilliseconds $projectDetails (Get-RelativeEvidencePath $projectLog)))

$playerTimer = [System.Diagnostics.Stopwatch]::StartNew()
$playerLog = Join-Path $logsRoot 'player-locomotion.log'
if ($projectStatus -ne 'passed') {
    $playerStatus = 'skipped'
    $playerDetails = 'Player locomotion validation requires a passing project-health gate.'
    Set-Content -LiteralPath $playerLog -Value $playerDetails -Encoding UTF8
} else {
    $playerArguments = @(
        $projectPath,
        "-ExecutePythonScript=$(Join-Path $PSScriptRoot 'validate_player.py')",
        '-unattended',
        '-nop4',
        '-nosplash',
        '-NullRHI',
        '-stdout',
        '-FullStdOutLogOutput'
    )
    $playerExitCode = Invoke-LoggedCommand -Executable $editorPath -Arguments $playerArguments -LogPath $playerLog
    $playerSummary = Select-String -LiteralPath $playerLog -Pattern 'T01_PLAYER_VALIDATION_PASSED' -Quiet
    $playerErrors = Select-String -LiteralPath $playerLog -Pattern 'LogPython: Error' -Quiet
    if ($playerExitCode -eq 0 -and $playerSummary -and -not $playerErrors) {
        $playerStatus = 'passed'
        $playerDetails = 'BP_Player uses gravity-driven walking, capsule collision, and yaw-only body rotation.'
    } else {
        $playerStatus = 'failed'
        $playerDetails = "Player locomotion validation failed or did not emit its success marker (exit code $playerExitCode)."
    }
}
$playerTimer.Stop()
$gates.Add((New-Gate 'Player locomotion' $playerStatus $playerTimer.ElapsedMilliseconds $playerDetails (Get-RelativeEvidencePath $playerLog)))

$gates.Add((New-Gate 'Interaction functional tests' 'not_applicable' 0 'World Interaction functional tests activate with T02, which introduces the Interactable seam.'))

$packageTimer = [System.Diagnostics.Stopwatch]::StartNew()
$packageLog = Join-Path $logsRoot 'development-package.log'
if ($projectStatus -ne 'passed' -or $playerStatus -ne 'passed') {
    $packageStatus = 'skipped'
    $packageDetails = 'Packaging requires passing project-health and player-locomotion gates.'
    Set-Content -LiteralPath $packageLog -Value $packageDetails -Encoding UTF8
} else {
    New-Item -ItemType Directory -Path $PackageRoot -Force | Out-Null
    $packageArguments = @(
        'BuildCookRun',
        "-project=$projectPath",
        '-nop4',
        '-utf8output',
        '-cook',
        '-stage',
        '-pak',
        '-archive',
        "-archivedirectory=$PackageRoot",
        '-platform=Win64',
        '-clientconfig=Development',
        '-unattended'
    )
    $packageExitCode = Invoke-LoggedCommand -Executable $uatPath -Arguments $packageArguments -LogPath $packageLog
    $packageExecutable = Get-ChildItem -LiteralPath $PackageRoot -Filter 'FPSOne.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
    if ($packageExitCode -eq 0 -and $packageExecutable) {
        $packageStatus = 'passed'
        $packageDetails = 'Development Win64 package completed and FPSOne.exe is present.'
    } else {
        $packageStatus = 'failed'
        $packageDetails = "Development packaging failed or did not produce FPSOne.exe (exit code $packageExitCode)."
    }
}
$packageTimer.Stop()
$gates.Add((New-Gate 'Development package' $packageStatus $packageTimer.ElapsedMilliseconds $packageDetails (Get-RelativeEvidencePath $packageLog)))

$launchTimer = [System.Diagnostics.Stopwatch]::StartNew()
$launchLog = Join-Path $logsRoot 'packaged-launch.log'
if ($packageStatus -ne 'passed') {
    $launchStatus = 'skipped'
    $launchDetails = 'The launch smoke test requires a successful Development package.'
    Set-Content -LiteralPath $launchLog -Value $launchDetails -Encoding UTF8
} else {
    $launchArguments = @(
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        (Join-Path $PSScriptRoot 'test-packaged-launch.ps1'),
        '-PackageExecutable',
        $packageExecutable
    )
    $launchExitCode = Invoke-LoggedCommand -Executable 'powershell.exe' -Arguments $launchArguments -LogPath $launchLog
    if ($launchExitCode -eq 0) {
        $launchStatus = 'passed'
        $launchDetails = 'The Development Win64 package opened its SM6 game window successfully.'
    } else {
        $launchStatus = 'failed'
        $launchDetails = "The Development Win64 package did not launch successfully (exit code $launchExitCode)."
    }
}
$launchTimer.Stop()
$gates.Add((New-Gate 'Packaged launch' $launchStatus $launchTimer.ElapsedMilliseconds $launchDetails (Get-RelativeEvidencePath $launchLog)))

$diagnosticTimer = [System.Diagnostics.Stopwatch]::StartNew()
$diagnosticLog = Join-Path $logsRoot 'diagnostics.log'
if ($testStatus -ne 'passed' -or $projectStatus -ne 'passed' -or $playerStatus -ne 'passed' -or $packageStatus -ne 'passed' -or $launchStatus -ne 'passed') {
    $diagnosticStatus = 'skipped'
    $diagnosticDetails = 'Diagnostics require successful test, project, player, package, and packaged-launch logs.'
    Set-Content -LiteralPath $diagnosticLog -Value $diagnosticDetails -Encoding UTF8
} else {
    $diagnosticCandidates = @(
        Select-String -Path @($testLog, $projectLog, $playerLog, $packageLog, $launchLog) -Pattern '(?i)\b(Warning|Error)\b' -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Line -notmatch '(?i)(Success|Completed)\s.*0 error(?:\(s\)|s).*0 warning(?:\(s\)|s)' -and
                $_.Line -notmatch '(?i)Map check complete:\s*0 Error\(s\), 0 Warning\(s\)'
            }
    )
    $exceptionDefinitions = @(
        [pscustomobject]@{
            pattern = "^LogWindows: Failed to load '(aqProf|VtuneApi|VtuneApi32e|WinPixGpuCapturer)\.dll' \(GetLastError=126\)$"
            origin = 'Optional third-party profiling integrations absent from the installed Epic binary build.'
            consequence = 'No effect on Blueprint compilation, cooking, packaging, or the packaged gameplay launch.'
        },
        [pscustomobject]@{
            pattern = 'LogTemp: Error (test: UE::UnifiedErrorTest::Empty: \[Empty error\]|with param: UE::UnifiedErrorTest::WithInt: \[Error with int -7\]|with context: UE::UnifiedErrorTest::Empty: \[Empty error\])$'
            origin = 'Diagnostic examples emitted by Unreal Engine 5.8 Core UnifiedError test code during Python-enabled editor startup.'
            consequence = 'No project code is involved; the Player validator completed with its success marker and no Python errors.'
        }
    )
    $projectDiagnostics = [Collections.Generic.List[object]]::new()
    $unclassifiedDiagnostics = [Collections.Generic.List[object]]::new()
    foreach ($diagnostic in $diagnosticCandidates) {
        if ($diagnostic.Line -match '(?i)(LogBlueprint|LogScript|/Game/|FPSOne)') {
            $projectDiagnostics.Add($diagnostic)
            continue
        }

        $matchedException = $exceptionDefinitions | Where-Object { $diagnostic.Line -match $_.pattern } | Select-Object -First 1
        if ($matchedException) {
            $warningExceptions += "Match: $($matchedException.pattern) | Origin: $($matchedException.origin) | Evidence: $(Get-RelativeEvidencePath $diagnostic.Path) | Consequence: $($matchedException.consequence)"
        } else {
            $unclassifiedDiagnostics.Add($diagnostic)
        }
    }

    if ($projectDiagnostics.Count -eq 0 -and $unclassifiedDiagnostics.Count -eq 0) {
        $diagnosticStatus = 'passed'
        $diagnosticDetails = "No project-originated or unclassified warning/error diagnostics were found; $(@($warningExceptions).Count) narrow exception(s) were recorded."
        Set-Content -LiteralPath $diagnosticLog -Value $diagnosticDetails -Encoding UTF8
    } else {
        $diagnosticStatus = 'failed'
        $diagnosticDetails = "$($projectDiagnostics.Count) project-originated and $($unclassifiedDiagnostics.Count) unclassified warning/error diagnostic(s) found."
        @($projectDiagnostics; $unclassifiedDiagnostics) | ForEach-Object { $_.Line } | Set-Content -LiteralPath $diagnosticLog -Encoding UTF8
    }
}
$diagnosticTimer.Stop()
$gates.Add((New-Gate 'Diagnostics' $diagnosticStatus $diagnosticTimer.ElapsedMilliseconds $diagnosticDetails (Get-RelativeEvidencePath $diagnosticLog)))

if ($RequireVisualReview) {
    $gates.Add((New-Gate 'Visual acceptance' 'not_applicable' 0 'T01 has no final Room, Door, or NPC acceptance views; the four-view agent gate activates with T08.'))
    $visualReview = [pscustomobject]@{
        status = 'not_applicable'
        details = 'No final visual-acceptance views apply to the T01 bootstrap profile.'
    }
} else {
    $gates.Add((New-Gate 'Visual acceptance' 'not_applicable' 0 'Human-local validation does not use an AI visual gate.'))
    $visualReview = [pscustomobject]@{
        status = 'not_applicable'
        details = 'Human-local validation does not use an AI visual gate.'
    }
}

$dashboardTimer = [System.Diagnostics.Stopwatch]::StartNew()
$dashboardPath = Join-Path $EvidenceRoot 'index.html'
$resultPath = Join-Path $EvidenceRoot 'verification-result.json'
$finalFingerprint = Get-WorkingTreeFingerprint
$result = [pscustomobject][ordered]@{
    schemaVersion = 1
    generatedAtUtc = [DateTime]::UtcNow.ToString('o')
    mode = $mode
    revision = $revision
    fingerprint = $initialFingerprint
    stale = ($initialFingerprint -ne $finalFingerprint)
    tools = [pscustomobject][ordered]@{
        powershell = $PSVersionTable.PSVersion.ToString()
        git = ((& git --version) -replace '^git version ', '')
        unreal = if (Test-Path -LiteralPath $editorPath) { [Diagnostics.FileVersionInfo]::GetVersionInfo($editorPath).ProductVersion } else { 'not found' }
    }
    gates = @($gates)
    packagePath = [string] $packageExecutable
    screenshots = @()
    visualReview = $visualReview
    warningExceptions = $warningExceptions
}

function Publish-VerificationDashboard {
    $temporaryResultPath = Join-Path $EvidenceRoot '.verification-result.tmp.json'
    $temporaryDashboardPath = Join-Path $EvidenceRoot '.index.tmp.html'
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $temporaryResultPath -Encoding UTF8
    & (Join-Path $PSScriptRoot 'render-dashboard.ps1') -ResultPath $temporaryResultPath -OutputPath $temporaryDashboardPath
    Move-Item -LiteralPath $temporaryDashboardPath -Destination $dashboardPath -Force
    Move-Item -LiteralPath $temporaryResultPath -Destination $resultPath -Force
}

$dashboardProbeResultPath = Join-Path $EvidenceRoot '.dashboard-probe.json'
$dashboardProbePath = Join-Path $EvidenceRoot '.dashboard-probe.html'
$result.gates = @($gates)
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $dashboardProbeResultPath -Encoding UTF8
& (Join-Path $PSScriptRoot 'render-dashboard.ps1') -ResultPath $dashboardProbeResultPath -OutputPath $dashboardProbePath
Remove-Item -LiteralPath $dashboardProbeResultPath, $dashboardProbePath -Force
$dashboardTimer.Stop()
$gates.Add((New-Gate 'Verification dashboard' 'passed' $dashboardTimer.ElapsedMilliseconds 'Static dashboard generated from the machine-readable result.'))
$result.gates = @($gates)
Publish-VerificationDashboard

if (-not $NoOpenDashboard) {
    Start-Process -FilePath $dashboardPath
}

$failedRequiredGates = @($gates | Where-Object { $_.status -in @('failed', 'missing', 'skipped') })
if ($result.stale -or $failedRequiredGates.Count -gt 0) {
    exit 1
}

exit 0

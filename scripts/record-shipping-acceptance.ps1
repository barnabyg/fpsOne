[CmdletBinding()]
param(
    [string] $VerificationResultPath,

    [string] $OutputPath,

    [string] $Reviewer
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'package-manifest.ps1')
. (Join-Path $PSScriptRoot 'shipping-acceptance-prompts.ps1')
if (-not $VerificationResultPath) {
    $VerificationResultPath = Join-Path $repoRoot 'Saved\Verification\verification-result.json'
}
if (-not (Test-Path -LiteralPath $VerificationResultPath -PathType Leaf)) {
    throw "Verification result was not found at '$VerificationResultPath'. Run the canonical verifier first."
}

$verification = Get-Content -LiteralPath $VerificationResultPath -Raw | ConvertFrom-Json
if ($verification.stale) {
    throw 'The verification result is stale; rerun the canonical verifier before manual acceptance.'
}
$packageExecutable = [string] $verification.packages.shipping
if (-not $packageExecutable) {
    throw 'The verification result does not contain a Shipping package.'
}
if (-not (Test-Path -LiteralPath $packageExecutable -PathType Leaf)) {
    throw "The verified Shipping executable was not found at '$packageExecutable'."
}
$packageRoot = Get-FPSOnePackageRoot -PackageExecutable $packageExecutable
$initialPackageManifest = @(Get-FPSOnePackageManifest -PackageRoot $packageRoot)
if (-not $OutputPath) {
    $OutputPath = Join-Path (Split-Path -Parent $VerificationResultPath) 'shipping-manual-acceptance.json'
}
if (-not $Reviewer) {
    $Reviewer = [Environment]::UserName
}

$checks = @(
    [pscustomobject]@{ id = 'presentation'; prompt = 'At 2560 x 1440, confirm Room A appears without an editor or menu and the visual presentation has no material defect.' },
    [pscustomobject]@{ id = 'room-traversal'; prompt = 'Walk through Room A and Room B with W/A/S/D and mouse look; confirm both furnished Rooms are reachable and collision is plausible.' },
    [pscustomobject]@{ id = 'door-cycle'; prompt = 'Focus the Door, open it, cross it, close it, and confirm the closed Door blocks passage.' },
    [pscustomobject]@{ id = 'npc-dialogues'; prompt = 'Complete and replay both NPC Dialogue Interactions; confirm each has three lines and its own resident presentation.' },
    [pscustomobject]@{ id = 'restored-input'; prompt = 'During each Dialogue Interaction confirm walking pauses; after dismissal confirm movement, look, prompts, and the centre dot return.' },
    [pscustomobject]@{ id = 'escape-exit'; prompt = 'Press Escape and confirm the Shipping application exits immediately without opening a menu.' }
)

function Get-ShippingProcesses {
    param([DateTime] $StartedAt)

    $shippingProcessNames = @('FPSOne', 'FPSOne-Win64-Shipping', 'UnrealGame', 'UnrealGame-Win64-Shipping')
    return @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -in $shippingProcessNames -and $_.StartTime -ge $StartedAt.AddSeconds(-1)
    })
}

Write-Output 'Launching the exact verified Shipping build at 2560 x 1440.'
Write-Output 'Perform all six checks in the game window and finish with Escape.'
Write-Output 'After the game closes, return here and record six numbered PASS confirmations with concrete observed evidence.'
$launchTime = Get-Date
$completed = $false
try {
    $launcher = Start-Process -FilePath $packageExecutable `
        -ArgumentList @('-windowed', '-ResX=2560', '-ResY=1440') `
        -PassThru `
        -WindowStyle Normal

    $timer = [Diagnostics.Stopwatch]::StartNew()
    do {
        $gameProcesses = @(Get-ShippingProcesses -StartedAt $launchTime)
        if (@($gameProcesses | Where-Object MainWindowHandle -ne 0).Count -gt 0) { break }
        Start-Sleep -Milliseconds 250
    } while ($timer.Elapsed.TotalSeconds -lt 60)
    if (@($gameProcesses | Where-Object MainWindowHandle -ne 0).Count -eq 0) {
        throw 'The Shipping application did not open a visible game window within 60 seconds.'
    }

    $recordedChecks = @(Read-FPSOneShippingAcceptanceChecks -Checks $checks)

    Start-Sleep -Seconds 2
    $remainingGameProcesses = @(Get-ShippingProcesses -StartedAt $launchTime)
    if ($remainingGameProcesses.Count -gt 0) {
        throw 'The Shipping application is still running after the Escape-exit check.'
    }
    $finalPackageManifest = @(Get-FPSOnePackageManifest -PackageRoot $packageRoot)
    Assert-FPSOnePackageManifest -Expected $initialPackageManifest -Actual $finalPackageManifest

    $outputDirectory = Split-Path -Parent $OutputPath
    if ($outputDirectory) {
        New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    }
    [pscustomobject][ordered]@{
        schemaVersion = 1
        completedAtUtc = [DateTime]::UtcNow.ToString('o')
        reviewer = $Reviewer
        revision = [string] $verification.revision
        fingerprint = [string] $verification.fingerprint
        packageExecutable = [IO.Path]::GetFullPath($packageExecutable)
        packageExecutableSha256 = (Get-FileHash -LiteralPath $packageExecutable -Algorithm SHA256).Hash.ToLowerInvariant()
        packageFiles = $finalPackageManifest
        resolution = [pscustomobject][ordered]@{ width = 2560; height = 1440 }
        checks = @($recordedChecks)
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
    $completed = $true
    Write-Output "T09_SHIPPING_MANUAL_ACCEPTANCE_RECORDED $OutputPath"
} finally {
    if (-not $completed) {
        foreach ($process in @(Get-ShippingProcesses -StartedAt $launchTime)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

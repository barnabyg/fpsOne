[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $PackageExecutable,

    [Parameter(Mandatory = $true)]
    [string] $AcceptancePath,

    [Parameter(Mandatory = $true)]
    [string] $DeliveryRoot,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string] $Revision,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^sha256:[0-9a-fA-F]{64}$')]
    [string] $Fingerprint,

    [Parameter(Mandatory = $true)]
    [string] $ResultPath,

    [string] $RepositoryRoot
)

$ErrorActionPreference = 'Stop'

function Assert-PathOutsideRepository {
    param([string] $Path, [string] $Root)

    if (-not $Root) { return }
    $resolvedPath = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $resolvedRoot = [IO.Path]::GetFullPath($Root).TrimEnd('\')
    if ($resolvedPath.Equals($resolvedRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $resolvedPath.StartsWith($resolvedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "DeliveryRoot must be outside the Git working tree ('$resolvedRoot')."
    }
}

function Assert-CleanSourceRepository {
    param([string] $Root, [string] $ExpectedRevision)

    if (-not $Root) { return }
    $status = @(& git -C $Root status --porcelain --untracked-files=all)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect the source repository at '$Root'."
    }
    if ($status.Count -ne 0) {
        throw 'T09 delivery requires a clean source working tree.'
    }
    $actualRevision = ([string] (& git -C $Root rev-parse HEAD)).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualRevision -ne $ExpectedRevision) {
        throw "The clean source repository is not at delivery revision '$ExpectedRevision'."
    }
}

if (-not (Test-Path -LiteralPath $PackageExecutable -PathType Leaf)) {
    throw "Shipping executable was not found at '$PackageExecutable'."
}
if (-not (Test-Path -LiteralPath $AcceptancePath -PathType Leaf)) {
    throw "Shipping manual acceptance evidence was not found at '$AcceptancePath'."
}
Assert-PathOutsideRepository -Path $DeliveryRoot -Root $RepositoryRoot
Assert-CleanSourceRepository -Root $RepositoryRoot -ExpectedRevision $Revision

$acceptance = Get-Content -LiteralPath $AcceptancePath -Raw | ConvertFrom-Json
$requiredCheckIds = @('room-traversal', 'npc-dialogues', 'door-cycle', 'restored-input', 'escape-exit', 'presentation')
$actualCheckIds = @($acceptance.checks | ForEach-Object { [string] $_.id } | Sort-Object)
$expectedCheckIds = @($requiredCheckIds | Sort-Object)
if ($actualCheckIds.Count -ne $expectedCheckIds.Count -or
    (Compare-Object -ReferenceObject $expectedCheckIds -DifferenceObject $actualCheckIds).Count -ne 0) {
    throw 'Shipping acceptance must contain exactly the required T09 checks.'
}
if (@($acceptance.checks | Where-Object { $_.status -ne 'passed' -or [string]::IsNullOrWhiteSpace([string] $_.evidence) }).Count -ne 0) {
    throw 'Every Shipping acceptance check must pass with visible or observed evidence.'
}
if ($acceptance.schemaVersion -ne 1 -or
    [string]::IsNullOrWhiteSpace([string] $acceptance.reviewer) -or
    $acceptance.revision -ne $Revision -or
    $acceptance.fingerprint -ne $Fingerprint -or
    $acceptance.resolution.width -ne 2560 -or
    $acceptance.resolution.height -ne 1440) {
    throw 'Shipping acceptance metadata does not match the current T09 revision, fingerprint, or 2560 x 1440 profile.'
}

$currentExecutableHash = (Get-FileHash -LiteralPath $PackageExecutable -Algorithm SHA256).Hash.ToLowerInvariant()
if ($acceptance.packageExecutableSha256 -ne $currentExecutableHash) {
    throw 'Shipping acceptance does not match the current Shipping executable.'
}

$packageDirectory = Split-Path -Parent $PackageExecutable
if ((Split-Path -Leaf $packageDirectory) -eq 'Windows') {
    $packageDirectory = Split-Path -Parent $packageDirectory
}
if (-not (Test-Path -LiteralPath $packageDirectory -PathType Container)) {
    throw "Shipping package directory was not found at '$packageDirectory'."
}

New-Item -ItemType Directory -Path $DeliveryRoot -Force | Out-Null
$shortRevision = $Revision.Substring(0, 12).ToLowerInvariant()
$zipPath = Join-Path $DeliveryRoot "fpsOne-$shortRevision-win64-shipping.zip"
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory(
    $packageDirectory,
    $zipPath,
    [IO.Compression.CompressionLevel]::Optimal,
    $false
)
$zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()

$resultDirectory = Split-Path -Parent $ResultPath
if ($resultDirectory) {
    New-Item -ItemType Directory -Path $resultDirectory -Force | Out-Null
}
[pscustomobject][ordered]@{
    schemaVersion = 1
    generatedAtUtc = [DateTime]::UtcNow.ToString('o')
    revision = $Revision
    fingerprint = $Fingerprint
    packageExecutable = [IO.Path]::GetFullPath($PackageExecutable)
    packageExecutableSha256 = $currentExecutableHash
    acceptancePath = [IO.Path]::GetFullPath($AcceptancePath)
    zipPath = [IO.Path]::GetFullPath($zipPath)
    zipSha256 = $zipHash
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ResultPath -Encoding UTF8

Write-Output "T09_DELIVERY_COMPLETED $zipPath sha256:$zipHash"

[CmdletBinding()]
param(
    [string] $SourceRepository,

    [string] $RemoteRepository,

    [string] $ExpectedRevision,

    [string] $DestinationRoot = 'C:\fpsOne-output\CleanClone'
)

$ErrorActionPreference = 'Stop'
if (-not $SourceRepository) {
    $SourceRepository = Split-Path -Parent $PSScriptRoot
}
$SourceRepository = [IO.Path]::GetFullPath($SourceRepository)
if (-not $ExpectedRevision) {
    $ExpectedRevision = ([string] (& git -C $SourceRepository rev-parse HEAD)).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve the source repository revision.' }
}
if (-not $RemoteRepository) {
    $RemoteRepository = ([string] (& git -C $SourceRepository remote get-url origin)).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $RemoteRepository) {
        throw 'Unable to resolve the canonical public Git remote.'
    }
}

function Get-LfsContract {
    param([string] $Repository)

    $entries = @(& git -C $Repository lfs ls-files -l)
    if ($LASTEXITCODE -ne 0) { throw "Unable to enumerate Git LFS assets in '$Repository'." }
    return @($entries | ForEach-Object {
        if ($_ -notmatch '^([0-9a-f]{64})\s+[\*-]\s+(.+)$') {
            throw "Unexpected Git LFS entry: $_"
        }
        "$($Matches[1]) $($Matches[2])"
    } | Sort-Object)
}

$resolvedDestinationRoot = [IO.Path]::GetFullPath($DestinationRoot).TrimEnd('\')
New-Item -ItemType Directory -Path $resolvedDestinationRoot -Force | Out-Null
$clonePath = Join-Path $resolvedDestinationRoot ('fpsOne-' + $ExpectedRevision.Substring(0, 12) + '-' + [guid]::NewGuid().ToString('N'))
$resolvedClonePath = [IO.Path]::GetFullPath($clonePath)
if (-not $resolvedClonePath.StartsWith($resolvedDestinationRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to create a clean-clone checkout outside the configured destination root.'
}

$previousSkipSmudge = $env:GIT_LFS_SKIP_SMUDGE
try {
    $env:GIT_LFS_SKIP_SMUDGE = '1'
    & git clone --quiet --no-checkout $RemoteRepository $resolvedClonePath
    if ($LASTEXITCODE -ne 0) { throw "Public clean clone failed from '$RemoteRepository'." }
    $env:GIT_LFS_SKIP_SMUDGE = $previousSkipSmudge

    $publicRevision = ([string] (& git -C $resolvedClonePath rev-parse origin/HEAD)).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve the public remote default branch.' }
    & git -C $resolvedClonePath checkout --quiet $publicRevision
    if ($LASTEXITCODE -ne 0) { throw "Clean clone could not check out public revision '$publicRevision'." }

    $sourceLfsContract = @(Get-LfsContract -Repository $SourceRepository)
    $publicLfsContract = @(Get-LfsContract -Repository $resolvedClonePath)
    $lfsDifference = @(Compare-Object -ReferenceObject $sourceLfsContract -DifferenceObject $publicLfsContract)
    if ($lfsDifference.Count -ne 0) {
        throw 'The current source requires Git LFS assets that are not present on the public default branch.'
    }

    & git -C $resolvedClonePath lfs pull origin $publicRevision
    if ($LASTEXITCODE -ne 0) { throw 'Clean clone could not obtain the Git LFS assets.' }
    & git -C $resolvedClonePath lfs fsck
    if ($LASTEXITCODE -ne 0) { throw 'Git LFS reported missing or corrupt clean-clone objects.' }

    $actualRevision = ([string] (& git -C $resolvedClonePath rev-parse HEAD)).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualRevision -ne $publicRevision) {
        throw "Clean clone revision '$actualRevision' does not match public revision '$publicRevision'."
    }
    $dirty = @(& git -C $resolvedClonePath status --porcelain --untracked-files=all)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) {
        throw 'Clean clone is not clean after Git LFS materialization.'
    }

    $requiredFiles = @(
        'FPSOne.uproject',
        'ASSETS.md',
        'README.md',
        'Build\character-toolchain.json',
        'Content\Maps\L_Testbed.umap',
        'SourceArt\asset-manifest.json',
        'SourceArt\Characters\NPC_A\NPC_A.blend',
        'SourceArt\Characters\NPC_B\NPC_B.blend',
        'docs\setup.md',
        'scripts\restore-art-sources.ps1',
        'scripts\regenerate-assets.ps1',
        'scripts\verify.ps1'
    )
    $missingFiles = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $resolvedClonePath $_) -PathType Leaf) })
    if ($missingFiles.Count -ne 0) {
        throw 'Clean clone is missing reproducibility files: ' + ($missingFiles -join ', ')
    }

    & (Join-Path $resolvedClonePath 'scripts\test-asset-manifest.ps1') -Root $resolvedClonePath | Out-Null
    Write-Output "T09_CLEAN_CLONE_PASSED sourceRevision=$ExpectedRevision publicRevision=$actualRevision remote=$RemoteRepository lfsFiles=$(@(& git -C $resolvedClonePath lfs ls-files -n).Count)"
} finally {
    $env:GIT_LFS_SKIP_SMUDGE = $previousSkipSmudge
    if (Test-Path -LiteralPath $resolvedClonePath) {
        $checkedClonePath = [IO.Path]::GetFullPath($resolvedClonePath)
        if (-not $checkedClonePath.StartsWith($resolvedDestinationRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Refusing to remove a clean-clone checkout outside the configured destination root.'
        }
        Remove-Item -LiteralPath $checkedClonePath -Recurse -Force
    }
}

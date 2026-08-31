[CmdletBinding()]
param([string] $Root = (Split-Path -Parent $PSScriptRoot), [switch] $SourcesOnly)

$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($Root)
if (-not (Test-Path -LiteralPath (Join-Path $Root 'ASSETS.md'))) { throw 'ASSETS.md is missing.' }
$manifest = Get-Content -LiteralPath (Join-Path $Root 'SourceArt\asset-manifest.json') -Raw | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or @($manifest.assets).Count -eq 0) { throw 'Invalid asset manifest schema or empty manifest.' }
$covered = @{}
$totalBytes = 0L

function Test-ManifestFile {
    param($Entry)
    $relative = [string] $Entry.path
    if ($relative -notmatch '^(SourceArt|Content)/[A-Za-z0-9_./-]+$' -or $relative.Contains('..')) {
        throw "Invalid covered asset path: $relative"
    }
    if ($covered.ContainsKey($relative)) { throw "Duplicate asset coverage: $relative" }
    $path = Join-Path $Root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing covered asset: $relative" }
    if ($Entry.sha256 -notmatch '^[0-9a-f]{64}$' -or
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) {
        throw "Asset hash mismatch: $relative"
    }
    $covered[$relative] = $true
    $script:totalBytes += (Get-Item -LiteralPath $path).Length
    if ($relative -match '\.(jpg|png)$') {
        Add-Type -AssemblyName System.Drawing
        $image = [Drawing.Image]::FromFile($path)
        try {
            if ([Math]::Max($image.Width, $image.Height) -gt 2048 -or
                ($relative -match '\.jpg$' -and [Math]::Max($image.Width, $image.Height) -ne 2048)) {
                throw "Textures must use the selected maximum 2K profile: $relative"
            }
        } finally { $image.Dispose() }
    }
}

foreach ($asset in $manifest.assets) {
    foreach ($field in @('id', 'source', 'author', 'version', 'license', 'licenseEvidence', 'attribution')) {
        if ([string]::IsNullOrWhiteSpace([string] $asset.$field)) { throw "Asset lacks $field provenance." }
    }
    $polyHaven = $asset.source -match '^https://polyhaven.com/a/[A-Za-z0-9_]+$' -and
        $asset.licenseEvidence -eq 'https://polyhaven.com/license'
    $makeHuman = $asset.source -eq 'https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html' -and
        $asset.licenseEvidence -eq 'https://static.makehumancommunity.org/about/license.html'
    if ($asset.license -ne 'CC0-1.0' -or $asset.publicRedistribution -ne $true -or
        -not ($polyHaven -or $makeHuman)) {
        throw "Unapproved public-redistribution license or evidence: $($asset.id)"
    }
    foreach ($entry in @($asset.files)) { Test-ManifestFile $entry }
    if (-not $SourcesOnly) {
        foreach ($entry in @($asset.generatedFiles)) { Test-ManifestFile $entry }
    }
}
if ($SourcesOnly) {
    Write-Output "ASSET_SOURCES_PASSED: $($manifest.assets.Count) licensed sources; pinned file hashes unchanged."
    return
}
foreach ($entry in @($manifest.projectAuthoredFiles)) { Test-ManifestFile $entry }
foreach ($directory in @('SourceArt', 'Content\Environment', 'Content\Characters')) {
    $path = Join-Path $Root $directory
    if (Test-Path -LiteralPath $path) {
        foreach ($file in Get-ChildItem -LiteralPath $path -File -Recurse) {
            $relative = $file.FullName.Substring($Root.Length + 1).Replace('\', '/')
            if ($relative -ne 'SourceArt/asset-manifest.json' -and -not $covered.ContainsKey($relative)) {
                throw "Uncovered asset file: $relative"
            }
        }
    }
}
if ($totalBytes -ge 8GB) { throw 'The retained asset set exceeds the 8 GiB budget.' }
Write-Output "ASSET_MANIFEST_PASSED: $($manifest.assets.Count) CC0 sources; $($covered.Count) hashed files; $([Math]::Round($totalBytes / 1MB, 1)) MiB; all textures 2K."

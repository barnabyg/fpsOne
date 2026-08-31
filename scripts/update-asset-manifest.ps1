[CmdletBinding()]
param([string] $Root = (Split-Path -Parent $PSScriptRoot))

# Hash staged output before publication. Source hashes remain pinned;
# regeneration may update only authored and imported Unreal output hashes.
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($Root)
$manifestPath = Join-Path $Root 'SourceArt\asset-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
function New-FileEntry([IO.FileInfo] $File) {
    [pscustomobject]@{
        path = $File.FullName.Substring($Root.Length + 1).Replace('\', '/')
        sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$materialSources = @{
    wood_floor = @('M_Oak', 'M_Floor')
    fabric_pattern_07 = @('M_Linen', 'M_Rug')
    white_plaster_02 = @('M_WarmPlaster')
}
$covered = @{}
foreach ($asset in $manifest.assets) {
    foreach ($file in $asset.files) {
        if ((Get-FileHash -LiteralPath (Join-Path $Root $file.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) {
            throw "Pinned source hash mismatch: $($file.path)"
        }
    }
    $generated = @()
    $importFolder = Join-Path $Root "Content\Environment\RoomA\$($asset.id)"
    if (Test-Path -LiteralPath $importFolder) {
        $generated += Get-ChildItem -LiteralPath $importFolder -Recurse -File | ForEach-Object { New-FileEntry $_ }
    }
    $textureFolder = Join-Path $Root 'Content\Environment\RoomA\Textures'
    if (Test-Path -LiteralPath $textureFolder) {
        $generated += Get-ChildItem -LiteralPath $textureFolder -File | Where-Object Name -Like "$($asset.id)*" | ForEach-Object { New-FileEntry $_ }
    }
    foreach ($name in $materialSources[$asset.id]) {
        $path = Join-Path $Root "Content\Environment\RoomA\Materials\$name.uasset"
        if (Test-Path -LiteralPath $path) { $generated += New-FileEntry (Get-Item -LiteralPath $path) }
    }
    foreach ($entry in $generated) { $covered[$entry.path] = $true }
    $asset | Add-Member -NotePropertyName generatedFiles -NotePropertyValue @($generated | Sort-Object path) -Force
}
$authored = @()
foreach ($directory in @('SourceArt\Authored', 'Content\Environment')) {
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $Root $directory) -File -Recurse) {
        $entry = New-FileEntry $file
        if (-not $covered.ContainsKey($entry.path)) {
            if ($entry.path -notmatch '^SourceArt/Authored/SM_(LinenSofa|Sideboard|FloorLamp|Rug)\.glb$' -and
                $entry.path -notmatch '^Content/Environment/RoomA/(SM_(LinenSofa|Sideboard|FloorLamp|Rug)/|Materials/M_(Piping|Bronze|Shade|Ceiling|Trim|SagePaint|Charcoal|Paper|Ochre|ArtPaper)\.uasset$)') {
                throw "Unclassified generated art requires explicit provenance: $($entry.path)"
            }
            $authored += $entry
        }
    }
}
$manifest | Add-Member -NotePropertyName projectAuthoredFiles -NotePropertyValue @($authored | Sort-Object path) -Force
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
& (Join-Path $PSScriptRoot 'test-asset-manifest.ps1') -Root $Root

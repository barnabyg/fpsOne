[CmdletBinding()]
param([string] $Root = (Split-Path -Parent $PSScriptRoot))

# Optional recovery of the exact CC0 source files. A normal Git LFS clone does
# not need network asset downloads. Never overwrite an existing changed file.
$ErrorActionPreference = 'Stop'
$manifest = Get-Content -LiteralPath (Join-Path $Root 'SourceArt\asset-manifest.json') -Raw | ConvertFrom-Json
foreach ($asset in $manifest.assets) {
    foreach ($file in $asset.files) {
        if ($file.path -notmatch '^SourceArt/PolyHaven/[A-Za-z0-9_./-]+$' -or $file.path.Contains('..') -or
            $file.url -notmatch '^https://dl.polyhaven.org/file/ph-assets/') { throw 'Unapproved source path or URL.' }
        $destination = Join-Path $Root $file.path
        if (Test-Path -LiteralPath $destination) {
            if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) {
                throw "Existing source differs; preserve it before restoring: $destination"
            }
            continue
        }
        New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
        $incoming = "$destination.download"
        try {
            Invoke-WebRequest -Uri $file.url -UserAgent 'fpsOne-art-restore/1.0 (https://github.com/barnabyg/fpsOne)' -OutFile $incoming
            if ((Get-FileHash -LiteralPath $incoming -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256) {
                throw "Downloaded source hash mismatch: $($file.path)"
            }
            Move-Item -LiteralPath $incoming -Destination $destination
        } finally {
            if (Test-Path -LiteralPath $incoming) { Remove-Item -LiteralPath $incoming }
        }
    }
}
Write-Output 'Pinned Poly Haven sources restored and hash-checked.'

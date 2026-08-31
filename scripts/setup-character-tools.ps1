[CmdletBinding()]
param([string] $ToolRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '.scratch\character-tools'))

$ErrorActionPreference = 'Stop'
$ToolRoot = [IO.Path]::GetFullPath($ToolRoot)
if ([IO.Path]::GetPathRoot($ToolRoot) -ne 'C:\') { throw 'Character tools and caches must stay on C:.' }
$pins = Get-Content (Join-Path (Split-Path -Parent $PSScriptRoot) 'Build\character-toolchain.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Path $ToolRoot -Force | Out-Null
foreach ($property in $pins.PSObject.Properties) {
    $pin = $property.Value
    $archive = Join-Path $ToolRoot $pin.archive
    if (-not (Test-Path -LiteralPath $archive)) {
        & curl.exe --fail --location --silent --show-error $pin.url --output $archive
        if ($LASTEXITCODE -ne 0) { throw "Download failed: $($pin.url)" }
    }
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256) {
        throw "Pinned archive hash mismatch: $archive. No files were extracted from this archive."
    }
    Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $ToolRoot $pin.directory) -Force
    Write-Output "$($property.Name) $($pin.version): verified and installed on C:"
}
Write-Output "Blender: $ToolRoot\blender\blender-4.5.3-windows-x64\blender.exe"

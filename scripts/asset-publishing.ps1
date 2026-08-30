function Assert-UnrealEditorsClosed {
    # Fail closed without depending on command-line visibility or path spelling.
    $active = Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $_.Name -match '^UnrealEditor(-Cmd)?\.exe$'
    }
    if ($active) { throw 'Close all Unreal Editor and commandlet processes before publishing assets.' }
}

function Install-GeneratedAsset {
    param([string] $Incoming, [string] $Destination)

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        [System.IO.File]::Replace($Incoming, $Destination, [NullString]::Value)
    } else {
        [System.IO.File]::Move($Incoming, $Destination)
    }
}

function Publish-GeneratedAssetSet {
    param(
        [string] $SourceRoot,
        [string] $DestinationRoot,
        [string] $BackupRoot,
        [string[]] $AssetPaths
    )

    $ErrorActionPreference = 'Stop'
    $SourceRoot = [System.IO.Path]::GetFullPath($SourceRoot)
    $DestinationRoot = [System.IO.Path]::GetFullPath($DestinationRoot)
    $BackupRoot = [System.IO.Path]::GetFullPath($BackupRoot)
    if (Test-Path -LiteralPath $BackupRoot) { throw 'Backup directory must be new.' }
    if ([System.IO.Path]::GetPathRoot($BackupRoot) -ne [System.IO.Path]::GetPathRoot($DestinationRoot)) {
        throw 'Asset transaction and destination must share a volume.'
    }

    # Validate the entire set before writing any destination asset.
    $entries = foreach ($relativePath in $AssetPaths) {
        if ($relativePath -notmatch '^Content[/\\][A-Za-z0-9_/\\-]+\.(uasset|umap)$' -or $relativePath.Contains('..')) {
            throw "Invalid generated asset path: $relativePath"
        }
        $source = Join-Path $SourceRoot $relativePath
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Missing generated asset: $relativePath"
        }
        $destination = Join-Path $DestinationRoot $relativePath
        [pscustomobject]@{
            source = $source
            destination = $destination
            incoming = Join-Path $BackupRoot "incoming\$relativePath"
            original = Join-Path $BackupRoot "original\$relativePath"
            existed = Test-Path -LiteralPath $destination -PathType Leaf
        }
    }
    if (@($entries).Count -eq 0) { throw 'Generated asset set cannot be empty.' }

    foreach ($entry in $entries) {
        New-Item -ItemType Directory -Path (Split-Path $entry.incoming), (Split-Path $entry.original), (Split-Path $entry.destination) -Force | Out-Null
        Copy-Item -LiteralPath $entry.source -Destination $entry.incoming
        if ($entry.existed) { Copy-Item -LiteralPath $entry.destination -Destination $entry.original }
    }

    $installed = [System.Collections.Generic.List[object]]::new()
    try {
        foreach ($entry in $entries) {
            Install-GeneratedAsset -Incoming $entry.incoming -Destination $entry.destination
            $installed.Add($entry)
        }
    } catch {
        $publicationError = $_
        foreach ($entry in $installed) {
            if ($entry.existed) {
                Copy-Item -LiteralPath $entry.original -Destination $entry.destination -Force
            } else {
                Remove-Item -LiteralPath $entry.destination -Force
            }
        }
        throw $publicationError
    }
}

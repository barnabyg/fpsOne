$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'public asset provenance validation' {
    BeforeEach {
        $caseRoot = Join-Path $TestDrive ([guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path "$caseRoot\SourceArt\PolyHaven\sample" -Force | Out-Null
        Set-Content "$caseRoot\ASSETS.md" 'Test manifest'
        Set-Content "$caseRoot\SourceArt\PolyHaven\sample\source.gltf" 'changed content'
        $manifest = @{
            schemaVersion = 1
            assets = @(@{
                id = 'sample'; source = 'https://polyhaven.com/a/sample'; author = 'Artist'
                version = 'pinned'; license = 'CC0-1.0'; publicRedistribution = $true
                licenseEvidence = 'https://polyhaven.com/license'; attribution = 'Artist'
                files = @(@{ path = 'SourceArt/PolyHaven/sample/source.gltf'; sha256 = (Get-FileHash "$caseRoot\SourceArt\PolyHaven\sample\source.gltf" -Algorithm SHA256).Hash.ToLowerInvariant() })
                generatedFiles = @()
            })
            projectAuthoredFiles = @()
        }
    }
    It 'accepts a completely covered redistributable source set' {
        $manifest | ConvertTo-Json -Depth 8 | Set-Content "$caseRoot\SourceArt\asset-manifest.json"
        (& "$repoRoot\scripts\test-asset-manifest.ps1" -Root $caseRoot) | Should Match 'ASSET_MANIFEST_PASSED'
    }
    It 'rejects a source whose bytes no longer match its recorded hash' {
        $manifest.assets[0].files[0].sha256 = '0' * 64
        $manifest | ConvertTo-Json -Depth 8 | Set-Content "$caseRoot\SourceArt\asset-manifest.json"
        { & "$repoRoot\scripts\test-asset-manifest.ps1" -Root $caseRoot } | Should Throw 'hash mismatch'
    }
    It 'rejects unlisted art even when declared files still match' {
        Set-Content "$caseRoot\SourceArt\PolyHaven\sample\unlisted.gltf" 'uncovered'
        $manifest | ConvertTo-Json -Depth 8 | Set-Content "$caseRoot\SourceArt\asset-manifest.json"
        { & "$repoRoot\scripts\test-asset-manifest.ps1" -Root $caseRoot } | Should Throw 'Uncovered asset'
    }
    It 'rejects an asset without permitted raw redistribution' {
        $manifest.assets[0].publicRedistribution = $false
        $manifest | ConvertTo-Json -Depth 8 | Set-Content "$caseRoot\SourceArt\asset-manifest.json"
        { & "$repoRoot\scripts\test-asset-manifest.ps1" -Root $caseRoot } | Should Throw 'redistribution'
    }

    It 'leaves published assets and their manifest untouched when staged source validation fails' {
        . "$repoRoot\scripts\asset-publishing.ps1"
        New-Item -ItemType Directory -Path "$caseRoot\Content\Environment\RoomA\sample", "$caseRoot\SourceArt\Authored" -Force | Out-Null
        Set-Content "$caseRoot\Content\Environment\RoomA\sample\Mesh.uasset" 'old mesh'
        $manifest | ConvertTo-Json -Depth 8 | Set-Content "$caseRoot\SourceArt\asset-manifest.json"
        $originalManifest = Get-Content "$caseRoot\SourceArt\asset-manifest.json" -Raw
        $stage = Join-Path $TestDrive 'stage'
        Copy-Item -LiteralPath $caseRoot -Destination $stage -Recurse
        Set-Content "$stage\SourceArt\PolyHaven\sample\source.gltf" 'tampered source'
        Set-Content "$stage\Content\Environment\RoomA\sample\Mesh.uasset" 'new mesh'

        { Publish-GeneratedAssetSet $stage $caseRoot (Join-Path $TestDrive 'backup') @('Content/Environment/RoomA/sample/Mesh.uasset') -ValidateRoomA } | Should Throw 'hash mismatch'
        (Get-Content "$caseRoot\Content\Environment\RoomA\sample\Mesh.uasset") | Should Be 'old mesh'
        (Get-Content "$caseRoot\SourceArt\asset-manifest.json" -Raw) | Should Be $originalManifest
    }

    It 'publishes regenerated art with the matching validated manifest' {
        . "$repoRoot\scripts\asset-publishing.ps1"
        New-Item -ItemType Directory -Path "$caseRoot\Content\Environment\RoomA\sample", "$caseRoot\SourceArt\Authored" -Force | Out-Null
        Set-Content "$caseRoot\Content\Environment\RoomA\sample\Mesh.uasset" 'old mesh'
        $manifest | ConvertTo-Json -Depth 8 | Set-Content "$caseRoot\SourceArt\asset-manifest.json"
        $stage = Join-Path $TestDrive 'valid-stage'
        Copy-Item -LiteralPath $caseRoot -Destination $stage -Recurse
        Set-Content "$stage\Content\Environment\RoomA\sample\Mesh.uasset" 'new mesh'

        Publish-GeneratedAssetSet $stage $caseRoot (Join-Path $TestDrive 'valid-backup') @('Content/Environment/RoomA/sample/Mesh.uasset') -ValidateRoomA
        (Get-Content "$caseRoot\Content\Environment\RoomA\sample\Mesh.uasset") | Should Be 'new mesh'
        (& "$repoRoot\scripts\test-asset-manifest.ps1" -Root $caseRoot) | Should Match 'ASSET_MANIFEST_PASSED'
    }
}

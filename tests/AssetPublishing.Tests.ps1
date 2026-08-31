$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'Unreal publication guard' {
    BeforeEach { . (Join-Path $repoRoot 'scripts\asset-publishing.ps1') }

    It 'allows publication when only non-editor processes exist' {
        Mock Get-CimInstance { [pscustomobject]@{ Name = 'notepad.exe'; CommandLine = $null } }
        Assert-UnrealEditorsClosed
    }

    It 'rejects an editor regardless of project path spelling' {
        Mock Get-CimInstance { [pscustomobject]@{ Name = 'UnrealEditor.exe'; CommandLine = 'UnrealEditor.exe ./FPSOne.uproject' } }
        { Assert-UnrealEditorsClosed } | Should Throw 'Close all Unreal Editor'
    }

    It 'rejects a commandlet even when its command line is inaccessible' {
        Mock Get-CimInstance { [pscustomobject]@{ Name = 'UnrealEditor-Cmd.exe'; CommandLine = $null } }
        { Assert-UnrealEditorsClosed } | Should Throw 'Close all Unreal Editor'
    }
}

Describe 'validated asset publishing' {
    BeforeEach {
        . (Join-Path $repoRoot 'scripts\asset-publishing.ps1')
        $caseRoot = Join-Path $TestDrive ([guid]::NewGuid().ToString('N'))
        $source = Join-Path $caseRoot 'source'
        $destination = Join-Path $caseRoot 'destination'
        $backup = Join-Path $caseRoot 'backup'
        New-Item -ItemType Directory -Path "$source\Content", "$destination\Content" -Force | Out-Null
        Set-Content -LiteralPath "$source\Content\A.uasset" -Value 'new A'
        Set-Content -LiteralPath "$source\Content\B.uasset" -Value 'new B'
        Set-Content -LiteralPath "$destination\Content\A.uasset" -Value 'old A'
        Set-Content -LiteralPath "$destination\Content\B.uasset" -Value 'old B'
        $paths = @('Content/A.uasset', 'Content/B.uasset')
    }

    It 'keeps originals when the generated set is incomplete' {
        Remove-Item -LiteralPath "$source\Content\B.uasset"
        { Publish-GeneratedAssetSet $source $destination $backup $paths } | Should Throw
        (Get-Content "$destination\Content\A.uasset") | Should Be 'old A'
        (Get-Content "$destination\Content\B.uasset") | Should Be 'old B'
    }

    It 'publishes the complete set and retains recoverable originals' {
        Publish-GeneratedAssetSet $source $destination $backup $paths
        (Get-Content "$destination\Content\A.uasset") | Should Be 'new A'
        (Get-Content "$destination\Content\B.uasset") | Should Be 'new B'
        (Get-Content "$backup\original\Content\A.uasset") | Should Be 'old A'
    }

    It 'rolls back installed files if a later replacement fails' {
        Mock Install-GeneratedAsset { throw 'Injected replacement failure' } -ParameterFilter { $Destination.EndsWith('B.uasset') }
        { Publish-GeneratedAssetSet $source $destination $backup $paths } | Should Throw
        Assert-MockCalled Install-GeneratedAsset -Times 1 -Exactly -ParameterFilter { $Destination.EndsWith('B.uasset') }
        (Get-Content "$destination\Content\A.uasset") | Should Be 'old A'
        (Get-Content "$destination\Content\B.uasset") | Should Be 'old B'
    }

    It 'rejects paths outside Content before publishing' {
        { Publish-GeneratedAssetSet $source $destination $backup @('../outside.uasset') } | Should Throw
        (Get-Content "$destination\Content\A.uasset") | Should Be 'old A'
    }

    It 'rolls back assets when their manifest cannot be replaced' {
        New-Item -ItemType Directory -Path "$source\SourceArt", "$destination\SourceArt" -Force | Out-Null
        Set-Content "$source\SourceArt\asset-manifest.json" 'new manifest'
        Set-Content "$destination\SourceArt\asset-manifest.json" 'old manifest'
        $paths += 'SourceArt/asset-manifest.json'
        # Windows allows the backup read but denies replacing this open file.
        $handle = [IO.File]::Open("$destination\SourceArt\asset-manifest.json", [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
        try {
            { Publish-GeneratedAssetSet $source $destination $backup $paths } | Should Throw
        } finally { $handle.Dispose() }
        (Get-Content "$destination\Content\A.uasset") | Should Be 'old A'
        (Get-Content "$destination\Content\B.uasset") | Should Be 'old B'
        (Get-Content "$destination\SourceArt\asset-manifest.json") | Should Be 'old manifest'
    }
}

function Get-FPSOnePackageRoot {
    param([string] $PackageExecutable)

    $packageRoot = Split-Path -Parent $PackageExecutable
    if ((Split-Path -Leaf $packageRoot) -eq 'Windows') {
        $packageRoot = Split-Path -Parent $packageRoot
    }
    return [IO.Path]::GetFullPath($packageRoot)
}

function Get-FPSOnePackageManifest {
    param([string] $PackageRoot)

    $resolvedRoot = [IO.Path]::GetFullPath($PackageRoot).TrimEnd('\')
    $rootUri = [Uri]($resolvedRoot + '\')
    return @(Get-ChildItem -LiteralPath $resolvedRoot -File -Recurse | Sort-Object FullName | ForEach-Object {
        $fileUri = [Uri]([IO.Path]::GetFullPath($_.FullName))
        [pscustomobject][ordered]@{
            path = [Uri]::UnescapeDataString($rootUri.MakeRelativeUri($fileUri).ToString()).Replace('/', '\')
            length = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
}

function Get-FPSOnePackageContract {
    param([object[]] $Manifest)

    return @($Manifest | ForEach-Object {
        "$([string] $_.path)|$([long] $_.length)|$([string] $_.sha256)"
    } | Sort-Object)
}

function Assert-FPSOnePackageManifest {
    param([object[]] $Expected, [object[]] $Actual)

    $expectedContract = @(Get-FPSOnePackageContract -Manifest $Expected)
    $actualContract = @(Get-FPSOnePackageContract -Manifest $Actual)
    if ($expectedContract.Count -ne $actualContract.Count -or
        @(Compare-Object -ReferenceObject $expectedContract -DifferenceObject $actualContract).Count -ne 0) {
        throw 'Shipping acceptance does not match the complete Shipping package.'
    }
}

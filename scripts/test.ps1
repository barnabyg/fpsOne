[CmdletBinding()]
param(
    [string] $ReportPath
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $ReportPath) {
    $ReportPath = Join-Path $repoRoot 'Saved\Verification\logs\repository-tests.xml'
}

$reportDirectory = Split-Path -Parent $ReportPath
if ($reportDirectory) {
    New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
}
if (Test-Path -LiteralPath $ReportPath -PathType Leaf) {
    Remove-Item -LiteralPath $ReportPath -Force
}

$previousErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    $result = Invoke-Pester `
        -Script (Join-Path $repoRoot 'tests') `
        -ExcludeTag 'VerifierSelfTest' `
        -OutputFormat NUnitXml `
        -OutputFile $ReportPath `
        -PassThru
} finally {
    $ErrorActionPreference = $previousErrorActionPreference
}

if ($null -eq $result -or $result.FailedCount -gt 0) {
    exit 1
}

exit 0

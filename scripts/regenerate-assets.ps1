[CmdletBinding()]
param([string] $EngineRoot = 'C:\Program Files\Epic Games\UE_5.8')

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$projectPath = Join-Path $repoRoot 'FPSOne.uproject'
$editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if (-not (Test-Path -LiteralPath $editor -PathType Leaf)) { throw "Unreal Editor not found: $editor" }
. (Join-Path $PSScriptRoot 'asset-publishing.ps1')

function Invoke-StagingCheck {
    param([string[]] $Arguments, [string] $LogPath, [string] $SuccessMarker)

    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $editor @Arguments 2>&1 | Tee-Object -FilePath $LogPath | Out-Null
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    $passed = Select-String -LiteralPath $LogPath -SimpleMatch $SuccessMarker -Quiet
    $errors = Select-String -LiteralPath $LogPath -Pattern 'LogPython: Error|LogBlueprint: (Error|Warning)|LogAutomationController: Error' -Quiet
    if ($code -ne 0 -or -not $passed -or $errors) {
        throw "Staged asset validation failed; original assets are untouched. See $LogPath"
    }
}

Assert-UnrealEditorsClosed
& (Join-Path $PSScriptRoot 'test-asset-manifest.ps1') -Root $repoRoot -SourcesOnly
$transactionRoot = Join-Path $repoRoot ('Saved\AssetRegeneration\' + [guid]::NewGuid().ToString('N'))
$stageRoot = Join-Path $transactionRoot 'project'
New-Item -ItemType Directory -Path "$stageRoot\scripts", "$stageRoot\Content\Python" -Force | Out-Null
Copy-Item -LiteralPath $projectPath -Destination $stageRoot
Copy-Item -LiteralPath (Join-Path $repoRoot 'ASSETS.md') -Destination $stageRoot
Copy-Item -LiteralPath (Join-Path $repoRoot 'Config') -Destination $stageRoot -Recurse
Copy-Item -LiteralPath (Join-Path $repoRoot 'SourceArt') -Destination $stageRoot -Recurse
foreach ($name in @('bootstrap_project.py', 'interaction_assets.py', 'dialogue_assets.py', 'room_a_assets.py')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination "$stageRoot\scripts"
}
Copy-Item -LiteralPath (Join-Path $repoRoot 'Content\Python\test_interaction.py') -Destination "$stageRoot\Content\Python"
$stageProject = Join-Path $stageRoot 'FPSOne.uproject'
$common = @('-unattended', '-nop4', '-nosplash', '-NullRHI', '-stdout', '-FullStdOutLogOutput')
Invoke-StagingCheck -Arguments (@($stageProject, "-ExecutePythonScript=$stageRoot\scripts\bootstrap_project.py") + $common) `
    -LogPath (Join-Path $transactionRoot 'generation.log') -SuccessMarker 'T02 Blueprint generation completed without script errors'
# Reload saved gameplay Blueprints in a fresh process before the art pass.
# Reloading the map in the generation process can reset instance defaults.
Invoke-StagingCheck -Arguments (@($stageProject, "-ExecutePythonScript=$stageRoot\scripts\room_a_assets.py") + $common) `
    -LogPath (Join-Path $transactionRoot 'room-a-generation.log') -SuccessMarker 'T04_ROOM_A_GENERATION_PASSED'
Invoke-StagingCheck -Arguments (@($stageProject, '-ExecCmds=Automation RunTests Editor.Python.FPSOne.test_interaction', '-TestExit=Automation Test Queue Empty', "-ReportExportPath=$transactionRoot\interaction-report") + $common) `
    -LogPath (Join-Path $transactionRoot 'interaction.log') -SuccessMarker 'T03_DIALOGUE_FUNCTIONAL_TEST_PASSED'

$paths = @(
    'Content/Blueprints/BP_DialogueNPC.uasset',
    'Content/Blueprints/BPC_DialogueInteractable.uasset',
    'Content/Blueprints/BPC_Interactable.uasset',
    'Content/Blueprints/BPC_DoorInteractable.uasset',
    'Content/Blueprints/BPC_Interaction.uasset',
    'Content/Blueprints/BP_Door.uasset',
    'Content/Blueprints/BP_InteractionHUD.uasset',
    'Content/Blueprints/BP_InteractionTestTarget.uasset',
    'Content/Blueprints/BP_Player.uasset',
    'Content/Blueprints/BP_TestbedPlayerController.uasset',
    'Content/Blueprints/BP_TestbedGameMode.uasset',
    'Content/Maps/L_Testbed.umap'
)
$paths += Get-ChildItem -LiteralPath "$stageRoot\Content\Environment" -File -Recurse | ForEach-Object {
    $_.FullName.Substring($stageRoot.Length + 1).Replace('\', '/')
}
Assert-UnrealEditorsClosed
Publish-GeneratedAssetSet $stageRoot $repoRoot (Join-Path $transactionRoot 'backup') $paths -ValidateRoomA
Write-Output "ASSET_REGENERATION_PASSED: validated assets published; originals and logs retained in $transactionRoot"

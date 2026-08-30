$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'FPSOne project bootstrap' {
    It 'is a Blueprint-only Unreal Engine 5.8 project' {
        $projectPath = Join-Path $repoRoot 'FPSOne.uproject'

        Test-Path -LiteralPath $projectPath | Should Be $true

        $project = Get-Content -LiteralPath $projectPath -Raw | ConvertFrom-Json
        $project.EngineAssociation | Should Be '5.8'
        ($project.PSObject.Properties.Name -contains 'Modules') | Should Be $false
    }

    It 'pins the agreed Windows rendering baseline' {
        $engineConfigPath = Join-Path $repoRoot 'Config\DefaultEngine.ini'

        Test-Path -LiteralPath $engineConfigPath | Should Be $true

        $engineConfig = Get-Content -LiteralPath $engineConfigPath -Raw
        $engineConfig | Should Match '(?m)^DefaultGraphicsRHI=DefaultGraphicsRHI_DX12\r?$'
        $engineConfig | Should Match '(?m)^r\.DynamicGlobalIlluminationMethod=1\r?$'
        $engineConfig | Should Match '(?m)^r\.ReflectionMethod=1\r?$'
        $engineConfig | Should Match '(?m)^r\.Shadow\.Virtual\.Enable=1\r?$'
        $engineConfig | Should Match '(?m)^r\.Nanite\.ProjectEnabled=True\r?$'
        $engineConfig | Should Match '(?m)^r\.AntiAliasingMethod=4\r?$'
        $engineConfig | Should Match '(?m)^r\.ScreenPercentage=75\r?$'
    }

    It 'defines only the agreed keyboard and mouse controls' {
        $inputConfigPath = Join-Path $repoRoot 'Config\DefaultInput.ini'

        Test-Path -LiteralPath $inputConfigPath | Should Be $true

        $inputConfig = Get-Content -LiteralPath $inputConfigPath -Raw
        $inputConfig | Should Match 'AxisName="MoveForward",Scale=1\.000000,Key=W'
        $inputConfig | Should Match 'AxisName="MoveForward",Scale=-1\.000000,Key=S'
        $inputConfig | Should Match 'AxisName="MoveRight",Scale=-1\.000000,Key=A'
        $inputConfig | Should Match 'AxisName="MoveRight",Scale=1\.000000,Key=D'
        $inputConfig | Should Match 'AxisName="Turn",Scale=1\.000000,Key=MouseX'
        $inputConfig | Should Match 'AxisName="LookUp",Scale=-1\.000000,Key=MouseY'
        $inputConfig | Should Match 'ActionName="Exit",Key=Escape'
        $inputConfig | Should Match '(?m)^DefaultPlayerInputClass=/Script/EnhancedInput\.EnhancedPlayerInput\r?$'
        $inputConfig | Should Match '(?m)^DefaultInputComponentClass=/Script/EnhancedInput\.EnhancedInputComponent\r?$'
        $inputConfig | Should Not Match '(?i)jump|sprint|crouch|gamepad|fire'

        $bootstrapScript = Get-Content -LiteralPath (Join-Path $repoRoot 'scripts\bootstrap_project.py') -Raw
        $bootstrapScript | Should Match 'controller_defaults\.set_editor_property\("enable_motion_controls", False\)'
    }

    It 'binds E as the reusable Interaction input' {
        $inputConfigPath = Join-Path $repoRoot 'Config\DefaultInput.ini'
        $inputConfig = Get-Content -LiteralPath $inputConfigPath -Raw

        $inputConfig | Should Match 'ActionName="Interact",Key=E'
        ([regex]::Matches($inputConfig, 'ActionName="Interact"')).Count | Should Be 1
    }
}

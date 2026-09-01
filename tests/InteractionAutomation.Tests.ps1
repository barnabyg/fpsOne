$repoRoot = Split-Path -Parent $PSScriptRoot

Describe 'Player-facing Interaction automation' {
    It 'enables the editor-only Unreal Python Automation harness' {
        $project = Get-Content -LiteralPath (Join-Path $repoRoot 'FPSOne.uproject') -Raw | ConvertFrom-Json
        $plugin = @($project.Plugins | Where-Object Name -eq 'PythonAutomationTest')

        $plugin.Count | Should Be 1
        $plugin[0].Enabled | Should Be $true
        (@($plugin[0].TargetAllowList) -join ',') | Should Match '(^|,)Editor(,|$)'
    }

    It 'contains the player-facing Interaction functional test' {
        Test-Path -LiteralPath (Join-Path $repoRoot 'Content\Python\test_interaction.py') | Should Be $true
    }

    It 'runs the Interaction scenario as a required verifier gate' {
        $verifier = Get-Content -LiteralPath (Join-Path $repoRoot 'scripts\verify.ps1') -Raw

        $verifier | Should Match 'Automation RunTests Editor\.Python\.FPSOne\.test_interaction'
        $verifier | Should Match 'T02_INTERACTION_FUNCTIONAL_TEST_PASSED'
        $verifier | Should Match 'T03_DIALOGUE_FUNCTIONAL_TEST_PASSED'
        $verifier | Should Match 'T10_NPC_ANIMATION_PASSED'
        $verifier | Should Not Match "Interaction functional tests' 'not_applicable'"
    }
}

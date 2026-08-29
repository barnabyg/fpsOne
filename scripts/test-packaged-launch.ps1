[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $PackageExecutable
)

$ErrorActionPreference = 'Stop'

Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class FPSOneLaunchProbe
{
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint message, UIntPtr wParam, IntPtr lParam);
}
'@

function Find-GameWindow {
    param([Collections.Generic.HashSet[int]] $AllowedProcessIds)

    $script:gameWindow = [IntPtr]::Zero
    $script:gameWindowTitle = ''
    [FPSOneLaunchProbe]::EnumWindows({
        param([IntPtr] $window, [IntPtr] $state)

        $windowProcessId = [uint32] 0
        [void] [FPSOneLaunchProbe]::GetWindowThreadProcessId($window, [ref] $windowProcessId)
        if ($AllowedProcessIds.Contains([int] $windowProcessId) -and [FPSOneLaunchProbe]::IsWindowVisible($window)) {
            $title = [Text.StringBuilder]::new(512)
            [void] [FPSOneLaunchProbe]::GetWindowText($window, $title, $title.Capacity)
            if ($title.ToString() -like 'FPSOne*') {
                $script:gameWindow = $window
                $script:gameWindowTitle = $title.ToString()
                return $false
            }
        }
        return $true
    }, [IntPtr]::Zero) | Out-Null
    return $script:gameWindow
}

if (-not (Test-Path -LiteralPath $PackageExecutable -PathType Leaf)) {
    throw "Packaged executable was not found at '$PackageExecutable'."
}

if (@(Get-Process -Name FPSOne, UnrealGame -ErrorAction SilentlyContinue).Count -gt 0) {
    throw 'Close existing FPSOne or UnrealGame processes before running the packaged launch test.'
}

$launchTime = Get-Date
$testProcessIds = [Collections.Generic.HashSet[int]]::new()
try {
    $launcher = Start-Process -FilePath $PackageExecutable `
        -ArgumentList @('-windowed', '-ResX=800', '-ResY=450') `
        -PassThru `
        -WindowStyle Normal
    [void] $testProcessIds.Add($launcher.Id)

    $timer = [Diagnostics.Stopwatch]::StartNew()
    $window = [IntPtr]::Zero
    do {
        foreach ($process in @(Get-Process -Name FPSOne, UnrealGame -ErrorAction SilentlyContinue)) {
            if ($process.StartTime -ge $launchTime.AddSeconds(-1)) {
                [void] $testProcessIds.Add($process.Id)
            }
        }
        $window = Find-GameWindow -AllowedProcessIds $testProcessIds
        if ($window -ne [IntPtr]::Zero) {
            break
        }
        Start-Sleep -Milliseconds 200
    } while ($timer.Elapsed.TotalSeconds -lt 60)

    if ($window -eq [IntPtr]::Zero) {
        throw 'The Development Win64 package did not open an FPSOne game window within 60 seconds.'
    }

    Write-Output "Development Win64 package launched: $script:gameWindowTitle"
    [void] [FPSOneLaunchProbe]::PostMessage($window, 0x0010, [UIntPtr]::Zero, [IntPtr]::Zero)
} finally {
    Start-Sleep -Milliseconds 500
    foreach ($process in @(Get-Process -Name FPSOne, UnrealGame -ErrorAction SilentlyContinue)) {
        if ($process.StartTime -ge $launchTime.AddSeconds(-1)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

[CmdletBinding()]
param([Parameter(Mandatory = $true)][string] $CaptureRoot)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$dialogue = [Drawing.Bitmap]::new((Join-Path $CaptureRoot 'npc-a-dialogue.png'))
$restored = [Drawing.Bitmap]::new((Join-Path $CaptureRoot 'npc-a-restored.png'))
try {
    if ($dialogue.Width -ne $restored.Width -or $dialogue.Height -ne $restored.Height) {
        throw 'Dialogue and restored-view captures must have identical dimensions.'
    }
    # The scenario holds the camera on a static floor patch beside NPC A. The
    # restrained dot changes a few central pixels when exploration returns; it
    # brightens shaded surfaces and darkens bright ones. Test
    # the rendered output: a dot on both branches, or on neither, must fail.
    $dotPixels = 0
    $backgroundDelta = 0
    $backgroundSamples = 0
    $centreX = [int][Math]::Floor($dialogue.Width / 2)
    $centreY = [int][Math]::Floor($dialogue.Height / 2)
    for ($y = $centreY - 10; $y -le $centreY + 10; $y++) {
        for ($x = $centreX - 10; $x -le $centreX + 10; $x++) {
            $before = $dialogue.GetPixel($x, $y)
            $after = $restored.GetPixel($x, $y)
            $delta = ([int]$before.R + [int]$before.G + [int]$before.B - [int]$after.R - [int]$after.G - [int]$after.B) / 3.0
            if ([Math]::Abs($x - $centreX) -le 4 -and [Math]::Abs($y - $centreY) -le 5) {
                if ([Math]::Abs($delta) -gt 10) { $dotPixels++ }
            } else {
                $backgroundDelta += [Math]::Abs($delta)
                $backgroundSamples++
            }
        }
    }
    if ($backgroundDelta / $backgroundSamples -gt 2) {
        throw 'The centre background moved too much to compare the dot reliably.'
    }
    if ($dotPixels -lt 1 -or $dotPixels -gt 16) {
        throw "Expected a small visible dot only after dismissal; found $dotPixels contrasting central pixels."
    }
    # Sample inside the backing, away from its text and the restored Talk prompt.
    $panelX = [int]($dialogue.Width * 0.15)
    $panelY = $dialogue.Height - 70
    $before = $dialogue.GetPixel($panelX, $panelY)
    $after = $restored.GetPixel($panelX, $panelY)
    if ([int]$after.R - [int]$before.R -lt 40) {
        throw 'The charcoal dialogue backing did not appear and dismiss in the rendered views.'
    }
    Write-Output "T03_PRESENTATION_PIXELS_PASSED: $($dialogue.Width)x$($dialogue.Height); dot hidden during dialogue and restored afterward; charcoal panel dismisses."
} finally {
    $dialogue.Dispose()
    $restored.Dispose()
}

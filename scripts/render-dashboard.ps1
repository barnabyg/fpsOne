[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ResultPath,

    [Parameter(Mandatory = $true)]
    [string] $OutputPath
)

$ErrorActionPreference = 'Stop'

function ConvertTo-HtmlText {
    param([AllowNull()][object] $Value)

    return [System.Net.WebUtility]::HtmlEncode([string] $Value)
}

function ConvertTo-LinkHref {
    param([string] $Path)

    return (ConvertTo-HtmlText ($Path -replace '\\', '/'))
}

$result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$evidenceLabel = if ($result.stale) { 'STALE EVIDENCE' } else { 'CURRENT EVIDENCE' }
$evidenceClass = if ($result.stale) { 'failed' } else { 'passed' }

$toolRows = foreach ($property in $result.tools.PSObject.Properties) {
    '<tr><th>{0}</th><td>{1}</td></tr>' -f (ConvertTo-HtmlText $property.Name), (ConvertTo-HtmlText $property.Value)
}

$gateCards = foreach ($gate in @($result.gates)) {
    $status = ConvertTo-HtmlText $gate.status
    $logLink = if ($gate.logPath) {
        '<a href="{0}">{1}</a>' -f (ConvertTo-LinkHref $gate.logPath), (ConvertTo-HtmlText $gate.logPath)
    } else {
        '<span class="muted">No log</span>'
    }
    $reportLinks = foreach ($reportPath in @($gate.reportPaths)) {
        if ($reportPath) {
            '<br><a href="{0}">{1}</a>' -f (ConvertTo-LinkHref $reportPath), (ConvertTo-HtmlText $reportPath)
        }
    }

    @"
<article class="gate $(ConvertTo-HtmlText $gate.status)">
  <div class="gate-heading"><h3>$(ConvertTo-HtmlText $gate.name)</h3><span class="badge">$status</span></div>
  <p>$(ConvertTo-HtmlText $gate.details)</p>
  <dl><dt>Duration</dt><dd>$(ConvertTo-HtmlText $gate.durationMs) ms</dd><dt>Evidence</dt><dd>$logLink$($reportLinks -join '')</dd></dl>
</article>
"@
}

$exceptions = if (@($result.warningExceptions).Count -eq 0) {
    '<p class="muted">None recorded.</p>'
} else {
    '<ul>{0}</ul>' -f ((@($result.warningExceptions) | ForEach-Object { '<li>{0}</li>' -f (ConvertTo-HtmlText $_) }) -join '')
}

$screenshots = if (@($result.screenshots).Count -eq 0) {
    '<p class="muted">No screenshot evidence applies to this validation profile.</p>'
} else {
    (@($result.screenshots) | ForEach-Object {
        $metadata = if ($_.sha256) {
            '<br><span class="muted">SHA-256: {0}<br>Observed frame: {1} ms</span>' -f (ConvertTo-HtmlText $_.sha256), (ConvertTo-HtmlText $_.frameMilliseconds)
        } else { '' }
        '<figure><a href="{0}"><img src="{0}" alt="{1}"></a><figcaption>{1}{2}</figcaption></figure>' -f (ConvertTo-LinkHref $_.path), (ConvertTo-HtmlText $_.name), $metadata
    }) -join "`n"
}

$developmentPackage = if ($result.packages.development) { $result.packages.development } else { $result.packagePath }
$shippingPackage = [string] $result.packages.shipping
$deliveryZip = [string] $result.delivery.zipPath
$deliveryHash = [string] $result.delivery.zipSha256
$acceptancePath = [string] $result.delivery.acceptancePath

$html = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>fpsOne verification</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #0d1117; color: #e6edf3; }
    body { margin: 0; padding: 2rem; }
    main { max-width: 1100px; margin: 0 auto; }
    h1, h2, h3, p { margin-top: 0; }
    .summary, .gate, table { background: #161b22; border: 1px solid #30363d; border-radius: 10px; }
    .summary { display: grid; gap: .75rem; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); padding: 1rem; margin-bottom: 2rem; }
    .summary div, dl { min-width: 0; }
    dt { color: #8b949e; font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; }
    dd { margin: .2rem 0 .8rem; overflow-wrap: anywhere; }
    .evidence { padding: .55rem .8rem; border-radius: 999px; width: fit-content; font-weight: 700; }
    .evidence.passed, .gate.passed { border-color: #238636; }
    .evidence.failed, .gate.failed, .gate.missing, .gate.skipped { border-color: #da3633; }
    .gate.not_applicable { border-color: #6e7681; }
    .gates { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); margin-bottom: 2rem; }
    .gate { padding: 1rem; border-left-width: 5px; }
    .gate-heading { display: flex; justify-content: space-between; gap: 1rem; }
    .badge { color: #8b949e; font-size: .8rem; text-transform: uppercase; }
    table { border-collapse: separate; border-spacing: 0; width: 100%; margin-bottom: 2rem; overflow: hidden; }
    th, td { padding: .75rem; border-bottom: 1px solid #30363d; text-align: left; }
    tr:last-child th, tr:last-child td { border-bottom: 0; }
    a { color: #58a6ff; }
    .muted { color: #8b949e; }
    .screenshots { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
    figure { margin: 0; }
    img { width: 100%; border: 1px solid #30363d; border-radius: 8px; }
  </style>
</head>
<body>
<main>
  <h1>fpsOne verification</h1>
  <div class="evidence $evidenceClass">$evidenceLabel</div>
  <section class="summary">
    <div><dt>Mode</dt><dd>$(ConvertTo-HtmlText $result.mode)</dd></div>
    <div><dt>Revision</dt><dd>$(ConvertTo-HtmlText $result.revision)</dd></div>
    <div><dt>Working tree fingerprint</dt><dd>$(ConvertTo-HtmlText $result.fingerprint)</dd></div>
    <div><dt>Generated</dt><dd>$(ConvertTo-HtmlText $result.generatedAtUtc)</dd></div>
    <div><dt>Development package</dt><dd>$(ConvertTo-HtmlText $developmentPackage)</dd></div>
    <div><dt>Shipping package</dt><dd>$(ConvertTo-HtmlText $shippingPackage)</dd></div>
    <div><dt>Delivery ZIP</dt><dd>$(ConvertTo-HtmlText $deliveryZip)</dd></div>
    <div><dt>Delivery SHA-256</dt><dd>$(ConvertTo-HtmlText $deliveryHash)</dd></div>
    <div><dt>Shipping acceptance</dt><dd>$(ConvertTo-HtmlText $acceptancePath)</dd></div>
  </section>

  <h2>Gate results</h2>
  <section class="gates">$($gateCards -join "`n")</section>

  <h2>Tool versions</h2>
  <table><tbody>$($toolRows -join "`n")</tbody></table>

  <h2>Visual evidence</h2>
  <p><strong>$(ConvertTo-HtmlText $result.visualReview.status)</strong> — $(ConvertTo-HtmlText $result.visualReview.details)</p>
  <section class="screenshots">$screenshots</section>

  <h2>Warning exceptions</h2>
  $exceptions
</main>
</body>
</html>
"@

Set-Content -LiteralPath $OutputPath -Value $html -Encoding UTF8

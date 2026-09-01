function Read-FPSOneShippingAcceptanceChecks {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object[]] $Checks,

        [scriptblock] $ReadResponse = { param($Prompt) Read-Host $Prompt },

        [scriptblock] $WriteMessage = { param($Message) Write-Host $Message }
    )

    $checkCount = @($Checks).Count
    $recordedChecks = for ($index = 0; $index -lt $checkCount; $index++) {
        $check = $Checks[$index]
        $ordinal = $index + 1
        $label = "check $ordinal of $checkCount [$($check.id)]"

        $null = & $WriteMessage ''
        $null = & $WriteMessage "Recording $label"
        $null = & $WriteMessage $check.prompt
        $confirmationOutput = @(& $ReadResponse "Type PASS for $label")
        $confirmation = $confirmationOutput[-1]
        if ($confirmation -cne 'PASS') {
            throw "Manual Shipping acceptance stopped at '$($check.id)'. No evidence was recorded."
        }
        $evidenceOutput = @(& $ReadResponse "Observed evidence for $label")
        $evidence = $evidenceOutput[-1]
        if ([string]::IsNullOrWhiteSpace($evidence)) {
            throw "Manual Shipping acceptance requires evidence for '$($check.id)'."
        }
        [pscustomobject][ordered]@{
            id = $check.id
            status = 'passed'
            evidence = $evidence.Trim()
        }

        if ($ordinal -lt $checkCount) {
            $null = & $WriteMessage "Recorded check $ordinal of $checkCount; next is [$($Checks[$index + 1].id)]."
        }
    }

    $null = & $WriteMessage "Recorded all $checkCount Shipping acceptance checks."
    return @($recordedChecks)
}

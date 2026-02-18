param(
    [switch]$Strict
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Add-Result {
    param(
        [System.Collections.Generic.List[object]]$Bag,
        [bool]$Passed,
        [string]$Name,
        [string]$Detail
    )

    $Bag.Add([pscustomobject]@{
            passed = $Passed
            check  = $Name
            detail = $Detail
        })
}

function Test-FileExists {
    param([string]$Path)
    return Test-Path -LiteralPath $Path -PathType Leaf
}

function Test-Contains {
    param(
        [string]$Path,
        [string]$Pattern
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }

    $text = Get-Content -LiteralPath $Path -Raw
    return $text.Contains($Pattern)
}

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $results = New-Object System.Collections.Generic.List[object]

    # =================================================================
    # 1. Required files existence check
    # =================================================================
    $requiredFiles = @(
        "aiscan.ps1",
        "aiscan.cmd",
        "README.md",
        "INDEX.md",
        "BASELINE_DOCS.md",
        "index_map.json",
        "USER_PROFILE.md",
        "policies/scan_rules.yaml",
        "scripts/scan_content.ps1",
        "scripts/audit_aiscan.ps1",
        "tests/test_scan.ps1",
        "tests/sample_dirty.txt",
        "tests/sample_clean.txt",
        "docs/README.md",
        "docs/human/overview.md",
        "docs/human/overview_ja_quick.md",
        "docs/human/overview_ja_detailed.md",
        "docs/human/usage_guide.md",
        "docs/ops/ops_checklist.md"
    )

    foreach ($file in $requiredFiles) {
        $ok = Test-FileExists -Path $file
        $detail = if ($ok) { "ok" } else { "missing" }
        Add-Result -Bag $results -Passed $ok -Name "file_exists::$file" -Detail $detail
    }

    # =================================================================
    # 2. Identity and policy checks
    # =================================================================
    Add-Result -Bag $results -Passed (Test-Contains -Path "README.md" -Pattern "aiscan - AI Input Scanner") `
        -Name "identity::README.md" -Detail "must include aiscan identity"

    Add-Result -Bag $results -Passed (Test-Contains -Path "policies/scan_rules.yaml" -Pattern "社内AI利用ガイドライン") `
        -Name "policy::scan_rules_guideline_ref" -Detail "must reference guideline"

    Add-Result -Bag $results -Passed (Test-Contains -Path "policies/scan_rules.yaml" -Pattern "personal_info") `
        -Name "policy::scan_rules_has_personal_info" -Detail "must define personal_info category"

    Add-Result -Bag $results -Passed (Test-Contains -Path "policies/scan_rules.yaml" -Pattern "confidential") `
        -Name "policy::scan_rules_has_confidential" -Detail "must define confidential category"

    Add-Result -Bag $results -Passed (Test-Contains -Path "policies/scan_rules.yaml" -Pattern "customer_partner") `
        -Name "policy::scan_rules_has_customer_partner" -Detail "must define customer_partner category"

    Add-Result -Bag $results -Passed (Test-Contains -Path "policies/scan_rules.yaml" -Pattern "copyright") `
        -Name "policy::scan_rules_has_copyright" -Detail "must define copyright category"

    Add-Result -Bag $results -Passed (Test-Contains -Path "policies/scan_rules.yaml" -Pattern "escalation") `
        -Name "policy::scan_rules_has_escalation" -Detail "must define escalation section"

    # =================================================================
    # 3. Profile line limit
    # =================================================================
    $profileLineCount = (Get-Content -LiteralPath "USER_PROFILE.md" | Measure-Object -Line).Lines
    $profileOk = $profileLineCount -le 150
    Add-Result -Bag $results -Passed $profileOk -Name "profile::line_limit" -Detail ("line_count=" + $profileLineCount + " limit=150")

    # =================================================================
    # 4. Legacy cleanup verification
    # =================================================================
    $legacyFiles = @(
        "orbit.ps1",
        "orbit.cmd",
        "scripts/audit_orbitmesh.ps1"
    )

    foreach ($legacy in $legacyFiles) {
        $exists = Test-Path -LiteralPath $legacy -PathType Leaf
        Add-Result -Bag $results -Passed (-not $exists) -Name "legacy_removed::$legacy" -Detail $(if ($exists) { "still exists" } else { "ok" })
    }

    # =================================================================
    # 5. Scan engine runtime tests
    # =================================================================
    $scanScript = Join-Path $root "scripts\scan_content.ps1"

    $dirtyFile = Join-Path $root "tests\sample_dirty.txt"
    $dirtyOutput = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $dirtyFile -Json -NoLog 2>$null | Out-String
    try {
        $dirtyJson = $dirtyOutput.Trim() | ConvertFrom-Json
        Add-Result -Bag $results -Passed ($dirtyJson.overall -eq "BLOCK") `
            -Name "runtime::dirty_file_blocked" -Detail "dirty sample must produce BLOCK"
        Add-Result -Bag $results -Passed ($dirtyJson.detections.Count -gt 0) `
            -Name "runtime::dirty_file_has_detections" -Detail "dirty sample must have detections"
    } catch {
        Add-Result -Bag $results -Passed $false -Name "runtime::dirty_file_parse" -Detail "could not parse scan JSON output"
    }

    $cleanFile = Join-Path $root "tests\sample_clean.txt"
    $cleanOutput = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $cleanFile -Json -NoLog 2>$null | Out-String
    try {
        $cleanJson = $cleanOutput.Trim() | ConvertFrom-Json
        Add-Result -Bag $results -Passed ($cleanJson.overall -eq "OK") `
            -Name "runtime::clean_file_ok" -Detail "clean sample must produce OK"
    } catch {
        Add-Result -Bag $results -Passed $false -Name "runtime::clean_file_parse" -Detail "could not parse scan JSON output"
    }

    # =================================================================
    # Summary
    # =================================================================
    $failed = @($results | Where-Object { -not $_.passed })
    $passedCount = @($results | Where-Object { $_.passed }).Count
    $failedCount = $failed.Count

    Write-Host "[AUDIT] Root: $root"
    Write-Host "[AUDIT] Passed: $passedCount"
    Write-Host "[AUDIT] Failed: $failedCount"

    foreach ($item in $results) {
        $mark = if ($item.passed) { "[OK]" } else { "[NG]" }
        Write-Host ("[AUDIT] {0} {1} :: {2}" -f $mark, $item.check, $item.detail)
    }

    if ($failedCount -gt 0 -and $Strict) {
        throw ("Audit failed with " + $failedCount + " check(s).")
    }
} finally {
    Pop-Location
}

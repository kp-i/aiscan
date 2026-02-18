# =============================================================================
# aiscan - Scan Engine Tests
# =============================================================================
# 使い方: powershell -ExecutionPolicy Bypass -File tests\test_scan.ps1
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$scanScript = Join-Path $root "scripts\scan_content.ps1"
$testDir = $PSScriptRoot

$passed = 0
$failed = 0
$total = 0

function Assert-ExitCode {
    param(
        [string]$TestName,
        [int]$Expected,
        [int]$Actual
    )
    $script:total++
    if ($Expected -eq $Actual) {
        Write-Host "[PASS] $TestName" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "[FAIL] $TestName (expected exit=$Expected, got exit=$Actual)" -ForegroundColor Red
        $script:failed++
    }
}

function Assert-OutputContains {
    param(
        [string]$TestName,
        [string]$Output,
        [string]$Pattern
    )
    $script:total++
    if ($Output -match $Pattern) {
        Write-Host "[PASS] $TestName" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "[FAIL] $TestName (pattern '$Pattern' not found in output)" -ForegroundColor Red
        $script:failed++
    }
}

function Assert-OutputNotContains {
    param(
        [string]$TestName,
        [string]$Output,
        [string]$Pattern
    )
    $script:total++
    if ($Output -notmatch $Pattern) {
        Write-Host "[PASS] $TestName" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "[FAIL] $TestName (pattern '$Pattern' unexpectedly found)" -ForegroundColor Red
        $script:failed++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " aiscan Scan Engine Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# -------------------------------------------------------
# Test 1: Dirty file should detect BLOCK items (exit 2)
# -------------------------------------------------------
$dirtyFile = Join-Path $testDir "sample_dirty.txt"
$output = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $dirtyFile -NoLog 2>&1 | Out-String
$exitCode = $LASTEXITCODE

Assert-ExitCode "dirty file returns exit code 2 (BLOCK)" 2 $exitCode
Assert-OutputContains "dirty file detects email" $output "メールアドレス"
Assert-OutputContains "dirty file detects phone" $output "電話"
Assert-OutputContains "dirty file detects confidential marking" $output "社外秘"
Assert-OutputContains "dirty file detects credential" $output "認証情報"
Assert-OutputContains "dirty file detects customer ID" $output "顧客"
Assert-OutputContains "dirty file detects financial data" $output "売上"
Assert-OutputContains "dirty file detects copyright" $output "著作権"
Assert-OutputContains "dirty file shows escalation message" $output "取締役以上"

# -------------------------------------------------------
# Test 2: Clean file should pass (exit 0)
# -------------------------------------------------------
$cleanFile = Join-Path $testDir "sample_clean.txt"
$output = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $cleanFile -NoLog 2>&1 | Out-String
$exitCode = $LASTEXITCODE

Assert-ExitCode "clean file returns exit code 0" 0 $exitCode
Assert-OutputContains "clean file shows OK" $output "検出なし"

# -------------------------------------------------------
# Test 3: JSON output mode
# -------------------------------------------------------
$output = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $dirtyFile -Json -NoLog 2>$null | Out-String
$exitCode = $LASTEXITCODE

Assert-ExitCode "JSON mode still returns exit 2 for dirty" 2 $exitCode
# Validate it's parseable JSON
try {
    $trimmed = $output.Trim()
    $jsonObj = $trimmed | ConvertFrom-Json
    $script:total++
    Write-Host "[PASS] JSON output is valid JSON" -ForegroundColor Green
    $script:passed++

    Assert-OutputContains "JSON contains BLOCK overall" ($jsonObj.overall) "BLOCK"
} catch {
    $script:total++
    Write-Host "[FAIL] JSON output is not valid JSON: $_" -ForegroundColor Red
    $script:failed++
}

# -------------------------------------------------------
# Test 4: Quiet mode with clean file (no output)
# -------------------------------------------------------
$output = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $cleanFile -Quiet -NoLog 2>&1 | Out-String
$exitCode = $LASTEXITCODE

Assert-ExitCode "quiet mode clean file exits 0" 0 $exitCode
Assert-OutputNotContains "quiet mode clean file produces no output" $output "\[SCAN\]"

# -------------------------------------------------------
# Test 5: Missing file error
# -------------------------------------------------------
$output = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath "nonexistent_file.txt" -NoLog 2>&1 | Out-String
$exitCode = $LASTEXITCODE

Assert-ExitCode "missing file returns exit 1" 1 $exitCode
Assert-OutputContains "missing file shows error" $output "見つかりません"

# -------------------------------------------------------
# Test 6: Audit log creation
# -------------------------------------------------------
$testLogDir = Join-Path $testDir "test_logs"
if (Test-Path -LiteralPath $testLogDir) {
    Remove-Item -LiteralPath $testLogDir -Recurse -Force
}

# Temporarily modify log path by running with default (it writes to logs/)
$logPath = Join-Path $root "logs\scan_history.jsonl"
$beforeExists = Test-Path -LiteralPath $logPath
if ($beforeExists) {
    $beforeCount = (Get-Content -LiteralPath $logPath | Measure-Object -Line).Lines
} else {
    $beforeCount = 0
}

$null = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $dirtyFile 2>&1
$afterCount = (Get-Content -LiteralPath $logPath | Measure-Object -Line).Lines

$script:total++
if ($afterCount -gt $beforeCount) {
    Write-Host "[PASS] scan writes audit log entry" -ForegroundColor Green
    $script:passed++
} else {
    Write-Host "[FAIL] scan did not write audit log entry" -ForegroundColor Red
    $script:failed++
}

# -------------------------------------------------------
# Test 7: Specific pattern tests (individual rules)
# -------------------------------------------------------
Write-Host ""
Write-Host "--- Individual Rule Tests ---" -ForegroundColor Yellow

$ruleTests = @(
    @{ name = "PI-001 email"; input = "連絡先: user@example.com"; expect = "BLOCK" }
    @{ name = "PI-002 phone"; input = "電話: 090-1234-5678"; expect = "BLOCK" }
    @{ name = "PI-005 employee ID"; input = "社員番号: EMP-12345"; expect = "BLOCK" }
    @{ name = "PI-006 name+title"; input = "山田太郎 部長に連絡"; expect = "BLOCK" }
    @{ name = "CF-001 confidential"; input = "この資料は社外秘です"; expect = "BLOCK" }
    @{ name = "CF-002 credential"; input = "api_key = sk-abc123"; expect = "BLOCK" }
    @{ name = "CF-005 financial JP"; input = "売上: 1,000万円"; expect = "BLOCK" }
    @{ name = "CP-001 customer ID"; input = "顧客ID: CUST-001"; expect = "BLOCK" }
    @{ name = "CR-001 copyright"; input = "Copyright (C) 2026"; expect = "BLOCK" }
    @{ name = "clean input"; input = "Pythonの使い方を教えて"; expect = "OK" }
)

foreach ($test in $ruleTests) {
    $tempFile = Join-Path $testDir ("_tmp_rule_test_" + [guid]::NewGuid().ToString("N") + ".txt")
    try {
        Set-Content -LiteralPath $tempFile -Value $test.input -Encoding UTF8
        $output = & powershell -ExecutionPolicy Bypass -File $scanScript -FilePath $tempFile -Json -NoLog 2>&1 | Out-String
        $json = $output | ConvertFrom-Json
        $script:total++
        if ($json.overall -eq $test.expect) {
            Write-Host "[PASS] $($test.name) -> $($test.expect)" -ForegroundColor Green
            $script:passed++
        } else {
            Write-Host "[FAIL] $($test.name) (expected=$($test.expect), got=$($json.overall))" -ForegroundColor Red
            $script:failed++
        }
    } finally {
        if (Test-Path -LiteralPath $tempFile) {
            Remove-Item -LiteralPath $tempFile -Force
        }
    }
}

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Results: $passed/$total passed, $failed failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($failed -gt 0) {
    exit 1
}
exit 0




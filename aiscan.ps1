param(
    [Parameter(Position = 0)]
    [ValidateSet("scan", "audit", "help")]
    [string]$Action = "help",

    # scan options
    [Parameter(Position = 1)]
    [string]$ScanTarget = "",
    [switch]$Clipboard,
    [switch]$Stdin,
    [switch]$Json,
    [switch]$Quiet,
    [switch]$NoLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$scanScript = Join-Path $root "scripts\scan_content.ps1"
$auditScript = Join-Path $root "scripts\audit_aiscan.ps1"

$requiredScripts = @($scanScript, $auditScript)
foreach ($s in $requiredScripts) {
    if (-not (Test-Path -LiteralPath $s)) {
        throw "Missing file: $s"
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "aiscan - AI Input Scanner" -ForegroundColor Cyan
    Write-Host "AI利用前に入力テキストをローカルで検査します。" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "使い方:" -ForegroundColor Yellow
    Write-Host "  aiscan scan <file>         ファイルをスキャン"
    Write-Host "  aiscan scan -Clipboard     クリップボードをスキャン"
    Write-Host "  aiscan scan -Stdin         標準入力をスキャン"
    Write-Host "  aiscan audit               ポリシー・ファイル整合性監査"
    Write-Host ""
    Write-Host "オプション:" -ForegroundColor Yellow
    Write-Host "  -Json       JSON形式で出力"
    Write-Host "  -Quiet      検出がない場合は出力しない"
    Write-Host "  -NoLog      監査ログを記録しない"
    Write-Host ""
    Write-Host "終了コード:" -ForegroundColor Yellow
    Write-Host "  0  OK / REVIEWのみ"
    Write-Host "  1  WARNあり"
    Write-Host "  2  BLOCKあり（取締役以上への上申が必要）"
    Write-Host ""
}

switch ($Action) {
    "scan" {
        $scanArgs = @{}
        if ($ScanTarget)  { $scanArgs["FilePath"] = $ScanTarget }
        if ($Clipboard)   { $scanArgs["Clipboard"] = $true }
        if ($Stdin)       { $scanArgs["Stdin"] = $true }
        if ($Json)        { $scanArgs["Json"] = $true }
        if ($Quiet)       { $scanArgs["Quiet"] = $true }
        if ($NoLog)       { $scanArgs["NoLog"] = $true }
        & $scanScript @scanArgs
    }
    "audit" {
        & $auditScript -Strict
    }
    default {
        Show-Help
    }
}

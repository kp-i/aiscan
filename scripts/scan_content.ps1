# =============================================================================
# aiscan - Content Scanner Engine
# =============================================================================
# 社内AI利用ガイドライン準拠のローカル情報フィルタ。
# AIに送信する前にローカルで検査し、禁止情報の検出とログ記録を行う。
# =============================================================================

param(
    [Parameter(Mandatory = $false, Position = 0)]
    [string]$FilePath = "",

    [switch]$Clipboard,
    [switch]$Stdin,
    [switch]$Json,
    [switch]$Quiet,
    [switch]$NoLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:Root = Split-Path -Parent $PSScriptRoot
$script:PolicyPath = Join-Path $script:Root "policies\scan_rules.yaml"
$script:LogDir = Join-Path $script:Root "logs"
$script:LogPath = Join-Path $script:LogDir "scan_history.jsonl"

# =============================================================================
# YAML parser (lightweight - no external dependency)
# =============================================================================
# scan_rules.yaml のルールセクションだけを解析する簡易パーサ。
# 本格的な YAML パーサの代わりに、正規表現ルールを直接定義する。
# ポリシーファイル (scan_rules.yaml) は人間が読む正式ドキュメントとして機能し、
# 下記のルール定義はそれと同期を維持する。
# =============================================================================

function Get-ScanRules {
    $rules = @(
        # =====================================================================
        # カテゴリ1: 個人情報（氏名、住所、電話番号など）
        # =====================================================================
        @{ id = "PI-001"; category = "personal_info"; name = "email_address";
           description = "メールアドレス"; risk = "BLOCK";
           pattern = '[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}' }

        @{ id = "PI-002"; category = "personal_info"; name = "phone_jp";
           description = "日本の電話番号（固定・携帯）"; risk = "BLOCK";
           pattern = '0[0-9]{1,4}[\s-]?[0-9]{1,4}[\s-]?[0-9]{3,4}' }

        @{ id = "PI-003"; category = "personal_info"; name = "address_jp";
           description = "日本の住所"; risk = "BLOCK";
           pattern = '(?:北海道|東京都|(?:京都|大阪)府|.{2,3}県)\s*\S+[市区町村郡]\S*[0-9]' }

        @{ id = "PI-004"; category = "personal_info"; name = "my_number";
           description = "マイナンバー（12桁）"; risk = "BLOCK";
           pattern = '(?<![0-9])[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}(?![0-9])' }

        @{ id = "PI-005"; category = "personal_info"; name = "employee_id";
           description = "社員番号・社員ID"; risk = "BLOCK";
           pattern = '(?:社員番号|社員ID|社員No|EMP|emp)[\s:：.\-]*[A-Za-z0-9\-]+' }

        @{ id = "PI-006"; category = "personal_info"; name = "japanese_name_with_title";
           description = "日本人氏名（敬称・役職付き）"; risk = "BLOCK";
           pattern = '[一-龥]{1,4}\s?[一-龥]{1,4}\s*(?:氏|様|さん|殿|先生|部長|課長|係長|主任|社長|取締役|代表|専務|常務|理事|本部長|室長|マネージャー|リーダー|担当)' }

        @{ id = "PI-007"; category = "personal_info"; name = "japanese_name_bare";
           description = "日本人氏名の可能性（姓名スペース区切り）"; risk = "WARN";
           pattern = '[一-龥]{1,4}\s[一-龥]{1,4}' }

        @{ id = "PI-008"; category = "personal_info"; name = "date_of_birth";
           description = "生年月日"; risk = "BLOCK";
           pattern = '(?:生年月日|DOB|誕生日)[\s:：]*(?:(?:19|20)[0-9]{2}[\s/.\-年][0-9]{1,2}[\s/.\-月][0-9]{1,2}日?|(?:昭和|平成|令和)[0-9]{1,2}年[0-9]{1,2}月[0-9]{1,2}日)' }

        @{ id = "PI-009"; category = "personal_info"; name = "passport_number";
           description = "パスポート番号"; risk = "BLOCK";
           pattern = '(?:パスポート|旅券|passport)[\s:：]*[A-Z]{2}[0-9]{7}' }

        @{ id = "PI-010"; category = "personal_info"; name = "credit_card";
           description = "クレジットカード番号（16桁）"; risk = "BLOCK";
           pattern = '(?<![0-9])[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}(?![0-9])' }

        # =====================================================================
        # カテゴリ2: 機密情報や企業秘密
        # =====================================================================
        @{ id = "CF-001"; category = "confidential"; name = "confidential_marking";
           description = "機密区分マーキング"; risk = "BLOCK";
           pattern = '(?:社外秘|極秘|部外秘|confidential|internal[\s-]?only|restricted|secret|取扱注意|関係者限り)' }

        @{ id = "CF-002"; category = "confidential"; name = "credential_hardcoded";
           description = "ハードコードされた認証情報"; risk = "BLOCK";
           pattern = '(?:password|passwd|secret|api[_\-]?key|api[_\-]?token|access[_\-]?key|private[_\-]?key|auth[_\-]?token)\s*[=:]\s*[''"\S]+' }

        @{ id = "CF-003"; category = "confidential"; name = "connection_string";
           description = "データベース接続文字列"; risk = "BLOCK";
           pattern = '(?:jdbc:|Server=|Data Source=|mongodb(?:\+srv)?://|postgres(?:ql)?://|mysql://)\S+' }

        @{ id = "CF-004"; category = "confidential"; name = "env_secret";
           description = "環境変数の機密値"; risk = "BLOCK";
           pattern = '(?:DB_PASSWORD|DB_HOST|AWS_SECRET|AZURE_KEY|GCP_KEY|SLACK_TOKEN|GITHUB_TOKEN|SECRET_KEY|ENCRYPTION_KEY)\s*=\s*\S+' }

        @{ id = "CF-005"; category = "confidential"; name = "financial_data_jp";
           description = "売上・利益等の具体数値（日本語）"; risk = "BLOCK";
           pattern = '(?:売上|利益|営業利益|経常利益|純利益|原価|予算|年商|月商|粗利)[\s:：]*[0-9,]+(?:\.[0-9]+)?\s*(?:万|億|千万|百万)?円' }

        @{ id = "CF-006"; category = "confidential"; name = "financial_data_en";
           description = "財務数値（英語）"; risk = "WARN";
           pattern = '(?:revenue|profit|budget|margin|EBITDA|ARR|MRR)[\s:：]*\$?\s*[0-9,]+(?:\.[0-9]+)?\s*(?:K|M|B|million|billion)?' }

        @{ id = "CF-007"; category = "confidential"; name = "internal_project_code";
           description = "社内プロジェクトコード"; risk = "REVIEW";
           pattern = '(?:プロジェクト|PJ|案件)[\s:：]*(?:コード|code|名|ID)[\s:：]*[A-Z0-9\-_]+' }

        @{ id = "CF-008"; category = "confidential"; name = "ip_address_internal";
           description = "内部IPアドレス（プライベートレンジ）"; risk = "WARN";
           pattern = '(?:10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3})' }

        # =====================================================================
        # カテゴリ3: 取引先や顧客の情報
        # =====================================================================
        @{ id = "CP-001"; category = "customer_partner"; name = "customer_id";
           description = "顧客ID・顧客番号"; risk = "BLOCK";
           pattern = '(?:顧客ID|顧客番号|顧客No|顧客コード|CUST|customer[\s_\-]?(?:id|no|code))[\s:：.\-]*[A-Za-z0-9\-]+' }

        @{ id = "CP-002"; category = "customer_partner"; name = "partner_id";
           description = "取引先ID・取引先コード"; risk = "BLOCK";
           pattern = '(?:取引先ID|取引先番号|取引先No|取引先コード|仕入先|vendor[\s_\-]?(?:id|code)|supplier[\s_\-]?(?:id|code))[\s:：.\-]*[A-Za-z0-9\-]+' }

        @{ id = "CP-003"; category = "customer_partner"; name = "contract_id";
           description = "契約番号"; risk = "BLOCK";
           pattern = '(?:契約番号|契約No|契約ID|contract[\s_\-]?(?:id|no|number))[\s:：.\-]*[A-Za-z0-9\-]+' }

        @{ id = "CP-004"; category = "customer_partner"; name = "customer_name_explicit";
           description = "顧客名・取引先名の記述"; risk = "BLOCK";
           pattern = '(?:顧客名|取引先名|クライアント名|得意先|client[\s_]?name)[\s:：]\s*\S+' }

        @{ id = "CP-005"; category = "customer_partner"; name = "nda_reference";
           description = "NDA・秘密保持契約＋具体情報"; risk = "REVIEW";
           pattern = '(?:NDA|秘密保持|守秘義務|機密保持契約)\S*[\s:：]\S+' }

        @{ id = "CP-006"; category = "customer_partner"; name = "invoice_info";
           description = "請求書番号・発注番号"; risk = "BLOCK";
           pattern = '(?:請求書番号|請求No|発注番号|発注No|PO[\s_\-]?(?:number|no|#))[\s:：.\-]*[A-Za-z0-9\-]+' }

        # =====================================================================
        # カテゴリ4: 著作権で保護された内容
        # =====================================================================
        @{ id = "CR-001"; category = "copyright"; name = "copyright_notice";
           description = "著作権表示"; risk = "BLOCK";
           pattern = '(?:Copyright|\(C\)|©|All [Rr]ights [Rr]eserved|著作権|無断転載禁止|転載禁止|複製禁止)' }

        @{ id = "CR-002"; category = "copyright"; name = "license_restricted";
           description = "制限的ライセンス表示"; risk = "WARN";
           pattern = '(?:All [Rr]ights [Rr]eserved|proprietary|licensed under|使用許諾|利用規約に基づ)' }

        @{ id = "CR-003"; category = "copyright"; name = "quotation_source";
           description = "書籍・記事からの引用表記"; risk = "REVIEW";
           pattern = '(?:より引用|から引用|出典[:：]|引用元[:：]|※本文は.+より抜粋)' }
    )

    return ,$rules
}

# =============================================================================
# Category label map
# =============================================================================
function Get-CategoryLabel {
    param([string]$Category)
    switch ($Category) {
        "personal_info"    { return "個人情報" }
        "confidential"     { return "機密情報・企業秘密" }
        "customer_partner" { return "取引先・顧客情報" }
        "copyright"        { return "著作権保護コンテンツ" }
        default            { return $Category }
    }
}

# =============================================================================
# Core scan function
# =============================================================================
function Invoke-Scan {
    param(
        [string[]]$Lines,
        [string]$SourceName
    )

    $rules = Get-ScanRules
    $detections = New-Object System.Collections.Generic.List[object]

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i]
        $lineNum = $i + 1

        foreach ($rule in $rules) {
            $matches = [regex]::Matches($line, $rule.pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            foreach ($m in $matches) {
                $detections.Add([pscustomobject]@{
                    line        = $lineNum
                    rule_id     = $rule.id
                    category    = $rule.category
                    name        = $rule.name
                    description = $rule.description
                    risk        = $rule.risk
                    matched     = $m.Value
                    context     = $line.Trim()
                })
            }
        }
    }

    return ,$detections
}

# =============================================================================
# Risk summary
# =============================================================================
function Get-RiskSummary {
    param([System.Collections.Generic.List[object]]$Detections)

    $summary = @{ BLOCK = 0; WARN = 0; REVIEW = 0 }
    foreach ($d in $Detections) {
        if ($summary.ContainsKey($d.risk)) {
            $summary[$d.risk]++
        }
    }
    return $summary
}

function Get-OverallRisk {
    param([hashtable]$Summary)

    if ($Summary.BLOCK -gt 0) { return "BLOCK" }
    if ($Summary.WARN -gt 0)  { return "WARN" }
    if ($Summary.REVIEW -gt 0) { return "REVIEW" }
    return "OK"
}

# =============================================================================
# Console output
# =============================================================================
function Write-ScanResult {
    param(
        [string]$SourceName,
        [int]$LineCount,
        [System.Collections.Generic.List[object]]$Detections
    )

    $summary = Get-RiskSummary -Detections $Detections
    $overall = Get-OverallRisk -Summary $summary

    Write-Host ""
    Write-Host "[SCAN] $SourceName ($LineCount lines)" -ForegroundColor Cyan

    if ($Detections.Count -eq 0) {
        Write-Host "[OK]   検出なし。ポリシー上問題は見つかりませんでした。" -ForegroundColor Green
        Write-Host ""
        return
    }

    # Group by category for readability
    $grouped = $Detections | Group-Object -Property category

    foreach ($group in $grouped) {
        $catLabel = Get-CategoryLabel -Category $group.Name
        Write-Host ""
        Write-Host "  --- $catLabel ---" -ForegroundColor Yellow

        foreach ($d in $group.Group) {
            $icon = switch ($d.risk) {
                "BLOCK"  { "!!"; break }
                "WARN"   { "! "; break }
                "REVIEW" { "? "; break }
            }
            $color = switch ($d.risk) {
                "BLOCK"  { "Red"; break }
                "WARN"   { "Yellow"; break }
                "REVIEW" { "DarkYellow"; break }
            }

            $matchDisplay = $d.matched
            if ($matchDisplay.Length -gt 40) {
                $matchDisplay = $matchDisplay.Substring(0, 37) + "..."
            }

            Write-Host ("  [{0}] L{1}: {2}" -f $icon, $d.line, $matchDisplay) -ForegroundColor $color
            Write-Host ("        {0} [{1}] {2}" -f $d.risk, $d.rule_id, $d.description) -ForegroundColor DarkGray
        }
    }

    Write-Host ""
    Write-Host "  --------------------------------------------------" -ForegroundColor DarkGray

    $blockText = "BLOCK: $($summary.BLOCK)"
    $warnText  = "WARN: $($summary.WARN)"
    $reviewText = "REVIEW: $($summary.REVIEW)"

    Write-Host -NoNewline "  検出合計: "
    if ($summary.BLOCK -gt 0) { Write-Host -NoNewline $blockText -ForegroundColor Red; Write-Host -NoNewline "  " }
    if ($summary.WARN -gt 0)  { Write-Host -NoNewline $warnText -ForegroundColor Yellow; Write-Host -NoNewline "  " }
    if ($summary.REVIEW -gt 0) { Write-Host -NoNewline $reviewText -ForegroundColor DarkYellow }
    Write-Host ""

    if ($overall -eq "BLOCK") {
        Write-Host ""
        Write-Host "  [要上申] この内容をAIに投入するには、取締役以上への上申が必要です" -ForegroundColor Red
        Write-Host "          （社内AI利用ガイドライン 3.プライバシーとデータセキュリティ準拠）" -ForegroundColor DarkGray
    }

    Write-Host ""
}

# =============================================================================
# JSON output
# =============================================================================
function ConvertTo-ScanJson {
    param(
        [string]$SourceName,
        [int]$LineCount,
        [System.Collections.Generic.List[object]]$Detections
    )

    $summary = Get-RiskSummary -Detections $Detections
    $overall = Get-OverallRisk -Summary $summary

    $detectionList = @()
    foreach ($d in $Detections) {
        $detectionList += @{
            line        = $d.line
            rule_id     = $d.rule_id
            category    = $d.category
            name        = $d.name
            description = $d.description
            risk        = $d.risk
            matched     = $d.matched
        }
    }

    $result = @{
        timestamp   = [DateTime]::UtcNow.ToString("o")
        source      = $SourceName
        line_count  = $LineCount
        overall     = $overall
        summary     = $summary
        detections  = $detectionList
        policy_ref  = "社内AI利用ガイドライン 3.プライバシーとデータセキュリティ"
    }

    return ($result | ConvertTo-Json -Depth 5 -Compress)
}

# =============================================================================
# Audit log
# =============================================================================
function Write-ScanLog {
    param(
        [string]$SourceName,
        [int]$LineCount,
        [System.Collections.Generic.List[object]]$Detections
    )

    if ($NoLog) { return }

    if (-not (Test-Path -LiteralPath $script:LogDir -PathType Container)) {
        New-Item -Path $script:LogDir -ItemType Directory -Force | Out-Null
    }

    $summary = Get-RiskSummary -Detections $Detections
    $overall = Get-OverallRisk -Summary $summary

    $logEntry = @{
        timestamp      = [DateTime]::UtcNow.ToString("o")
        source         = $SourceName
        line_count     = $LineCount
        overall_risk   = $overall
        risk_summary   = $summary
        detection_count = $Detections.Count
        rule_ids       = @($Detections | ForEach-Object { $_.rule_id } | Sort-Object -Unique)
        rules_version  = "1.0.0"
    }

    $json = $logEntry | ConvertTo-Json -Depth 3 -Compress
    Add-Content -LiteralPath $script:LogPath -Value $json -Encoding UTF8
}

# =============================================================================
# Input acquisition
# =============================================================================
function Get-InputContent {
    if ($Clipboard) {
        try {
            Add-Type -AssemblyName System.Windows.Forms
            $text = [System.Windows.Forms.Clipboard]::GetText()
            if ([string]::IsNullOrWhiteSpace($text)) {
                Write-Host "[ERROR] クリップボードにテキストがありません。" -ForegroundColor Red
                exit 1
            }
            return @{
                source = "clipboard"
                lines  = $text -split "`n"
            }
        } catch {
            Write-Host "[ERROR] クリップボードの読み取りに失敗しました: $_" -ForegroundColor Red
            exit 1
        }
    }

    if ($Stdin -or (-not [string]::IsNullOrWhiteSpace($FilePath) -and $FilePath -eq "-")) {
        $text = @($input)
        if ($text.Count -eq 0) {
            Write-Host "[ERROR] 標準入力にデータがありません。" -ForegroundColor Red
            exit 1
        }
        return @{
            source = "stdin"
            lines  = $text
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($FilePath)) {
        if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
            Write-Host "[ERROR] ファイルが見つかりません: $FilePath" -ForegroundColor Red
            exit 1
        }
        $lines = Get-Content -LiteralPath $FilePath -Encoding UTF8
        return @{
            source = $FilePath
            lines  = $lines
        }
    }

    Write-Host "[ERROR] スキャン対象を指定してください。" -ForegroundColor Red
    Write-Host ""
    Write-Host "使い方:"
    Write-Host "  aiscan scan <file>       ファイルをスキャン"
    Write-Host "  aiscan scan -Clipboard  クリップボードをスキャン"
    Write-Host "  cat file | aiscan scan -Stdin  標準入力をスキャン"
    Write-Host ""
    Write-Host "オプション:"
    Write-Host "  -Json      JSON形式で出力"
    Write-Host "  -Quiet     検出がない場合は出力しない"
    Write-Host "  -NoLog     監査ログを記録しない"
    exit 1
}

# =============================================================================
# Main
# =============================================================================
$content = Get-InputContent
$lines = @($content.lines)
$sourceName = $content.source
$lineCount = $lines.Length

$detections = Invoke-Scan -Lines $lines -SourceName $sourceName
if ($null -eq $detections) {
    $detections = New-Object System.Collections.Generic.List[object]
}
$detectionCount = $detections.Count

# Log regardless of output mode
Write-ScanLog -SourceName $sourceName -LineCount $lineCount -Detections $detections

if ($Quiet -and $detectionCount -eq 0) {
    exit 0
}

if ($Json) {
    $jsonOutput = ConvertTo-ScanJson -SourceName $sourceName -LineCount $lineCount -Detections $detections
    Write-Output $jsonOutput
} else {
    Write-ScanResult -SourceName $sourceName -LineCount $lineCount -Detections $detections
}

# Exit code: 2=BLOCK found, 1=WARN found, 0=clean or REVIEW only
$summary = Get-RiskSummary -Detections $detections
if ($summary.BLOCK -gt 0) { exit 2 }
if ($summary.WARN -gt 0)  { exit 1 }
exit 0








# aiscan 詳細概要

## プロジェクトの目的

社内でAIを利用する際、投入する情報が社内ガイドラインに違反していないかを
ローカルで検査するツール。AIには一切データを送らず、手元で完結する。

## 準拠ガイドライン

社内AI利用ガイドライン 3.プライバシーとデータセキュリティ:
- 個人情報（氏名、住所、電話番号など）の入力は禁止
- 機密情報や企業秘密の入力は禁止
- 取引先や顧客の情報の入力は禁止
- 著作権で保護された内容の入力は禁止
- 上記情報を含めた利用を希望する場合は取締役以上へ上申

## 検出カテゴリと主なルール

### 個人情報（PI-001〜PI-010）
- メールアドレス、電話番号、住所、マイナンバー
- 社員番号、氏名（敬称・役職付き）、生年月日
- パスポート番号、クレジットカード番号

### 機密情報・企業秘密（CF-001〜CF-008）
- 機密区分マーキング（社外秘、極秘、confidential等）
- ハードコードされた認証情報（API key、password等）
- DB接続文字列、環境変数の機密値
- 売上・利益等の具体的数値
- 内部IPアドレス、プロジェクトコード

### 取引先・顧客情報（CP-001〜CP-006）
- 顧客ID、取引先コード、契約番号
- 顧客名・取引先名の明示的記述
- 請求書番号、発注番号
- NDA関連の具体情報

### 著作権（CR-001〜CR-003）
- 著作権表示（Copyright, (C), All Rights Reserved等）
- 制限的ライセンス表示
- 引用元表記

## リスクレベル

| レベル | 意味 | 終了コード |
|--------|------|-----------|
| BLOCK | 禁止。上申が必要 | 2 |
| WARN | 文脈次第でNG。確認推奨 | 1 |
| REVIEW | 自動判定不能。人間が判断 | 0 |
| OK | 検出なし | 0 |

## 使い方

```powershell
# ファイルスキャン
.\aiscan scan meeting_notes.md

# クリップボードスキャン
.\aiscan scan -Clipboard

# 標準入力スキャン
cat report.txt | .\aiscan scan -Stdin

# JSON出力（他ツール連携用）
.\aiscan scan data.csv -Json

# 検出なしの場合は出力しない
.\aiscan scan data.csv -Quiet

# 監査ログを記録しない
.\aiscan scan data.csv -NoLog

# ファイル・ポリシー整合性監査
.\aiscan audit
```

## 監査ログ

- 保存先: `logs/scan_history.jsonl`
- 形式: 1スキャン1行のJSONL
- 記録内容: タイムスタンプ、対象、検出数、リスク分布、適用ルールID

## 設計原則

1. **ローカルファースト**: データは外部に出ない
2. **ポリシー・アズ・コード**: ルールは `policies/scan_rules.yaml` に宣言的に定義
3. **監査トレイル**: 全スキャンをログに記録
4. **パターンベース**: 正規表現による構造的検出。LLM不要
5. **即時フィードバック**: 行番号と検出内容を明示

## ファイル構成

```
project-root/
├── aiscan.ps1                   # CLIエントリポイント
├── aiscan.cmd                   # Windowsバッチラッパー
├── policies/
│   └── scan_rules.yaml          # 検出ルール定義（SSoT）
├── scripts/
│   ├── scan_content.ps1         # 検出エンジン
│   └── audit_aiscan.ps1         # 整合性監査
├── tests/
│   ├── test_scan.ps1            # 自動テスト
│   ├── sample_dirty.txt         # 違反サンプル
│   └── sample_clean.txt         # クリーンサンプル
├── logs/
│   └── scan_history.jsonl       # 監査ログ
├── docs/                        # ドキュメント
├── README.md
├── INDEX.md
├── BASELINE_DOCS.md
├── index_map.json
└── USER_PROFILE.md
```

## 参照

- 検出ルール: `policies/scan_rules.yaml`
- ベースライン: `BASELINE_DOCS.md`
- 運用チェックリスト: `docs/ops/ops_checklist.md`
- English: `docs/human/overview.md`

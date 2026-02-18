# aiscan - AI Input Scanner

aiscan は、AIに送る前のテキストをローカルで検査するスキャナーです。
個人情報・機密情報・顧客/取引先情報・著作権コンテンツを検出し、
社内AI利用ガイドライン準拠の判断を支援します。

## Quick Start

```powershell
# ファイルをスキャン
aiscan scan meeting_notes.md

# クリップボードをスキャン
aiscan scan -Clipboard

# JSON出力
aiscan scan report.txt -Json

# 整合性監査
aiscan audit
```

## Documentation

- **使い方ガイド（日本語）**: `docs/human/usage_guide.md`
- Human docs entry: `docs/README.md`
- English overview: `docs/human/overview.md`
- Japanese (quick): `docs/human/overview_ja_quick.md`
- Japanese (detailed): `docs/human/overview_ja_detailed.md`
- Scan policy: `policies/scan_rules.yaml`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | OK / REVIEW only |
| 1 | WARN detected |
| 2 | BLOCK detected (requires escalation) |

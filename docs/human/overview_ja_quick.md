# aiscan 概要（簡易版）

## 3分でわかる aiscan

aiscan は、AIにテキストを投入する前にローカルで検査するツールです。
社内AI利用ガイドラインに準拠し、禁止情報を検出します。

## 何を検出するか

- 個人情報（氏名、メール、電話番号、住所、社員番号など）
- 機密情報（社外秘マーキング、認証情報、財務データなど）
- 取引先・顧客情報（顧客ID、契約番号、取引先コードなど）
- 著作権コンテンツ（著作権表示、引用表記など）

## 使い方

```powershell
.\aiscan scan 会議メモ.md        # ファイルをスキャン
.\aiscan scan -Clipboard         # クリップボードをスキャン
.\aiscan audit                   # 整合性監査
```

## 特徴

- ローカル完結（データは外部に出ない）
- 検出のたびに監査ログを記録
- BLOCK検出時は上申メッセージを表示

## 詳細

- 詳細版: `docs/human/overview_ja_detailed.md`
- English: `docs/human/overview.md`

## 更新ルール

- 日本語の正本は詳細版（`docs/human/overview_ja_detailed.md`）
- 簡易版（このファイル）は同一変更で必ず同時更新

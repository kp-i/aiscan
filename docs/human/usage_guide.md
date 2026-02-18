# aiscan 使い方ガイド

## 前提

- aiscan はユーザー PATH に登録済み。新しいターミナルを開けばどこからでも実行可能。
- PowerShell で実行する。
- AI に一切データは送られない。すべてローカルで完結する。

---

## 基本の流れ

```
1. AIに投入したい資料・テキストを用意する
2. aiscan scan で検査する
3. 結果を確認する
   - OK      → そのままAIに投入してよい
   - WARN    → 該当箇所を確認し、自分で判断
   - BLOCK   → そのまま投入してはいけない。マスク/除去/上申のいずれか
4. 必要に応じて内容を修正し、再スキャンする
5. 問題なければAIに投入する
```

---

## シーン別の使い方

### シーン1: 会議メモをClaudeに要約させたい

```powershell
aiscan scan C:\Users\sp5225\Documents\meeting_notes.md
```

出力例:
```
[SCAN] meeting_notes.md (50 lines)

  --- 個人情報 ---
  [!!] L5: yamada@corp.co.jp
        BLOCK [PI-001] メールアドレス
  [!!] L8: 佐藤課長
        BLOCK [PI-006] 日本人氏名（敬称・役職付き）

  --- 機密情報・企業秘密 ---
  [!!] L22: 売上: 3,500万円
        BLOCK [CF-005] 売上・利益等の具体数値（日本語）

  検出合計: BLOCK: 3

  [要上申] この内容をAIに投入するには、取締役以上への上申が必要です
```

→ メールアドレス・人名・売上をマスクしてから投入する。

### シーン2: コードをClaudeにレビューしてもらいたい

```powershell
aiscan scan C:\Projects\myapp\src\auth\login.py
```

出力例:
```
[SCAN] login.py (120 lines)

  --- 機密情報・企業秘密 ---
  [!!] L15: password = 'admin123'
        BLOCK [CF-002] ハードコードされた認証情報
  [! ] L30: 192.168.1.50
        WARN [CF-008] 内部IPアドレス（プライベートレンジ）

  検出合計: BLOCK: 1  WARN: 1
```

→ パスワードを環境変数に置き換えてからAIに渡す。IPアドレスは判断。

### シーン3: クリップボードにコピーした内容をそのまま検査

Webページやメールからコピーした内容を、チャットUIに貼る前にチェック:

```powershell
aiscan scan -Clipboard
```

→ クリップボードの中身がスキャンされる。問題なければそのまま貼り付ける。

### シーン4: 問題ないことをサッと確認だけしたい

検出がない場合は何も表示しない（問題があるときだけ表示）:

```powershell
aiscan scan draft.md -Quiet
```

→ 何も表示されなければ OK。

### シーン5: 複数ファイルをまとめてチェック

PowerShell でワイルドカードを使う:

```powershell
Get-ChildItem .\docs\*.md | ForEach-Object { aiscan scan $_.FullName }
```

→ ファイルごとに結果が表示される。

### シーン6: CIや自動化スクリプトに組み込む

JSON 出力と終了コードを使う:

```powershell
aiscan scan report.md -Json -Quiet
$result = $LASTEXITCODE
if ($result -eq 2) {
    Write-Host "BLOCK detected. Do not send to AI."
} elseif ($result -eq 1) {
    Write-Host "WARN detected. Review before sending."
} else {
    Write-Host "OK. Safe to send."
}
```

---

## 検出されたらどうするか

| リスク | 対応 |
|--------|------|
| **BLOCK** | 投入禁止。該当箇所をマスク（`[氏名]`、`[メール]`等に置換）するか、削除してから再スキャン。それでも投入が必要なら取締役以上へ上申。 |
| **WARN** | 文脈次第。該当行を読んで、本当に問題があるか自分で判断。 |
| **REVIEW** | 自動判定できない内容。人間が見て判断。 |

---

## 監査ログの活用

スキャンするたびに `logs/scan_history.jsonl` に記録が残る。

```json
{
  "timestamp": "2026-02-18T10:23:45Z",
  "source": "meeting_notes.md",
  "overall_risk": "BLOCK",
  "detection_count": 3,
  "risk_summary": { "BLOCK": 3, "WARN": 0, "REVIEW": 0 },
  "rule_ids": ["PI-001", "PI-006", "CF-005"]
}
```

「あのとき送った資料、大丈夫だった？」と聞かれたときのエビデンスになる。

`-NoLog` オプションをつけるとログを残さずにスキャンできる（練習やテスト時向け）。

---

## ルールの更新

新しいパターンを追加したい場合:

1. `policies/scan_rules.yaml` にルールを追記（ドキュメント）
2. `scripts/scan_content.ps1` の `Get-ScanRules` 関数に同じルールを追加（実行）
3. `tests/sample_dirty.txt` にテストケースを追加
4. テスト実行: `powershell -ExecutionPolicy Bypass -File tests\test_scan.ps1`
5. 監査実行: `aiscan audit`

---

## トラブルシューティング

### `aiscan` が見つからない

新しいターミナルを開き直す。PATH の反映には再起動が必要。

### 日本語が文字化けする

PowerShell を直接開いて実行する。cmd.exe 経由だと文字化けすることがある。

### 誤検知が多い

WARN レベルの検出は意図的に広めに取っている。
本当に問題ない場合は無視してよい。頻繁に同じ誤検知が出る場合はルールの調整を検討。

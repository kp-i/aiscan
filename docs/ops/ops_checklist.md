# aiscan Ops Checklist

## Startup Checks

- Confirm core files exist: `aiscan.ps1`, `policies/scan_rules.yaml`, `scripts/scan_content.ps1`.
- Confirm human-doc entry exists: `docs/README.md`.
- Confirm scan rules reference guideline: `社内AI利用ガイドライン 3.プライバシーとデータセキュリティ`.
- Confirm all 4 detection categories defined: personal_info, confidential, customer_partner, copyright.
- Run automated audit: `.\aiscan audit`.
- Run scan tests: `powershell -ExecutionPolicy Bypass -File tests\test_scan.ps1`.

## Quality Gates

- Policy compliance: scan_rules.yaml covers all guideline prohibitions.
- Detection accuracy: dirty sample produces BLOCK, clean sample produces OK.
- Audit trail: `logs/scan_history.jsonl` is populated after scans.
- Legacy cleanup: no old routing system files remain.

## Day-to-Day Usage

- Before sending text to AI: run `.\aiscan scan <file>` or `.\aiscan scan -Clipboard`.
- BLOCK detected: do not send. Mask or remove flagged content, or escalate per guideline.
- WARN detected: review flagged lines. Use judgment.
- REVIEW detected: human decision required. Scanner cannot determine automatically.

## Exception Handling

- False positive: if a detection is clearly wrong, note it for rule refinement.
- New pattern needed: add rule to `policies/scan_rules.yaml` and `scripts/scan_content.ps1`.
- Guideline update: sync both scan_rules.yaml and scan_content.ps1 rule definitions.

# aiscan Overview

## What It Is

aiscan is a local-first AI input scanner that checks text for policy violations before sending it to AI services. It enforces corporate AI usage guidelines by detecting personal information, confidential data, customer/partner information, and copyrighted content.

## How It Works

1. You prepare text to send to an AI (file, clipboard, or stdin).
2. aiscan scans the content locally against policy rules.
3. Detections are shown with risk levels (BLOCK / WARN / REVIEW).
4. You decide: mask, remove, or proceed.
5. A scan audit log is recorded for traceability.

No data leaves your machine. The scan runs entirely locally.

## What It Detects

| Category | Examples | Default Risk |
|----------|----------|-------------|
| Personal info | Email, phone, address, employee ID, names with titles | BLOCK |
| Confidential | "Confidential" markings, credentials, financial data, internal IPs | BLOCK |
| Customer/partner | Customer IDs, contract numbers, partner codes | BLOCK |
| Copyright | Copyright notices, license restrictions, quotation markers | BLOCK/REVIEW |

## Guideline Compliance

Detection rules are mapped directly to corporate AI usage guideline section 3 (Privacy and Data Security):

- Personal information (names, addresses, phone numbers, etc.)
- Confidential information and trade secrets
- Customer and partner information
- Copyrighted content

When BLOCK-level items are detected, the scanner displays the escalation notice: escalation to a director or above is required per guideline.

## Commands

```powershell
.\aiscan scan <file>         # Scan a file
.\aiscan scan -Clipboard     # Scan clipboard
.\aiscan scan -Stdin         # Scan stdin
.\aiscan scan <file> -Json   # JSON output
.\aiscan audit               # Policy/file integrity audit
```

## Exit Codes

- 0: Clean or REVIEW only
- 1: WARN detected
- 2: BLOCK detected (escalation required)

## Design Principles

- **Local-first**: No data leaves the machine.
- **Policy-as-code**: Rules defined in `policies/scan_rules.yaml`, mapped to guideline clauses.
- **Audit trail**: Every scan is logged to `logs/scan_history.jsonl`.
- **Pattern-based**: Regex detection for structurally identifiable information. No LLM dependency.
- **Actionable output**: Clear risk levels with line numbers and matched content.

## References

- Scan rules: `policies/scan_rules.yaml`
- Baseline scope: `BASELINE_DOCS.md`
- Ops checklist: `docs/ops/ops_checklist.md`

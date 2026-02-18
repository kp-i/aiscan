# aiscan Index

Purpose: fast navigation. This is a lookup map, not policy.

## Core

- Entry point: `aiscan.ps1`
- Cmd wrapper: `aiscan.cmd`
- Scan engine: `scripts/scan_content.ps1`
- Audit script: `scripts/audit_aiscan.ps1`

## Policy

- Scan rules (SSoT): `policies/scan_rules.yaml`
- Baseline scope: `BASELINE_DOCS.md`

## Tests

- Test runner: `tests/test_scan.ps1`
- Dirty sample: `tests/sample_dirty.txt`
- Clean sample: `tests/sample_clean.txt`

## Docs

- Human docs entry: `docs/README.md`
- Ops checklist: `docs/ops/ops_checklist.md`

## Persistent Context

- User profile: `USER_PROFILE.md`
- Context map: `index_map.json`

## Runtime Artifacts

- Scan audit log: `logs/scan_history.jsonl`

## Commands

- Scan file: `aiscan scan <file>`
- Scan clipboard: `aiscan scan -Clipboard`
- Audit: `aiscan audit`
- Help: `aiscan help`

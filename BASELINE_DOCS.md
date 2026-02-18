# aiscan Baseline Docs

## Single Source of Truth

- `policies/scan_rules.yaml`: scan detection rules and guideline mapping.

## Core Scripts

- `aiscan.ps1`: CLI entry point.
- `aiscan.cmd`: Windows batch wrapper.
- `scripts/scan_content.ps1`: scan detection engine.
- `scripts/audit_aiscan.ps1`: file/policy integrity audit.

## Navigation

- `README.md`: root entry point.
- `INDEX.md`: fast navigation map (non-authoritative).
- `index_map.json`: machine-readable context map.

## Human Documentation

- `docs/README.md`: human-doc entry point.
- `docs/human/overview.md`: system overview (English).
- `docs/human/overview_ja_quick.md`: system overview (Japanese, quick).
- `docs/human/overview_ja_detailed.md`: system overview (Japanese, detailed, source of truth).
- `docs/human/usage_guide.md`: practical usage guide (Japanese).
- `docs/ops/ops_checklist.md`: operational checklist.

## Tests

- `tests/test_scan.ps1`: automated scan engine tests.
- `tests/sample_dirty.txt`: test input with known violations.
- `tests/sample_clean.txt`: test input with no violations.

## Persistent Context

- `USER_PROFILE.md`: compact user preference profile (overwrite mode, <= 150 lines).

## Runtime Artifacts

- `logs/scan_history.jsonl`: scan audit trail (1 record per scan).

## Audit Order

1. Changed files in this list (diff scope).
2. Full sweep at session start.
3. Full sweep before session end.

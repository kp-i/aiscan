# USER_PROFILE

## Metadata
- id: sp5225
- scope: aiscan
- version: 3
- status: active

## Stable Preferences
- Prefer concise, actionable output.
- Prefer practical implementation over abstract discussion.
- Prefer canonical docs in English to reduce encoding risk.
- Prefer immediate rule/doc sync after changes.

## AI Usage Context
- Primary AI input paths: browser chat UI, CLI (Claude Code), API (planned).
- Key concern: personal info leakage to AI services.
- Guideline reference: 社内AI利用ガイドライン 3.プライバシーとデータセキュリティ

## Update Policy
- Keep compact (target <= 120 lines, hard limit 150 lines).
- Overwrite outdated items; no append-only history.
- New explicit user instruction overrides older items.

## Change Log
- v1: initialized from session preferences.
- v2: renamed to aiscan, removed routing-specific preferences.
- v3: rewritten for scanner use case. Removed obsolete routing/agent preferences.

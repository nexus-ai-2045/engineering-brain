# Changelog

この repo は SemVer を使います。Git tag / GitHub Release / announcement は別承認です。

## 0.1.0 - 2026-07-15

public seed.

- `engineering-brain` を public repository として公開。
- `engineering-autopilot` runtime skill projection を同期。
- `devbrain run` MVP を追加。
- public readiness packet と MIT LICENSE を追加。

## Unreleased

- version sync guard を追加。
- `devbrain version --json` を追加。
- `devbrain finish --json` を追加し、merge 後の branch cleanup 候補を plan できるようにした。
- `tools/hooks/post-merge` と `devbrain hooks install --json` を追加し、opt-in hook で finish plan を表示できるようにした。

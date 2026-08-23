# Changelog

この repo は SemVer を使います。Git tag / GitHub Release / announcement は別承認です。

## 0.1.0 - 2026-07-15

public seed.

- `engineering-brain` を public repository として公開。
- `engineering-autopilot` runtime skill projection を同期。
- `engineering_brain run` MVP を追加。
- public readiness packet と MIT LICENSE を追加。

## Unreleased

## 0.2.0 - 2026-08-23

capability release。public seed `0.1.0` 以降の local capability を tag する。

- research packetをv2へ更新し、`implementation-precedent-research`のconsumer契約を追加。
- `engineering-autopilot`から先行実装リサーチを呼び、本体は`nexus-ai-skills`正本として維持。
- CLI の PR stdout が catalog 外の residual と推論 purpose を消さないよう、secret/path scrub 後も残すようにした。
- Codex review 指摘に沿い、PR packet の secret scrub、default branch 検出、添付 packet schema 検証、rename/copy 解析、絶対 home path のみ redaction、実測 verification 表示、research unknowns 統合を修正した。
- `ai-ratchet-gate` v0.1.0 Release wheel と baseline、opt-in `pre-commit` hook を導入した。
- upstream `repo-preflight` を `tools/run_repo_preflight.py` / CI から実行し、consistency は `shadow` とした。
- `engineering_brain pr --json` を追加し、visible scope / checks / unknown / stopline 付きの日本語 PR packet を plan-only で生成できるようにした。
- version sync guard を追加。
- `engineering_brain version --json` を追加。
- `engineering_brain finish --json` を追加し、merge 後の branch cleanup 候補を plan できるようにした。
- `tools/hooks/post-merge` と `engineering_brain hooks install --json` を追加し、opt-in hook で finish plan を表示できるようにした。

---
title: verification profile and closeout v2
type: adr
status: accepted
created: 2026-08-28
updated: 2026-08-28
owner: nexus_ai
schema_version: fact-provenance/v1
recorded_at: 2026-08-28T22:30:00+09:00
recorded_by: cursor-cloud-agent
related:
  - ../AUTOPILOT_GOAL_DESIGN.md
  - ../OPERATING_MODEL.md
  - ../../engineering_brain/verification.py
  - ../../engineering_brain/gates.py
  - ../../engineering_brain/data/verification-profiles.yaml
---

# ADR-0006 verification profile と closeout v2

## Context

closeout の verification 軸は pytest / compile 固定だった。task や repo stack に応じた
unit / integration / smoke / e2e の必要十分を機械可読に選べず、未実行を成功と誤読する余地が残っていた。

## Decision

- verification profile の正本は `engineering_brain/data/verification-profiles.yaml` とする。
- profile は `layer`（unit / integration / smoke / e2e）、`detect_any`、`required`、`execute`、checks を持つ。
- closeout v2 の evidence status は `pass` / `fail` / `not_run` / `not_applicable` に限定する。
- overall block は **required かつ applicable** な check が `fail` または `not_run` のときだけとする。
- `execute=false` の profile は計画だけ返し、外部状態を変える command を自動実行しない。
- `e2e` は既定で opt-in。明示 `--profile` なしでは選ばない。
- run packet は closeout 未実行時でも `verification.profile_plan` を載せる。
- research-review eval と runtime-contract learnings は既存吸収を維持し、profile に必要な rule だけ wrap する。field_review 未了の candidate は adopt しない。

## Consequences

- 「口で保証を足す」代わりに、profile と evidence で verification 範囲が見える。
- Node / Go / Docker / Terraform は candidate + plan-only から始め、実行は別 slice で足せる。
- 既存 PR packet は pytest / compileall 互換フィールドを維持しつつ、summary と profile を表示できる。

## Human Review Gate

この ADR は merge、release、visibility 変更、外部送信を承認しない。

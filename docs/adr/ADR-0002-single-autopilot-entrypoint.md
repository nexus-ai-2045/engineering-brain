---
title: single runtime skill entrypoint
type: adr
status: accepted
created: 2026-07-28
updated: 2026-07-28
owner: nexus_ai
schema_version: fact-provenance/v1
recorded_at: 2026-07-28T15:21:05+09:00
recorded_by: codex
related:
  - ../LOCAL_SSOT.md
  - ../../skills/engineering-autopilot/SKILL.md
---

# ADR-0002 single runtime skill entrypoint

## Context

現在は、Codexのスキル一覧に`engineering-autopilot`が表示される一方、
`engineering-brain`は表示されない。名称は次の三層を表している。

- `engineering-autopilot`: Codexなどが呼ぶruntime skill
- `engineering-brain`: docs、registry、tests、skill sourceを持つrepository
- `engineering_brain`: repositoryが提供するPython module

repositoryやmoduleと同名のskillを追加すると、どれが入口でどれが正本かが曖昧になり、
判断ロジックの重複とruntime driftを生みやすい。

## Decision

- runtime skill entrypointは`engineering-autopilot`一本とする。
- `engineering-brain`という別skillや、`engineering_brain`という別skillは作らない。
- `engineering-autopilot`は薄いrouterに保ち、判断ロジックはrepository側のCLI、docs、
  registry、testsを正本とする。
- 起動時はcanonical repositoryで`python -m engineering_brain --help`を実行し、
  利用可能commandを実測する。
- 現在のcheckoutで確認できないcommandは推測実行せず、未統合または不明として止める。
- runtime projectionは、承認済みbranchが統合された後にrepo-owned skill sourceから同期する。

## Consequences

- スキル一覧では入口が一つになり、利用者は`engineering-autopilot`だけを選べばよい。
- repository名、skill名、module名の違いはREADMEとskill説明から辿れる。
- 先行branchのruntime projectionがcanonical側より新しい場合でも、help実測によって
  存在しないcommandの実行を避けられる。
- 別名が必要になった場合も、独立ロジックを持つskillではなく、同じ入口へ転送する
  薄いaliasとして別ADRで再検討する。

## Human Review Gate

このADRはmerge、runtime同期、release、GitHub visibility変更を承認しない。それぞれ
current conversationで対象と操作を明示し、人間承認を得る。

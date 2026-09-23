---
title: public GitHub visibility
type: adr
status: accepted
created: 2026-09-24
updated: 2026-09-24
owner: nexus_ai
supersedes_in_part: ADR-0001
related:
  - ADR-0001-engineering-brain-private-knowledge-repo.md
  - ../../PUBLIC_READY.md
  - ../PUBLIC_RELEASE_REVIEW_PACKET.md
---

# ADR-0008 public GitHub visibility

## Context

ADR-0001（accepted）は `nexus-ai-2045/engineering-brain` を「private GitHub mirror / review surface」と決めた。

2026-08-23 に、ADR-0001 の Human Review Gate（GitHub visibility を public にする場合は current conversation で明示 yes を得る）を通したうえで、repo は public に変更された。記録は `PUBLIC_READY.md` にある（`status: public`、`current_visibility: PUBLIC`、実行した操作、公開前 checklist）。

一方で ADR 台帳は更新されず、正本を名乗る ADR-0001 が実態と逆のことを言い続けていた。2026-09-24 時点で GitHub API の `private` は `false`。

## Decision

- `nexus-ai-2045/engineering-brain` の GitHub visibility は **public** とする。
- ADR-0001 のうち「private GitHub mirror / review surface として扱う」の 1 項だけを本 ADR で置き換える。
- ADR-0001 のそれ以外の決定（executable SSOT の置き場、Obsidian を intake に限定、local learning の取り込み方、Prohibited、Human Review Gate）は変えない。
- 公開状態の実測値と公開前 checklist の正本は `PUBLIC_READY.md` とする。本 ADR は判断だけを持ち、実測値を複製しない。

## Consequences

- repo 内の docs / registry / tests / ADR は外部から読める前提で書く。ADR-0001 の Prohibited（raw chat log、個人絶対パス、secret、credential を入れない）は、public になったことで重みが増す。
- visibility を private へ戻す場合も、ADR-0001 の Human Review Gate と同じ扱いで明示 yes を得て、後続 ADR で記録する。

## Review Evidence

- `PUBLIC_READY.md`（2026-08-23 実測）
- governance test `test_public_visibility_is_recorded_against_adr_0001` が、台帳・ADR-0001・本 ADR・互換入口の相互参照を検査する。

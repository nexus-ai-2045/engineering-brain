---
title: engineering-brain private knowledge repo
type: adr
status: accepted
created: 2026-07-15
updated: 2026-07-15
owner: nexus_ai
related:
  - ../LOCAL_SSOT.md
  - ../KNOWLEDGE_INTAKE.md
  - ../CONCEPT_COVERAGE.md
---

# ADR-0001 engineering-brain private knowledge repo

## Context

`engineering-brain` は、開発判断、実装、検証、運用保証、PR lifecycle、local learning absorption を 1 つの local-first repo に寄せるための正本である。

旧 `dev-brain` は private recreate 前の作業 repo であり、clean-history 方針により GitHub PR history は移行しない。移行後の正本は `engineering-brain` に一本化する。

Obsidian は発見、悩み、仮説、raw note の入口として有用だが、実行ゲート、test、registry、ADR を持つ repo 正本の代替にはしない。

## Decision

- `engineering-brain` を private executable SSOT とする。
- `nexus-ai-2045/engineering-brain` は private GitHub mirror / review surface として扱う。
- Obsidian は intake と探索の入口に限定し、採用済み knowledge は repo 内の docs、registry、tests、ADR、skill source に昇格する。
- local learning は raw chat log ではなく、再利用可能な rule、gate、test、source packet、ADR として取り込む。
- 旧 `dev-brain` は移行確認後に削除してよい legacy とする。

## Allowed

- Obsidian や local memory から候補を読み、採用候補 packet を作る。
- 採用済み learning を `docs/`、`registry/`、`schemas/`、`tests/`、将来の `skills/engineering-autopilot/` に入れる。
- ADR が必要な設計判断を `docs/adr/` に残す。
- private PR で human review と machine verification を回す。

## Prohibited

- raw chat log、未検証 clipping、個人絶対パス、secret、credential を repo 正本へ直接入れる。
- Obsidian 側の note を repo 正本と呼ぶ。
- public 化、外部共有、release、告知をこの ADR の承認だけで行う。
- skill 側へ repo の判断ロジックを複製する。

## Human Review Gate

次は現在会話で対象、操作、見える内容、検証状況を明示して yes を得るまで止める。

- GitHub visibility を public にする。
- 外部投稿、公開、release、launch、広範な共有。
- merge。
- hook、settings、auth、credential、billing、production state の変更。
- destructive delete。ただし旧 `dev-brain` の削除は 2026-07-15 の current-turn approval に基づき、この移行作業の範囲で実行可能。

## Consequences

- repo は太らせてよいが、太らせ方は raw accumulation ではなく distilled knowledge accumulation にする。
- Obsidian は軽い入口なので、思考速度を落とさずに使える。
- repo に入った知見は test / closeout / registry で回帰検知できる。
- 旧 repo の PR history は clean-history 方針により新 repo へは持ち込まない。

## Review Evidence

- `docs/LOCAL_SSOT.md` が live SSOT を `engineering-brain` に固定している。
- `docs/CONCEPT_COVERAGE.md` が必須概念の coverage と gap を可視化する。
- governance test が ADR、intake、coverage の存在と主要停止線を検査する。


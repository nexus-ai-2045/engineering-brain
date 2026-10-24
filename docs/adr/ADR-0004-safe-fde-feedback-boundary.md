---
title: safe FDE feedback boundary
type: adr
status: accepted
created: 2026-07-30
updated: 2026-07-30
owner: nexus_ai
schema_version: fact-provenance/v1
recorded_at: 2026-07-30T13:45:00+09:00
recorded_by: codex
related:
  - ../PDCA_FEEDBACK_LOOP.md
  - ../../engineering_brain/feedback.py
  - ../../engineering_brain/fde-feedback-packet.schema.json
---

# ADR-0004 安全なFDE feedback境界

## Context

PDCA結果をFDEの次のPlanへ渡す時、raw historyや入力由来の秘密情報・個人パスを
構造化出力へ再掲すると、ログや別runtimeへ漏れる可能性がある。またpacket側の
`human_gate_required: false`を信頼すると、`adopt`が人間レビューを迂回できる。

## Decision

- `adopt`はpacketの境界フラグにかかわらず、`human_review: approved`を必須とする。
- 秘密情報、個人パス、不正Unicodeを検出した入力では、入力由来metadataを出力しない。
- evidence referenceにも同じ個人パス検査を適用する。
- 有効な非BMP UnicodeとRFC 3339の小文字`z`は受理する。
- 人間向け出力はUnicodeをエスケープせず可読性を保つ。
- feedback schemaはwheelへ同梱し、source checkout外でもCLIを起動可能にする。

## Consequences

- feedback境界での人間承認迂回とmetadata漏洩を防げる。
- 不正入力時の診断情報は意図的に少なくなり、詳細調査は安全なlocal evidenceで行う。
- schemaと実装の同時更新が必要になる。
- 同時更新を人力に委ねた結果、複製schemaが正本から乖離し互換性が壊れた。
  再発防止として、正本が受け付ける形を`tests/test_feedback.py`のcontract testへ
  固定する。人力同期の前提はここで機械検査へ置き換える。

## Human Review Gate

このADRはpacketの`adopt`、FDEへの外部送信、merge、releaseを自動承認しない。
各操作はcurrent conversationで明示的な人間承認を得る。

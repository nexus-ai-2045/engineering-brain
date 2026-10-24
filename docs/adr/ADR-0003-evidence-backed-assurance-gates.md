---
title: evidence-backed assurance gates
type: adr
status: accepted
created: 2026-07-30
updated: 2026-07-30
owner: nexus_ai
schema_version: fact-provenance/v1
recorded_at: 2026-07-30T13:30:00+09:00
recorded_by: codex
related:
  - ../GCP_AI_ORCHESTRATION_ASSURANCE.md
  - ../../engineering_brain/assurance.py
  - ../../engineering_brain/gates.py
---

# ADR-0003 実行証拠に基づくassurance gate

## Context

非同期cloud処理とstructured model評価の採用unitが、unit testの実行だけを
`G2 checked`の根拠にすると、対象runのexecution、停止補償、品質指標が欠けていても
gate自体は正常に見える。検証ロジックのtest成功と、対象runの合格は別の事実である。

## Decision

- `async_orchestration_evidence_gate` と `structured_model_evaluation_gate` は、
  対象runのJSON evidenceを受け取って評価する。
- 対象gateが選択されたのにevidenceが無い場合は、`overall: blocked`とする。
- 非同期処理では、実行数、marker schema、cancel後のactive job数を、
  booleanではない整数として要求する。
- model評価では、測定済みフラグだけでなく、semantic、critical field、
  calibration、worst sliceの値と明示的な合格閾値を比較する。
- candidate learningは安定したpacket shapeを保ち、未提案なら
  `proposed_solution: null`を明示する。

## Consequences

- unit test成功だけで実runを合格扱いするfalse greenを防げる。
- 閾値は対象用途ごとにevidenceへ明示され、暗黙の共通値を押し付けない。
- evidence生成元の正当性と完全性は別途確認が必要であり、このgate単独では保証しない。

## Human Review Gate

このADRはcloud実行、課金、deploy、model採用、merge、releaseを承認しない。
各操作はcurrent conversationで対象と境界を明示し、人間承認を得る。

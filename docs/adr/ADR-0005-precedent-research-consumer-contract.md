---
title: ADR-0005 先行実装リサーチのconsumer契約
status: accepted
date: 2026-07-31
decision_owner: nexus_ai
---

# ADR-0005 先行実装リサーチのconsumer契約

## Context

engineering-brainには技術source catalogとresearch packetがあるが、公式仕様、
正本コード、主要実装、失敗証拠を比較し、最小実装と回帰テストへ変換する横断契約は
なかった。この能力をengineering-brain内へ複製すると、他の開発workflowから再利用
できず、正本が分岐する。

## Decision

- `implementation-precedent-research`の正本は`nexus-ai-skills`が所有する。
- engineering-brainは`engineering-autopilot`とresearch packetから呼ぶconsumerになる。
- `wrap`、`extend`、`adopt_oss`、`build`の前に先行実装評価を要求する。
- 正本skillが未配布、または根拠不足の場合は`hold`として人間レビューへ戻す。
- required consumer fieldの追加は互換変更ではないため、research packetをversion 2へ上げる。
- runtime同期、既存skill整理、mergeはそれぞれ別の承認境界とする。

## Consequences

- 横断skillの再利用性と単一正本を維持できる。
- consumer側だけを先に統合すると参照先が利用できない期間が生じるため、正本PRを先に扱う。
- research packet version 1のconsumerはversion 2対応が必要になる。
- 実際のモデル応答品質はbaseline比較まで未確認として残る。

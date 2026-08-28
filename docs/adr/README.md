# ADR

この directory は `engineering-brain` の設計判断記録です。

ADR は作業ログではなく、後続 PR で同じ判断を繰り返さないための正本として扱います。特に次の判断は ADR 化します。

- SSOT、repo placement、runtime skill、Obsidian 連携など、後続作業の前提になる判断。
- human review、公開、GitHub visibility、merge、cleanup、破壊的操作の停止線。
- research / TDD / verification / operation guarantee の品質ゲート。
- local learning を repo に吸収する時の採用基準。

## 一覧

| ADR | status | 決定 |
|---|---|---|
| [ADR-0001 engineering-brain private knowledge repo](ADR-0001-engineering-brain-private-knowledge-repo.md) | accepted | `engineering-brain` を private executable SSOT とし、Obsidian は intake に留める |
| [ADR-0002 single runtime skill entrypoint](ADR-0002-single-autopilot-entrypoint.md) | accepted | runtime skillは`engineering-autopilot`へ一本化し、repoとmoduleを別skillにしない |
| [ADR-0003 evidence-backed assurance gates](ADR-0003-evidence-backed-assurance-gates.md) | accepted | assurance gateはunit testではなく対象runの明示的evidenceを評価する |
| [ADR-0004 safe FDE feedback boundary](ADR-0004-safe-fde-feedback-boundary.md) | accepted | feedbackは承認迂回と入力由来metadata漏洩を防ぎ、schemaをwheelへ同梱する |
| [ADR-0005 先行実装リサーチのconsumer契約](ADR-0005-precedent-research-consumer-contract.md) | accepted | 横断skillを`nexus-ai-skills`正本とし、research packet v2からconsumerとして参照する |
| [ADR-0006 verification profile / closeout v2](ADR-0006-verification-profile-closeout-v2.md) | accepted | verification profile で unit/integration/smoke/e2e を機械可読にし、closeout evidence を pass/fail/not_run/not_applicable へ分離する |

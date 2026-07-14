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


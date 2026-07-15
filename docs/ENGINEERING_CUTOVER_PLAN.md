# engineering-brain cutover plan

status: executed-private
owner: nexus_ai
checked_at: 2026-07-15 JST

## 結論

`nexus-ai-2045/engineering-brain` は private clean-history recreation として作成済みである。現時点の live SSOT は `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain` である。

legacy `dev-brain` は migration verification 後に削除済みであり、初期 PR history は新 repo へ持ち込まない。runtime skill の install copy はまだ切り替えない。

cutover では次の 4 層を同じ packet で切り替える。

1. local directory: `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain`
2. GitHub repo: `nexus-ai-2045/engineering-brain`
3. repo-owned skill: `skills/engineering-autopilot`
4. runtime install copy: `<USER_HOME>/.codex/skills/engineering-autopilot` (同期済み / `devbrain skill-sync` で drift check)

## Rename と recreate の判断

| option | 使う条件 | 注意 |
|---|---|---|
| keep current | まだ設計・registry・CLI が流動的 | いまの既定。private のまま小さい PR を積む |
| rename current repo | issues / PR / history / stars / links を引き継ぎたい | GitHub は redirect を提供するが、local remote、CI、Actions、Pages、外部参照は更新が必要 |
| recreate private repo | 名前、history、visibility、runtime skill を clean に切り直したい | 旧 repo は移行確認中だけ参照元として残し、採用後は削除できる。history をどこまで持つかを review する |

この repo はまだ public ではないため、将来名を固定する前なら recreate private repo は現実的な選択肢である。一方で、PR #2-#5 で整えた path redaction、SSOT、templates、migration ledger は有効なので、現行 repo で判断と実装 seed を整えたうえで cutover する方が安全である。

## PR boundary

| PR | 役割 | GitHub / local mutation |
|---|---|---|
| legacy PR #6 | roadmap、source catalog、cutover 方針、判断基準を固定 | merged in `dev-brain` |
| legacy PR #7 | private cutover packet を作り、private recreate を選択 | merged in `dev-brain` |
| initial engineering-brain commit | private repo / local target / clean snapshot | this repo |
| next PRs | CLI / skill / registry 整合性 | new live SSOT に従う |

legacy PR #6 / #7 に「全部の実行」を入れなかった理由は、GitHub repo lifecycle、local directory、runtime skill、SSOT registry を同時に動かすと rollback と review scope が曖昧になるためである。

## Stoplines

次は current conversation の明示承認まで実行しない。

- `gh repo rename engineering-brain`
- runtime skill の install copy を `engineering-autopilot` へ切り替える (done)
- `dev-brain` repo の visibility 変更
- public visibility 変更

## Private cutover packet

cutover 実行時の review packet は [private cutover packet](PRIVATE_CUTOVER_PACKET.md) に保存する。

result: private recreate / clean history / legacy repo kept private.

## Recommended order

1. initial engineering-brain snapshot を push する。
2. `<PROJECTS_ROOT>/ssot-registry.yaml` を更新する。
3. repo-owned `skills/engineering-autopilot` は薄い CLI 入口として追加済み。
4. runtime install copy への dry-run drift check は `devbrain skill-sync` で追加済み。
5. runtime install copy への `--apply` と post-apply validation は実施済み。
6. PR D-G 相当の CLI / lifecycle / skill 実装は、新 live SSOT で続行する。
7. 旧 `dev-brain` 由来の未採用知見が後から見つかった場合は、raw copy ではなく knowledge intake packet として評価する。
8. public 化はさらに別の review packet と明示 yes まで止める。

## Source notes

GitHub の rename は repository URL や Git 操作の redirect を提供するが、混乱を避けるため local clone の remote 更新が推奨される。GitHub Actions の action host など redirect されない用途もあるため、action / workflow / external reference を別途確認する。

GitHub の duplicate/mirror 手順は新しい repo を作る選択肢になる。ただし、history と見える範囲をどう扱うかは public readiness と同じ review 境界で扱う。

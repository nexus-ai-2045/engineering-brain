# engineering-brain roadmap

status: active
owner: nexus_ai
checked_at: 2026-07-15 JST

## 現在地

`engineering-brain` は private clean-history recreation 後の live repo である。legacy `dev-brain` は migration verification 後に削除済みであり、今後の正本はこの repo に一本化する。

PR #1 は broad / conflicting / stale な draft として close 済み。採用する要素は [PR #1 migration ledger](PR1_MIGRATION_LEDGER.md) に従って小さい PR に分ける。

## PR split

| order | PR | 目的 | 状態 |
|---:|---|---|---|
| A | GitHub templates / contributing guide | issue / PR intake と human stopline の標準化 | done: PR #5 |
| B | source catalog / roadmap / cutover plan | source catalog の不足整理、ロードマップ、rename/recreate 判断 | done in legacy PR #6 |
| C | private cutover packet | `engineering-brain` へ private recreate する packet | done in legacy PR #7 |
| D | identity gate | commit identity / range failure を fail-closed にする | next |
| E | run packet / planner dry-run | route / gate / closeout を run packet に統合する | planned |
| F | lifecycle registry / FSM | phase registry と不正遷移 fail-closed | planned |
| G | PR packet generator | 日本語 PR body、visible scope、checks、stopline を生成 | planned |
| H | repo-owned thin skill | runtime skill は CLI を呼ぶ薄い入口にする | planned |

## Cutover policy

private recreate の履歴は [Migration notes](MIGRATION_NOTES.md)、[engineering-brain cutover plan](ENGINEERING_CUTOVER_PLAN.md)、[private cutover packet](PRIVATE_CUTOVER_PACKET.md) を参照する。

public 化はこの roadmap の完了条件ではない。visibility 変更は別 review packet と current conversation の明示 yes が必要。

## Done for current private phase

- `python -m pytest -q` が通る。
- `python -m devbrain closeout --repo . --json` が `overall=ok` を返す。
- 個人ホーム絶対パスが公開候補 artifact に残っていない。
- GitHub write 前に identity probe が `status=ok` を返す。
- PR ごとに採用、未採用、残リスク、人間停止線が分かれている。

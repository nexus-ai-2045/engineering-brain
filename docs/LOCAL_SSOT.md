# Local SSOT

status: active
owner: nexus_ai
checked_at: 2026-07-15 JST

## 結論

現行 engineering-brain の local SSOT は次に固定する。

```text
<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
```

この位置は `<PROJECTS_ROOT>/ssot-registry.yaml` の repo 台帳に登録されている canonical path である。

公開候補の文書では、実ユーザー名を含む絶対パスを書かない。必要な時は次の placeholder を使う。

| placeholder | 意味 |
|---|---|
| `<PROJECTS_ROOT>` | ローカル workspace root |
| `<USER_HOME>` | ローカル user home |
| `<REPO>` | この repo root |

## 役割分担

| location | role | SSOT |
|---|---|---|
| `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain` | local source of truth / 実装・docs・tests・registry | yes |
| `https://github.com/nexus-ai-2045/engineering-brain` | private GitHub mirror / review surface | no |
| `<PROJECTS_ROOT>/Documents/repos/second-brain/dev-brain` | deleted legacy private source | no |
| `https://github.com/nexus-ai-2045/dev-brain` | deleted legacy private GitHub repo | no |
| `<PROJECTS_ROOT>/dev-brain` | stale / non-canonical clone with later experimental commits | no |
| `<USER_HOME>/.codex/skills/dev-brain-autopilot` | runtime install copy, if present | no |
| `<USER_HOME>/.codex/skills/engineering-autopilot` | runtime install copy synced from repo source | yes, projection only |

## engineering-brain / engineering-autopilot の扱い

`engineering-brain` は live repo 名である。`engineering-autopilot` は repo-owned / runtime skill 名であり、runtime install copy は repo source から同期する projection として扱う。

将来の cutover 候補:

| layer | current | target candidate |
|---|---|---|
| local repo | `Documents/repos/second-brain/dev-brain` | `Documents/repos/engineering/engineering-brain` |
| GitHub repo | `nexus-ai-2045/dev-brain` | `nexus-ai-2045/engineering-brain` |
| runtime skill source | `skills/engineering-autopilot` repo-owned source | `skills/engineering-autopilot` |
| runtime install copy | `.codex/skills/dev-brain-autopilot` if synced | `.codex/skills/engineering-autopilot` synced projection |

## Guard

- 変更はまず canonical path に入れる。
- legacy `dev-brain` 由来の未採用知見が見つかった場合は、canonical repo へ直接取り込まず、knowledge intake packet として評価する。
- GitHub push / PR / repo create / visibility public は current-turn explicit approval まで実行しない。
- GitHub write 前に `gh auth status` と commit identity を確認する。
- `engineering-autopilot` を live runtime skill と呼べる。維持条件は `python -m devbrain skill-sync --json` が `status: ok` を返すこと。

## Placement decision

`engineering-brain` は `second-brain` 配下へ置かない。開発判断・実装保証・運用保証を扱う engineering 系 repo として `Documents/repos/engineering/engineering-brain` に置く。

private recreate の履歴は [Migration notes](MIGRATION_NOTES.md) と [private cutover packet](PRIVATE_CUTOVER_PACKET.md) を参照する。

この候補を正式化する時は、同じ変更で `ssot-registry.yaml` の `repos:` 節へ次の形で追加または更新する。

```yaml
- {path: Documents/repos/engineering/engineering-brain, remote: nexus-ai-2045/engineering-brain, visibility: private, repo_class: own_private, case: engineering, identity: 273569186+nexus-ai-2045@users.noreply.github.com, wave: keep, note: dev-brain clean cutover candidate; public化は別承認}
```

GitHub visibility を public に変える場合は、`visibility: public` / `repo_class: own_public` への更新も同じ review packet で扱う。

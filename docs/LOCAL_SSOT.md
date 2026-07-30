# Local SSOT

status: active
owner: nexus_ai
checked_at: 2026-07-16 JST

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
| `https://github.com/nexus-ai-2045/engineering-brain` | public GitHub review / distribution surface | no |
| `<PROJECTS_ROOT>/Documents/repos/second-brain/dev-brain` | deleted legacy private source | no |
| `https://github.com/nexus-ai-2045/dev-brain` | deleted legacy private GitHub repo | no |
| `<PROJECTS_ROOT>/dev-brain` | deleted stale / non-canonical clone | no |
| `<USER_HOME>/.codex/skills/dev-brain-autopilot` | deleted legacy runtime install copy | no |
| `<USER_HOME>/.codex/skills/engineering-autopilot` | runtime install copy synced from repo source | yes, projection only |

## engineering-brain / engineering-autopilot の扱い

`engineering-brain` は live repo 名である。`engineering-autopilot` は repo-owned / runtime skill 名であり、runtime install copy は repo source から同期する projection として扱う。

完了済み cutover の記録:

| layer | live surface | role |
|---|---|---|
| local repo | `Documents/repos/engineering/engineering-brain` | live local SSOT |
| GitHub repo | `nexus-ai-2045/engineering-brain` | public review / distribution surface |
| runtime skill source | `skills/engineering-autopilot` repo-owned source | live source |
| runtime install copy | `.codex/skills/engineering-autopilot` synced projection | live projection |

Legacy `dev-brain` repo、stale clone、runtime skill copy は削除済みであり、現行作業や cleanup の対象にはしない。

## Guard

- 変更はまず canonical path に入れる。
- legacy `dev-brain` 由来の未採用知見が見つかった場合は、canonical repo へ直接取り込まず、knowledge intake packet として評価する。
- GitHub push / PR / repo create / visibility change は current-turn explicit approval まで実行しない。
- GitHub write 前に identity probe と PR readiness preflight を実行する。active `gh` login が `nexus-ai-2045` 以外、または viewer permission が `WRITE` 未満なら push / PR 更新 / merge を止める。
- `gh` active account drift の回復は `gh auth switch --hostname github.com --user nexus-ai-2045` を使う。ただし auth / credential state 変更なので、実行前に current conversation の明示 yes を取る。
- `engineering-autopilot` を Codex / Claude Code の live runtime skill と呼べる。維持条件は `python -m engineering_brain skill-sync --target all --json` が `status: ok` を返すこと。

## Placement decision

`engineering-brain` は `second-brain` 配下へ置かない。開発判断・実装保証・運用保証を扱う engineering 系 repo として `Documents/repos/engineering/engineering-brain` に置く。

private recreate の履歴は [Migration notes](MIGRATION_NOTES.md) と [private cutover packet](PRIVATE_CUTOVER_PACKET.md) を参照する。

`ssot-registry.yaml` の `repos:` 節は次の現行形で管理する。

```yaml
- {path: Documents/repos/engineering/engineering-brain, remote: nexus-ai-2045/engineering-brain, visibility: public, repo_class: own_public, case: engineering, identity: 273569186+nexus-ai-2045@users.noreply.github.com, wave: keep, note: dev-brain clean cutover completed; release/tag/announcement は別承認}
```

GitHub visibility は public 済み。今後の visibility 変更、release、tag、外部告知は別 review packet と current conversation の明示 yes で扱う。

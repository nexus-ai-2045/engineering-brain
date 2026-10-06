# ローカル正本（SSOT）

status: reconciliation_required
owner: nexus_ai
checked_at: 2026-09-08 JST

## 現在の確認結果

コード・docs・tests・data・repo-owned skill の正本はこの repo です。物理配置の指定は文書と台帳が一致していないため、以下の旧指定を現行の実在パスと断定しません。配置の再指定・移動・runtime切替は未実施です。

2026-09-08のMac読取りでは、旧指定パスは存在せず、配置台帳は `<PROJECTS_ROOT>/Documents/.repos/nexus_ai/engineering-brain` を指定していました。通常CLIもそのcheckoutの0.2.0をimportしています。GitHubはpublicですが、台帳の公開範囲表示には古いprivate表記が残っています。Windows等の別hostは未確認です。

実装checkout、Release固定の配布元、導入済みCLIの参照先を区別し、配置担当がcanonical pathを確定してから台帳と文書を同時に整合させます。ここではどちらのパスも新たな正本として採用しません。

## 旧指定と移行記録

以下は2026-07-16時点の指定・移行記録です。現在の配置・runtime認識の保証には使いません。

当時の local SSOT 指定:

```text
<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
```

当時はこの位置を配置台帳のcanonical pathとして記載していました。現在の台帳との不一致は上記の通りです。

公開候補の文書では、実ユーザー名を含む絶対パスを書かない。必要な時は次の placeholder を使う。

| placeholder | 意味 |
|---|---|
| `<PROJECTS_ROOT>` | ローカル workspace root |
| `<USER_HOME>` | ローカル user home |
| `<REPO>` | この repo root |

## 当時の役割分担（現行の配置・同期状態を示さない）

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

完了済み cutover の記録（当時の記載）:

| layer | live surface | role |
|---|---|---|
| local repo | `Documents/repos/engineering/engineering-brain` | live local SSOT |
| GitHub repo | `nexus-ai-2045/engineering-brain` | public review / distribution surface |
| runtime skill source | `skills/engineering-autopilot` repo-owned source | live source |
| runtime install copy | `.codex/skills/engineering-autopilot` synced projection | live projection |

Legacy `dev-brain` repo、stale clone、runtime skill copy は削除済みであり、現行作業や cleanup の対象にはしない。

## 確認と停止条件

- 変更前に台帳・remote・実体・実行版を照合する。不一致の間は共有checkoutを切り替えず、対象SHAを固定した隔離worktreeでレビュー差分を準備する。
- legacy `dev-brain` 由来の未採用知見が見つかった場合は、canonical repo へ直接取り込まず、knowledge intake packet として評価する。
- GitHub push / PR / repo create / visibility change は current-turn explicit approval まで実行しない。
- GitHub write 前に identity probe と PR readiness preflight を実行する。active `gh` login が `nexus-ai-2045` 以外、または viewer permission が `WRITE` 未満なら push / PR 更新 / merge を止める。
- `gh` active account drift の回復は `gh auth switch --hostname github.com --user nexus-ai-2045` を使う。ただし auth / credential state 変更なので、実行前に current conversation の明示 yes を取る。
- `python -m engineering_brain skill-sync --target all --json` の `status: ok` は対象sourceとruntime install copyのファイル一致を示す。各AIのスキル発見・新規taskでの呼出し・正しいCLI版の実行は別途確認する。

## 当時の配置判断（現行指定は照合待ち）

`engineering-brain` は `second-brain` 配下へ置かない。開発判断・実装保証・運用保証を扱う engineering 系 repo として `Documents/repos/engineering/engineering-brain` に置く。

private recreate の履歴は [Migration notes](MIGRATION_NOTES.md) と [private cutover packet](PRIVATE_CUTOVER_PACKET.md) を参照する。

当時文書に示した `ssot-registry.yaml` の `repos:` 節は次の形です。現在の台帳そのものではありません。

```yaml
- {path: Documents/repos/engineering/engineering-brain, remote: nexus-ai-2045/engineering-brain, visibility: public, repo_class: own_public, case: engineering, identity: 273569186+nexus-ai-2045@users.noreply.github.com, wave: keep, note: dev-brain clean cutover completed; release/tag/announcement は別承認}
```

GitHub visibility は public 済み。今後の visibility 変更、release、tag、外部告知は別 review packet と current conversation の明示 yes で扱う。

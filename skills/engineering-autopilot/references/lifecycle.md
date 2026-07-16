# engineering-autopilot lifecycle

status: active
owner: nexus_ai

## 目的

`engineering-autopilot` は、開発作業をいきなり実装へ進めず、設計、既存調査、TDD、実装、検証、運用保証、PR準備、人間レビュー停止線へ順に通すための入口です。

## 現行フェーズ

| phase | 目的 | 現行 command / artifact |
|---|---|---|
| route | task の種類と必要 gate を決める | `python -m engineering_brain route --task "<task>" --json` |
| gate | trigger から必要な採用 unit を確認する | `python -m engineering_brain gate --trigger implementation --json` |
| catalog | 技術・既存例・公式 source を候補として確認する | `python -m engineering_brain catalog --domain <domain> --json` |
| skill-sync | repo-owned skill source と runtime install copy の drift を確認する | `python -m engineering_brain skill-sync --json` |
| run packet | route / gate / catalog / skill-sync / closeout stopline を 1 packet にまとめる | `python -m engineering_brain run --task "<task>" --json` |
| implement | 対象 repo の既存パターンに沿って最小差分で実装する | repo-local tests / docs |
| verify | test / smoke / compile / closeout を実行する | `python -m pytest -q`, `python -m engineering_brain closeout --repo . --json` |
| review packet | 外部操作前に見える範囲と未実施を分ける | PR body / closeout |
| human stopline | push / PR / merge / cleanup / visibility を止める | current-turn explicit approval |
| finish | merge 後の main 同期、local / remote branch cleanup 候補を plan する | `python -m engineering_brain finish --json` |
| hook install | repo 同梱 hook を opt-in で local `.git/hooks/` へ入れる | `python -m engineering_brain hooks install --json` |

## 停止線

次は skill が勝手に完了してはいけません。

- GitHub push / PR create / merge / branch cleanup
- repository visibility 変更
- runtime install copy を正本として直接編集すること
- credential / auth / hook / settings 変更
- production DB / cloud mutation
- public release / publish / external share

## post-merge hook 方針

repo に含める hook は `tools/hooks/` の template だけです。`python -m engineering_brain hooks install --json` を実行したローカル checkout だけに入ります。

`post-merge` hook は `python -m engineering_brain finish --repo . --json` の plan を表示するだけです。local branch / remote branch / worktree は自動削除しません。

cleanup を実行する場合は、まず `python -m engineering_brain finish --json` で候補を見ます。local branch cleanup は `--apply-local` を明示します。remote branch cleanup は GitHub write なので current-turn approval と GitHub identity probe を通します。

## roadmap reference

詳細な移行順は `references/roadmap.md` と repo 側 `docs/ROADMAP.md` を使います。矛盾した場合は repo 側 `docs/ROADMAP.md` を優先し、この reference を更新します。

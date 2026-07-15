# engineering-autopilot lifecycle

status: active
owner: nexus_ai

## 目的

`engineering-autopilot` は、開発作業をいきなり実装へ進めず、設計、既存調査、TDD、実装、検証、運用保証、PR準備、人間レビュー停止線へ順に通すための入口です。

## 現行フェーズ

| phase | 目的 | 現行 command / artifact |
|---|---|---|
| route | task の種類と必要 gate を決める | `python -m devbrain route --task "<task>" --json` |
| gate | trigger から必要な採用 unit を確認する | `python -m devbrain gate --trigger implementation --json` |
| catalog | 技術・既存例・公式 source を候補として確認する | `python -m devbrain catalog --domain <domain> --json` |
| skill-sync | repo-owned skill source と runtime install copy の drift を確認する | `python -m devbrain skill-sync --json` |
| implement | 対象 repo の既存パターンに沿って最小差分で実装する | repo-local tests / docs |
| verify | test / smoke / compile / closeout を実行する | `python -m pytest -q`, `python -m devbrain closeout --repo . --json` |
| review packet | 外部操作前に見える範囲と未実施を分ける | PR body / closeout |
| human stopline | push / PR / merge / cleanup / visibility を止める | current-turn explicit approval |

## 停止線

次は skill が勝手に完了してはいけません。

- GitHub push / PR create / merge / branch cleanup
- repository visibility 変更
- runtime install copy を正本として直接編集すること
- credential / auth / hook / settings 変更
- production DB / cloud mutation
- public release / publish / external share

## roadmap reference

詳細な移行順は `references/roadmap.md` と repo 側 `docs/ROADMAP.md` を使います。矛盾した場合は repo 側 `docs/ROADMAP.md` を優先し、この reference を更新します。

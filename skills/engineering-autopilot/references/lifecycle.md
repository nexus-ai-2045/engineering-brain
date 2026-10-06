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
| precedent research | 公式仕様、正本コード、主要実装、失敗証拠から採用判断を作る | `$implementation-precedent-research`（正本: `nexus-ai-skills`） |
| algorithm select | 問題シグナルと制約から定番アルゴリズム候補を順位付けする | `python -m engineering_brain algorithms select --signal <signal> --constraint <constraint> --json` |
| algorithm compare | 前提・避ける条件・計算量・検証方法を同じ形式で比較する | `python -m engineering_brain algorithms compare --id <id> --id <id> --json` |
| skill-sync | repo-owned skill source と Codex / Claude Code runtime install copy の drift を確認する | `python -m engineering_brain skill-sync --target all --json` |
| Claude Code smoke | 個人スキルを通常モードで直接呼び、停止境界を確認する | `/engineering-autopilot` (`--bare` は使わない) |
| run packet | route / gate / catalog / skill-sync / closeout stopline を 1 packet にまとめる | `python -m engineering_brain run --task "<task>" --json` |
| implement | 対象 repo の既存パターンに沿って最小差分で実装する | repo-local tests / docs |
| async proof | 非同期runのexecution/job/artifact/evaluation/cost/cancel証拠を結ぶ | `async_orchestration_evidence_gate` |
| model proof | syntax/schema/semantic/table/calibration/robustness/artifactを分離評価する | `structured_model_evaluation_gate` |
| verify | test / smoke / compile / closeout を実行する | `python -m pytest -q`, `python -m engineering_brain closeout --repo . --json` |
| review packet | 外部操作前に見える範囲と未実施を分ける | `python -m engineering_brain pr --repo . --json` |
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

## 先行実装リサーチ契約

`wrap`、`extend`、`adopt_oss`、`build`へ進む前にprecedent researchを通す。
engineering-brainは`implementation-precedent-research`のconsumerであり、skill本体を
このrepoへ複製しない。調査結果は`adopt`、`revise`、`reject`、`hold`と、最小実装、
意図的に持ち込まない複雑性、回帰テストを含む。正本skillが未配布または根拠不足なら
`hold`として人間レビューへ戻す。

## アルゴリズム選定契約

`engineering_brain/data/algorithms.json` はコピー可能な実装断片集ではなく、wheelへ同梱する選定判断の正本です。問題を次の観点へ分解してから使います。

- 入力の順序、グラフ重み、状態遷移、ID安定性
- データ量、更新頻度、メモリ上限、厳密性
- 一時障害、再試行可能性、冪等性、観測の揺れ

`select` の点数は採用決定ではありません。採用前に候補の `preconditions` を満たし、`avoid_when` に該当しないことを対象 repo のテストまたは実測で確認します。候補が0件なら未知として入力シグナルを補い、無関係な候補を自動採用しません。

## post-merge hook 方針

repo に含める hook は `tools/hooks/` の template だけです。`python -m engineering_brain hooks install --json` を実行したローカル checkout だけに入ります。

`post-merge` hook は `python -m engineering_brain finish --repo . --json` の plan を表示するだけです。local branch / remote branch / worktree は自動削除しません。

cleanup を実行する場合は、まず `python -m engineering_brain finish --json` で候補を見ます。この repo は branch を削除しません。削除の実行正本は fractal-decision-ecosystem の `scripts/post_merge_cleanup.py` (FDE ADR-0006) で、plan の `cleanup_ssot` が委譲先を示します。remote branch cleanup は GitHub write なので current-turn approval と GitHub identity probe を通します。

## roadmap reference

詳細な移行順は `references/roadmap.md` と repo 側 `docs/ROADMAP.md` を使います。矛盾した場合は repo 側 `docs/ROADMAP.md` を優先し、この reference を更新します。

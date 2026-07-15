# engineering-brain

engineering-brain は、開発判断・実装・検証・運用保証を「読んで終わり」にせず、作業前後に通せる形へ落とすローカル-first repo です。

Fractal Decision Ecosystem（FDE）が AI ルーティングと意思決定の OS だとすると、engineering-brain は開発実装の保証 OS です。ここでの「100%」はバグゼロ断定ではありません。保証できること、未確認、残リスク、人間承認が必要な境界を、毎回 100% 分離して返すという意味です。

## 使い方

```powershell
python -m devbrain route --task "bug fix with public release risk" --json
python -m devbrain gate --trigger implementation --trigger security --json
python -m devbrain catalog --domain go --json
python -m devbrain skill-sync --json
python -m devbrain closeout --repo . --json
```

## Local SSOT

現行 engineering-brain の local SSOT は `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain` です。`nexus-ai-2045/engineering-brain` は private GitHub mirror / review surface です。詳しくは [Local SSOT](docs/LOCAL_SSOT.md) を参照します。

`dev-brain` からの private recreate については [Migration notes](docs/MIGRATION_NOTES.md)、[engineering-brain cutover plan](docs/ENGINEERING_CUTOVER_PLAN.md)、[private cutover packet](docs/PRIVATE_CUTOVER_PACKET.md) を参照します。

## 初期ゲート

| gate | 目的 |
|---|---|
| fact/source | 事実・推測・不明を分ける |
| scope/write-boundary | 作業範囲、owner、write scope、Type1 risk を固定する |
| TDD/regression | bug fix と実装を test/smoke なしに完了扱いしない |
| security/containment | agent、browser、connector、credential、hook/settings の境界を確認する |
| publication/GitHub visibility | 公開、外部送信、repo public 化、push/PR を人間確認まで止める |
| public path redaction | 実ユーザー名を含むローカル絶対パスを公開候補 artifact に残さない |

## Autopilot goal design

`engineering-brain / engineering-autopilot` の発展形は [Autopilot goal design](docs/AUTOPILOT_GOAL_DESIGN.md) にまとめています。設計、リサーチ、TDD、実装、検証、PR、人間レビュー、merge、branch/worktree cleanup までを 1 つの run packet として扱うための状態機械です。

Repo-owned skill source は `skills/engineering-autopilot/` にあります。runtime install copy は `<USER_HOME>/.codex/skills/engineering-autopilot` へ同期済みです。差分は `python -m devbrain skill-sync --json` で確認します。

Contribution / PR の境界は [Contributing](CONTRIBUTING.md) と `.github/` templates を参照します。

直近の実装順序は [Next goal design](docs/NEXT_GOAL_DESIGN.md) を参照します。

## ADR / knowledge intake

設計判断は [ADR](docs/adr/README.md) に残します。Obsidian や local memory は正本ではなく入口として扱い、採用済みの知見だけを [Knowledge intake](docs/KNOWLEDGE_INTAKE.md) の流れで docs / registry / tests / ADR / skill source へ昇格します。

Vision、GitHub、X、Web 上の他者の詰まりや解決策は [Community learning intake](docs/COMMUNITY_LEARNING_INTAKE.md) の source packet として扱います。

ブラウズ中に良いと思ったものや Obsidian に落とした note を採用する時は、[Field review loop](docs/FIELD_REVIEW_LOOP.md) で local experiment と human field review を通します。

実行結果とレビューを次の gate / docs / registry / tests へ戻す仕組みは [PDCA feedback loop](docs/PDCA_FEEDBACK_LOOP.md) を参照します。

必須概念がどこまで入っているかは [Concept coverage](docs/CONCEPT_COVERAGE.md) を参照します。

## 技術別ベスプラ catalog

`registry/technology-sources.yaml` に Go、Bun、Vue/Nuxt、Azure、サーバー/API、コンテナ/Kubernetes、GitHub repo lifecycle の公式・一次情報 source を `candidate` として登録しています。

これは「採用済み保証」ではなく、実プロジェクトへ入る前の source catalog です。`devbrain catalog --domain <domain> --json` で対象 domain の source と gate hint を確認します。

## 完了判定

`closeout` は次を分けて返します。

- `implementation`: 実装差分や構成があるか
- `verification`: test / compile / smoke が揃うか
- `operation`: 継続運用に必要な gate が揃うか
- `external_public`: 公開・外部送信・GitHub visibility などの人間承認境界
- `public_path_redaction`: `<PROJECTS_ROOT>` / `<USER_HOME>` / `<REPO>` へ置換されているか

## 公開境界

この repo は private-first です。public 化、release、外部告知、広範な共有は実行しません。実行する場合は、対象 repo、見える内容、secret scan、README、LICENSE、SECURITY.md、公開可否を提示して current conversation の明示承認を取ります。

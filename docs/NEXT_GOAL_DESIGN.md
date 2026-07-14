# Next Goal Design

status: draft
owner: nexus_ai
checked_at: 2026-07-15 JST

## 結論

次のゴールは、`engineering-brain` を「読む repo」から「毎回の開発 run を組み立てる repo」へ進めること。

その中心は `run packet` である。task を受けたら、SSOT、write scope、candidate research、車輪の再発明チェック、TDD、verification、human stopline、PR packet を 1 つの JSON 相当へまとめる。

## 目指す状態

```text
user task
  -> devbrain run
  -> run packet
  -> candidate / adopted gate selection
  -> research and reinvention decision
  -> TDD and verification plan
  -> implementation evidence
  -> PR packet
  -> human-approved merge / cleanup plan
```

## 設計原則

1. 毎回 `reinvention_check` を走らせる。
2. candidate は広く拾うが、adopted とは分ける。
3. AI は `reuse / wrap / extend / adopt_oss / build / hold` を提案してよい。
4. 採用・公開・merge・設定変更・credential・production 変更は human stopline を越えない。
5. raw chat log、Obsidian note、X post、GitHub issue、Web 記事はそのまま入れず、採用 packet に圧縮する。
6. Vision / memory / official docs / primary source / repo-local truth / GitHub / X / Web evidence を source として区別する。
7. まずは local-first。cloud / external mutation は計画だけ作り、実行は別承認。

## 次の PR sequence

| PR | 目的 | 成果物 | Done |
|---:|---|---|---|
| 3 | run packet MVP | `schemas/run-packet.schema.json`, `devbrain/run_packet.py`, `devbrain run --task ... --json` | route / gate / closeout / human stopline が 1 packet に入る |
| 4 | research packet | `schemas/research-packet.schema.json`, `devbrain/research.py` | candidate source と decision が `hold` 可能になる |
| 5 | local learnings registry | `registry/local-learnings.yaml`, schema, intake tests | local struggle を rule / failure pattern として吸収できる |
| 6 | PR packet generator | `devbrain/review.py`, PR body template | visible scope / checks / unknown / stopline を日本語で生成できる |
| 7 | community learning intake | `docs/COMMUNITY_LEARNING_INTAKE.md`, source packet importer | Vision / GitHub / X / Web の詰まりを candidate 化できる |

## PR 3: run packet MVP

最初に作るべき最小実装。

入力:

```powershell
python -m devbrain run --task "implement small feature" --json
```

出力:

```json
{
  "task": "implement small feature",
  "repo": "<REPO>",
  "mode": "implement",
  "selected_gates": [],
  "candidate_gates": [],
  "reinvention_check": {
    "required": true,
    "decision": "hold",
    "reason": "research packet not yet attached"
  },
  "verification_plan": [],
  "human_stoplines": [],
  "external_actions": {
    "allowed": false,
    "reason": "current-turn approval required"
  }
}
```

MVP では外部 search を自動実行しない。まず packet 形を固める。

## PR 4: research packet

research packet は candidate を拾うための器。

見る順番:

1. repo-local truth: docs、ADR、registry、tests、CLI。
2. workspace-local: shared scripts、既存 skill、Documents/FDE 正本。
3. official / primary source: 言語、framework、SDK、cloud、OpenAI / GitHub / Azure docs。
4. GitHub evidence: upstream repo、release、issues、PR、security、license、CI。
5. local fit: Windows、private-first、secret/public boundary、既存依存。

AI が判断してよい範囲:

- `reuse`: 既存で足りる。
- `wrap`: 既存を薄く包む。
- `extend`: 既存に小さく足す。
- `adopt_oss`: OSS を採用候補にする。
- `build`: 自作が必要。
- `hold`: 不明、最新性不足、security 不明。

## PR 5: local learnings registry

ローカルで悩んだことや発見は、次の単位に圧縮して入れる。

```yaml
- id:
  source: vision|memory|obsidian|github|x|web|pr_review|failure_log|manual
  problem:
  reusable_rule:
  applies_when:
  evidence:
  adoption_target: docs|registry|tests|skill|adr
  status: candidate|adopted|hold|rejected
```

入れないもの:

- raw chat log
- secret / credential
- 実ユーザー名入り絶対パス
- 検証不能な印象

## PR 6: PR packet generator

PR 前に次を自動で揃える。

- 何を変えたか。
- 何が外から見えるか。
- 検証結果。
- 未確認。
- human stopline。
- merge / cleanup は承認待ちか。

## Human / AI responsibility

| 判断 | AI がしてよいこと | human gate |
|---|---|---|
| candidate 探索 | 広く拾い、source と risk を分類する | 不要 |
| 採用提案 | `reuse / wrap / extend / adopt_oss / build / hold` を提案する | high-risk は必要 |
| repo への採用 | test / docs / registry として PR 化する | PR review |
| merge | readiness を測る | current-turn merge OK |
| public 化 | packet を作る | repo ごとの exact yes |
| credential / auth / settings | plan と risk を出す | exact yes |

## Current stoplines

- `engineering-autopilot` runtime install copy はまだ切り替えない。
- public 化はしない。
- cloud / production mutation はしない。
- Obsidian からの自動取り込みは read-only candidate packet まで。
- candidate gate は advisory。採用済み gate と混ぜない。
- Machine-readable rule: candidate gate is advisory.

## Success metric

次の 4 PR が入ると、`engineering-brain` は最低限の self-driving repo と呼べる。

- run packet が出る。
- research / reinvention の判断が packet に残る。
- local learning を candidate として蓄積できる。
- PR body が evidence と stopline を持つ。

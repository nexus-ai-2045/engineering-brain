# Field Review Loop

status: draft
owner: nexus_ai
checked_at: 2026-07-15 JST

## 目的

ブラウズ中に「これは良い」と思った知見、Obsidian 拡張でローカル vault に落とした note、外部 community learning intake の candidate を、実際にローカルで試し、人間が実地レビューしてから `engineering-brain` に採用する。

この loop は、机上の best practice をそのまま信じないための現場検証である。

## Flow

```text
browser discovery
  -> Obsidian capture
  -> candidate packet
  -> local experiment plan
  -> local trial
  -> human field review
  -> adopt / hold / reject
  -> docs / registry / tests / ADR
```

## Step 1: Browser discovery

ブラウザで見つけた情報は、その場で採用しない。

記録するもの:

- source URL / title / author / published or updated date
- 何が良さそうか
- どの問題に効きそうか
- どの repo / workflow で試せそうか
- その場で気になる risk

保存しないもの:

- 長い本文コピー
- credential / private URL / personal data
- X post や blog の長い引用

## Step 2: Obsidian capture

Obsidian 拡張や Web clipper で落とした note は、raw intake として扱う。

Obsidian note から repo に入れる時は、次へ圧縮する。

```yaml
source_lane: obsidian
source_pointer: "<vault note pointer or source URL>"
observed_problem:
candidate_solution:
why_interesting:
local_trial_target:
privacy_check:
decision: candidate
```

Obsidian note 自体は SSOT ではない。SSOT は repo 内の docs / registry / tests / ADR である。

## Step 3: Candidate packet

candidate packet は、実験前の仮説である。

```yaml
id:
source_lane: browser|obsidian|github|x|web|memory|vision
source_pointer:
hypothesis:
expected_effect:
trial_scope:
risk:
stopline:
decision: candidate|hold
```

## Step 4: Local experiment plan

ローカルで試す時は、最初に小さい実験計画を作る。

```yaml
experiment:
  target_repo:
  baseline:
  command_or_manual_steps:
  success_signal:
  failure_signal:
  rollback:
  timebox:
  data_boundary:
```

必須:

- production data を使わない。
- secret / credential / billing / cloud mutation は別承認。
- rollback できる範囲で試す。
- Windows / local-first 条件を明示する。

## Step 5: Local trial

実行したら、効果と摩擦を分けて記録する。

```yaml
trial_result:
  commands_run:
  observed_effect:
  developer_friction:
  failure_or_surprise:
  changed_files:
  tests_or_smoke:
  time_cost:
  confidence: low|medium|high
```

`observed_effect` は、気分ではなく、できるだけ実測にする。

例:

- test が増えた / 落ちた / 通った。
- 作業時間が減った。
- 誤操作が防げた。
- review comment が減った。
- rollback が簡単になった。

## Step 6: Human field review

人間レビューは PR 画面だけではなく、実地で行う。

見ること:

- 実際の作業で邪魔にならないか。
- 説明なしで使えるか。
- 逆に判断を鈍らせないか。
- AI が誤採用しやすくならないか。
- local / private / public boundary が守られるか。
- 次も使いたいか。

review packet:

```yaml
human_field_review:
  reviewer:
  scenario:
  what_worked:
  what_failed:
  keep:
  change:
  decision: adopt|hold|reject
  reason:
```

## Decision

| decision | 条件 | 次 action |
|---|---|---|
| `adopt` | local trial と human field review の両方で有効 | docs / registry / tests / ADR に入れる |
| `hold` | 面白いが効果や安全性が不足 | source pointer と experiment result だけ残す |
| `reject` | 効果なし、危険、摩擦が大きい | 採用しない |

## Repo adoption target

| result | target |
|---|---|
| rule | `registry/local-learnings.yaml` |
| repeated gate | `engineering_brain/data/adoption-units.yaml` |
| workflow | `docs/*.md` |
| irreversible design decision | `docs/adr/ADR-*.md` |
| regression | `tests/` |
| runtime entry | `skills/engineering-autopilot/` |

## Stoplines

- Browser / Obsidian / X / GitHub から raw dump しない。
- private note を外部 AI に送らない。
- external write しない。
- public 化しない。
- credential / auth / cloud / production mutation は別承認。
- human field review なしに `adopted` へ昇格しない。

## Done

field review loop が機能していると言えるのは、次を満たす時。

- browser discovery と Obsidian capture が candidate packet に圧縮される。
- local experiment plan がある。
- local trial の実行手順と効果が記録される。
- human field review が `adopt|hold|reject` を決める。
- adopted の場合は docs / registry / tests / ADR のどれかに接続される。
- Field review の結果は [PDCA feedback loop](PDCA_FEEDBACK_LOOP.md) の `Check` と `Act` に戻す。

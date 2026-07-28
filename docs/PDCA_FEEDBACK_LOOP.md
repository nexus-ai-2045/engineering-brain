# PDCA Feedback Loop

status: active
owner: nexus_ai
checked_at: 2026-07-28 JST

## 目的

`engineering-brain` は、知見を集めるだけでなく、実行結果とレビューを次の gate / docs / registry / tests へ戻す。

PDCA は、candidate を採用するかどうかの判断だけではなく、採用後に本当に効いたかを見直し、repo 自体を育てる feedback loop である。

## Loop

```text
Plan
  -> Do
  -> Check
  -> Act
  -> next Plan
```

## Plan

作業前に次を固定する。

```yaml
plan:
  task:
  target_repo:
  source_packet:
  hypothesis:
  expected_effect:
  selected_gates:
  candidate_gates:
  verification_plan:
  human_stoplines:
  rollback:
```

必須:

- `reinvention_check` を含める。
- adopted / candidate / hold を分ける。
- expected effect を書く。
- human stopline を書く。

## Do

小さく実行する。

```yaml
do:
  commands_run:
  files_changed:
  local_trial:
  tests_or_smoke:
  skipped_steps:
  reason_for_skip:
```

禁止:

- production / cloud / credential / public mutation を current-turn approval なしに実行する。
- raw source を大量に保存する。
- 任意 shell 実行を policy なしに広げる。

## Check

結果を見る。

```yaml
check:
  expected_effect_met: true|false|partial
  evidence:
  test_result:
  human_field_review:
  regressions:
  friction:
  surprises:
  confidence: low|medium|high
```

見るもの:

- test / compile / smoke / closeout。
- local trial の実感ではなく観測された効果。
- 人間実地レビュー。
- 失敗、摩擦、想定外。
- path / secret / public boundary。

## Act

学びを repo に戻す。

```yaml
act:
  decision: adopt|hold|reject|revise
  update_targets:
    - docs
    - registry
    - tests
    - adr
    - skill
  follow_up_pr:
  residual_risk:
```

Act の原則:

- 同じ失敗をもう一度人間が覚えなくていい形にする。
- repeated failure は test / gate / checklist に昇格する。
- useful pattern は docs / registry / skill entry に昇格する。
- irreversible decision は ADR に残す。
- 効果不明なら `hold` に戻す。

## Feedback Sources

| source | Check で見ること | Act の候補 |
|---|---|---|
| test failure | 再現条件、root cause | regression test / gate |
| PR review comment | 人間が見つけた抜け | checklist / PR packet |
| local trial | 実際の摩擦、効果 | docs / local learning |
| field review | 使いやすさ、判断の鈍り | adopt / revise / reject |
| incident / near miss | stopline 不足 | ADR / security gate |
| external candidate | 裏取り結果 | research packet / hold |

## Learning Ledger

将来 `registry/local-learnings.yaml` を追加したら、PDCA の Act は次の形に畳む。

```yaml
- id:
  source: pdca|field_review|pr_review|test_failure|incident|external_candidate
  plan:
  do:
  check:
  act:
  status: candidate|adopted|hold|rejected
  linked_pr:
```

## Integration Points

| phase | connection |
|---|---|
| `run packet` | Plan / Do / Check / Act の最小 fields を持つ |
| `research packet` | Plan の source と hypothesis になる |
| `field review loop` | Check の human evidence になる |
| `closeout` | Check の machine evidence になる |
| `PR packet` | Act の update target と residual risk を出す |
| `ADR` | Act で不可逆判断を記録する |

## FDEとの受け渡し

FDEはrouting、scope、owner、risk、human gateを担当し、`engineering-brain`はPlan / Do / Check / Actの実行証拠を担当する。両者の受け渡しには`fde.feedback.v1`を使う。

```powershell
python -m devbrain feedback --input <feedback.json> --json
```

このcommandはpacketをread-onlyで検証し、`act.next_plan_input`とCheckの型付きevidence pointerだけを`engineering-brain.next-plan.v1`へ圧縮する。raw chat、raw tool output、会話履歴全体は次Planへ再投入しない。`next_plan_input`は1000文字以内とし、個人ホーム絶対パスを拒否する。

互換schemaはpackage resourceの`devbrain/fde-feedback-packet.schema.json`に置く。正本はFDE repositoryの`schemas/fde_feedback_packet.v1.schema.json`であり、互換性を壊す変更は新しいschema versionで行う。

## Stoplines

- Check なしに Act しない。
- human field review なしに `adopted` へ昇格しない。
- failed experiment を消さない。`hold` / `reject` として学習に戻す。
- public / external / credential / cloud / production mutation は別承認。
- secret、private URL、個人絶対パスを ledger に残さない。

## Done

PDCA feedback loop が機能していると言えるのは、次を満たす時。

- Plan が expected effect と verification plan を持つ。
- Do が実行手順を残す。
- Check が machine evidence と human field review を分ける。
- Act が docs / registry / tests / ADR / skill のどこへ戻すかを決める。
- 次の Plan で過去の Act を参照できる。

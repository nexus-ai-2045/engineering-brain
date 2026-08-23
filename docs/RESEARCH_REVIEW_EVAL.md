# Research & Review Eval

## 目的

Research & Review Runtime が、対象タスクにおいて素の GPT-5.6 Sol へそのまま渡す方式より有効かを、同じ課題と評価軸で比較する。

「一般知能で Sol を超えた」とは主張しない。障害切り分け、依存選定、性能改善、リファクタ判断、build versus reuse、ベストプラクティス採否など、engineering-brain が扱う範囲だけを評価する。

## 比較arm

| arm | 役割 |
|---|---|
| `sol_direct` | Sol直渡しの対照群 |
| `sol_prompt` | Sol＋良質な単発prompt |
| `sol_runtime` | Sol＋Research & Review Runtime |
| `terra_runtime` | Terra＋Runtime。安価な構成でSol直渡しを超えられるかを見る |

toolの有無による差をRuntimeの効果と誤認しないよう、各armの`tool_profile`を揃える。

## dataset

suiteは`development`、`validation`、`held_out`へ分ける。最終判断はheld-outだけで行い、比較実行後にdatasetや閾値を書き換えない。

初期suiteは形式と実行経路を検証するseedであり、統計的有意差を主張できる件数ではない。実運用へ昇格する前に、実案件由来の匿名化case、反例、難易度別caseを追加する。

`research-review-v2.json` は、障害切り分け、依存選定、性能改善、リファクタ判断の8課題を持つpilotである。正解、重大な見落とし、禁止判断は、この配布repoやrun manifestへ保存しない。ground truthは別ACLのreview owner保管領域へ置き、`schemas/eval-ground-truth.schema.json` で検証する。

v2の契約は次のschemaで固定する。

- `schemas/eval-suite-v2.schema.json`
- `schemas/eval-ground-truth.schema.json`
- `schemas/eval-review-result.schema.json`
- `schemas/eval-run-artifact.schema.json`

## metrics

- `task_success`: 要求された判断・成果を満たした割合
- `citation_support`: 引用が主張を実際に支える割合
- `human_win`: blind pairwise human reviewで選ばれた割合
- `critical_misses`: 重大な見落としの総件数。平均で薄めない
- `boundary_violations`: 承認・公開・削除などの境界違反の総件数。品質点とは別のhard gate
- `latency_ms`: 応答時間。平均に加えてp50とp95を保持
- `cost_usd`: 比較runの費用

LLM graderだけで合格を決めない。決定的テスト、source確認、blind human reviewを組み合わせる。

v2は小規模pipeline pilotであり、「Sol直渡しより優れる」という確証には使わない。本評価件数はpilotで得た効果量と分散を基に決める。

## commands

比較計画を確認する。

```powershell
python -m engineering_brain eval-plan `
  --suite engineering_brain/data/eval-suites/research-review-v1.json `
  --json
```

held-outのcase×armとsuite digestを固定する。これはrunnerを起動しない。

```powershell
python -m engineering_brain eval-manifest `
  --suite engineering_brain/data/eval-suites/research-review-v1.json `
  --run-id rr-YYYYMMDD-seed `
  --json > run-manifest.json
```

保存先やAPIなしで、評価pipelineの構造だけをE2E smokeする。

```powershell
python -m engineering_brain eval-smoke `
  --suite engineering_brain/data/eval-suites/research-review-v1.json `
  --run-id rr-smoke-local `
  --json
```

このcommandはsynthetic fixtureだけを使い、manifest生成、blind review生成、manifest-bound result import、採点を順に通す。`status: pass`は配線の成功だけを意味し、model品質、Sol直渡しへの優位、統計的有意差を一切証明しない。出力は`synthetic_only: true`、`performance_measured: false`、`api_calls_performed: false`を必ず持つ。

runnerが保存した全case×armの出力から、arm名を含まないblind review packetとanswer keyを生成する。

```powershell
python -m engineering_brain eval-blind `
  --suite engineering_brain/data/eval-suites/research-review-v1.json `
  --outputs <OUTPUTS_JSON> `
  --run-id rr-YYYYMMDD-seed `
  --json > blind-review-bundle.json
```

blind review担当者へ渡すのは`review_packet`だけとし、`answer_key`はreview完了まで別ownerが保管する。CLIはbundleを同じJSONへ出すため、配布前の物理分離は呼び出し側の責務である。回答本文に自らmodel名やarm名が含まれる場合、CLIは本文を改変しないため、blind性は保証できない。

全case×armの結果JSONを採点する。

```powershell
python -m engineering_brain eval-score `
  --suite engineering_brain/data/eval-suites/research-review-v1.json `
  --results <RESULTS_JSON> `
  --manifest run-manifest.json `
  --json
```

`--manifest`を指定すると、結果行の`run_id`と`suite_sha256`をmanifestへ照合する。manifestなしの採点は既存データ互換用であり、新しい比較runでは指定を必須運用とする。

## 保証境界

`eval-plan`と`eval-manifest`はplan-onlyであり、モデルAPIを呼ばない。`eval-blind`と`eval-score`も保存済みJSONだけを処理する。API課金、外部送信、dataset変更後の再採点、adopt、push、PR作成は別の人間承認境界である。

`eval-score`がpassでも、統計的有意差、human reviewの独立性、実運用適合は自動では保証しない。結果は`candidate_for_human_review`に留め、人間レビュー後に採否を決める。

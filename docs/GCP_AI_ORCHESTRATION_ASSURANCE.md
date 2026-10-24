# GCP AIオーケストレーションとOCR評価の保証

status: adopted
updated: 2026-07-18

## 成功の証明鎖

以下は公式仕様と実障害から採用したengineering-brainの推奨設計であり、Google Cloud製品が自動提供する保証ではない。

非同期AI処理は、次の値を同一runへ束縛して初めて成功とする。

`execution_id / run_id / candidate / attempt / cloud job resource / input generation+hash / output generation+hash / target schema / GT metrics / cost ledger`

`Workflow ACTIVE`、HTTP 2xx、Vertex job `SUCCEEDED`、JSON parse成功、`_SUCCESS`存在、SHA一致は、それぞれ単独では完了証拠にならない。

## Preflight

`Billing Budgetはhard capではない`、`parallel concurrency limitは子階層へ自動継承されない`、`Workflow cancelだけでVertex jobは停止しない`は公式仕様に基づく事実。費用予約ledger、共有semaphore、cancel sagaは、それらを補う本repoの推奨設計。

- Workflow execution開始経路と固定control endpointが存在する。
- private serviceはOIDC、固定audience、専用service account、最小Invokerで接続する。
- synthetic-onlyを必須値として検証し、欠落時は拒否する。
- heldoutは通常PDCAのbucket、service account、image、Workflowから物理的に到達不能にする。
- GPU quota、region、API、GCS、immutable image/model revisionをread-onlyで確認する。
- Billing Budgetは通知でありhard capではない。発射前にworst-case費用をrun ledgerへ予約する。

## 実行と補償

- 副作用のあるjob createは、`run_id+stage+candidate+attempt`を永続化してから限定retryする。
- `concurrency_limit`は子階層へ継承される前提にせず、共有semaphoreで全ACTIVE GPU数を制限する。
- Workflow停止時は、発射済みjobを個別cancelし、terminal状態を再取得する。
- callback URLをログへ出さない。run、nonce、期限、候補digestを照合し、再利用を拒否する。
- markerはimmutable prefixへCAS作成し、run、attempt、入力、出力generation、digestを含める。

## TDD、smoke、E2E

1. Unit: schema、idempotency key、費用予約、marker検証、retry predicate、cancel plan。
2. Smoke: synthetic 1件でexecutionからjob terminal、marker、schema、metricまで追跡。
3. Integration: success/failure混在、429/503、create timeout、stale marker、hash不一致、重複callback。
4. E2E: 全体8並列上限、部分失敗時の次stage禁止、全job terminal、費用reconcile。

実行0件はidleではなく、起動を期待するrunではpreflight failureとする。

## OCRと構造化出力

各metricの定義は参照OSS・論文に基づく。組み合わせ順とzero-tolerance gateは本repoの推奨設計。

- 評価をJSON構文、JSON Schema、field意味精度、明細行対応、表構造、confidence校正、劣化耐性へ分離する。
- missingをFN、unknown fieldをFPとしてmicro/macro/key-wise F1を残す。
- critical field exact、明細alignment、TEDS/GriTS、ECE、risk-coverage、worst-sliceを併記する。
- confidence自己申告だけでacceptしない。overconfident-wrongを独立指標にする。
- hard subsetはfailure taxonomy別に層化し、base replayを残す。反復利用するhard-devとfinal heldoutを分離する。
- teacherはlabel生成、採否、judgeを兼任させない。generator GTまたは人手goldを独立anchorにする。
- 量子化後の実artifact digestごとに精度、cold/warm latency、p50/p95、VRAM、sizeを測りParetoを残す。

## トートロジー検査

以下の言い換えだけで成功を証明していないか確認する。

- deployedだからrunnable
- 2xxだから処理成功
- job終了コード0だからモデル正解
- JSONだから目的schema
- schema適合だから意味正解
- markerがあるから現在attempt成功
- SHA一致だからprovenance正当
- confidenceが高いから正しい
- budget設定済みだから上限保証
- Workflow cancel済みだからGPU停止済み

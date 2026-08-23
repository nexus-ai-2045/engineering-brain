---
title: 鮮度・証拠パターン比較
type: reference
status: active
recorded_at: 2026-07-30T14:52:10+09:00
recorded_by: codex
schema_version: fact-provenance/v1
---

# 鮮度・証拠パターン比較

比較に使用した公式原資料ごとの日本語要約は [鮮度・証拠設計 公式資料 日本語要約](FRESHNESS_EVIDENCE_OFFICIAL_SOURCES_JA.md) を参照する。

## 結論

「ライブ測定」を一つの仕組みとして実装するのではなく、目的に応じて次を組み合わせる。

1. point-in-time revalidation（回答直前の再確認）
2. artifact-bound status check（特定commit・artifactに束縛した検証）
3. reconciliation loop（期待状態と現在状態の差分修復）
4. monitoring（既知の指標の継続収集）
5. observability（未知の問題を調べられるテレメトリ）
6. continuous monitoring（セキュリティ・統制状態の継続評価）
7. black-box / white-box monitoring（外部挙動と内部状態の二面観測）

これらは代替関係ではない。観測、判定、修復、統制という別の責務を持つ。

## 違い

| pattern | 主な問い | 良さ | 弱点・誤用 | 適する例 |
|---|---|---|---|---|
| point-in-time revalidation | 「今この瞬間どうなっているか」 | 安価で説明しやすく、回答時点のstale情報を減らす | snapshotなので直後に古くなる。継続変化や原因は分からない | `git fetch`後のahead/behind、現在の価格・件数、PR状態 |
| artifact-bound status check | 「この正確な版は検証済みか」 | 証拠をcommit SHAやartifact digestへ束縛し、古い成功結果の流用を防ぐ | 検査対象外の品質や、deploy後のruntimeまでは証明しない | latest HEADのCI、署名、評価suite digest |
| reconciliation loop | 「期待状態との差をどう埋め続けるか」 | driftや一時障害へ自己修復的に対応できる | desired stateが誤っていると誤状態へ収束する。破壊操作、振動、retry増幅への防御が必要 | replica数、設定projection、skill同期 |
| monitoring | 「既知の指標は正常範囲か」 | trend、閾値、alert、容量計画に強い | 測っていない問題は見えない。alert fatigueや高cardinality costがある | error rate、latency、CPU、queue長 |
| observability | 「なぜ起きたか。未知の問題を調べられるか」 | traces・metrics・logsを相関し、unknown unknownの調査に強い | instrumentationと保存costが必要。観測できても自動修復や合否判定は別 | 分散requestの遅延原因、断続的障害 |
| continuous monitoring | 「統制・リスク状態が継続的に許容範囲か」 | 資産・security control・riskを経時的に追跡し、監査判断へ接続できる | 全項目をreal-timeに見る意味ではない。形式的収集だけでは保証にならない | software inventory、security posture、compliance |
| black-box monitoring | 「利用者から見て動くか」 | 内部実装に依存せず、実際の利用可能性を検証できる | 原因特定が弱く、深い経路を網羅しにくい | HTTP smoke、ログイン、購入flow |
| white-box monitoring | 「内部のどこで何が起きているか」 | 原因候補と内部飽和を早く絞れる | 内部指標が正常でも利用者体験が壊れる場合がある | cache hit率、DB pool、GC、内部queue |

## 方式ごとの本質

### 1. Point-in-time revalidation

これは最小のfreshness gateである。保存済み記録を現在値として再利用せず、回答または操作の直前に一次sourceを読む。

必須metadata:

- `observed_at`
- `source`
- `scope`
- 対象identity
- 取得不能時の`unknown`

「一度確認したので以後も正しい」という保証はしない。

### 2. Artifact-bound status check

GitHubのrequired status checkは、以前のcommitのcheckではなく、最新の関連commit SHAに対する成功を要求する。engineering-brainでは同じ原則を次へ適用する。

- code: commit SHA
- build: artifact digest
- model evaluation: suite digest + run ID
- documentation review: reviewed head SHA

`passed`だけでなく「何に対してpassしたか」を証拠の一部にする。

### 3. Reconciliation loop

Kubernetes controller型の設計である。

```text
desired state
  -> observe current state
  -> compute diff
  -> apply bounded action
  -> observe again
```

採用条件:

- desired stateが宣言的かつversioned
- 操作がidempotent
- retry上限、backoff、circuit breakerがある
- 削除・公開・課金などは自動reconcile対象外
- current stateを再観測してから完了する

### 4. Monitoring

既知の質問へ継続的に答える。主役は時系列metricsとalertである。

強い問い:

- error rateは増えているか
- latencyはSLOを超えたか
- queueは詰まっているか

弱い問い:

- なぜこの一件だけ失敗したか
- 想定していなかった経路で何が起きたか

### 5. Observability

OpenTelemetryは、traces、metrics、logsなどのsignalを生成・収集・exportする標準化された枠組みを提供する。observabilityは「正常か」を判定するgateではなく、「外部出力から内部状態を理解し、未知の問題を調査できる能力」である。

engineering-brainでは、実行packetへ次を相関可能なidentityとして持たせる。

- task / run ID
- commit SHA
- suite digest
- tool / model profile
- start / finish time
- result / evidence path

### 6. Continuous monitoring

NIST型のcontinuous monitoringは、security・privacy・asset・risk状態を継続的な意思決定へ供給する。全項目を秒単位で取得することではなく、リスクに応じた頻度と信頼できる収集経路が重要である。

単なる定期実行では不足する。少なくとも次を持つ。

- owner
- cadence / trigger
- evidence path
- success / failure condition
- stale判定
- failure時の通知・再オープン

### 7. Black-boxとwhite-box

Google SREの区分では、black-boxは利用者から見える挙動を、white-boxは内部metrics・logs・interfacesを観測する。

優劣ではなく二重化する。

```text
black-box: 実際に使えるか
white-box: なぜそうなっているか
```

black-boxだけでは原因が弱く、white-boxだけでは利用者影響を見落とす。

## engineering-brainへの推奨レイヤ

| layer | contract | 自動化 |
|---|---|---|
| L0 Provenance | source、actor、event time、observed time、scope、unknownを記録 | 常時 |
| L1 Fresh Read | 回答・判断直前に変化しやすい現在値を再取得 | read-onlyで自動 |
| L2 Bound Check | SHA / digest / run IDへtest・review・evalを束縛 | local / CIで自動 |
| L3 Runtime Evidence | smoke、black-box、white-box、telemetryを分離 | risk-based |
| L4 Reconciliation | 安全で可逆なdriftだけを収束 | allowlist内で自動 |
| L5 Continuous Assurance | security・asset・運用保証をcadence付きで継続確認 | report / notify |
| Human Gate | 公開、外部送信、課金、削除、visibility、production変更 | current conversation承認 |

ユーザー向け表示では「ライブ測定」とまとめず、実際に行った操作を表示する。

例:

- 「2026-07-30 14:52 JSTにGitHub APIでPR状態を再確認」
- 「現在HEAD `abc1234`に対してtestを再実行」
- 「runtimeのHTTP smokeは成功、内部telemetryは未確認」
- 「automationへfuture-only確認を移管。期限と証跡先を記録」

## 公式sourceと事実来歴

| classification | source | actor | event_time | observed_at | scope | 採用した事実 |
|---|---|---|---|---|---|---|
| fact | https://kubernetes.io/docs/concepts/architecture/controller/ | Kubernetes documentation | unknown | 2026-07-30T14:52:10+09:00 | controller pattern | controllerはcurrent stateを観測し、desired stateへ近づけるcontrol loop |
| fact | https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks | GitHub documentation | unknown | 2026-07-30T14:52:10+09:00 | required status checks | required checkは最新の関連commit SHAに対して成功が必要 |
| fact | https://sre.google/sre-book/monitoring-distributed-systems/ | Google SRE | unknown | 2026-07-30T14:52:10+09:00 | monitoring terminology | monitoring、black-box、white-boxの区分 |
| fact | https://opentelemetry.io/docs/concepts/observability-primer/ | OpenTelemetry documentation | 2026-04-23 | 2026-07-30T14:52:10+09:00 | observability | 外部出力から内部状態を理解し、未知の問題を調査する能力 |
| fact | https://opentelemetry.io/docs/concepts/signals/metrics/ | OpenTelemetry documentation | unknown | 2026-07-30T14:52:10+09:00 | runtime metrics | metric eventは値、取得時刻、metadataを持つ |
| fact | https://csrc.nist.gov/pubs/pd/2015/09/16/software-asset-management-continuous-monitoring/final | NIST | 2015-09-16 | 2026-07-30T14:52:10+09:00 | continuous monitoring | endpointのcurrent stateについてtimelyでaccurateな情報を提供 |

## 未確認・非事実

- `live measurement`が業界全体で一切使われないという網羅証明はしていない。
- 「鮮度・証拠ゲート（Freshness & Evidence Gate）」はengineering-brain向けの提案名であり、業界標準語ではない。
- 各patternの採用範囲と自動化levelは設計提案であり、公式sourceがengineering-brainへの適用を保証するものではない。
- 実runtimeへのhook・hard block・自動reconciliation適用は、この資料の保存には含めない。

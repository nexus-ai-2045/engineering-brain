---
title: 鮮度・証拠設計 公式資料 日本語要約
type: reference
status: active
recorded_at: 2026-07-30T15:03:55+09:00
recorded_by: codex
schema_version: fact-provenance/v1
translation_policy: faithful-summary
canonical_ssot: <PROJECTS_ROOT>/Documents/references/freshness-evidence-official-sources-ja.md
---

# 鮮度・証拠設計 公式資料 日本語要約

## この資料について

鮮度・証拠設計の比較に使用した公式資料を、原資料ごとに日本語で読める形へ整理したもの。

横断リファレンスの正本（SSOT）は `<PROJECTS_ROOT>/Documents/references/freshness-evidence-official-sources-ja.md` である。この文書は engineering-brain 内で利用するための投影版であり、更新判断は正本を起点にする。

- 原文の全文翻訳・転載ではなく、著作権に配慮した忠実な要約翻訳である。
- 原資料が述べている内容と、engineering-brainへの適用提案を分離する。
- 原資料の意味を確認する時は、必ず記載した公式URLを正本とする。
- `observed_at`はCodexが公式ページを再取得した時刻であり、原資料の公開日時ではない。

## 1. Kubernetes Controllers

### 原資料

- title: Controllers
- actor: Kubernetes Documentation
- URL: https://kubernetes.io/docs/concepts/architecture/controller/
- 日本語版: https://kubernetes.io/ja/docs/concepts/architecture/controller/
- event_time: unknown
- observed_at: 2026-07-30T15:03:55+09:00
- scope: controller、control loop、desired stateとcurrent state

### 日本語要約

Kubernetesのcontrollerは、clusterの状態を監視し、必要な変更を実行または要求する制御ループである。それぞれのcontrollerは、現在のcluster状態を期待状態へ近づけようとする。

Kubernetes objectの`spec`は期待状態を表す。controllerは対象resourceを監視し、実際の状態との差を調べる。差があれば、API serverへresourceの作成・更新・削除を要求するか、外部systemへ直接操作を行う。

Job controllerの場合、controller自身がPodを実行するのではない。Jobを完了状態へ近づけるため、API serverへPod作成を要求する。実際の実行はschedulerやkubeletなど別componentが担う。完了後、controllerはJobの現在状態を`Finished`として更新する。

Kubernetesではsystem全体が完全な静止状態へ到達し続けることを前提にしない。systemが変化する中でも、controllerが動作し、期待状態へ近づけ続けられることを重視する。

### 原資料から得られる設計原則

- desired stateとcurrent stateを別に持つ。
- 一度の実行結果ではなく、再観測を含むloopとして設計する。
- controllerは必ずしも処理本体を実行せず、別componentへ要求できる。
- 状態変化を前提とし、継続的な収束を目指す。

### engineering-brainへの適用提案

- skill同期、設定projection、生成artifact更新など、可逆で冪等な処理へ適用する。
- 公開、削除、課金、外部送信は自動reconciliation対象にしない。
- desired stateのversion、再試行上限、backoff、停止条件を必須にする。

この節の「engineering-brainへの適用提案」は原資料の主張ではなく、Codexの設計提案である。

## 2. GitHub Required Status Checks

### 原資料

- title: Troubleshooting required status checks
- actor: GitHub Documentation
- URL: https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks
- event_time: unknown
- observed_at: 2026-07-30T15:03:55+09:00
- scope: protected branch、required check、latest commit SHA

### 日本語要約

required status checkは、protected branchへのmergeやpushを許可する前に、指定された検証が成功していることを要求する仕組みである。

重要なのは、過去のcommitで成功したcheckではなく、最新の関連commit SHAに対してcheckが成功している必要がある点である。以前のcommitに対する成功結果は、最新HEADの要件を満たさない。

branch protectionがbranchの最新化を要求している場合、base branchをmergeまたはrebaseしてからcheckを通す必要がある。test merge commitにcheckが存在する場合はそのmerge commitが、存在しない場合はhead commitが検証対象になる。

required workflowをpath filterなどで起動しない構成にすると、checkが`Pending`のまま残りmergeを妨げる場合がある。一方、job単位のskipは`Success`として扱われる場合があるため、単なるstatus名だけでなく実際のworkflow契約を確認する必要がある。

### 原資料から得られる設計原則

- test結果を対象identityへ束縛する。
- `pass`だけでなく「どのSHAに対するpassか」を記録する。
- base更新後は以前のcheckを流用せず再検証する。
- skip、neutral、successの意味をworkflow設計側で確認する。

### engineering-brainへの適用提案

- code reviewはreviewed head SHAを持つ。
- model評価はsuite digestとrun IDを持つ。
- build検証はartifact digestを持つ。
- staleな証拠を現在HEADの完了証拠へ昇格しない。

## 3. Google SRE Monitoring Distributed Systems

### 原資料

- title: Monitoring Distributed Systems
- actor: Google SRE
- URL: https://sre.google/sre-book/monitoring-distributed-systems/
- event_time: unknown
- observed_at: 2026-07-30T15:03:55+09:00
- scope: monitoring、black-box monitoring、white-box monitoring、alert

### 日本語要約

monitoringは、systemについてのreal-timeな定量dataを収集、処理、集約、表示する活動である。例としてquery件数、error件数、処理時間、server寿命などが挙げられる。

black-box monitoringは、利用者と同じように外部から見える挙動をtestする。質問は「systemは実際に動いているか」である。

white-box monitoringは、system内部が公開するmetrics、logs、runtime interface、HTTP metrics endpointなどを使用する。質問は「内部で何が起きているか」である。

dashboardは、serviceの重要metricsを要約して表示する。alertは、人間が読むことを意図した通知であり、ticket、email、pagerなどへ送られる。すべての異常を人間へ即時通知するのではなく、人間の即応が本当に必要な条件を設計することが重要である。

Google SREは、monitoring用語が組織間だけでなくGoogle内部でも完全には統一されていないことを明記した上で、実務上よく使う意味を定義している。

### 原資料から得られる設計原則

- 利用者視点と内部視点を併用する。
- dashboardとalertを分ける。
- 取得可能なdataを増やすだけでなく、人間を起こす条件を絞る。
- monitoring用語は曖昧になりやすいため、system内で定義する。

### engineering-brainへの適用提案

- black-box: CLI exit code、HTTP smoke、実際のuser flow。
- white-box: logs、step status、tool call、latency、queue、retry。
- `test passed`と`runtime available`を別の証拠面にする。
- alertはactionableでownerとnext actionを持つ場合だけ送る。

## 4. OpenTelemetry Observability Primer

### 原資料

- title: Observability primer
- actor: OpenTelemetry Documentation
- URL: https://opentelemetry.io/docs/concepts/observability-primer/
- event_time: 2026-04-23
- observed_at: 2026-07-30T15:03:55+09:00
- scope: observability、telemetry、traces、metrics、logs

### 日本語要約

observabilityは、system内部の実装をあらかじめ完全に知っていなくても、systemが外へ出す情報から内部状態を理解できる能力である。既知の問題だけでなく、未知の問題を調査し、「なぜ起きているのか」に答えられることを目指す。

そのためにはapplicationをinstrumentationし、traces、metrics、logsなどのsignalを生成させる必要がある。問題が起きるたびに追加instrumentationしなくても調査に必要な情報が得られる状態が望ましい。

metricsは一定期間における数値dataの集約であり、error rate、CPU利用率、request rateなどに向く。

distributed traceは、一つのrequestがgateway、backend、databaseなど複数componentを通過する流れを追跡する。各処理単位をspanとして表現し、親子関係と時間情報によってend-to-endの経路を理解する。

logsはtimestamp付きeventを記録するが、単独では呼び出し文脈が不足する場合がある。traceやspanと相関させることで有用性が高まる。

### 原資料から得られる設計原則

- observabilityは単なるmetric収集ではない。
- traces、metrics、logsを共通contextで相関する。
- unknown unknownを調査できる情報量を設計する。
- telemetry生成にはinstrumentationが必要である。

### engineering-brainへの適用提案

- task ID、run ID、commit SHA、suite digestを共通contextにする。
- stepごとのstart、finish、tool、result pathをtrace相当として扱う。
- observabilityの成功を、品質合格や自動修復成功と混同しない。

## 5. OpenTelemetry Metrics

### 原資料

- title: Metrics
- actor: OpenTelemetry Documentation
- URL: https://opentelemetry.io/docs/concepts/signals/metrics/
- event_time: unknown
- observed_at: 2026-07-30T15:03:55+09:00
- scope: runtime measurement、metric event、aggregation、cardinality

### 日本語要約

metricはruntime中に取得されるserviceの測定値である。metric eventは値だけでなく、取得時刻と関連metadataを持つ。

metric instrumentはname、kind、unit、descriptionなどで定義される。測定値はaggregationによってtime window内の統計値へまとめられる。metricsはrequest個別の完全な経路よりも、全体傾向や統計の把握に向く。

用途にはrequest件数、処理時間、CPU・memory使用量、active request数、data量、平均値などがある。outage alertやautoscaling判断にも利用できる。

cardinalityはattributeの組み合わせ数である。user IDやraw URLなど高cardinalityな値をmetric属性へ無制限に入れると、memory costが増え続ける危険がある。

### 原資料から得られる設計原則

- 測定値には取得時刻とmetadataを持たせる。
- metricsはaggregateされた傾向に強く、個別requestの文脈には弱い。
- name、unit、descriptionを標準化する。
- attribute cardinalityを制御する。

### engineering-brainへの適用提案

- 件数には対象scope、取得時刻、unitを付ける。
- user pathやsecretをmetric labelへ入れない。
- latency、cost、success rateを同じ総合点へ潰さず別metricとして保持する。

## 6. NIST Software Asset Management: Continuous Monitoring

### 原資料

- title: Software Asset Management: Continuous Monitoring
- actor: National Institute of Standards and Technology（NIST）
- URL: https://csrc.nist.gov/pubs/pd/2015/09/16/software-asset-management-continuous-monitoring/final
- event_time: 2015-09-16
- observed_at: 2026-07-30T15:03:55+09:00
- scope: software asset management、continuous monitoring、current state

### 日本語要約

software asset managementはcontinuous monitoringの重要な構成要素である。software inventory dataを標準化された形で収集し、risk-based decision、software mediaの検証、execution allowlisting、inventoryに基づくnetwork access controlなどへ利用する。

Software Identification（SWID）tagは、software単位を記述する標準data formatである。endpoint上のSWID tagを集めることで、computing deviceの現在状態について、適時で正確な情報を得ることを目指す。

組織はこの状態情報を使い、組織resourceへアクセスするsoftwareのassurance levelや、重要業務を支えるsoftwareの状態を判断する。

automationでは、inventory dataを適時に収集できることだけでなく、各endpoint上の収集process自体が信頼できること、安全なtransportでdata交換できることが重要になる。

### 原資料から得られる設計原則

- current stateの収集をrisk decisionへ接続する。
- data formatと収集経路を標準化する。
- dataそのものだけでなく、収集processのtrustworthinessを評価する。
- timelyかつaccurateなinventoryを維持する。

### engineering-brainへの適用提案

- dependency、runtime、skill、model、tool versionをinventory化する。
- automationにはowner、cadence、evidence path、stale条件を持たせる。
- 定期実行した事実だけでcontinuous assuranceを主張しない。

## 横断用語対応

| 原資料の用語 | 日本語での意味 | engineering-brainでの扱い |
|---|---|---|
| current state | 現在観測されている状態 | `observed_at`付きで記録 |
| desired state | 期待する宣言済み状態 | versioned SSOT |
| reconciliation | 差分を継続的に収束させる処理 | 可逆・冪等範囲のみ |
| status check | 特定版に対する検証状態 | SHA / digestへ束縛 |
| monitoring | 既知のsystem状態を継続観測 | metrics、dashboard、alert |
| observability | system出力から内部状態を調査できる能力 | traces、metrics、logsの相関 |
| black-box | 利用者と同じ外部挙動の確認 | smoke / E2E |
| white-box | 内部signalの確認 | logs / metrics / traces |
| continuous monitoring | security・asset・risk状態の継続把握 | cadence、owner、stale判定 |

## 事実と提案の境界

### fact

- 各「日本語要約」は、記載した公式原資料を2026-07-30に取得して要約した。
- Kubernetes、GitHub、Google SRE、OpenTelemetry、NISTは、それぞれ異なる目的で状態・証拠・監視を扱う。

### non_fact: proposal

- 各節の「engineering-brainへの適用提案」。
- これらをL0-L5とHuman Gateへ積層する設計。
- 「鮮度・証拠ゲート」という名称。

### unknown

- 各公式ページの今後の改訂内容。
- ここに挙げていない組織を含む、業界全体での用語使用率。
- 全文翻訳と比較した場合の、細部のニュアンス差。

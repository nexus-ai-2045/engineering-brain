# Community Learning Intake

status: draft
owner: nexus_ai
checked_at: 2026-07-15 JST

## 目的

`engineering-brain` は、ローカルで悩んだ内容だけでなく、Vision、過去 run、GitHub、X、Web 上に落ちている他者の詰まりと解決策も candidate として吸い上げる。

ただし、外部の投稿や issue を raw knowledge として丸ごと保存しない。保存するのは、検証可能な claim、source pointer、再利用可能な rule、採否判断、残リスクである。

## Source lanes

| lane | source examples | default action |
|---|---|---|
| `vision` | Vision / 長期構想 / 過去に書いた方針 | candidate packet |
| `memory` | local memory / rollout summary / 過去の失敗 | candidate packet |
| `obsidian` | raw note / 仮説 / 悩み | candidate packet |
| `github` | issue / PR / discussion / code search / release note | source packet |
| `x` | X post / thread / search result | source pointer only |
| `web` | blog / docs / forum / Stack Overflow | source packet |
| `official` | official docs / API docs / changelog | primary source |

## Intake packet

```yaml
id:
source_lane: vision|memory|obsidian|github|x|web|official
source_pointer:
observed_problem:
proposed_solution:
reusable_rule:
evidence:
freshness:
rights_and_privacy:
adoption_target: docs|registry|tests|skill|adr|hold
decision: candidate|field_review|adopted|hold|rejected
decision_reason:
field_review: pending|in_progress|passed
review_trigger:
assurance_gate:
```

`decision` の alias: intake 文言の `adopt` / `reject` はそれぞれ `adopted` / `rejected` として正規化する。

## Field review / adopt gate

SSOT は `engineering_brain/data/local-learnings.yaml`。FDE が decision OS であり、ここは learning packet の ladder だけを扱う。

| stage | decision | field_review | 意味 |
|---|---|---|---|
| intake | `candidate` | `pending` | 再利用候補。運用保証ではない |
| review | `field_review` | `in_progress` | 実地レビュー中 |
| terminal | `adopted` \| `hold` \| `rejected` | `passed`（adopt 時は必須） | adopt のみ運用保証の候補 |

Fail-closed 規則:

- `field_review: pending` の packet は、decision を `adopted` と書いてあっても **運用保証 / adopted として報告してはならない**。
- 遷移は `candidate -> field_review -> adopted|hold|rejected` のみ。`candidate -> adopted|hold|rejected` の直遷移は拒否する（terminal は field_review 経由）。
- `adopt` は plan / evidence のみ。current-turn の人間承認がなければ apply 扱いにしない。
- CLI: `python -m engineering_brain learnings list|field-review|adopt|assurance`

## 外部 source の扱い

### GitHub

GitHub は、issue、PR、discussion、release、code search を candidate 探索に使う。

見る項目:

- 同じエラーや設計悩みが issue / discussion にあるか。
- workaround が accepted / merged / released されているか。
- repo が保守されているか。
- license と security policy があるか。
- Windows / local-first / private repo 運用に合うか。

### X

X は、短い実体験や最新の詰まりが早く出ることがある一方、文脈不足、削除、誤情報、引用制限、API access の制約がある。

扱い:

- X post 本文を repo に長く保存しない。
- 取り込むのは source pointer、短い claim、検証が必要な仮説だけ。
- X API / browser / connector / credential が必要な操作は human stopline に置く。
- 採用前に official docs、GitHub issue、repo-local reproduction のいずれかで裏取りする。

### Web / forum

Web 上の blog、forum、Q&A は candidate として扱う。採用する時は次を確認する。

- 投稿日と最終更新。
- 対象 version。
- reproducible な条件。
- 公式 docs または実コードで裏取りできるか。
- license / quote / attribution の制約。

## Decision ladder

| decision | 意味 | repo action |
|---|---|---|
| `rejected` | 誤り、古い、対象外 | 採用しない |
| `hold` | 面白いが裏取り不足 | source pointer だけ残す |
| `candidate` | 再利用可能そう | `engineering_brain/data/local-learnings.yaml` か research packet へ |
| `field_review` | 実地レビュー中 | field review loop で検証 |
| `adopted` | 検証済みで繰り返し使う | docs / registry / tests / ADR へ。`field_review: passed` 必須 |

## Safety gates

- secret、token、private URL、個人情報を保存しない。
- 実ユーザー名入り絶対パスを保存しない。
- X や Web の文章を長く引用しない。
- 外部 API credential を作成・変更しない。
- private corpus を外部 AI に送らない。
- 未検証の外部発言を best practice と呼ばない。

## Automation design

自動化してよい:

- query plan の生成。
- read-only search。
- source pointer の収集。
- claim / problem / solution の短い要約。
- duplicate detection。
- `hold` / `candidate` の初期分類。

自動化しない:

- raw source の大量保存。
- 外部投稿者への返信。
- X / GitHub への write。
- public 共有。
- adopted への昇格。

## Field review

外部や Obsidian から拾った candidate は、採用前に [Field review loop](FIELD_REVIEW_LOOP.md) へ通す。

最低限、次を確認する。

- ローカルで小さく試せるか。
- 実行手順が残っているか。
- 実際の効果が観測できたか。
- 人間が実地レビューして `adopt|hold|reject` を決めたか。

## Query families

| target | query examples |
|---|---|
| same error | exact error message, stack trace key phrase |
| design doubt | "why not", "tradeoff", "migration", "production" |
| reliability | "flaky", "timeout", "race condition", "windows" |
| security | "secret leak", "token", "path traversal", "prompt injection" |
| operations | "rollback", "cleanup", "merge conflict", "rate limit" |
| local-first | "offline", "private repo", "local dev", "Windows PowerShell" |

## Done

community learning intake が機能していると言えるのは、次を満たす時。

- Vision / memory / Obsidian / GitHub / X / Web の candidate を同じ packet 形で扱える。
- source pointer と claim が分離される。
- `hold` が自然に選べる。
- adopted へ昇格する時は docs / registry / tests / ADR のいずれかに接続される。
- external write / public / credential は stopline に残る。

## Reference sources

- GitHub REST API docs: search and issue endpoints are suitable for read-only candidate collection when authenticated access and rate limits are handled.
- GitHub code search docs: query terms and qualifiers can narrow code search, but results remain candidate evidence until local fit is checked.
- X API docs: recent search and search operators can collect public post candidates, but access level, bearer token, time range, and attribution/quote limits must be handled as stoplines.

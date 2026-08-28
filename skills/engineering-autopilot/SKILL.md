---
name: engineering-autopilot
description: engineering-brain を通して開発作業を設計し、定番アルゴリズムの選択・比較、既存調査、TDD、実装、検証、運用保証、PR準備、人間レビュー停止線まで進めるときに使う。ユーザーが「自走」「開発ブレイン」「アルゴリズム選定」「比較検討」「ベスプラ確認」「車輪の再発明回避」「PRまで」「運用保証」「ローカルの学びを吸収」と言ったら使う。
---

# Engineering Autopilot

この skill は `engineering-brain` repo の薄い入口です。判断ロジックは skill 内に複製せず、repo の CLI / docs / registry を正本として使います。

## 起動

1. `references/lifecycle.md` を読む。
2. 対象 repo と作業範囲を確認する。
3. canonical `engineering-brain` repo で `python -m engineering_brain --help` を実行し、
   利用可能commandを実測する。
4. `engineering-brain` repo から、現行 CLI で使える gate だけを実行する。
5. `wrap`、`extend`、`adopt_oss`、`build`を判断する前に、
   `$implementation-precedent-research`で先行実装を評価する。

`engineering-brain`という別skillは作らない。これはrepo名であり、Codexからのruntime
入口は`engineering-autopilot`へ一本化する。`engineering_brain`はPython module名として
扱う。helpに出ない未確認のcommandを推測実行しない。

`implementation-precedent-research`の正本は`nexus-ai-skills`が所有する。
engineering-brainはconsumerとして呼び出し、本体を複製しない。利用できないruntimeでは
調査済みと推測せず、research packetの判断を`hold`にして不足証拠を返す。

```powershell
python -m engineering_brain route --task "<task>" --json
python -m engineering_brain gate --trigger implementation --json
python -m engineering_brain catalog --domain <domain> --json
python -m engineering_brain algorithms select --signal <problem-signal> --constraint <constraint> --json
python -m engineering_brain algorithms compare --id <candidate-a> --id <candidate-b> --json
python -m engineering_brain skill-sync --target all --json
python -m engineering_brain run --task "<task>" --domain <domain> --json
python -m engineering_brain verify --repo . --json
python -m engineering_brain pr --repo . --json
python -m engineering_brain closeout --repo . --json
```

## 必須規律

- 作る前に、repo-local / workspace shared / 公式機能 / OSS 候補を確認する。
- 問題をデータ量、順序、更新頻度、厳密性、メモリ、失敗モデルへ分解し、該当シグナルがあれば `algorithms select` で候補を絞る。
- 候補を自動採用しない。`preconditions` と `avoid_when` を実データで確認し、迷う候補は `algorithms compare` で計算量・交換条件・検証法を並べる。
- シグナルが取れない場合は `unknown` のままにし、汎用アルゴリズムを推測採用しない。
- source catalog は採用ではない。`candidate` / `adopted` / `hold` / `rejected` を分ける。
- research packetの`precedent_research`契約に従い、先行実装調査の
  `adopt` / `revise` / `reject` / `hold`を実装判断へ接続する。
- TDD または対象 smoke なしに実装完了と言わない。
- 非同期cloud処理では deploy、HTTP 2xx、job成功、marker存在を完了の代用にせず、executionから成果物・評価・費用・停止補償まで同一runへ束縛する。
- OCR/structured outputでは JSON構文、schema、field意味精度、表構造、校正、劣化耐性、量子化artifact実測を分離する。
- 実行開始を期待するrunで execution 0件は idle ではなく preflight failure とする。
- local で悩んだことは raw chat ではなく、docs / registry / test / ADR のどれかへ薄く吸収する。
- push、PR作成、merge、remote branch削除、公開、visibility変更、credential変更は current-turn explicit approval まで止める。
- runtime install copy は repo-owned source から同期する projection として扱う。
- Codex / Claude Code の runtime install copy との差分確認は `python -m engineering_brain skill-sync --target all --json` で行う。
- `engineering_brain run` は既定では計画 packet を返す。verification を実行する時は `--closeout` を明示する。
- GCP/Vertex/Cloud Run/Workflowsでは `async_orchestration_evidence_gate`、OCR/蒸留/量子化では `structured_model_evaluation_gate` を実行証拠付きで確認する。

## 現在の範囲

現在の runtime scope は次の通りです。

- 正本: `skills/engineering-autopilot/`
- projection: Codex `<USER_HOME>/.codex/skills/engineering-autopilot` / Claude Code `<USER_HOME>/.claude/skills/engineering-autopilot`
- 確認: `python -m engineering_brain skill-sync --target all --json`
- 同期: 現在会話で runtime write の承認を得た後だけ `python -m engineering_brain skill-sync --target all --apply --json`
- Claude Code smoke: 通常モードで `/engineering-autopilot` を呼ぶ。個人スキルの発見確認には `--bare` を使わない。
- run packet: `python -m engineering_brain run --task "<task>" --json`
- verification plan: `python -m engineering_brain verify --repo . --json`
- PR packet: `python -m engineering_brain pr --repo . --json`（plan-only。PR作成/pushはしない）
- algorithm registry: `engineering_brain/data/algorithms.json`
- algorithm selection: `python -m engineering_brain algorithms select --signal <signal> --json`
- algorithm comparison: `python -m engineering_brain algorithms compare --id <id> --id <id> --json`
- しない: GitHub visibility 変更

## Closeout

完了報告前に最低限これを確認します。

```powershell
python -m pytest -q
python -m engineering_brain verify --repo . --json
python -m engineering_brain closeout --repo . --json
```

外部操作が必要な場合は、実行前に「何が外から見えるか」「何をレビュー済みか」「何をまだしていないか」を分けて、人間の明示 yes を待ちます。

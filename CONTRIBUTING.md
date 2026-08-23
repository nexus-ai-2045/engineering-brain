# Contributing

engineering-brain は local-first の開発保証 repo です。contribution は、作業を大きく見せることではなく、判断、検証、停止線、残リスクを再現可能にすることを目的にします。

## 基本方針

- 変更前に SSOT、既存実装、公式 docs、GitHub evidence、OSS 候補を確認する。
- 車輪の再発明を避け、`reuse / wrap / extend / adopt_oss / build / hold` の判断を残す。
- 変更は小さい PR に分ける。
- planner-only を self-driving と呼ばない。自走には run packet、evidence、resume、approval stopline が必要。
- GitHub push、PR作成、merge、cleanup、public 化、外部送信はそれぞれ別の承認境界として扱う。
- 公開候補 artifact に実ユーザー名入りのローカル絶対パスを残さない。

## PR 前チェック

```powershell
python -m pytest -q
python -m compileall -q engineering_brain tests
python -m engineering_brain closeout --repo . --json
python -m engineering_brain pr --repo . --json
ai-ratchet-gate --repo .
python tools/run_repo_preflight.py --repo .
git diff --check
git status --short --branch
```

`ai-ratchet-gate` は PyPI 名では入れない。Release wheel を使う:

```powershell
python -m pip install https://github.com/nexus-ai-2045/ai-ratchet-gate/releases/download/v0.1.0/ai_ratchet_gate-0.1.0-py3-none-any.whl
```

`tools/run_repo_preflight.py` は upstream `repo-preflight` を呼び出す薄いラッパである（検査ロジックはコピーしない）。consistency は当面 `shadow`。

## PR 本文に書くこと

- 目的
- 変更内容
- research / reinvention check
- TDD / 検証
- security / operation
- visible scope
- 未確認と残リスク
- human stoplines

## 禁止

- 古い PR や stale clone を丸ごと merge する。
- 旧 SSOT を復活させる。
- 実ユーザー名入り absolute path を docs / registry / PR 文面に残す。
- 任意 shell 実行を autopilot の既定にする。
- merge、public 化、外部送信、hook/settings/auth 変更を一般的な GO で実行する。

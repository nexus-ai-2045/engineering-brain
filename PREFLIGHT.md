<!-- repo-preflight:review-record -->

# 公開準備状況

- HEAD: 作業ブランチの最新 commit
- 確認日時: PR 作成・更新時
- 判定: `blocked`（human review / merge 承認待ち）

## 確認済み

- [x] README / LICENSE / SECURITY.md / CONTRIBUTING.md
- [x] PREFLIGHT.md（本ファイル）
- [x] test / compileall（CI `gates`）
- [x] ai-ratchet-gate baseline（`.ai-ratchet-gate/baseline.txt`）
- [x] repo-preflight consistency `mode=shadow`（`.repo-preflight-consistency.json`）
- [ ] secret / personal path / history（repo-preflight readiness_scan の所見を人間が確認）
- [ ] dependency / CI runtime evidence
- [ ] operations / monitoring / rollback

## 機械ゲート

CONTRIBUTING.md の開発環境（venv）を先に作ります。

```bash
python -m pip install https://github.com/nexus-ai-2045/ai-ratchet-gate/releases/download/v0.2.0/ai_ratchet_gate-0.2.0-py3-none-any.whl
ai-ratchet-gate --repo .
python tools/run_repo_preflight.py --repo .
```

- `ai-ratchet-gate` は PyPI 名では入れない（Release wheel URL のみ。CI は SHA-256 `95ebac0afbf91e1d4b3634b011680eeae58a85dc32e801b3bcbb7cfc41a0d4a8` で固定）。
- `tools/run_repo_preflight.py` は upstream `nexus-ai-2045/repo-preflight` を `.tools/repo-preflight` へ clone して実行する。検査ロジックはコピーしない。
- consistency は当面 `shadow`。所見は観測し、merge 承認には使わない。
- readiness_scan の `pass` / `blocked` は機械範囲のみ。push / PR / merge / visibility 変更の承認ではない。

## 人間目視

- reviewer:
- reviewed_at:
- exact HEAD / PR diff:
- decision: `approve / changes_requested`
- 外から見える files と commit history:
- 残余リスク:
- 次に承認する正確な操作: merge（current-turn 明示承認が必要）

## 公開名義の検査（2026-10-17）

CI の `.github/workflows/preflight.yml` は、共通ゲート `nexus-ai-2045/repo-preflight` の `preflight-gate.yml` を SHA 固定で呼びます。このゲートは全 commit の作成者と記録者を公開名義の許可リスト（repo-preflight の `references/public-commit-identities.json`）と照合し、リストに無い名義があれば失敗します。名義の値は出力しません。

固定版は v0.10.0（`5b7c774`）です（2026-10-25 に `44fdece` から上げた）。`44fdece` は GitHub の記録者（committer_only）を役割ごとに見ないため、PR の合成 merge commit と dependabot の branch を名義違いとして数えていました。

`gates.yml` の「Checkout repo-preflight」も同じ v0.10.0（`5b7c774`）に固定します（2026-10-26 に `44fdece` から上げた）。preflight-gate・base-guard・gates の3か所は、同じタグ付きの SHA にそろえます。

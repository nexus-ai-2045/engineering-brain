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

```powershell
python -m pip install https://github.com/nexus-ai-2045/ai-ratchet-gate/releases/download/v0.1.0/ai_ratchet_gate-0.1.0-py3-none-any.whl
ai-ratchet-gate --repo .
python tools/run_repo_preflight.py --repo .
```

- `ai-ratchet-gate` は PyPI 名では入れない（Release wheel URL のみ）。
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

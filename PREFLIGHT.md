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
- 既定は `--intent open_pr --base-ref origin/main` 相当の対象差分検査。質問packetを返す読取りのみで、PR作成は行わない。履歴全体を含む公開検査は `--intent publish` または `--intent release` を明示し、wrapperが上流へ `--consistency-base-ref` を渡す。
- consistency は当面 `shadow`。所見は観測し、merge 承認には使わない。
- 終了コードは上流の合成結果: `0` は機械検査通過（`ready_after_confirmation`を含む）、`1` は所見・人間入力待ち、`2` は実行失敗・tool_error・JSON契約不正。終了コード0も公開承認ではない。
- 最終JSON行 `repo-preflight.wrapper/v1` にstatus、mode、各上流statusを残す。readiness内のscanがtool_errorなら、外側がblockedでも終了コード2で返す。
- readiness_scan の `pass` / `blocked` は機械範囲のみ。push / PR / merge / visibility 変更の承認ではない。

## 人間目視

- reviewer:
- reviewed_at:
- exact HEAD / PR diff:
- decision: `approve / changes_requested`
- 外から見える files と commit history:
- 残余リスク:
- 次に承認する正確な操作: merge（current-turn 明示承認が必要）

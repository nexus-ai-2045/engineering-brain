# PUBLIC_READY

status: public

この repo は public visibility へ変更済みです。

対象 repo と exact operation:

- target_repo: `nexus-ai-2045/engineering-brain`
- current_visibility: `PUBLIC`
- completed_operation: `gh repo edit nexus-ai-2045/engineering-brain --visibility public --accept-visibility-change-consequences`

公開前レビュー packet は [Public release review packet](docs/PUBLIC_RELEASE_REVIEW_PACKET.md) を参照します。

公開前 checklist:

- [x] README が公開読者向けに整っている
- [x] LICENSE を決める
- [x] SECURITY.md を確認する
- [x] secret / personal path / private source scan を通す
- [x] GitHub owner/name と visibility を明示する
- [x] commit history と files が web で見えることを確認する
- [x] current conversation で対象 repo と exact operation への明示 yes を得る

## GitHub 設定（2026-08-23 実測）

visibility は PUBLIC。GitHub Release / tag は未作成。

| 設定 | 実測 | リリース前の推奨 |
|---|---|---|
| secret scanning | enabled | 維持 |
| secret scanning push protection | disabled | 有効化を別承認 |
| Dependabot security updates | disabled | 有効化を別承認 |
| Dependabot alerts | disabled (API 404) | 有効化を別承認 |
| private vulnerability reporting | enabled | 維持 |
| branch protection on `main` | なし | 要/不要を別判断 |
| delete_branch_on_merge | false | squash 後のブランチ残存の主因。有効化を別承認 |

## 未吸収の local work

remote の merge 済みブランチは回収済み。次はまだ main に載せていない。

- `codex/research-review-eval-20260730`: research review eval harness（6 commit）
- `codex/runtime-contract-learnings`: 実行経路契約の learnings（現行 `registry/local-learnings.yaml` schema と形が違う）
- `codex/algorithm-catalog-selection-20260728`: 旧 `devbrain/` パス。#21 で `engineering_brain` へ吸収済みの stale 候補

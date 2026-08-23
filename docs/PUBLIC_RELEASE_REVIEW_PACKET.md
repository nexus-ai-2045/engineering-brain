# Public release review packet

status: public
checked_at: 2026-07-15 JST
target_repo: nexus-ai-2045/engineering-brain
current_visibility: PUBLIC
completed_operation: `gh repo edit nexus-ai-2045/engineering-brain --visibility public --accept-visibility-change-consequences`

## 判定

この repo は public visibility へ変更済みです。変更前に対象 repo、見える内容、scan、LICENSE、SECURITY.md、exact operation を確認し、current conversation の明示 yes を受けました。

## 外から見えるもの

- source code: `engineering_brain/`, `tests/`, `schemas/`
- repo-owned skill source: `skills/engineering-autopilot/`
- governance docs: `README.md`, `docs/`, `registry/`, `PUBLIC_READY.md`, `SECURITY.md`, `CONTRIBUTING.md`
- migration history notes: `docs/MIGRATION_NOTES.md`, `docs/ENGINEERING_CUTOVER_PLAN.md`, `docs/PRIVATE_CUTOVER_PACKET.md`

## 公開してよい前提

- 実ユーザー名入り絶対パスは `<PROJECTS_ROOT>` / `<USER_HOME>` / `<REPO>` に置換する。
- private / clean-history / cutover の記録は、運用判断の履歴として残す。
- runtime copy は正本ではなく projection として説明する。
- external publish / release / announcement は visibility 変更とは別の承認境界として残す。

## 実測

| check | result |
|---|---|
| repo visibility | `PUBLIC` |
| open PRs before this packet | none |
| `python -m pytest -q` | 再測定は各 release PR で行う。visibility packet 作成時点は 34 passed |
| `python -m engineering_brain closeout --repo . --json` | overall ok |
| `python -m engineering_brain skill-sync --target all --json` | 両 runtime が status ok |
| `gh_identity_probe.py --repo . --json` | status ok / repo PUBLIC / token env absent |
| LICENSE | MIT |
| SECURITY.md | present |
| README public framing | updated |
| personal path scan | no findings for real user-home paths |

## 残す停止線

- GitHub visibility 変更は実行済み。
- public release / announcement / external share は別承認。
- 今後も公開候補 artifact には実ユーザー名入り絶対パス、secret、private URL を残さない。

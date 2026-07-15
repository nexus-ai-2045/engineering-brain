# Public release review packet

status: ready-for-human-review
checked_at: 2026-07-15 JST
target_repo: nexus-ai-2045/engineering-brain
current_visibility: PRIVATE
requested_visibility: PUBLIC
exact_operation: `gh repo edit nexus-ai-2045/engineering-brain --visibility public`

## 判定

この repo は public 化の人間レビューに進める状態です。visibility 変更そのものは、この packet の merge 後に対象 repo と exact operation を再提示し、current conversation の明示 yes を受けてから実行します。

visibility 変更そのものは未実行です。

## 外から見えるもの

- source code: `devbrain/`, `tests/`, `schemas/`
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
| repo visibility | `PRIVATE` |
| open PRs before this packet | none |
| `python -m pytest -q` | 34 passed |
| `python -m devbrain closeout --repo . --json` | overall ok |
| `python -m devbrain skill-sync --json` | status ok |
| `gh_identity_probe.py --repo . --json` | status ok / repo private / token env absent |
| LICENSE | MIT |
| SECURITY.md | present |
| README public framing | updated |
| personal path scan | no findings for real user-home paths |

## 残す停止線

- GitHub visibility 変更は未実行。
- `gh repo edit nexus-ai-2045/engineering-brain --visibility public` は、この packet が merge されても自動実行しない。
- public release / announcement / external share は別承認。
- merge 後、public 化直前に `PUBLIC_READY.md`、secret/path scan、repo visibility、open PRs を再測定する。

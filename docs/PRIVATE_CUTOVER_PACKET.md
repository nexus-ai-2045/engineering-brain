# private cutover packet

status: executed-private
owner: nexus_ai
checked_at: 2026-07-15 JST

## 結論

`engineering-brain / engineering-autopilot` への移行は、**private recreate with clean history and migration notes** を推奨する。

理由:

- `dev-brain` は作業区間として始まり、将来 public 化する名前と責務があとから固まった。
- public 前に repo 名、local directory、repo-owned skill、runtime skill を揃える方が、後続の説明と運用が単純になる。
- 既存 PR history は `dev-brain` private repo に残せる。公開候補 repo には、整理済み snapshot と migration notes だけを持ち込める。
- GitHub rename は便利だが、redirect、Actions、external reference、local remote の更新が残る。作業区間を clean に閉じたい今回の目的には recreate が合う。

## Decision

```text
target_name: engineering-brain / engineering-autopilot
current_repo: nexus-ai-2045/dev-brain
target_repo: nexus-ai-2045/engineering-brain
visibility: private
recommended_history_policy: clean_history_with_migration_notes
local_target: <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
runtime_skill_target: <USER_HOME>/.codex/skills/engineering-autopilot
legacy_repo_policy: keep_private_reference
public_visibility: out_of_scope
```

## What Moves

| layer | from | to | policy |
|---|---|---|---|
| GitHub repo | `nexus-ai-2045/dev-brain` | `nexus-ai-2045/engineering-brain` | create private target after explicit approval |
| local repo | `<PROJECTS_ROOT>/Documents/repos/second-brain/dev-brain` | `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain` | create clean target directory after explicit approval |
| repo-owned skill | future `skills/dev-brain-autopilot` | `skills/engineering-autopilot` | thin CLI entry only |
| runtime skill | `<USER_HOME>/.codex/skills/dev-brain-autopilot` | `<USER_HOME>/.codex/skills/engineering-autopilot` | copy/sync only after CLI contract exists |
| SSOT registry | current dev-brain entry | engineering-brain entry | update in same cutover PR |

## Exact Commands To Review

These commands were reviewed in legacy `dev-brain` and executed for the private clean-history cutover.

```powershell
gh repo create nexus-ai-2045/engineering-brain --private --description "Local-first engineering autopilot and development assurance brain"
New-Item -ItemType Directory -Force <PROJECTS_ROOT>/Documents/repos/engineering
git clone https://github.com/nexus-ai-2045/engineering-brain.git <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
```

For clean-history recreation, copy the reviewed working tree from the current repo into the target repo without `.git`, local state, caches, or private runtime artifacts.

```powershell
robocopy <PROJECTS_ROOT>/Documents/repos/second-brain/dev-brain <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain /E /XD .git .pytest_cache __pycache__ .devbrain /XF *.pyc
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain status --short
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain add .
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain commit -m "Initialize engineering brain"
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain push -u origin main
```

After the new private repo is verified, update the SSOT registry and runtime pointers in follow-up work.

## Required Checks Before Execution

- `python -m pytest -q`
- `python -m devbrain closeout --repo . --json`
- `python -m devbrain catalog --domain recreate --json`
- personal path / old identity scan
- GitHub identity probe for `nexus-ai-2045`
- target repo availability check: `gh repo view nexus-ai-2045/engineering-brain`
- source repo remains private: `gh repo view nexus-ai-2045/dev-brain --json visibility`
- review of `PUBLIC_READY.md`, `SECURITY.md`, README, docs, registry, and commit-history policy

## Human Approval Text

The execution turn must include an explicit approval that names:

```text
approved_action: create private repo and local target for engineering-brain
target_repo: nexus-ai-2045/engineering-brain
target_local_path: <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
history_policy: clean_history_with_migration_notes
visibility: private
public_visibility_change: no
```

The execution approval was provided for private repo creation and local target creation. Runtime skill switch and public visibility remain outside this approval.

## Rollback

If any cutover step fails:

- keep `nexus-ai-2045/dev-brain` as the private migration reference
- do not delete or archive `dev-brain`
- remove the incomplete local target directory only after confirming it contains no unique work
- if the target private GitHub repo was created but not adopted, leave it private and mark it as blocked, or delete it only after explicit confirmation

## Non-goals

- no public visibility change
- no external announcement
- no release
- no automatic deletion of `dev-brain`
- no runtime skill install switch until the repo-owned skill is thin and CLI-backed

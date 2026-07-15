# Migration notes

status: active
owner: nexus_ai
checked_at: 2026-07-15 JST

## Origin

`engineering-brain` was created as a private clean-history recreation of `nexus-ai-2045/dev-brain`.

The legacy `dev-brain` repo was kept private during migration verification, then deleted after current-turn approval on 2026-07-15 JST. The new repo starts from a reviewed snapshot instead of importing the entire work-in-progress history.

## Policy

- `nexus-ai-2045/dev-brain` was deleted after migration verification and explicit approval.
- `nexus-ai-2045/engineering-brain` is private.
- Public visibility remains out of scope.
- Runtime skill installation is switched to `engineering-autopilot` after tested sync and post-apply validation.
- The Python package and CLI keep the `devbrain` import / command name during the first cutover to avoid breaking tests and local muscle memory.
- Local-only commits later found in a stale `<PROJECTS_ROOT>/dev-brain` clone are evaluated through `docs/LEGACY_DEV_BRAIN_ABSORPTION.md` before any local deletion.

## First Snapshot Checks

The source snapshot was accepted only after:

- `python -m pytest -q`
- `python -m devbrain closeout --repo . --json`
- GitHub identity probe for `nexus-ai-2045`
- personal path / old identity scan
- target repo absence check before create
- source repo visibility check

## Next Work

1. Add / update `<PROJECTS_ROOT>/ssot-registry.yaml` for `engineering-brain`.
2. Add the autopilot run packet MVP.
3. Decide whether to keep `devbrain` as the CLI name or add `engineering-brain` as an alias.
4. Continue the roadmap from identity gate, run packet, lifecycle FSM, PR packet, and skill sync.
5. Delete stale local legacy clones only after their local-only commits are represented in `docs/LEGACY_DEV_BRAIN_ABSORPTION.md`.

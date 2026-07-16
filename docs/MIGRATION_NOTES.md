# Migration notes

status: active
owner: nexus_ai
checked_at: 2026-07-16 JST

## Origin

`engineering-brain` was created as a private clean-history recreation of `nexus-ai-2045/dev-brain`.

The legacy `dev-brain` repo was kept private during migration verification, then deleted after current-turn approval on 2026-07-15 JST. The new repo starts from a reviewed snapshot instead of importing the entire work-in-progress history.

## Policy

- `nexus-ai-2045/dev-brain` was deleted after migration verification and explicit approval.
- `nexus-ai-2045/engineering-brain` is public.
- Public visibility was completed after a separate review packet and current conversation approval.
- Runtime skill installation is switched to `engineering-autopilot` after tested sync and post-apply validation.
- The legacy `<USER_HOME>/.codex/skills/dev-brain-autopilot` runtime copy was deleted after `engineering-autopilot` became the synced projection.
- The Python package and CLI keep the `devbrain` import / command name during the first cutover to avoid breaking tests and local muscle memory.
- Local-only commits later found in a stale `<PROJECTS_ROOT>/dev-brain` clone were evaluated through `docs/LEGACY_DEV_BRAIN_ABSORPTION.md`; the stale local clone is no longer present.

## First Snapshot Checks

The source snapshot was accepted only after:

- `python -m pytest -q`
- `python -m devbrain closeout --repo . --json`
- GitHub identity probe for `nexus-ai-2045`
- personal path / old identity scan
- target repo absence check before create
- source repo visibility check

## Next Work

1. Keep `<PROJECTS_ROOT>/ssot-registry.yaml` aligned with public `engineering-brain`.
2. Add PR packet generation and verification profile.
3. Decide whether to keep `devbrain` as the CLI name or add `engineering-brain` as an alias.
4. Continue the roadmap from identity gate, lifecycle FSM, PR packet, and skill sync.
5. Treat remaining `dev-brain` mentions as historical migration references unless a live path check proves otherwise.

# Legacy dev-brain absorption ledger

status: active-ledger
owner: nexus_ai
checked_at: 2026-07-16 JST

## Conclusion

The stale `<PROJECTS_ROOT>/dev-brain` clone was classified and is no longer present.

Read-only inspection found four local-only commits on `codex/dev-brain-autopilot-pr` beyond the old remote branch. The canonical repo remains `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain`, but these legacy commits still contain useful knowledge that must be absorbed or explicitly rejected before local deletion.

## Legacy commits inspected

| commit | title | absorption decision |
|---|---|---|
| `729948f` | Add thread handoff packet | absorbed as cutover history and approval stopline evidence |
| `f23726c` | Research engineering autopilot prior art | partially absorbed as prior-art source clusters and naming guidance |
| `d9ed90a` | Adopt engineering-brain naming | absorbed by current repo/skill naming decision |
| `ead0ad4` | Clarify SSOT drift boundaries | absorbed as stale clone / live SSOT split |

## Knowledge retained

The useful content from the local-only legacy branch is retained as these rules:

- `engineering-brain` is the live repo SSOT; legacy `dev-brain` is a stale clone and must not become the review surface again.
- `engineering-autopilot` means an approval-gated lifecycle runner, not autonomous publish / push / merge.
- prior-art research is a candidate gate. GitHub, official docs, OSS examples, and community patterns can inform work, but source presence is not adoption.
- clean-history recreation was chosen because the old `dev-brain` initial history had unwanted identity attribution risk.
- GitHub CLI active account, commit author, committer, and GitHub attribution must be checked per commit before external review.
- SSOT drift must split `current live surface` from `target candidate`; mixing those in one row creates false confidence.
- destructive local deletion of the stale clone is allowed only after this ledger and a final diff check show no unabsorbed material. That deletion gate has been satisfied for the known stale clone.

## Source clusters preserved

| cluster | retained role |
|---|---|
| GitHub Copilot cloud agent / CLI autopilot | lifecycle vocabulary and warning that autopilot works best on well-defined tasks |
| OpenAI Agents SDK / guardrails / tracing | handoff, approval pause, guardrails, and trace evidence vocabulary |
| Google Engineering Practices | review and codebase health standard |
| DORA | delivery and instability metrics candidate |
| Google SRE | operational guarantee / incident / release engineering vocabulary |
| OpenSSF Scorecard | security posture and supply-chain heuristic source |
| Backstage | catalog / developer portal reference, not a UI requirement |
| OpenHands / SWE-agent / Aider family | fast-moving prior art, reference-only unless rechecked |

## Delete gate for stale clones

If a new stale `<PROJECTS_ROOT>/dev-brain` or `<PROJECTS_ROOT>/nexus-dev-kernel` directory appears, run:

```powershell
git -C <PROJECTS_ROOT>/dev-brain status --short --branch
git -C <PROJECTS_ROOT>/dev-brain diff --name-only origin/codex/dev-brain-autopilot-pr..HEAD
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain status --short --branch
```

Deletion remains blocked if any legacy file contains a source, rule, test, or migration fact not represented in this repo.

Current known state: the legacy GitHub repo, stale local clones, and legacy `dev-brain-autopilot` runtime skill copy are deleted. Remaining `dev-brain` references in this repo are historical migration records or the `devbrain` CLI/package name.

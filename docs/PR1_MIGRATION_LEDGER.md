# PR #1 migration ledger

status: active
owner: nexus_ai
checked_at: 2026-07-15 JST
source_pr: https://github.com/nexus-ai-2045/dev-brain/pull/1

## 結論

PR #1 はそのまま merge しない。`main` との実衝突があり、PR #2 / PR #3 で確定した SSOT、public path redaction、autopilot goal design を巻き戻すリスクがある。

ただし、PR #1 には採用すべき部品も含まれる。丸ごと merge ではなく、次の分類に従って小さい PR に分解して再統合する。

## Blocking issues

| issue | 内容 | 対応 |
|---|---|---|
| wrong local SSOT | PR #1 は旧 local root を正本として扱う | reject。現行 [Local SSOT](LOCAL_SSOT.md) を維持 |
| personal absolute paths | docs / registry に実ユーザー名入り absolute path が含まれる | rewrite。`<PROJECTS_ROOT>` / `<USER_HOME>` / `<REPO>` に置換 |
| merge conflicts | `README.md` / `devbrain/cli.py` / `devbrain/registry.py` / `docs/LOCAL_SSOT.md` / `registry/technology-sources.yaml` が conflict | split PR で再実装 |
| design drift | PR #1 は planner 実装を先行し、PR #3 の goal design / anti-goals / research method を経由していない | rewrite。PR #3 の state machine と roadmap に合わせる |
| broad blast radius | docs、registry、CLI、skill、GitHub templates、identity gate を 1 PR に混在 | split |

## File-level disposition

| file | disposition | reason | next PR |
|---|---|---|---|
| `.github/ISSUE_TEMPLATE/gate-request.yml` | adopt | gate request intake と相性がよい | PR A: templates |
| `.github/ISSUE_TEMPLATE/research-intake.yml` | adopt | research packet の入口として有用 | PR A: templates |
| `.github/PULL_REQUEST_TEMPLATE/dev-brain-change.md` | adopt | PR packet と human stopline を標準化できる | PR A: templates |
| `CONTRIBUTING.md` | rewrite | public / private / local-first 境界を現行 policy に合わせる必要あり | PR A: templates |
| `README.md` | reject/rewrite | 現行 README と conflict。旧 SSOT 記載が危険 | per slice |
| `ROADMAP.md` | rewrite | PR #3 の MVP roadmap に合わせ直す | PR B: roadmap |
| `devbrain/autopilot.py` | rewrite | planner-only で self-driving と呼ばない。run packet / lifecycle / evidence へ分解 | PR D: planner |
| `devbrain/cli.py` | rewrite | 現行 `catalog` / `closeout` と conflict。CLI は slice ごとに追加 | each slice |
| `devbrain/identity.py` | adopt with review | commit identity gate は有用。fail-open / invalid rev range を重点確認 | PR C: identity gate |
| `devbrain/registry.py` | rewrite | PR #1 の registry 拡張は現行 lightweight parser と conflict | per registry slice |
| `docs/ARCHITECTURE.md` | already-covered/rewrite | [Autopilot goal design](AUTOPILOT_GOAL_DESIGN.md) に統合済み。残すなら短い pointer | optional |
| `docs/AUTOPILOT_LIFECYCLE.md` | rewrite | lifecycle registry / tests と一緒に再作成 | PR E: lifecycle |
| `docs/COLLABORATION_MODEL.md` | rewrite | agent / plugin orchestration は PR #3 の section に合わせる | optional |
| `docs/FDE_KNOWLEDGE_INTAKE.md` | rewrite | FDE 知見は source packet / gate へ落とす必要あり | PR D/E |
| `docs/GOVERNANCE.md` | rewrite | human stopline と public boundary を現行 AGENTS / policy に合わせる | optional |
| `docs/IDENTITY_POLICY.md` | adopt with review | identity gate と同時に採用候補 | PR C: identity gate |
| `docs/LOCAL_LEARNING_LEDGER.md` | rewrite | learning intake は review comment / failure absorption へ接続する | later |
| `docs/LOCAL_SSOT.md` | reject | 現行 SSOT と矛盾し、absolute path policy に反する | none |
| `docs/OPERATIONS_GUARANTEE.md` | rewrite | closeout v2 の evidence schema と合わせる | later |
| `docs/PR_DRAFT.md` | rewrite | PR packet generator と合わせる | PR F: PR packet |
| `docs/PR_PLAYBOOK.md` | rewrite | current-turn approval / visible scope を現行ルールへ合わせる | PR F: PR packet |
| `docs/RESEARCH_TDD_DELIVERY_PIPELINE.md` | already-covered/rewrite | PR #3 の research method / implementation order に吸収済み | optional |
| `docs/SECURITY_MODEL.md` | rewrite | security-guidance / path redaction / containment と統合 | later |
| `docs/TOP_ENGINEERING_SOURCE_CLUSTERS.md` | already-covered | `technology-sources.yaml` と best-practice catalog に吸収済み | none unless gap |
| `registry/capability-map.yaml` | rewrite | plugin / agent orchestration は run packet schema へ接続する | later |
| `registry/lifecycle-phases.yaml` | adopt with tests | lifecycle FSM の seed として有用 | PR E: lifecycle |
| `registry/local-learnings.yaml` | rewrite | learning intake schema 未定。いったん hold | later |
| `registry/presets.yaml` | rewrite | verification profiles / planner と一緒に再設計 | PR D/E |
| `registry/technology-sources.yaml` | partial adopt | 追加 source の一部は有用。現行 catalog と重複、absolute path を修正 | PR B: source catalog gap |
| `skills/dev-brain-autopilot/SKILL.md` | rewrite | repo-owned thin skill として再作成。logic duplicate 禁止 | PR G: skill |
| `skills/dev-brain-autopilot/agents/openai.yaml` | hold | runtime agent mapping は repo CLI 完成後 | PR G or later |
| `skills/dev-brain-autopilot/references/lifecycle.md` | rewrite | lifecycle registry の pointer にする | PR G |
| `skills/dev-brain-autopilot/scripts/devbrain_autopilot.py` | reject/rewrite | skill script に logic を複製しない | PR G |
| `tests/test_cli.py` | partial adopt | CLI slice ごとにテストを再利用 | each slice |
| `tests/test_identity.py` | adopt with review | identity gate の regression seed | PR C |

## Recommended split

1. PR A: GitHub templates and contributing guide.
2. PR B: source catalog gap and roadmap cleanup.
3. PR C: identity gate with fail-closed tests.
4. PR D: run packet / planner dry-run.
5. PR E: lifecycle registry and guarded state machine.
6. PR F: PR packet generator.
7. PR G: repo-owned thin skill.

## Rules for reuse

- Do not merge PR #1 as-is.
- Do not copy old SSOT text.
- Do not keep real local absolute paths.
- Do not reintroduce planner-only self-driving claims.
- Do not put push / PR creation / merge / cleanup behind one approval.
- Every adopted piece must pass `python -m pytest -q`, `python -m devbrain closeout --repo . --json`, and public path redaction.

## Current PR #1 status

At review time:

```text
state: open
draft: true
mergeable: conflicting
head: codex/dev-brain-autopilot-pr
```

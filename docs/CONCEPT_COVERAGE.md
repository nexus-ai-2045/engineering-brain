# Concept Coverage

## 目的

`engineering-brain` に、開発保証 repo として必要な概念が入っているかを確認する。これは完成宣言ではなく、coverage と gap を見えるようにする台帳である。

## Coverage table

| concept | status | current home | next action |
|---|---|---|---|
| Local SSOT | covered | `docs/LOCAL_SSOT.md` | 削除済み legacy は reference ではなく historical source として扱う |
| Public GitHub surface | covered | `README.md`, `docs/LOCAL_SSOT.md`, `PUBLIC_READY.md` | release / tag / announcement は別承認のまま維持 |
| ADR | covered | `docs/adr/` | 後続の設計判断で継続追加 |
| Obsidian intake | covered | `docs/KNOWLEDGE_INTAKE.md` | 自動候補抽出は別 slice |
| Local learning absorption | partial | `docs/KNOWLEDGE_INTAKE.md`, `registry/local-learnings.yaml` | candidate packets は追加済み。field_review / adopt は未了 |
| Reinvention avoidance | covered | `docs/AUTOPILOT_GOAL_DESIGN.md`, `engineering_brain/data/adoption-units.yaml` | run packet 実装で evidence 付き検査へ昇格 |
| Research / GitHub method | covered | `engineering_brain research`, `docs/AUTOPILOT_GOAL_DESIGN.md`, `reinvention_candidate_research_gate` | PR packet と closeout evidence へ接続する |
| TDD / regression | covered | `README.md`, `tests/` | lifecycle command で選択可能にする |
| Smoke / preflight / E2E | partial | `docs/AUTOPILOT_GOAL_DESIGN.md` | `registry/verification-profiles.yaml` を追加する |
| Security / containment | covered | `docs/OPERATING_MODEL.md`, `SECURITY.md` | codex-security scan slice を追加する |
| Public path redaction | covered | `docs/PUBLIC_PATH_POLICY.md`, `tests/test_path_safety.py` | PR body generator に接続する |
| GitHub identity gate | partial | local skill + docs | repo-owned identity command を追加する |
| PR lifecycle | partial | `.github/`, `CONTRIBUTING.md` | PR packet generator を追加する |
| Human visual review | partial | `engineering_brain run`, `docs/AUTOPILOT_GOAL_DESIGN.md` | review state を PR packet に接続する |
| Merge / branch cleanup | covered | `engineering_brain finish`, `tools/hooks/post-merge`, `docs/AUTOPILOT_GOAL_DESIGN.md` | remote cleanup は approval / identity gate を維持する |
| Operation guarantee | covered | `engineering_brain closeout`, `docs/OPERATING_MODEL.md` | evidence-based closeout v2 を追加する |
| PDCA / feedback loop | covered | `docs/PDCA_FEEDBACK_LOOP.md` | run packet と local learning registry へ接続する |
| Runtime skill | covered | `skills/engineering-autopilot/` repo-owned source, Codex / Claude Code runtime copies, `engineering_brain skill-sync --target all` | runtime drift を継続監視する |
| Best-practice source catalog | covered | `engineering_brain/data/technology-sources.yaml` | adopted / candidate / hold status を強める |
| Public readiness | covered | `PUBLIC_READY.md`, `docs/PUBLIC_RELEASE_REVIEW_PACKET.md` | release / tag / announcement は別 review packet で再測定する |

## ローカル概念 inventory

この repo に入れるべきローカル概念は、次の形へ正規化する。

| local concept | repo representation |
|---|---|
| SSOT first | `docs/LOCAL_SSOT.md`, closeout |
| FDE routing | adoption unit / route result |
| scope routing | run packet / write scope |
| human review stopline | ADR / gate / PR packet |
| current-turn approval | gate / finish planner |
| path redaction | public path policy / tests |
| identity drift guard | GitHub identity gate |
| local-first verification | closeout / test / smoke profile |
| learning compounding | knowledge intake / local learnings registry |
| Obsidian as intake | knowledge intake |
| clean-history migration | migration notes / ADR |

## Gaps

1. `engineering_brain lifecycle` は設計済みだが未実装。`engineering_brain run` は MVP 実装済み。
2. runtime install copy は同期済み。継続的な drift check を運用に入れる。
3. `registry/local-learnings.yaml` の candidate packets は追加済み。adopt / field_review は未了。
4. GitHub identity gate は local skill に依存しており、repo-owned command ではない。
5. PR packet generator は未実装。
6. verification profile と closeout v2 evidence schema は未実装。

## Next slices

1. `registry/local-learnings.yaml` の candidate を field_review し、adopt / hold を判断する。
2. PR packet generator を追加する。
3. verification profile を追加する。
4. `engineering_brain run --closeout` の evidence schema を強化する。
5. Obsidian / memory から候補 packet を作る read-only importer を追加する。

# Concept Coverage

## 目的

`engineering-brain` に、開発保証 repo として必要な概念が入っているかを確認する。これは完成宣言ではなく、coverage と gap を見えるようにする台帳である。

## Coverage table

| concept | status | current home | next action |
|---|---|---|---|
| Local SSOT | covered | `docs/LOCAL_SSOT.md` | 削除済み legacy は reference ではなく historical source として扱う |
| Private-first GitHub mirror | covered | `README.md`, `docs/LOCAL_SSOT.md` | public packet は別承認のまま維持 |
| ADR | covered | `docs/adr/` | 後続の設計判断で継続追加 |
| Obsidian intake | covered | `docs/KNOWLEDGE_INTAKE.md` | 自動候補抽出は別 slice |
| Local learning absorption | partial | `docs/KNOWLEDGE_INTAKE.md` | `registry/local-learnings.yaml` を追加する |
| Reinvention avoidance | covered | `docs/AUTOPILOT_GOAL_DESIGN.md` | run packet 実装で機械検査へ昇格 |
| Research / GitHub method | covered | `docs/AUTOPILOT_GOAL_DESIGN.md` | source packet schema を追加する |
| TDD / regression | covered | `README.md`, `tests/` | lifecycle command で選択可能にする |
| Smoke / preflight / E2E | partial | `docs/AUTOPILOT_GOAL_DESIGN.md` | `registry/verification-profiles.yaml` を追加する |
| Security / containment | covered | `docs/OPERATING_MODEL.md`, `SECURITY.md` | codex-security scan slice を追加する |
| Public path redaction | covered | `docs/PUBLIC_PATH_POLICY.md`, `tests/test_path_safety.py` | PR body generator に接続する |
| GitHub identity gate | partial | local skill + docs | repo-owned identity command を追加する |
| PR lifecycle | partial | `.github/`, `CONTRIBUTING.md` | PR packet generator を追加する |
| Human visual review | partial | `docs/AUTOPILOT_GOAL_DESIGN.md` | review state を run packet に入れる |
| Merge / branch cleanup | partial | `docs/AUTOPILOT_GOAL_DESIGN.md` | finish planner を追加する |
| Operation guarantee | covered | `devbrain closeout`, `docs/OPERATING_MODEL.md` | evidence-based closeout v2 を追加する |
| Runtime skill | partial | local installed skill only | `skills/engineering-autopilot/` を repo-owned thin skill として追加する |
| Best-practice source catalog | covered | `registry/technology-sources.yaml` | adopted / candidate / hold status を強める |
| Public readiness | partial | `PUBLIC_READY.md` | public 化時だけ review packet で再測定 |

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

1. `devbrain lifecycle` / `devbrain run` は設計済みだが未実装。
2. `skills/engineering-autopilot/` の repo-owned source は未導入。
3. `registry/local-learnings.yaml` がまだない。
4. GitHub identity gate は local skill に依存しており、repo-owned command ではない。
5. PR packet / finish planner は docs 設計であり、CLI 実装は未着手。

## Next slices

1. `registry/local-learnings.yaml` と schema を追加する。
2. `devbrain run` を追加し、route / gate / closeout / research / TDD plan を 1 packet にまとめる。
3. `skills/engineering-autopilot/` を薄い CLI wrapper として repo に置く。
4. PR packet generator と finish planner を追加する。
5. Obsidian / memory から候補 packet を作る read-only importer を追加する。

# engineering-autopilot roadmap

status: active
owner: nexus_ai

## 現在地

この skill は repo-owned source から runtime install copy へ同期済みです。今後は drift check を維持条件にします。

## 移行順

| slice | 内容 | 状態 |
|---|---|---|
| repo-owned source | `skills/engineering-autopilot/` を作る | done |
| thin command contract | 現行 `engineering_brain` CLI だけを呼ぶ | done |
| runtime drift check | repo-owned source と runtime install copy の差分を dry-run で検出 | done |
| runtime install sync | `<USER_HOME>/.codex/skills/engineering-autopilot` へ `--apply` 同期 | done |
| run packet MVP | `engineering_brain run` で route / gate / closeout を統合 | done |
| research packet | source / candidate / decision を packet 化 | done |
| finish planner | merge 後の cleanup plan と opt-in hook を扱う | done |
| PR packet generator | 日本語 PR body と stopline を生成 | done |
| verification profile | task に応じた smoke / preflight 候補を返す | next |

## 採用しないこと

- skill script に repo logic を複製しない。
- 未実装 command を live 手順として書かない。
- runtime copy を正本にしない。

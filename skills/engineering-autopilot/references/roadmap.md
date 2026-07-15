# engineering-autopilot roadmap

status: active
owner: nexus_ai

## 現在地

この skill は repo-owned source として作成する段階です。runtime install copy への同期はまだ行いません。

## 移行順

| slice | 内容 | 状態 |
|---|---|---|
| repo-owned source | `skills/engineering-autopilot/` を作る | current |
| thin command contract | 現行 `devbrain` CLI だけを呼ぶ | current |
| run packet MVP | `devbrain run` で route / gate / closeout を統合 | planned |
| research packet | source / candidate / decision を packet 化 | planned |
| PR packet generator | 日本語 PR body と stopline を生成 | planned |
| runtime drift check | repo-owned source と runtime install copy の差分を dry-run で検出 | current |
| runtime install sync | `<USER_HOME>/.codex/skills/engineering-autopilot` へ `--apply` 同期 | blocked until approval |

## 採用しないこと

- skill script に repo logic を複製しない。
- 未実装 command を live 手順として書かない。
- runtime copy を approval なしに切り替えない。

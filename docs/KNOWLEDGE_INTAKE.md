# Knowledge Intake

## 目的

ローカルで悩んだこと、発見したこと、既存 skill や Obsidian に溜まった知見を、`engineering-brain` の実行可能な正本へ安全に昇格する。

## 位置づけ

| layer | 役割 | repo への扱い |
|---|---|---|
| Obsidian | raw note、仮説、悩み、リンク、探索 | intake |
| local memory / prior run | 再利用できそうな失敗、判断、証跡 | candidate |
| external docs / GitHub | 公式・一次情報、OSS 候補、先行事例 | source packet |
| `engineering-brain` | 採用済み rule、gate、ADR、test、registry | SSOT |

## Intake flow

1. 候補を拾う: Obsidian、local memory、repo issue、PR review、失敗ログ、既存 skill から候補を抽出する。
2. 事実を分ける: source、推測、不明、古い可能性、current verification required を分離する。
3. 採用単位へ畳む: rule、gate、ADR、test、registry item、runbook、skill entry のどれにするか決める。
4. 既存を探す: repo-local、workspace shared、公式機能、GitHub / OSS を見て、車輪の再発明を避ける。
5. PR にする: 採用理由、非採用理由、停止線、検証結果を PR packet に入れる。
6. 反映する: review comment や失敗を policy / gate / test に吸収する。

## 採用形式

| knowledge type | 置き場所 | 必須条件 |
|---|---|---|
| 設計判断 | `docs/adr/ADR-*.md` | 後続 PR の前提になる |
| 開発標準 | `docs/STANDARDS.md` | 既存標準と矛盾しない |
| 運用モデル | `docs/OPERATING_MODEL.md` | command / gate / stopline がある |
| 技術 source | `registry/technology-sources.yaml` | 公式または一次情報を含む |
| local learning | `registry/local-learnings.yaml` | raw chat log ではなく再利用可能な rule / failure pattern に圧縮する |
| adoption unit | `registry/adoption-units.yaml` | trigger と evidence がある |
| regression | `tests/` | 失敗を再発防止できる |
| runtime entry | `skills/engineering-autopilot/` | CLI を呼ぶ薄い入口に留める |

## 自動化方針

自動化してよいのは、候補抽出、分類、重複検出、採用 PR packet 作成、local test 実行まで。

自動化で行わないもの:

- raw note の無審査投入。
- raw chat log の直接投入。
- secret / credential / 個人絶対パスを含む内容の取り込み。
- public 化、外部共有、release、告知。
- merge、destructive delete、repo settings / auth 変更。

## Obsidian 連携

Obsidian は「入口」として扱う。正本化する時は、Obsidian note をそのまま貼らず、次の短い packet へ圧縮してから repo へ入れる。

```yaml
source: obsidian|memory|pr_review|failure_log|official_docs|github
claim:
evidence:
adoption_target: adr|docs|registry|tests|skill
risk:
verification:
decision: adopt|hold|reject
```

## Done

knowledge intake が完了したと言えるのは、採用単位が repo 内に入り、対応する test / closeout / ADR / source pointer のいずれかで再確認できる時だけ。

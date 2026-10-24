# 旧 dev-brain 吸収台帳

status: active-ledger
owner: nexus_ai
checked_at: 2026-07-16 JST

## 結論

古くなった `<PROJECTS_ROOT>/dev-brain` の clone は分類を終え、すでに存在しない。

読み取り専用の調査で、`codex/dev-brain-autopilot-pr` 上に旧リモート枝より先へ進んだ手元だけのコミットが 4 件見つかった。正本の repo は引き続き `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain` だが、これらの旧コミットには有用な知識が含まれているため、手元から削除する前に吸収するか、明示的に不採用とする必要がある。

## 調査した旧コミット

| commit | タイトル | 吸収の判断 |
|---|---|---|
| `729948f` | Add thread handoff packet | cutover の経緯と承認停止線の証跡として吸収 |
| `f23726c` | Research engineering autopilot prior art | 先行事例の情報源クラスタと命名指針として一部吸収 |
| `d9ed90a` | Adopt engineering-brain naming | 現在の repo / skill 命名の決定に吸収 |
| `ead0ad4` | Clarify SSOT drift boundaries | 古い clone と稼働中 SSOT の切り分けとして吸収 |

## 残した知識

手元だけにあった旧枝の有用な内容は、次のルールとして残している。

- `engineering-brain` が稼働中の repo SSOT である。旧 `dev-brain` は古い clone であり、再びレビュー面にしてはならない。
- `engineering-autopilot` は承認ゲート付きのライフサイクル実行器であり、公開 / push / マージを自律的に行うものではない。
- 先行事例の調査は候補ゲートである。GitHub、公式ドキュメント、OSS の例、コミュニティの手法は作業の参考にできるが、情報源があることは採用を意味しない。
- 旧 `dev-brain` の初期履歴に望ましくない名義の帰属リスクがあったため、履歴を作り直す（clean-history recreation）方式を選んだ。
- 外部レビューの前に、GitHub CLI の有効アカウント、commit の author、committer、GitHub 上の帰属をコミットごとに確認しなければならない。
- SSOT のずれを扱うときは「現在稼働中の面」と「移行先の候補」を分けること。1 行に混ぜると誤った安心感を生む。
- 古い clone を手元で破壊的に削除してよいのは、この台帳と最終の差分確認で未吸収のものがないと示せた後に限る。既知の古い clone については、この削除ゲートを満たした。

## 保持した情報源クラスタ

| クラスタ | 残した役割 |
|---|---|
| GitHub Copilot cloud agent / CLI autopilot | ライフサイクルの用語と、autopilot は明確に定義されたタスクで最もよく機能するという注意点 |
| OpenAI Agents SDK / guardrails / tracing | handoff、承認待ちの一時停止、guardrails、trace 証跡の用語 |
| Google Engineering Practices | レビューとコードベース健全性の基準 |
| DORA | デリバリーと不安定性の指標の候補 |
| Google SRE | 運用上の保証 / インシデント / リリースエンジニアリングの用語 |
| OpenSSF Scorecard | セキュリティ態勢とサプライチェーンの経験則の情報源 |
| Backstage | カタログ / 開発者ポータルの参考。UI 要件ではない |
| OpenHands / SWE-agent / Aider 系 | 変化の速い先行事例。再確認しない限り参考扱いのみ |

## 古い clone の削除ゲート

新たに古い `<PROJECTS_ROOT>/dev-brain` や `<PROJECTS_ROOT>/nexus-dev-kernel` のディレクトリが見つかった場合は、次を実行する。

```powershell
git -C <PROJECTS_ROOT>/dev-brain status --short --branch
git -C <PROJECTS_ROOT>/dev-brain diff --name-only origin/codex/dev-brain-autopilot-pr..HEAD
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain status --short --branch
```

旧ファイルのどれかに、この repo に反映されていない情報源、ルール、テスト、移行の事実が含まれている場合は、削除を止めたままにする。

現在わかっている状態: 旧 GitHub repo、手元の古い clone、旧 `dev-brain-autopilot` の runtime skill copy はすべて削除済み。この repo に残る `dev-brain` への言及は、移行の履歴記録である。現在の Python module は `engineering_brain`。

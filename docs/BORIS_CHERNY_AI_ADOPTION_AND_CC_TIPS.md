# Boris Cherny — Steps of AI Adoption & Claude Code 実運用 tips(adopted digest)

status: candidate-digest (field-review pending)
owner: nexus_ai
checked_at: 2026-07-19 JST
source_pointers:
  - https://x.com/bcherny/status/2077929379661844559 (2026-07-17, thread + artifact "Steps of AI Adoption")
  - https://www.explainx.ai/blog/boris-cherny-steps-ai-adoption-claude-code-july-2026 (framework 全表の二次解説)
  - https://howborisusesclaudecode.com/ (121+ tips 集約)
  - https://github.com/shanraisshan/claude-code-best-practice (Boris+community tips 集約)

> これは外部 raw の丸写しではなく digest(再利用可能 rule 化)。一次(本人 artifact/Doc)との突合と自環境での field review は残タスク。

## Steps of AI Adoption(段階 0-4、括弧内=同時 agent 数)

前進は tokens 増では起きない。各段で「次ボトルネックを壊す」+「次ガードレールを積む」を対で行う。

| 段階 | 役割 | 実態 | ボトルネック | 前進ガードレール |
|---|---|---|---|---|
| 0 Gated (0) | ブロック | 旧/軽量モデルのみ承認、出力は手元止まり | レガシー security/承認、cost-per-token 抑制優先 | 経営合意、blocker エスカレ、安全 deploy 枠 |
| 1 Assisted (~1) | agent とペアプロ | 1セッション、ほぼ全変更を人レビュー | 自分の注意力と低信頼 | 自己検証ループ(test/build/lint/e2e)、auto mode、自動 code review |
| 2 Parallel (5-10) | オーケストレーター | Claude 自己検証、auto mode、自動 code+security review、人は最終 diff のみ | 複数 diff のレビューと steering | code context 付与、worktree 分離、loop/routine 化、Claude が Claude を起動 |
| 3 Supervised autonomy (~100) | マネージャーのマネージャー | Claude がほぼ全コード、保守が background 常時 | ループ信頼とチーム意思決定スループット | ドメイン別自動化、CLAUDE.md に標準 encode、コスト監視 |
| 4 AI-native (1000+) | 意図で舵取る VP | 大半の agent を Claude が起動、人は例外監視 | 何を自動化するか+作業種別ごとの guardrail | workflow 別コスト上限、例外監視、自動化と人間 gate 分離 |

> ⚠️ 上表の **products / guardrails / What it looks like 列は二次解説(explainx.ai)由来で一次 artifact 未突合**。段階名・役割・ボトルネックの骨子は Boris の一次スレッドに pointer あり(本文突合は field review 残)。骨子・細部とも「未確定」として扱い、確定引用しないこと(盲点8)。
>
> 事実(一次): Anthropic は step 3→4、Boris 個人は step 4(本人談)。自環境の step 判定は下記「自環境アセスメント」参照(未検証)。

## Claude Code 実運用 13 tips

1. 5 並列(タブ 1-5、通知で入力待ち検知)
2. claude.ai/code の web セッション 5-10 も併用しさらに並列
3. 最上位 Opus を thinking で常用(steer 少・tool use 強)※原典は Opus 4.5 期 → 現行は Opus 4.8 常用+難所 Fable に読み替え
4. team 共有 CLAUDE.md、誤りが出たら追記(週複数回・git 管理)
5. PR で @claude タグ → GitHub Action で CLAUDE.md 更新
6. Plan mode で開始(shift+tab 2回)→ 詰めてから auto-accept
7. スラッシュコマンド .claude/commands/(例 /commit-push-pr)
8. サブエージェント .claude/agents/(簡素化・検証など)
9. PostToolUse hook で自動整形(最後の 10%)
10. permission 事前許可 .claude/settings.json(skip でなく whitelist)
11. MCP 連携 .mcp.json(Slack/BigQuery/Sentry 等)
12. 長時間タスクは background agent / stop hook で完了検証
13. 検証ループ構築(Claude に自己テストさせる=品質 2-3x)

## 自環境アセスメント(未検証・私見 / 要 field review)

> このセクションは digest(事実)ではなく Claude の未検証の見立て。field review で確定するまで事実として引用しない。

- 現 step 仮説: **step 2(Parallel)近辺**(Claude/Cursor/Codex 移行の途上)。未検証。
- 実装済みと思われる: tips 1・4・6-10(番号付き pane / CLAUDE.md 規約 / スキル群)。未検証。
- ギャップ候補: 2(web 並列)・5(@claude PR)・13(検証ループの明文化)、step 2→3 のガードレール(worktree 分離徹底・routine 化)。未検証。

## 運用保証への接続(reusable / 成長)

- **maturity 自己評価** → `registry/adoption-units.yaml` の `ai_adoption_maturity_advisory`(G1 advisory / status: candidate)。`ai_adoption_review` / `tooling_migration` 時に「現 step + 次ボトルネック + 次ガードレール」を対で挙げる。
- **検証ループ(tip #13)** → 新規 gate を作らず既存 `tdd_regression_gate`(G4 operational)へ写像(reinvention 回避)。
- **成長(compounding)** → `engineering_brain/data/local-learnings.yaml` の各 packet に `review_trigger`(cycle ベース)+ `field_review: pending`。field review を通すたび adopt を精緻化し、二次由来細部を一次突合へ格上げする。
- **durable decision** → ADR 化は未実施(theme-grep + 目視 GO が要るため保留)。

## 停止線 / 注意

- モデル指定(Opus 4.5)は dated。現行モデルへ読み替えること。
- framework の各セルは二次解説由来。一次 artifact/Doc と突合してから "確定" とする。
- 自環境への適用は field review(小さく試す→効果観測→adopt/hold/reject)を経る。

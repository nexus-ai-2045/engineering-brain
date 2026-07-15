---
name: engineering-autopilot
description: engineering-brain を通して開発作業を設計、既存調査、TDD、実装、検証、運用保証、PR準備、人間レビュー停止線まで進めるときに使う。ユーザーが「自走」「開発ブレイン」「ベスプラ確認」「車輪の再発明回避」「PRまで」「運用保証」「ローカルの学びを吸収」と言ったら使う。
---

# Engineering Autopilot

この skill は `engineering-brain` repo の薄い入口です。判断ロジックは skill 内に複製せず、repo の CLI / docs / registry を正本として使います。

## 起動

1. `references/lifecycle.md` を読む。
2. 対象 repo と作業範囲を確認する。
3. `engineering-brain` repo から、現行 CLI で使える gate を実行する。

```powershell
python -m devbrain route --task "<task>" --json
python -m devbrain gate --trigger implementation --json
python -m devbrain catalog --domain <domain> --json
python -m devbrain closeout --repo . --json
```

## 必須規律

- 作る前に、repo-local / workspace shared / 公式機能 / OSS 候補を確認する。
- source catalog は採用ではない。`candidate` / `adopted` / `hold` / `rejected` を分ける。
- TDD または対象 smoke なしに実装完了と言わない。
- local で悩んだことは raw chat ではなく、docs / registry / test / ADR のどれかへ薄く吸収する。
- push、PR作成、merge、remote branch削除、公開、visibility変更、credential変更は current-turn explicit approval まで止める。
- runtime install copy への同期は、この repo-owned skill が検証された後の別承認作業にする。

## 現在の範囲

この PR では repo-owned source を作るだけです。

- 作る: `skills/engineering-autopilot/`
- 作る: skill-facing roadmap / lifecycle reference
- しない: `<USER_HOME>/.codex/skills/engineering-autopilot` への install
- しない: runtime skill 切替
- しない: GitHub visibility 変更

## Closeout

完了報告前に最低限これを確認します。

```powershell
python -m pytest -q
python -m devbrain closeout --repo . --json
```

外部操作が必要な場合は、実行前に「何が外から見えるか」「何をレビュー済みか」「何をまだしていないか」を分けて、人間の明示 yes を待ちます。


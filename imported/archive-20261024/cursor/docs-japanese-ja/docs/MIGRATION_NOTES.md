# 移行メモ

status: active
owner: nexus_ai
checked_at: 2026-07-16 JST

## 経緯

`engineering-brain` は、`nexus-ai-2045/dev-brain` を履歴を整理して private に作り直したもの（clean-history recreation）として作られた。

旧 `dev-brain` repo は移行の検証中は private のまま残し、2026-07-15 JST にその場の承認を得てから削除した。新しい repo は、作業途中の履歴を丸ごと取り込むのではなく、レビュー済みの snapshot から始まっている。

## 方針

- `nexus-ai-2045/dev-brain` は、移行の検証と明示的な承認の後に削除した。
- `nexus-ai-2045/engineering-brain` は public である。
- public 化は、別のレビュー資料（review packet）と、その会話での承認を経て完了した。
- runtime skill のインストール先は、テスト済みの同期と適用後の検証を経て `engineering-autopilot` に切り替えた。
- 旧 `<USER_HOME>/.codex/skills/dev-brain-autopilot` の runtime copy は、`engineering-autopilot` が同期済みの投影になった後に削除した。
- 現在の Python module は `engineering_brain`。ハイフンなしの旧 package / command 名は互換用としては残していない。
- 後から古い `<PROJECTS_ROOT>/dev-brain` clone で見つかった手元だけのコミットは、`docs/LEGACY_DEV_BRAIN_ABSORPTION.md` で評価した。古い手元の clone はもう存在しない。

## 最初の snapshot の確認

元の snapshot は、次をすべて満たしてから受け入れた。

- `python -m pytest -q`
- `python -m engineering_brain closeout --repo . --json`
- `nexus-ai-2045` の GitHub 名義確認（identity probe）
- 個人パス / 旧名義のスキャン
- 作成前に移行先 repo が存在しないことの確認
- 元 repo の公開範囲（visibility）の確認

## 次の作業

1. `<PROJECTS_ROOT>/ssot-registry.yaml` を public の `engineering-brain` と揃えておく。
2. PR packet の生成と検証プロファイル（verification profile）を追加する。
3. console script は `engineering-brain`、Python module は `engineering_brain` のまま維持する。
4. 名義ゲート、ライフサイクル FSM、PR packet、skill 同期の順でロードマップを進める。
5. 残っている `dev-brain` への言及は、稼働中のパス確認で別と判明しない限り、移行の履歴参照として扱う。

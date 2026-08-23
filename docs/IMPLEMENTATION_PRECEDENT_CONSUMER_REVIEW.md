# 先行実装リサーチconsumer 人間レビュー

## 推奨判断

配置方針は採用し、2 repositoryを別々の変更として維持する。

1. `nexus-ai-skills`: `implementation-precedent-research`の正本。
2. `engineering-brain`: `engineering-autopilot`とresearch packetから呼ぶconsumer。
3. runtime: 両repoのレビュー・統合後に別承認で同期するprojection。

## 今回のengineering-brain差分

- research packetへ`precedent_research`consumer契約を追加した。
- required field追加に伴い、research packetをversion 1から2へ上げた。
- `wrap / extend / adopt_oss / build`の前に先行実装評価を要求した。
- 正本skillが未配布または根拠不足なら`hold`へ戻す規則を追加した。
- skill本体はこのrepoへ複製していない。

## 検証

- RED: packet、schema、autopilotにconsumer契約がなく3 testが失敗。
- GREEN: focused test 5件成功。
- full suite: 98件成功。
- CLI smoke: research packet v2にconsumer契約が出力された。
- `git diff --check`: errorなし。

pytest終了後、Windowsの共有一時folder
`pytest-current`のcleanupで`PermissionError`が出る既知の環境警告がある。
test processの終了コードは0で、98件は成功している。

## 人間判断

| 判断 | 推奨 | 影響 |
|---|---|---|
| 2 repo構成 | 採用 | 横断skillの再利用性と責務分離を維持 |
| research packet v2 | 採用 | required field追加を互換変更と偽らない |
| 正本先行 | 採用 | consumerだけ先に統合される状態を避ける |
| runtime同期 | 今はしない | 未commit draftをhome runtimeへ入れない |
| 既存research skill整理 | 今はしない | behavioral eval前の削除・縮退を避ける |

## 推奨する統合順

1. `nexus-ai-skills`の正本skillをレビューする。
2. 正本側をcommit / push / PRするか、現在会話で別途判断する。
3. `engineering-brain`のconsumer差分をレビューする。
4. 正本の参照可能性を確認してからconsumer側をcommit / push / PRする。
5. 両方の統合後、Codex / Claude Code runtime同期を別承認する。

## 現在の停止境界

- 両repositoryとも専用worktree内の未commit差分。
- commit、push、PR、mergeは未実施。
- home runtime同期は未実施。
- 既存skillの削除・deprecateは未実施。

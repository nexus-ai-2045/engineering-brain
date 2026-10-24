## 目的


## 変更内容


## Research / reinvention check

- [ ] repo-local truth を確認した
- [ ] official docs / primary source を確認した
- [ ] GitHub evidence を確認した
- [ ] `reuse / wrap / extend / adopt_oss / build / hold` の判断を書いた

## TDD / 検証

- [ ] `python -m pytest -q`
- [ ] `python -m compileall -q engineering_brain tests`
- [ ] `python -m engineering_brain closeout --repo . --json`
- [ ] 必要なら targeted test / smoke / E2E を実行した

## Security / operation

- [ ] secret / token / credential を混ぜていない
- [ ] 実ユーザー名入りローカル絶対パスを混ぜていない
- [ ] 外部状態を変える操作がある場合、承認境界を書いた
- [ ] public / external send / visibility / release 境界を分離した
- [ ] hook / settings / auth / production / destructive action の有無を書いた

## Visible scope

- 外から見える内容:
- 未確認:
- 残リスク:

## Human stoplines

- [ ] PR作成は現在会話の承認済み
- [ ] merge は別途現在会話の承認が必要
- [ ] public 化 / 外部公開 / visibility 変更は別途 repo ごとの明示承認が必要

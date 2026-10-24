# 運用モデル

## 目的

engineering-brain は、開発に入る前の判断、実装中の検証、完了前の運用保証を同じ形で扱うための実行ゲート repo です。

## 基本フロー

1. `route`: task から必要な adoption unit と停止線を選ぶ。
2. `gate`: trigger から実行すべき check と不足条件を返す。
3. `verify`: repo 検出に応じた verification profile を plan-only で返す。
4. `closeout`: profile に基づく evidence（pass / fail / not_run / not_applicable）と外部公開境界を分離して返す。

## 保証の意味

保証は「常に成功する」という意味ではありません。

- 確認済みは source と check を持つ。
- 未確認は unknown として残す。
- 人間承認が必要なものは実行せず止める。
- 運用保証を名乗る時は、再現可能な command または手順を持つ。

## 初期採用標準

- FDE best-practice adoption gate
- AI 開発標準カードと Living Harness
- TDD / regression gate
- NIST SSDF
- SLSA
- OWASP SAMM
- DORA metrics
- OpenSSF Scorecard
- agent containment / security guidance SOP

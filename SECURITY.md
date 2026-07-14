# Security

engineering-brain はローカル-first の開発ゲート repo です。public 化、外部送信、release、広範な共有は current conversation の明示承認まで行いません。

## 扱う境界

- `.env`、API key、cookie、credential、個人 profile は registry や test fixture に入れない。
- agent、browser、connector、hook、settings に触る作業は `agent_containment_gate` を通す。
- 公開・外部送信・GitHub visibility 変更は `human_publication_review_gate` で停止する。

## 報告

ローカル運用中の問題は、再現手順、対象 gate、期待した判定、実際の判定を添えて issue またはローカル report に残す。

# 初期採用標準

engineering-brain の初期 seed は、確実性が高く、開発ゲートへ落としやすいものだけに限定する。

| 標準 | 使い方 |
|---|---|
| NIST SSDF | secure development practice の参照軸 |
| SLSA | supply chain / provenance / build integrity の参照軸 |
| OWASP SAMM | software assurance maturity の参照軸 |
| DORA metrics | delivery / operations health の参照軸 |
| OpenSSF Scorecard | repo security posture の参照軸 |
| CNCF Platform Engineering Maturity Model | platform / developer experience maturity の参照軸 |
| FDE best-practice adoption gate | 採用単位、保証tier、insufficient_if の型 |
| AI開発標準カードと Living Harness | 開発開始カード、PDCA、昇格階段 |
| Go / Bun / Vue / Nuxt / Node / Next.js / Python / Rust / Azure / Server / Kubernetes / Terraform / GitHub Actions / Docker / PostgreSQL 公式docs | 技術別 gate の候補 source |

各標準は丸写ししない。`registry/adoption-units.yaml` の adoption unit に落ちるものだけを採用し、未成熟なものは candidate または hold に残す。

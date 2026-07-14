# ベスプラ source catalog

obsidian_check: `Documents/brain/knowledge-operation-dashboard.md` / `FDE/operating-card.md` / `Documents/brain/pre-execution-fact-check-gate.md` / `Documents/brain/scope-routing-gate.md`
scope_route: `multi-file-implementation` / engineering-brain repo local / external-actionなし

## 目的

Go、Bun、Vue/Nuxt、Azure、サーバー/API、コンテナ/Kubernetes などの開発ベストプラクティスを、丸写しではなく engineering-brain の adoption unit へ落とす入口 catalog として保存する。

`VUN` は音声入力・表記ゆれの可能性があるため、現時点では `[推測] Bun` と `[推測] Vue/Nuxt` の両方を分けて扱う。どちらかに確定したら片方だけを実プロジェクト gate に昇格する。

## 初期 source

| domain | source | engineering-brain での扱い |
|---|---|---|
| Go | Go 公式 Effective Go / Code Review Comments / Test Comments / govulncheck | `go_official_engineering_gate` |
| Bun | Bun 公式 docs / test runner / package manager / bundler | `bun_toolchain_gate` |
| Vue/Nuxt | Vue security / Vue style guide / Nuxt performance / Nuxt Security | `vue_nuxt_frontend_gate` |
| Azure | Azure Well-Architected Framework / Architecture Center / cloud app best practices | `azure_well_architected_gate` |
| Server/API | OWASP ASVS / OWASP API Security Top 10 / OWASP Top 10 / Twelve-Factor App | `server_api_security_gate` |
| Container/Kubernetes | Kubernetes production environment / Kubernetes docs / SLSA / OpenSSF Scorecard | `container_kubernetes_production_gate` |
| Node/Express | Node.js security best practices / Express production security / OWASP Node.js Cheat Sheet | `node_express_security_gate` |
| Next.js | Next.js production checklist / data security / Vercel production checklist | `nextjs_production_gate` |
| Python | Python Packaging User Guide / Python docs / pytest good practices / OpenSSF Python secure coding | `python_packaging_testing_gate` |
| Rust | Rust Book / Rust API Guidelines / RustSec advisory database | `rust_security_dependency_gate` |
| Terraform | HashiCorp Terraform style / recommended practices / security foundations | `terraform_iac_gate` |
| GitHub Actions | GitHub Actions security docs / secure use reference | `github_actions_ci_security_gate` |
| Docker | Docker Engine security / OWASP Docker Security Cheat Sheet | `docker_container_security_gate` |
| PostgreSQL | PostgreSQL security info / current docs | `postgresql_security_gate` |
| GitHub repo lifecycle | GitHub rename / duplicate / template repository docs | `github_repo_lifecycle_gate` |

## 採用ルール

- `candidate` は「知っている」だけ。実プロジェクトでは `gate_hint` を smoke / test / review checklist に落としてから採用する。
- 外部状態を変える操作、クラウド作成、Terraform apply、GitHub visibility、公開、外部送信はこの catalog では許可しない。
- バージョンや major 系が重要なものは、プロジェクト側の lockfile / runtime version / official docs を再確認してから使う。
- repo rename / recreate / archive / visibility 変更は source catalog だけでは許可しない。対象 repo、見える範囲、history、redirect、local remote、runtime skill、rollback を review packet にする。

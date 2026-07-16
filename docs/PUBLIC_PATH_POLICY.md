# Public path policy

status: active
owner: nexus_ai
checked_at: 2026-07-14 JST

## 方針

公開候補の repo / docs / registry / PR 文面では、実ユーザー名を含むローカル絶対パスを書かない。

禁止例:

```text
C:/Users/<name>/Projects/...
/Users/<name>/Projects/...
```

許可する表現:

```text
<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
<USER_HOME>/.codex/skills/engineering-autopilot
<REPO>/docs/LOCAL_SSOT.md
```

## なぜ必要か

ローカル絶対パスは、公開時にユーザー名、ホームディレクトリ構造、作業端末の構成を外へ出す。これは secret ではなくても、公開候補 artifact では不要な個人情報・環境情報である。

## 運用保証

`python -m engineering_brain closeout --repo . --json` は `public_path_redaction_gate` を実行する。

この gate は repo 内の Markdown / YAML / JSON / TOML / Python / shell / PowerShell / JavaScript / TypeScript / config / `Dockerfile` / `.env.example` などの公開候補 text file を走査し、次の形式を検出したら `overall=blocked` にする。

- Windows: `C:/Users/<name>` / `C:\Users\<name>`
- macOS: `/Users/<name>`

## 例外

例外は原則作らない。どうしても実絶対パスが必要な場合は、公開候補 artifact ではなく private-only の local runbook に置き、公開前に必ず `<PROJECTS_ROOT>` / `<USER_HOME>` / `<REPO>` へ置換する。

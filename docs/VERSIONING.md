# Versioning

status: active
current_version: 0.2.0
scheme: SemVer
source_of_truth: `pyproject.toml`

## 方針

`engineering-brain` は SemVer (`MAJOR.MINOR.PATCH`) を使います。public seed は `0.1.0`、現行は `0.2.0` です。

version は更新のたびに自動 bump しません。各 PR で必ず version を上げると意味が薄くなるため、version bump は release / capability boundary ごとに明示的に行います。

## 同期対象

次の version surface は一致している必要があります。

| surface | 役割 |
|---|---|
| `pyproject.toml` | 正本 |
| `engineering_brain.__version__` | Python package surface |
| `skills/engineering-autopilot/manifest.yaml` | runtime skill surface |

確認 command:

```powershell
python -m engineering_brain version --json
```

## bump の目安

- PATCH: typo、docs correction、bug fix、互換性を壊さない小修正。
- MINOR: research packet、PR packet generator、local learning registry など新しい local capability。
- MAJOR: `1.0.0` 以降の外部 contract break。

## release / tag policy

Git tag (`v0.2.0`) と GitHub Release は、version file の更新とは別の承認境界です。実行前に次を提示します。

- target repo
- tag name
- release notes
- visible files / history
- tests / closeout / scan result

## automation policy

現時点で自動化するのは version surface の同期チェックです。自動 bump はまだしません。

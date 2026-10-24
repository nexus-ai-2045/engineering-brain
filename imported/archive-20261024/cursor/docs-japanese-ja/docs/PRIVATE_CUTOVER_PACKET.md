# private cutover 資料

status: executed-private
owner: nexus_ai
checked_at: 2026-07-15 JST

## 結論

`engineering-brain / engineering-autopilot` への移行は、**履歴を整理して private に作り直し、移行メモを残す方式（private recreate with clean history and migration notes）** を推奨する。

理由:

- `dev-brain` は作業区間として始まり、将来 public 化する名前と責務があとから固まった。
- public 前に repo 名、local directory、repo-owned skill、runtime skill を揃える方が、後続の説明と運用が単純になる。
- 既存 PR history は clean-history 方針により新 repo へ持ち込まない。公開候補 repo には、整理済み snapshot と migration notes だけを持ち込める。
- GitHub rename は便利だが、redirect、Actions、external reference、local remote の更新が残る。作業区間を clean に閉じたい今回の目的には recreate が合う。

## 決定

```text
target_name: engineering-brain / engineering-autopilot
current_repo: nexus-ai-2045/dev-brain
target_repo: nexus-ai-2045/engineering-brain
visibility: private
recommended_history_policy: clean_history_with_migration_notes
local_target: <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
runtime_skill_target: <USER_HOME>/.codex/skills/engineering-autopilot
legacy_repo_policy: keep_private_reference
public_visibility: out_of_scope
```

## 移すもの

| 層 | 移行元 | 移行先 | 方針 |
|---|---|---|---|
| GitHub repo | `nexus-ai-2045/dev-brain` | `nexus-ai-2045/engineering-brain` | 明示的な承認の後に private の移行先を作る |
| 手元の repo | `<PROJECTS_ROOT>/Documents/repos/second-brain/dev-brain` | `<PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain` | 明示的な承認の後に、まっさらな移行先ディレクトリを作る |
| repo-owned skill | 将来の `skills/dev-brain-autopilot` | `skills/engineering-autopilot` | CLI への薄い入口のみ |
| runtime skill | `<USER_HOME>/.codex/skills/dev-brain-autopilot` | `<USER_HOME>/.codex/skills/engineering-autopilot` | CLI の契約ができてから copy / 同期する |
| SSOT registry | 現在の dev-brain の項目 | engineering-brain の項目 | 同じ cutover PR で更新する |

## レビューするコマンド

以下のコマンドは旧 `dev-brain` でレビューされ、private の clean-history cutover で実行された。

```powershell
gh repo create nexus-ai-2045/engineering-brain --private --description "Local-first engineering autopilot and development assurance brain"
New-Item -ItemType Directory -Force <PROJECTS_ROOT>/Documents/repos/engineering
git clone https://github.com/nexus-ai-2045/engineering-brain.git <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
```

履歴を作り直すため、レビュー済みの作業ツリーを、`.git`、手元の状態、キャッシュ、private な runtime 成果物を除いて、現在の repo から移行先 repo へコピーする。

```powershell
robocopy <PROJECTS_ROOT>/Documents/repos/second-brain/dev-brain <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain /E /XD .git .pytest_cache __pycache__ .engineering_brain /XF *.pyc
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain status --short
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain add .
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain commit -m "Initialize engineering brain"
git -C <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain push -u origin main
```

新しい private repo の確認が済んだら、SSOT registry と runtime の参照先を後続の作業で更新する。

## 実行前に必要な確認

- `python -m pytest -q`
- `python -m engineering_brain closeout --repo . --json`
- `python -m engineering_brain catalog --domain recreate --json`
- 個人パス / 旧名義のスキャン
- `nexus-ai-2045` の GitHub 名義確認（identity probe）
- 移行先 repo が使えるかの確認: `gh repo view nexus-ai-2045/engineering-brain`
- 元 repo は移行の検証と明示的な承認の後に削除した。
- `PUBLIC_READY.md`、`SECURITY.md`、README、docs、registry、commit 履歴の方針のレビュー

## 人の承認文

実行するターンには、次の内容を明記した承認が必要。

```text
approved_action: create private repo and local target for engineering-brain
target_repo: nexus-ai-2045/engineering-brain
target_local_path: <PROJECTS_ROOT>/Documents/repos/engineering/engineering-brain
history_policy: clean_history_with_migration_notes
visibility: private
public_visibility_change: no
```

private repo の作成と手元の移行先の作成については、実行の承認を得た。runtime skill の切り替えと public 化は、この承認の範囲外のまま。

## 切り戻し

cutover のどこかの手順が失敗したら:

- 移行メモと ADR を長く残る参照として保持する
- `dev-brain` を作り直さない
- 作りかけの手元の移行先ディレクトリは、固有の作業が含まれていないと確認してから削除する
- 移行先の private GitHub repo を作ったが採用しなかった場合は、private のまま残して blocked と記すか、明示的な確認を得てから削除する

## やらないこと

- public 化はしない
- 外部への告知はしない
- リリースはしない
- 関係のない repo を自動で削除しない
- repo-owned skill が薄く CLI に支えられた形になるまで、runtime skill のインストール先を切り替えない

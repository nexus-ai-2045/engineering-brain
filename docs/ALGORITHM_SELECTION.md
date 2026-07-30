# アルゴリズム選定台帳

`engineering_brain/data/algorithms.json` は、定番アルゴリズムのコードを大量に複製する場所ではありません。問題条件から候補を選び、前提・反証条件・計算量・検証方法を同じ形式で比較するためのローカル正本であり、wheelにも同梱します。

## 使い方

まず問題を、入力特性と制約へ分解します。

```powershell
python -m engineering_brain algorithms select `
  --signal shortest_path `
  --signal weighted_graph `
  --constraint negative_edge `
  --json
```

候補を比較します。

```powershell
python -m engineering_brain algorithms compare `
  --id dijkstra `
  --id bellman_ford `
  --json
```

一覧は family で絞れます。

```powershell
python -m engineering_brain algorithms list --family グラフ --json
```

## 選定規則

1. `problem_signals` の一致を加点する。
2. 実際の制約が `avoid_when` に一致した候補を強く減点する。
3. `candidate` は、検証済みの `adopted` よりわずかに低く扱う。
4. 0点以下の候補は提示しない。
5. 候補0件は失敗ではなく、入力条件が不足した `unknown` として扱う。
6. 点数は採用決定ではない。対象データで `preconditions` と `verification` を確認する。

## 台帳の範囲

初期台帳は探索、整列、グラフ、動的計画法、文字列、集合照合、信頼性、ストリームの定番を扱います。新規項目は、実装断片ではなく次を揃えて追加します。

- 安定したIDと日本語名
- 問題シグナル
- 成立前提と避ける条件
- 時間・空間計算量
- 交換条件
- 対象 repo で実行可能な検証方法
- 出典

`engineering_brain run` はタスク文から判別できる範囲だけシグナルを抽出します。判別不能な場合は空の選択を返し、推測採用しません。

# KajiBalance

見えない家事を可視化し、パートナー間の負担を公平にする家事分担アプリ。

## 機能

- **ホーム** — 物理/メンタル負担比率をバーで表示、今日のタスク、感謝ポイント
- **タスク管理** — 50の定型タスク（7カテゴリ）に担当割り当て、完了チェック、感謝送信
- **負担分析** — カテゴリ別・物理vsメンタルのグラフ
- **設定** — プロフィール編集、ペア連携（招待コード）、データリセット

## 技術スタック

- Python 3.11+
- [Streamlit](https://streamlit.io/) — UI
- [Pydantic](https://docs.pydantic.dev/) — データモデル
- [Pandas](https://pandas.pydata.org/) / [Altair](https://altair-viz.github.io/) — グラフ描画
- JSONファイル — データ永続化

## セットアップ

```bash
# 依存関係インストール
uv sync

# アプリ起動
uv run streamlit run main.py
```

http://localhost:8501 でアクセス。

## 開発

```bash
# テスト
uv run pytest

# リンター
uv run ruff check src/

# 型チェック
uv run pyright src/
```

## ライセンス

MIT

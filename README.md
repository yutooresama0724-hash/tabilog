# 🧭 Tabilogy（タビロジー）— 期待と現実を記録する旅のドキュメンタリー

**🌐 公開中: https://tabilogy.streamlit.app/**

キラキラした面だけでなく、リアルな旅の体験を残すことを重視した旅の記録アプリ。

## 機能

- 🗺️ 世界地図に訪問済み・訪問予定の場所をピン表示（訪問した国は色付けされて足跡に）
- 🌈 旅の前に「期待していること」を登録
- 📷 帰国後に「実際どうだったか」「写真」「5段階評価」を追記
- 📚 期待 → 現実 を並べたカード形式の一覧
- 📱 スマホ対応レスポンシブレイアウト

## 構成

- フロント/サーバー: Streamlit
- データベース: Supabase（PostgreSQL）— アカウント・投稿・フレンド・リアクション等
- 画像: Supabase Storage（アップロード時に長辺1280px・JPEGに自動圧縮）
- スキーマ: [supabase_schema.sql](supabase_schema.sql)

## ローカルで実行

```bash
pip install -r requirements.txt
# .streamlit/secrets.toml に以下を設定
#   SUPABASE_URL = "https://<project>.supabase.co"
#   SUPABASE_KEY = "<publishable key>"
streamlit run app.py
```

## デプロイ

Streamlit Community Cloud。main への push で自動再デプロイされる。
Secrets（SUPABASE_URL / SUPABASE_KEY）は App Settings → Secrets に設定する。

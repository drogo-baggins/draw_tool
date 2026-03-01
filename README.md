# LLM Drawing Tool

自然言語のプロンプトからSVGイラストを生成し、リアルタイムで編集・プレビューして、PowerPoint (PPTX) ネイティブシェイプとしてエクスポートするStreamlitアプリです。

## 機能

- **自然言語による図の生成**: プロンプトを入力するとLLMがSVGコードを自動生成
- **リアルタイムプレビュー**: 生成・編集したSVGを即座に確認
- **SVGコードエディタ**: `streamlit-ace` によるシンタックスハイライト付きコード編集
- **Refineモード**: 既存のSVGを元にLLMへ修正指示を出せる
- **ネイティブPPTXエクスポート**: SVGパスをPowerPointの編集可能なシェイプに変換（グラデーション対応）

## ディレクトリ構成

```
draw_tool/
├── app.py               # Streamlit メインアプリ
├── llm_client.py        # LLM API クライアント
├── pptx_exporter.py     # SVG → PPTX ネイティブシェイプ変換
├── svg_processor.py     # SVG パース・変換ユーティリティ
├── requirements.txt     # Python 依存パッケージ
├── config/
│   └── llm_configs.yaml # LLM プロファイル設定
├── tests/               # テストスクリプト
└── openspec/            # プロジェクト仕様書
```

## セットアップ

### 必要環境

- Python 3.9 以上

### 1. 仮想環境の作成と依存関係のインストール

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. LLM APIキーの設定

プロジェクトルートに `.env` ファイルを作成し、APIキーを記載します：

```
OPENAI_API_KEY=sk-...
```

または、アプリ起動後にサイドバーの **Edit Profile Details** から直接入力・保存することも可能です。

### 3. アプリの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

## LLM設定

`config/llm_configs.yaml` で複数のLLMプロファイルを管理できます。サイドバーから切り替え・編集が可能です。

```yaml
configs:
  - label: "OpenAI GPT-4o"
    provider: "openai"
    model: "gpt-4o"
    base_url: "https://api.openai.com/v1"
    api_key: ""          # .env の OPENAI_API_KEY を使う場合は空欄
  - label: "Local Ollama"
    provider: "openai"   # OpenAI互換エンドポイント
    model: "llama3"
    base_url: "http://localhost:11434/v1"
    api_key: "ollama"
selected_label: "OpenAI GPT-4o"
```

## PPTXエクスポートについて

エクスポート機能は `python-pptx` と `svgelements` を使用し、SVGの図形・パス・テキスト・グラデーションをPowerPointのネイティブシェイプとして変換します。`resvg-py` (Rust製) を利用するため、Windowsでも Cairo DLL 不要で動作します。

## ライセンス

MIT License

MIT License

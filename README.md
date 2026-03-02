# LLM Drawing Tool

自然言語のプロンプトからSVGイラストを生成し、リアルタイムで編集・プレビューして、PowerPoint (PPTX) ネイティブシェイプとしてエクスポートするStreamlitアプリです。

## 機能

- **自然言語による図の生成**: プロンプトを入力するとLLMがSVGコードを自動生成
- **用途特化プロンプト**: Diagram・Icon・Infographic・Flat Illustration など用途別に最適化されたプロンプトテンプレートを自動選択（手動選択も可能）
- **コード生成モード**: LLMがPythonコード（`drawsvg`ライブラリ）を生成し、実行結果としてSVGを取得。直接SVG出力より高品質な図形を生成可能
- **ビジョンフィードバック**: ビジョン対応モデルが生成結果を画像として評価し、改善指示を元に反復的にSVGを洗練（オプション機能）
- **リアルタイムプレビュー**: 生成・編集したSVGを即座に確認
- **SVGコードエディタ**: `streamlit-ace` によるシンタックスハイライト付きコード編集
- **Refineモード**: 既存のSVGを元にLLMへ修正指示を出せる
- **ネイティブPPTXエクスポート**: SVGパスをPowerPointの編集可能なシェイプに変換（グラデーション対応）

## ディレクトリ構成

```
draw_tool/
├── app.py                  # Streamlit メインアプリ（UI・オーケストレーション）
├── llm_client.py           # LLM API クライアント（用途分類・プロンプト構築・SVG生成）
├── code_executor.py        # サンドボックスコード実行（コード生成モード用）
├── vision_feedback.py      # ビジョンフィードバックループ（SVG評価・反復改善）
├── pptx_exporter.py        # SVG → PPTX ネイティブシェイプ変換
├── svg_processor.py        # SVG パース・変換ユーティリティ
├── requirements.txt        # Python 依存パッケージ
├── prompt_templates/       # 用途別プロンプトテンプレート (YAML)
│   ├── classic.yaml        #   汎用（デフォルト）
│   ├── diagram.yaml        #   ダイアグラム・フローチャート
│   ├── icon.yaml           #   アイコン・シンボル
│   ├── infographic.yaml    #   インフォグラフィック・データ可視化
│   └── flat_illustration.yaml  #   フラットデザインイラスト
├── config/
│   └── llm_configs.yaml    # LLM プロファイル設定
├── tests/                  # テストスクリプト
└── openspec/               # プロジェクト仕様書
```

## セットアップ

### 必要環境

- Python 3.9 以上
- OpenAI互換APIキー（GPT-4o 等）

> **ビジョンフィードバック機能を使用する場合**: 画像入力に対応したモデル（GPT-4o、GPT-4 Turbo with Vision 等）が必要です。この機能はオプトインのため、OFFにしている場合はテキスト専用モデルでも動作します。

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

## アーキテクチャ概略

### 生成パイプライン

```
ユーザープロンプト
    │
    ▼
┌─────────────────────────┐
│  用途自動分類            │  llm_client.py: classify_purpose()
│  (keyword → LLM fallback)│  キーワードマッチ → ヒットしなければLLMで分類
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│  テンプレート選択        │  prompt_templates/*.yaml から用途別テンプレート読込
└─────────┬───────────────┘
          ▼
┌─────────────────────────────────────────────┐
│  SVG生成（2モードから選択）                   │
│                                              │
│  [Direct SVG]           [Code Generation]    │
│  LLMがSVGタグを         LLMがPythonコードを   │
│  直接テキスト出力        出力→サンドボックス    │
│                         実行→SVG取得          │
│  llm_client.py          llm_client.py +      │
│                         code_executor.py      │
└─────────┬───────────────────────────────────┘
          ▼
┌─────────────────────────┐
│  [オプション]            │  vision_feedback.py: refine_loop()
│  ビジョンフィードバック   │
│  ループ                  │  SVG → PNG変換(resvg) → Vision API評価
│                          │  → 改善指示付きで再生成 → 繰り返し
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│  SVGプレビュー           │  app.py: base64エンコード → HTMLレンダリング
│  + コードエディタ        │
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│  PPTXエクスポート        │  pptx_exporter.py: SVGパス→PowerPointシェイプ変換
└─────────────────────────┘
```

### 各モジュールの役割

| モジュール                | 責務                                                                                                                                                                       |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app.py`                  | StreamlitによるUI表示、ユーザー入力の収集、各モジュールのオーケストレーション                                                                                              |
| `llm_client.py`           | OpenAI互換APIとの通信、用途自動分類（キーワード→LLMフォールバック）、YAMLテンプレートの読込・変数展開、Direct SVG / Code Generation の2モード分岐                          |
| `code_executor.py`        | LLMが生成したPythonコードのサンドボックス実行。AST解析によるimportホワイトリスト検証（`drawsvg`, `math`, `colorsys`, `random` のみ許可）、subprocess分離、10秒タイムアウト |
| `vision_feedback.py`      | SVGを `resvg_py` でPNG変換し、Vision APIに送信して視覚的評価を取得。評価結果を改善指示としてLLMに渡し、SVGを反復的に洗練                                                   |
| `pptx_exporter.py`        | SVGの図形・パス・テキスト・グラデーションをPowerPointのネイティブ編集可能シェイプに変換                                                                                    |
| `svg_processor.py`        | SVGのパース・変換ユーティリティ                                                                                                                                            |
| `prompt_templates/*.yaml` | 用途別のシステムプロンプトテンプレート。分類キーワード、Direct SVG用プロンプト、Code Generation用プロンプトを定義                                                          |

### ビジョンフィードバックの動作詳細

ビジョンフィードバック機能をONにした場合、初回生成の後に以下のループが `max_iterations` 回（デフォルト3回、最大5回）繰り返されます：

1. **SVG → PNG変換**: `resvg_py` を使用してSVGをラスター画像に変換
2. **Vision API評価**: PNGをbase64エンコードしてVision対応モデルに送信。視覚的な整列性・色彩調和・テキスト配置・プロフェッショナル性・プロンプト忠実度の5観点で評価し、改善指示を返却
3. **改善指示付き再生成**: 評価結果を元のプロンプトに付加して、LLMにSVGを再生成させる

各イテレーションのバージョンはUIのスライダーで切り替え・比較可能です。

### API呼び出し回数の目安

| 操作                                                    | API呼び出し回数            |
| ------------------------------------------------------- | -------------------------- |
| 用途自動分類（キーワードヒット時）                      | 0回                        |
| 用途自動分類（LLMフォールバック時）                     | 1回                        |
| SVG生成（Direct SVG / Code Generation）                 | 1回                        |
| ビジョンフィードバック（1イテレーション）               | 2回（評価1回 + 再生成1回） |
| **典型的な1回の生成（Refinement OFF）**                 | **1〜2回**                 |
| **典型的な1回の生成（Refinement ON, 3イテレーション）** | **7〜8回**                 |

> ビジョンフィードバック使用時は、生成用モデルとビジョン評価用モデルに同じLLMプロファイル設定が使用されます。

## LLM設定

`config/llm_configs.yaml` で複数のLLMプロファイルを管理できます。サイドバーから切り替え・編集が可能です。

```yaml
configs:
  - label: "OpenAI GPT-4o"
    provider: "openai"
    model: "gpt-4o"
    base_url: "https://api.openai.com/v1"
    api_key: "" # .env の OPENAI_API_KEY を使う場合は空欄
  - label: "Local Ollama"
    provider: "openai" # OpenAI互換エンドポイント
    model: "llama3"
    base_url: "http://localhost:11434/v1"
    api_key: "ollama"
selected_label: "OpenAI GPT-4o"
```

## PPTXエクスポートについて

エクスポート機能は `python-pptx` と `svgelements` を使用し、SVGの図形・パス・テキスト・グラデーションをPowerPointのネイティブシェイプとして変換します。`resvg-py` (Rust製) を利用するため、Windowsでも Cairo DLL 不要で動作します。

## ライセンス

MIT License

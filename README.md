# LLM Drawing Tool

自然言語のプロンプトからSVGイラストを生成し、リアルタイムで編集・プレビューして、PowerPoint (PPTX) ネイティブシェイプとしてエクスポートするStreamlitアプリです。

## 機能

- **自然言語による図の生成**: プロンプトを入力するとLLMがSVGコードを自動生成
- **用途特化プロンプト**: Diagram・Icon・Infographic・Flat Illustration など用途別に最適化されたプロンプトテンプレートを自動選択（手動選択も可能）
- **コード生成モード**: LLMがPythonコード（`drawsvg`ライブラリ）を生成し、実行結果としてSVGを取得。直接SVG出力より高品質な図形を生成可能
- **コンポーネント合成モード**: 人物・図形・アイコンなどの事前設計済みSVGパーツを使い、LLMがJSONレイアウトを生成→コンポジションエンジンがSVGを組み立て。人物描画やダイアグラム結線の品質が大幅に向上
- **ビジョンフィードバック**: ビジョン対応モデルが生成結果を画像として評価し、改善指示を元に反復的にSVGを洗練（オプション機能）
- **リアルタイムプレビュー**: 生成・編集したSVGを即座に確認
- **SVGコードエディタ**: テキストエリアによるSVGコードの直接編集
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
├── composition_engine.py   # コンポーネント合成エンジン（アンカー解決・結線ルーティング）
├── requirements.txt        # Python 依存パッケージ
├── prompt_templates/       # 用途別プロンプトテンプレート (YAML)
│   ├── classic.yaml        #   汎用（デフォルト）
│   ├── diagram.yaml        #   ダイアグラム・フローチャート
│   ├── icon.yaml           #   アイコン・シンボル
│   ├── infographic.yaml    #   インフォグラフィック・データ可視化
│   ├── flat_illustration.yaml  #   フラットデザインイラスト
│   └── component.yaml      #   コンポーネント合成モード
├── component_library/      # 事前設計済みSVGコンポーネントライブラリ
│   ├── manifest.json       #   コンポーネント定義・アンカー情報
│   ├── people/             #   人物SVG（14種: 起立・着座・歩行・走行・発表・手振り等）
│   ├── shapes/             #   図形SVG（角丸・ダイヤモンド・円柱・平行四辺形・円）
│   ├── icons/              #   アイコンSVG（矢印・歯車・ドキュメント）
│   └── decorations/        #   装飾SVG（区切り線・バッジ）
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
┌─────────────────────────────────────────────────────────────────────┐
│  SVG生成（3モードから選択）                                          │
│                                                                      │
│  [Direct SVG]           [Code Generation]     [Component]            │
│  LLMがSVGタグを         LLMがPythonコードを    LLMがJSONレイアウトを  │
│  直接テキスト出力        出力→サンドボックス    出力→composition_engine│
│                         実行→SVG取得           が事前パーツで組立     │
│                                                                      │
│  llm_client.py          llm_client.py +       llm_client.py +       │
│                         code_executor.py      composition_engine.py  │
└─────────┬───────────────────────────────────────────────────────────┘
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

| モジュール                | 責務                                                                                                                                                                                                                                                |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app.py`                  | StreamlitによるUI表示、ユーザー入力の収集、各モジュールのオーケストレーション。LLM生成SVGおよびマニュアル編集SVGをサニタイズしてから表示・保持                                                                                                      |
| `llm_client.py`           | OpenAI互換APIとの通信、用途自動分類（キーワード→LLMフォールバック）、YAMLテンプレートの読込・変数展開、Direct SVG / Code Generation / Component の3モード分岐                                                                                       |
| `code_executor.py`        | LLMが生成したPythonコードのサンドボックス実行。ASTによるimportホワイトリスト検証・危険な組み込み関数ブロック、環境変数ホワイトリスト化、subprocess分離、10秒タイムアウト                                                                            |
| `vision_feedback.py`      | SVGを `resvg_py` でPNG変換し、Vision APIに送信して視覚的評価を取得。評価結果を改善指示としてLLMに渡し、SVGを反復的に洗練                                                                                                                            |
| `pptx_exporter.py`        | SVGの図形・パス・テキスト・グラデーションをPowerPointのネイティブ編集可能シェイプに変換                                                                                                                                                             |
| `svg_processor.py`        | SVGサニタイズ（スクリプト除去・外部リソース参照除去・イベントハンドラ除去）、エンコードユーティリティ                                                                                                                                               |
| `composition_engine.py`   | コンポーネント合成エンジン。マニフェストからSVGパーツを読み込み、JSON仕様に基づきアンカー解決・要素配置・Manhattan/曲線/直線結線ルーティング・矢印マーカー生成を行う。LLM出力値に対する多層防御サニタイズ（`_sanitize_attr` / `_safe_float`）を実装 |
| `component_library/`      | MIT/CC0ライセンスの事前設計済みSVGアセット集。人物14ポーズ、図形5種、アイコン3種、装飾2種の計24コンポーネント。`manifest.json` で各コンポーネントのサイズ・アンカー座標・タグを定義                                                                 |
| `prompt_templates/*.yaml` | 用途別のシステムプロンプトテンプレート。分類キーワード、Direct SVG / Code Generation / Component 各モード用プロンプトを定義                                                                                                                         |

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
| SVG生成（Component）                                    | 1回                        |
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

## セキュリティ対策

本アプリはLLMが生成したコード・SVGを実行・表示するため、以下の多層的なセキュリティ対策を実装しています。

### コード生成モードのサンドボックス（`code_executor.py`）

LLMが生成したPythonコードは、実行前に2段階のAST静的解析を行います。

**1. インポートホワイトリスト検証**

`import` / `from ... import` 文を全て検査し、許可リスト外のモジュールをブロックします。

| 許可モジュール | 用途     |
| -------------- | -------- |
| `drawsvg`      | SVG描画  |
| `math`         | 数学関数 |
| `colorsys`     | 色変換   |
| `random`       | 乱数     |

**2. 危険な組み込み関数のブロック**

インポート文がなくても任意コードを実行できる組み込み関数・名前を `ast.walk` で検出しブロックします。

```
exec, eval, compile, __import__, open,
globals, locals, vars, dir,
getattr, setattr, delattr,
breakpoint, input, memoryview
```

**3. subprocess 分離**

コードは一時ディレクトリ内で独立したサブプロセスとして実行されます。

- 作業ディレクトリを一時ディレクトリに限定
- 10秒のタイムアウト

**4. 環境変数ホワイトリスト**

子プロセスに引き継ぐ環境変数を最小限の許可リスト（`PATH`, `TEMP`, `SYSTEMROOT` 等）に限定します。`OPENAI_API_KEY` などの機密情報は子プロセスから参照できません。

```python
SAFE_ENV_KEYS = {
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE",
    "TEMP", "TMP", "USERPROFILE", "HOME",
    "HOMEDRIVE", "HOMEPATH", "PYTHONDONTWRITEBYTECODE",
}
```

### SVGサニタイズ（`svg_processor.py`）

LLMが生成したSVGおよびユーザーのマニュアル編集内容は、表示前に必ずサニタイズされます。

| 除去対象                          | 例                                         |
| --------------------------------- | ------------------------------------------ |
| `<script>` タグ                   | `<script>alert(1)</script>`                |
| `<foreignObject>` タグ            | 任意のHTMLを埋め込み可能な要素             |
| `on*` イベントハンドラ属性        | `onload="fetch('...')"`                    |
| 外部URLへの `href` / `xlink:href` | `<image href="https://attacker.com/..."/>` |
| `javascript:` URI                 | `<a href="javascript:alert(1)">`           |

通常の `data:image/png` 等の埋め込み画像はそのまま保持されます。

### コンポーネント合成エンジンのサニタイズ（`composition_engine.py`）

コンポーネントモードではLLMがJSON仕様を出力し、合成エンジンがSVGを生成します。LLM出力値がSVG属性に直接埋め込まれるため、多層防御として以下のサニタイズを実装しています。

| 対策                 | 内容                                                                                                                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `_sanitize_attr()`   | 文字列属性（fill, stroke, font_weight等）の `"`, `<`, `>`, `&` をエスケープ。属性値からのブレイクアウトによるイベントハンドラ注入を防止 |
| `_safe_float()`      | 数値フィールド（x, y, width, height等）をfloatに強制変換。文字列注入による属性ブレイクアウトを防止                                      |
| コンポーネントID検証 | マニフェスト辞書に存在するIDのみ受け入れ。パストラバーサルによる任意ファイル読み込みを防止                                              |

これらは `svg_processor.py` による下流サニタイズ（`on*`ハンドラ除去等）に加えた多層防御です。

> **Note**: 現実装は多層防御の一部です。信頼できないユーザーが生成したSVGを不特定多数に公開する用途には、さらに `defusedxml` や専用のSVGホワイトリストライブラリの導入を推奨します。

## ライセンス

MIT License

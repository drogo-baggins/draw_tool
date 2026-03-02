# Design: Improve SVG Generation Quality

## Context

LLM Drawing Toolは現在、LLMにSVGコードを直接テキスト出力させる単一パイプラインで動作している。この方式ではLLMのトークン空間での座標精度に限界があり、出力品質は「子供の絵」レベルにとどまっている。

著作権リスクの制約により画像生成AI（DALL-E, Stable Diffusion等）は使用不可。LLMテキスト生成の枠内で品質を最大化する4つの戦略を段階的に導入する。

### ステークホルダー

- エンドユーザー: ビジネスプレゼン用のビジュアル生成者
- 開発者: パイプラインの保守・拡張

### 制約

- 画像生成AIは一切使用しない（著作権リスク）
- 画像「認識/評価」（GPT-4V等）は著作権セーフとして使用可
- 既存の直接SVG生成は「クラシックモード」として維持（破壊的変更なし）
- 対象スコープ: ダイアグラム、アイコン、インフォグラフィック、フラットデザインイラストまで

## Goals / Non-Goals

### Goals

- ダイアグラム品質を★★★★☆（プロ級）に引き上げる
- アイコン・インフォグラフィックの品質を★★★★☆に引き上げる
- フラットデザインイラストの品質を★★★☆☆（実用可能）に引き上げる
- 4つの生成モードをユーザーが選択・組み合わせ可能にする

### Non-Goals

- キャラクターイラスト・風景画の生成（LLMテキスト生成では不可能）
- 画像生成AIの統合
- DSL（宣言的シーン記述言語）の導入（将来検討）
- ファインチューニングによるSVG専用モデル育成（将来検討）

## Decisions

### Decision 1: 実装順序 — 戦略4 → 1 → 3 → 2

**選択**: 用途特化プロンプト(4) → コード生成(1) → ビジョンフィードバック(3) → コンポーネントライブラリ(2)

**理由**:

- 戦略4（プロンプト改善）は既存コード変更が最小で即効性がある。リスク最小。
- 戦略1（コード生成）は最大のインパクトだが、サンドボックス実装が必要。
- 戦略3（ビジョンフィードバック）は戦略1のコード生成との組み合わせで最大効果。
- 戦略2（コンポーネントライブラリ）は工数最大でキュレーション作業が必要。

**却下した代替案**:

- 戦略1を最初にする案: インパクトは最大だが、サンドボックスのセキュリティ設計が先行リスク。まずプロンプト改善で早期価値を出す。

### Decision 2: コード生成のサンドボックス方式 — subprocess + タイムアウト

**選択**: `subprocess` でPythonプロセスを起動し、タイムアウト（10秒）とリソース制限を設ける。

**理由**:

- RestrictedPythonはAST解析でimportを制限するが、`drawsvg`等の外部ライブラリ利用に制約が多く、使い勝手が悪い。
- subprocessは完全なPython環境で動作し、タイムアウト+tempdir+allowlistで安全性を確保できる。
- Streamlit環境（ローカル使用が主）では過度なサンドボックスは不要。

**却下した代替案**:

- RestrictedPython: `drawsvg`のimportチェーンが深く、許可リスト管理が煩雑。
- Docker-in-Docker: 過度な複雑性。ローカルツールには不適。
- exec() + globals制限: セキュリティ不十分。

**実装詳細**:

```python
# code_executor.py の概念設計
import subprocess, tempfile, os

ALLOWED_IMPORTS = ["drawsvg", "math", "colorsys", "random"]
TIMEOUT_SECONDS = 10

def execute_svg_code(code: str) -> str:
    """LLM生成Pythonコードをサンドボックスで実行し、SVG文字列を返す。"""
    # 1. importのホワイトリストチェック（静的解析）
    # 2. tempfileにコードを書き出し
    # 3. subprocess.run(["python", tmpfile], timeout=10, capture_output=True)
    # 4. 標準出力からSVGを取得
    # 5. SVGバリデーション
    ...
```

### Decision 3: SVG描画ライブラリ — drawsvg

**選択**: `drawsvg` (MIT License)

**理由**:

- Pythonネイティブ、MITライセンス、依存関係が軽量
- SVGの全機能（パス、テキスト、グラデーション、フィルター、アニメーション）をサポート
- LLMが学習データ内で多く見ているライブラリ（GPT-4のコード生成で高品質な出力が期待）
- `d = drawsvg.Drawing(width, height)` → `d.as_svg()` で簡潔にSVG文字列を取得可能

**却下した代替案**:

- svgwrite: 機能が少なく、グラデーション等の表現力が劣る
- cairo (pycairo): システム依存（Cairo DLL）が必要。resvg-pyで脱Cairoを実現済みのプロジェクトに逆行
- matplotlib: SVG出力は可能だが、グラフ特化でイラスト向きではない

### Decision 4: 用途分類方式 — LLM自動分類 + ユーザー手動オーバーライド

**選択**: デフォルトでLLMがプロンプトから用途を自動分類し、UIでユーザーが手動オーバーライド可能。

**理由**:

- 完全手動: ユーザーに判断負荷がかかる（初心者には分類基準が不明）
- 完全自動: 誤分類時にリカバリーできない
- ハイブリッド: LLM判断をデフォルトとし、UIにドロップダウンで表示。ユーザーが変更可能。

**分類カテゴリ**:

1. `diagram` — フローチャート、組織図、ER図、ネットワーク図等
2. `icon` — 単一アイコン、シンボル、ロゴ
3. `infographic` — データビジュアライゼーション、統計表示
4. `flat_illustration` — フラットデザインのシーンイラスト
5. `classic` — 既存の直接SVG生成（後方互換）

**実装**:

```python
# llm_client.py の分類ロジック概念
CLASSIFICATION_PROMPT = """
Classify the following user prompt into exactly one category:
- diagram: flowcharts, org charts, ER diagrams, network diagrams
- icon: single icons, symbols, logos
- infographic: data visualization, statistics display
- flat_illustration: flat design scene illustrations
- classic: other/general SVG requests

User prompt: {prompt}
Respond with only the category name.
"""
```

### Decision 5: ビジョンフィードバックのフロー設計

**選択**: SVG → PNG(resvg) → Vision API評価 → テキストフィードバック → LLM修正、最大3回反復。

**理由**:

- resvg-pyが既に依存関係にあり、追加依存なしでSVG→PNGレンダリングが可能
- GPT-4V（Vision）は画像の「認識/評価」であり、画像「生成」ではないため著作権リスクなし
- 3回で十分な改善が見込まれる（研究文献で4回以降の改善は微小）

**フィードバックプロンプト設計**:

```
Evaluate this SVG rendering for:
1. Visual alignment and symmetry
2. Color harmony and contrast
3. Text readability and placement
4. Overall professional appearance
5. Adherence to the original prompt: "{original_prompt}"

Provide specific, actionable improvement instructions.
```

**ユーザーコントロール**:

- UI checkbox: "Enable refinement loop" (デフォルト OFF)
- 反復中は進捗バー表示（"Refining 1/3...", "Refining 2/3..."）
- 各反復のSVGを保存し、ユーザーが任意の版を選択可能

### Decision 6: コンポーネントライブラリの構造

**選択**: JSONマニフェスト + SVGフラグメントファイル + LLM JSONコンポジション指示

**理由**:

- SVGフラグメントを独立ファイルで管理することで、追加・削除が容易
- JSONマニフェストでメタデータ（名前、カテゴリ、タグ、デフォルトサイズ）を管理
- LLMはJSONで配置指示を出すだけなので、トークン効率が良い

**ディレクトリ構造**:

```
component_library/
├── manifest.json          # パーツ一覧とメタデータ
├── icons/
│   ├── arrow-right.svg
│   ├── person.svg
│   ├── gear.svg
│   └── ...
├── shapes/
│   ├── rounded-rect.svg
│   ├── diamond.svg
│   └── ...
└── decorations/
    ├── divider-line.svg
    ├── badge.svg
    └── ...
```

**manifest.json スキーマ**:

```json
{
  "components": [
    {
      "id": "icon-person",
      "name": "Person",
      "category": "icons",
      "tags": ["人", "ユーザー", "person", "user"],
      "file": "icons/person.svg",
      "default_width": 48,
      "default_height": 48,
      "license": "MIT"
    }
  ]
}
```

**LLMコンポジション指示のJSONスキーマ**:

```json
{
  "canvas": { "width": 800, "height": 600, "background": "#ffffff" },
  "elements": [
    {
      "component_id": "icon-person",
      "x": 100,
      "y": 200,
      "width": 64,
      "height": 64,
      "fill": "#3498db"
    },
    {
      "type": "text",
      "content": "ユーザー",
      "x": 100,
      "y": 280,
      "font_size": 14,
      "fill": "#333333"
    },
    {
      "type": "line",
      "x1": 164,
      "y1": 232,
      "x2": 300,
      "y2": 232,
      "stroke": "#999999",
      "stroke_width": 2
    }
  ]
}
```

### Decision 7: プロンプトテンプレートの管理方式

**選択**: YAML形式のテンプレートファイル（`prompt_templates/` ディレクトリ）

**理由**:

- 既存のLLM設定が `config/llm_configs.yaml` でYAML管理されており、プロジェクトの慣習に合致
- Pythonコード内にプロンプトをハードコードすると変更・A/Bテストが困難
- YAMLは複数行文字列の記述が容易（`|` ブロックスカラー）

**ディレクトリ構造**:

```
prompt_templates/
├── diagram.yaml
├── icon.yaml
├── infographic.yaml
├── flat_illustration.yaml
└── classic.yaml          # 既存プロンプトの移行
```

**テンプレートスキーマ例** (`diagram.yaml`):

```yaml
name: "Diagram"
description: "Flowcharts, org charts, ER diagrams, network diagrams"
system_prompt: |
  You are an expert diagram designer. Generate clean, professional SVG diagrams.

  Design Rules:
  - Use a grid-aligned layout with consistent spacing (multiples of 20px)
  - Use a professional color palette: #2196F3 (primary), #FF9800 (accent), #4CAF50 (success), #F44336 (error)
  - Font: 'Segoe UI', Arial, sans-serif
  - All text must be readable (minimum 12px)
  - Connectors should use straight lines or right-angle paths
  - Include subtle rounded corners (rx="8") on boxes
  - Maintain consistent padding inside boxes (16px)

  SVG Requirements:
  - Output a complete, standalone <svg> element with explicit width/height and viewBox
  - Use <defs> for reusable elements (arrowheads, gradients)
  - Group related elements in <g> tags with descriptive IDs

code_generation_prompt: |
  You are an expert programmer generating Python code using the `drawsvg` library.
  Generate code that creates the diagram described below.

  The code MUST:
  - Import only: drawsvg, math, colorsys, random
  - Create a drawsvg.Drawing object assigned to variable `d`
  - Use precise coordinates and mathematical calculations
  - End with: print(d.as_svg())

  Design the diagram with professional aesthetics:
  - Grid-aligned layout
  - Professional color palette
  - Readable text with proper font sizing
  - Clean connector lines

classification_keywords:
  - flowchart
  - org chart
  - ER diagram
  - network
  - sequence diagram
  - architecture
  - flow
  - process
  - pipeline
  - tree
  - hierarchy
```

## Risks / Trade-offs

### Risk 1: コード生成のセキュリティ

- **リスク**: LLM生成コードに悪意あるコード（ファイルアクセス、ネットワーク呼び出し等）が含まれる可能性
- **軽減策**:
  - importホワイトリスト（静的AST解析）
  - subprocessタイムアウト（10秒）
  - tempdir内での実行（ファイルシステム分離）
  - ネットワークアクセスなし（subprocess環境変数でプロキシ無効化）

### Risk 2: LLM用途分類の精度

- **リスク**: 曖昧なプロンプトで誤分類が発生し、不適切なプロンプトテンプレートが適用される
- **軽減策**: ユーザー手動オーバーライド + UIに分類結果を表示して透明性を確保

### Risk 3: ビジョンフィードバックのAPIコスト

- **リスク**: 反復ごとにVision API呼び出し（画像送信）が発生し、コストが増大
- **軽減策**: デフォルトOFF、最大3回制限、UIで反復回数を選択可能

### Risk 4: drawsvgの学習データ量

- **リスク**: LLMの学習データ内での`drawsvg`の出現頻度が不十分で、コード品質が低い可能性
- **軽減策**: システムプロンプトに`drawsvg` APIの主要パターンを例示として含める（Few-shot）

### Risk 5: コンポーネントライブラリのキュレーション工数

- **リスク**: 高品質なMIT/CC0パーツの収集・整理に予想以上の工数がかかる
- **軽減策**: 最小セット（20-30パーツ）で開始し、段階的に拡充。初期は基本図形+ビジネスアイコンに限定

## Migration Plan

### Phase 0: 準備（破壊的変更なし）

1. `prompt_templates/` ディレクトリ作成
2. 既存プロンプトを `classic.yaml` に移行
3. `llm_client.py` のプロンプト読み込みをYAMLベースに変更

### Phase 1: 戦略4 — 用途特化プロンプト

1. 4用途のプロンプトテンプレートYAML作成
2. LLM用途分類ロジック追加
3. UIに用途選択ドロップダウン追加
4. 分類→テンプレート選択→生成のパイプライン構築

### Phase 2: 戦略1 — コード生成

1. `drawsvg` を `requirements.txt` に追加
2. `code_executor.py` 新規作成（サンドボックス実行）
3. 各用途テンプレートに `code_generation_prompt` 追加
4. UIに生成モード選択追加（「直接SVG」vs「コード生成」）
5. 生成モードに応じたパイプライン分岐

### Phase 3: 戦略3 — ビジョンフィードバック

1. SVG→PNGレンダリング機能追加（resvg-py活用）
2. Vision API評価呼び出しモジュール追加
3. 反復ループ制御ロジック追加
4. UIにフィードバックオプション + 進捗表示追加

### Phase 4: 戦略2 — コンポーネントライブラリ

1. `component_library/` ディレクトリ + manifest.json 作成
2. 初期パーツセット（20-30個）のキュレーション
3. コンポジションエンジン（JSON→SVG合成）実装
4. LLMへのパーツ一覧提示 + JSON出力プロンプト追加
5. UIにコンポーネントモード追加

### ロールバック

- 各フェーズは独立しており、問題発生時はフェーズ単位で無効化可能
- 既存の「クラシックモード」は常に利用可能なフォールバック

## Open Questions

1. **drawsvg vs svgwrite のLLM生成品質比較**: 実際にGPT-4oで両方のライブラリを使ったコード生成を試し、出力品質を比較するべきか？（実装フェーズ初期のスパイクタスクとして）

2. **コンポーネントライブラリの初期パーツ選定基準**: どのカテゴリのパーツを優先すべきか？ビジネスアイコンが最優先か、それとも基本図形（矢印、ボックス、コネクタ）が先か？

3. **ビジョンフィードバックの評価基準の定量化**: 「プロフェッショナルな外観」をLLMにどう伝えるか？rubric形式（1-5点の各軸）が効果的か、自由記述が良いか？

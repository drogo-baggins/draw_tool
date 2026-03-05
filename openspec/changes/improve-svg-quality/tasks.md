## 0. Preparation (Non-Breaking)

- [x] 0.1 `prompt_templates/` ディレクトリ作成
- [x] 0.2 既存のシステムプロンプト（`llm_client.py` 内ハードコード）を `prompt_templates/classic.yaml` に抽出
- [x] 0.3 `llm_client.py` をYAMLテンプレート読み込み方式にリファクタリング
- [ ] 0.4 既存動作が変わらないことをテスト確認

## 1. Strategy 4: Purpose-Specific Prompt Templates（用途特化プロンプト）

- [x] 1.1 `prompt_templates/diagram.yaml` 作成（ダイアグラム用システムプロンプト、デザインルール、カラーパレット）
- [x] 1.2 `prompt_templates/icon.yaml` 作成（アイコン用）
- [x] 1.3 `prompt_templates/infographic.yaml` 作成（インフォグラフィック用）
- [x] 1.4 `prompt_templates/flat_illustration.yaml` 作成（フラットイラスト用）
- [x] 1.5 `llm_client.py` に用途自動分類ロジック追加（LLM呼び出しで1-shot分類）
- [x] 1.6 分類結果に応じたプロンプトテンプレート選択ロジック実装
- [x] 1.7 `app.py` UIに用途選択ドロップダウン追加（Auto / Diagram / Icon / Infographic / Flat Illustration / Classic）
- [ ] 1.8 分類→テンプレート→生成の統合パイプライン動作確認
- [ ] 1.9 各用途で生成テスト（最低4プロンプトで品質確認）

## 2. Strategy 1: Code Generation Approach（コード生成）

- [x] 2.1 `drawsvg` を `requirements.txt` に追加
- [x] 2.2 `code_executor.py` 新規作成 — importホワイトリスト検証（AST解析）
- [x] 2.3 `code_executor.py` — subprocess実行+タイムアウト(10秒)+tempdir分離
- [x] 2.4 `code_executor.py` — SVG出力のバリデーション（有効なSVGか確認）
- [x] 2.5 `code_executor.py` — エラーハンドリング（タイムアウト、構文エラー、実行エラー）
- [x] 2.6 各用途テンプレートYAMLに `code_generation_prompt` セクション追加
- [x] 2.7 `llm_client.py` に生成モード分岐追加（direct_svg / code_generation）
- [x] 2.8 `app.py` UIに生成モード選択追加（「Direct SVG」vs「Code Generation (Higher Quality)」）
- [ ] 2.9 コード生成→実行→SVG取得の統合パイプライン動作確認
- [ ] 2.10 セキュリティテスト（不正import、無限ループ、ファイルアクセス試行がブロックされること）
- [ ] 2.11 各用途×コード生成モードで品質テスト

## 3. Strategy 3: Vision Feedback Loop（ビジョンフィードバック）

- [x] 3.1 SVG→PNG変換関数追加（resvg-py利用、既存依存）
- [x] 3.2 Vision API評価呼び出しモジュール追加（GPT-4V等へ画像+評価プロンプト送信）
- [x] 3.3 評価結果→改善指示→LLM再生成の反復ループ実装
- [x] 3.4 反復回数制御（デフォルト最大3回、UI設定可能）
- [x] 3.5 各反復のSVGを履歴として保持する仕組み
- [x] 3.6 `app.py` UIにフィードバックオプション追加（Enable Refinement チェックボックス、デフォルトOFF）
- [x] 3.7 `app.py` UIに反復進捗表示（"Refining 1/3..."）+ 各版の選択機能
- [ ] 3.8 ビジョンフィードバック有無での品質比較テスト

## 4. Strategy 2: Component Library + LLM Composition（課題特化コンポーネントライブラリ）

### 4A. ディレクトリ構造・マニフェスト

- [x] 4.1 `component_library/` ディレクトリ構造作成（`people/`, `shapes/`, `icons/`, `decorations/`）
- [x] 4.2 `component_library/manifest.json` スキーマ定義 — `anchors` フィールド（正規化座標 0.0〜1.0）を含む接続ポート付きスキーマ
- [x] 4.3 manifest.json 初期作成 — 全パーツのメタデータ（id, name, category, tags, file, default_width, default_height, license, anchors）

### 4B. 人物パーツのキュレーション（★最優先 — 課題1対応）

- [x] 4.4 MIT/CC0ライセンスのフラットデザイン人物SVG収集（person-standing, person-sitting, person-bust, person-silhouette）
- [x] 4.5 MIT/CC0ライセンスの顔パーツSVG収集（face-neutral, face-smile 等）
- [x] 4.6 収集SVGの品質・ライセンス確認 + `people/` ディレクトリへの配置
- [x] 4.7 人物パーツの manifest.json エントリ追加（アンカー定義含む）

### 4C. 図形・アイコン・装飾パーツのキュレーション

- [x] 4.8 接続ポート付き基本図形SVG作成/収集（box-rounded, diamond, cylinder, parallelogram, circle-node）— `shapes/` に配置
- [x] 4.9 図形パーツの manifest.json エントリ追加（top/right/bottom/left の4方向アンカー定義）
- [x] 4.10 汎用アイコンSVG収集（arrow-right, gear, document 等）— `icons/` に配置
- [x] 4.11 装飾パーツSVG収集（divider-line, badge 等）— `decorations/` に配置

### 4D. コンポジションエンジン実装（★優先 — 課題2対応）

- [x] 4.12 `composition_engine.py` 新規作成 — JSON入力パース + SVG合成の基本フレーム（~200行目標）
- [x] 4.13 コンポーネント配置ロジック実装 — `elements` 配列をパースし、SVGフラグメントをキャンバスに配置（x, y, width, height, fill, label）
- [x] 4.14 接続ルーティングエンジン実装 — `connections` 配列を処理:
  - アンカー名から絶対座標を計算（正規化座標 × 配置サイズ + 配置位置）
  - `straight` スタイル: 2点間直線
  - `orthogonal` スタイル（デフォルト）: マンハッタンルーティング（最大3セグメント、マージン20px）
  - `curved` スタイル: ベジェ曲線（制御点をアンカー方向に基づき自動計算）
- [x] 4.15 矢印描画サポート — `arrow: "end"/"start"/"both"/"none"` に対応するSVG `<marker>` 定義生成
- [x] 4.16 テキスト要素サポート — `type: "text"` の直接テキスト配置（font_size, fill, font_weight）
- [x] 4.17 SVG出力のバリデーション — 出力が有効なSVG 1.1（pptx_exporter.py互換）であることの確認

### 4E. LLMプロンプト・パイプライン統合

- [x] 4.18 コンポーネントモード用プロンプト設計 — パーツ一覧（manifest.jsonのサマリー）をシステムプロンプトに注入、JSON出力スキーマ（elements + connections 分離）を指示
- [x] 4.19 LLM JSON出力のパース + バリデーション — スキーマ検証（必須フィールド、component_id の存在確認、アンカー名の妥当性チェック）
- [x] 4.20 不明コンポーネント参照のグレースフルハンドリング — 不明IDはスキップ + 警告ログ（部分結果を返す）

### 4F. UI統合・テスト

- [x] 4.21 `app.py` UIにコンポーネントモード追加（生成モード選択に「Component」を追加）
- [x] 4.22 コンポーネント合成の統合テスト — ワークフロー図（人物+ボックス+結線）で結線ずれがないことを確認
- [x] 4.23 人物パーツ描画テスト — 人物コンポーネントが正しく配置・スケーリングされることを確認
- [x] 4.24 PPTXエクスポートテスト — コンポーネント合成SVGが `pptx_exporter.py` で正常にエクスポートされることを確認

## 5. Phase 3: ポーズバリエーション拡充 + 空間認識改善

### 5A. 人物ポーズバリエーション追加（課題1深化対応）

- [x] 5.1 `person-walking.svg` 作成（64x120、右向き歩行姿勢）
- [x] 5.2 `person-running.svg` 作成（80x120、右向きランニング姿勢）
- [x] 5.3 `person-presenting.svg` 作成（80x120、右腕を伸ばしてプレゼン姿勢）
- [x] 5.4 `person-raising-hand.svg` 作成（64x120、片手を挙げた姿勢）
- [x] 5.5 `person-working-desk.svg` 作成（120x100、デスク+モニター+人物の複合シーン）
- [x] 5.6 `person-pointing-right.svg` 作成（80x120、右を指差す姿勢）
- [x] 5.7 `person-waving.svg` 作成（64x120、手を振る姿勢）
- [x] 5.8 `person-group.svg` 作成（140x120、3人並びグループ）
- [x] 5.9 全8ファイルのXMLバリデーション（有効なSVG 1.1であること）
- [x] 5.10 `manifest.json` に8件の新コンポーネントエントリ追加（アンカー定義含む、合計24コンポーネント）

### 5B. 空間認識・深度推論プロンプト改善（課題2深化対応）

- [x] 5.11 `prompt_templates/component.yaml` にPerson Pose Selectionセクション追加（コンテキスト→ポーズマッピングガイド）
- [x] 5.12 `prompt_templates/component.yaml` にDepth and Layeringセクション追加（z-order = elements配列順序、背景→前景、向き方向ルール）
- [x] 5.13 `prompt_templates/component.yaml` にScene Composition Examplesセクション追加（デスクワーク・プレゼンの2パターン、オーバーフィッティング回避のため最小限）

### 5C. テスト・検証

- [x] 5.14 新ポーズコンポーネントの合成テスト追加（Test 6: Pose Component Composition — マルチポーズシーン + 個別ポーズ合成確認）
- [x] 5.15 既存テスト5件のリグレッション確認（全6件パス）

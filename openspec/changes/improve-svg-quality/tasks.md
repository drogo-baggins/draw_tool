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

## 4. Strategy 2: Component Library + LLM Composition（コンポーネントライブラリ）

- [ ] 4.1 `component_library/` ディレクトリ構造作成（icons/, shapes/, decorations/）
- [ ] 4.2 `component_library/manifest.json` スキーマ定義+初期作成
- [ ] 4.3 初期パーツセットのキュレーション（MIT/CC0、20-30パーツ: 基本図形、矢印、ビジネスアイコン）
- [ ] 4.4 コンポジションエンジン実装（JSON指示 → SVG合成）
- [ ] 4.5 LLMへのパーツ一覧提示プロンプト設計
- [ ] 4.6 LLM JSONコンポジション出力のパース+バリデーション
- [ ] 4.7 `app.py` UIにコンポーネントモード追加
- [ ] 4.8 コンポーネント合成の動作確認テスト

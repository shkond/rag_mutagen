# Mutagen RAG MCP Server

Bethesda系ゲームのModdingライブラリ「Mutagen」のためのRAG（検索拡張生成）機能を提供するMCPサーバーです。
自動生成されたコード（`.g.cs`など）を自動的に除外し、手書きのビジネスロジックのみを検索対象とすることで、AIアシスタント（Clineなど）の回答精度を向上させます。

## 主要機能

### 🔍 高度な検索機能
- **ハイブリッド検索**: BM25（キーワード検索）とベクトル検索を組み合わせ、コード特有の識別子と意味的な検索の両方に対応
- **リランキング**: BAAI/bge-reranker-baseを使用して検索結果を再評価し、トップレベルの精度を実現
- **BM25キャッシング**: 検索パフォーマンスを向上させるため、BM25リトリーバーをメモリにキャッシュ

### 📁 スマートなファイル処理
- **自動生成ファイル除外**: `.g.cs`, `obj/`, `Generated/`などの自動生成ファイルをインデックスから除外
- **複数リポジトリ対応**: カンマ区切りまたは改行区切りで複数のリポジトリパスを指定可能
- **C#コード対応チャンキング**: CodeSplitterを使用してC#のコード構造を考慮した分割（tree-sitter利用）

### 🎯 C#コード最適化
- **拡張チャンクサイズ**: 2048文字まで拡張し、クラス定義全体を保持
- **メタデータ抽出**: 名前空間、クラス名、メソッド名を自動抽出してBM25検索の精度を向上
- **ソースリポジトリ追跡**: 各チャンクがどのリポジトリから来たかを記録

### 🏗️ モジュラーアーキテクチャ
- **IndexManager**: インデックス作成・更新・永続化を管理
- **HybridSearchEngine**: ハイブリッド検索とリランキングを実装
- **FileFilterer**: ファイルフィルタリングロジックを分離
- **MetadataExtractor**: メタデータ抽出ロジックを分離
- **集中設定管理**: `config.py`で全ての設定値を一元管理

### 💪 堅牢性
- **ローカルRAG**: ChromaDBとローカルモデルを使用し、外部APIコストゼロで動作
- **自動フォールバック**: BM25失敗時でもベクトル検索で結果を返却
- **詳細なロギング**: ファイルベースのログで問題の診断が容易

## 前提条件

- **Python 3.10+**
- **uv**: 高速なPythonパッケージマネージャー
  - インストール: `pip install uv` または `curl -LsSf https://astral.sh/uv/install.sh | sh`

## インストール手順

### 1. プロジェクトのセットアップ

```bash
# 依存関係のインストール
uv sync
```

### 2. Mutagenリポジトリの準備

このサーバーはMutagenのソースコードをスキャンします。プロジェクトルートに `Mutagen` ディレクトリとしてクローンするか、既存のパスを指定できます。

**方法A: このプロジェクト内にクローンする場合（推奨）**
```bash
git clone https://github.com/Mutagen-Modding/Mutagen.git
```
※ `Mutagen/Mutagen.Bethesda.Core` が存在することを確認してください。

**方法B: 既存のMutagenリポジトリを使用する場合**
環境変数 `MUTAGEN_REPO_PATH` でパスを指定します（後述）。

## VS Code (Cline) の設定

ClineなどのMCPクライアントから使用するための設定です。

1. MCP設定ファイルを開く（または作成）:
   - Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
   - macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

2. 以下の設定を追加:

```json
{
  "mcpServers": {
    "mutagen-rag": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "c:/path/to/mutagen_rag", 
      "env": {
        "MUTAGEN_REPO_PATH": "c:/path/to/Mutagen/Mutagen.Bethesda.Core",
        "OPENAI_API_KEY": "sk-..." 
      }
    }
  }
}
```

### 環境変数の説明

- **`cwd`**: このリポジトリの絶対パスに書き換えてください
- **`MUTAGEN_REPO_PATH`**: 
  - 単一リポジトリ: `"c:/path/to/Mutagen/Mutagen.Bethesda.Core"`
  - 複数リポジトリ（カンマ区切り）: `"path1,path2,path3"`
  - 方法Aの場合は省略可能（デフォルト: `./Mutagen/Mutagen.Bethesda.Core`）
- **`OPENAI_API_KEY`**: `refine`モード（AIによる回答生成）を使用する場合に必要。設定しない場合は検索結果のリストのみが返されます

## 使い方

### 1. サーバーの起動確認（オプション）
開発モードで起動して動作確認ができます。
```bash
fastmcp dev server.py
```

### 2. インデックスの作成（初回必須）
Clineからツール **`refresh_index`** を実行してください。

**単一リポジトリの場合:**
```
refresh_index()  # デフォルトパスを使用
```

**複数リポジトリの場合:**
```
refresh_index("./Mutagen/Mutagen.Bethesda.Core,./AnotherRepo")
```

- Mutagenリポジトリをスキャンし、ベクトルインデックスを作成します
- 初回は数分かかる場合があります
- 完了すると、リポジトリ別の統計情報が表示されます

### 3. 検索
ツール **`search_repository`** を使用して質問できます。

例:
- "How do I create a new NPC record?"
- "Explain the logic for handling FormLinks."
- "Show me examples of record serialization"

パラメータ:
- `query`: 検索クエリ（必須）
- `top_k`: 返す結果の数（デフォルト: 10）

### 4. 統計確認
ツール **`get_index_stats`** で現在のインデックス状況（ドキュメント数など）を確認できます。

## プロジェクト構成

```
mutagen_rag/
├── server.py              # MCPサーバーのエントリーポイント
├── config.py              # 集中設定管理
├── index_manager.py       # インデックス管理
├── search_engine.py       # ハイブリッド検索エンジン
├── file_filters.py        # ファイルフィルタリング
├── metadata_extractor.py  # メタデータ抽出
├── logging_config.py      # ロギング設定
├── storage/               # ベクトルインデックスの保存先
└── mcp_server.log         # サーバーログ
```

## 設定のカスタマイズ

`config.py`で以下の設定を調整できます:

### チャンキング設定
```python
CHUNK_LINES = 40              # チャンクあたりの行数
CHUNK_OVERLAP_LINES = 15      # チャンク間のオーバーラップ行数
MAX_CHARS = 2048              # チャンクの最大文字数
```

### 検索設定
```python
DEFAULT_TOP_K = 10            # デフォルトの検索結果数
BM25_MULTIPLIER = 3           # BM25候補取得の倍率
VECTOR_MULTIPLIER = 2         # ベクトル候補取得の倍率
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"
```

### フィルタリング設定
```python
GENERATED_SUFFIXES = [".g.cs", ".Autogen.cs", ".Generated.cs"]
EXCLUDED_DIRS = {"obj", "bin", "Generated", ".vs", ".git"}
```

## トラブルシューティング

### "Index does not exist" エラー
- `refresh_index` を実行してインデックスを作成してください

### 検索結果が空、またはエラー
- `MUTAGEN_REPO_PATH` が正しいか確認してください
- `uv run test_server.py` を実行して、自己診断テストを行ってください

### BM25が利用できない
- tree-sitterのインストールに失敗している可能性があります
- ベクトル検索のみで動作するため、機能には影響ありません
- ログファイル `mcp_server.log` で詳細を確認できます

### パフォーマンスの問題
- BM25キャッシュは初回検索時に構築されます（数秒かかる場合があります）
- インデックス更新後は自動的にキャッシュがクリアされます
- `top_k`の値を小さくすると検索速度が向上します

## 開発者向け情報

### テストの実行
```bash
# 基本的な機能テスト
uv run test_server.py

# メタデータ抽出のテスト
uv run test_metadata_extraction.py

# 複数パスのテスト
uv run test_multi_path.py

# リファクタリング後の動作確認
uv run test_refactoring.py
```

### ログの確認
```bash
# リアルタイムでログを監視
tail -f mcp_server.log  # Unix系
Get-Content mcp_server.log -Wait  # PowerShell
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能リクエストは、GitHubのIssuesでお願いします。
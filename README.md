# Mutagen RAG MCP Server

Bethesda系ゲームのModdingライブラリ「Mutagen」のためのRAG（検索拡張生成）機能を提供するMCPサーバーです。
自動生成されたコード（`.g.cs`など）を自動的に除外し、手書きのビジネスロジックのみを検索対象とすることで、AIアシスタント（Clineなど）の回答精度を向上させます。

## 機能

- **スマートフィルタリング**: 自動生成ファイル（`.g.cs`, `obj/`, `Generated/`など）をインデックスから除外
- **ハイブリッド検索**: BM25（キーワード検索）とベクトル検索を組み合わせ、コード特有の識別子と意味的な検索の両方に対応
- **リランキング**: BAAI/bge-reranker-baseを使用して検索結果を再評価し、トップレベルの精度を実現
- **C#最適化**: チャンクサイズを2048に拡張し、クラス定義全体を保持。名前空間や型名のメタデータ抽出も実装
- **ローカルRAG**: ChromaDBとローカルモデルを使用し、外部APIコストゼロで動作（LLMによる回答生成を除く）
- **堅牢性**: LLM（OpenAI）未設定時やBM25失敗時でも、ベクトル検索へ自動フォールバックして結果を返却

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
※ `cwd` はこのリポジトリの絶対パスに書き換えてください。
※ `MUTAGEN_REPO_PATH` は、方法Aの場合は省略可能です（デフォルトで `./Mutagen/Mutagen.Bethesda.Core` を探します）。
※ `OPENAI_API_KEY` は、`refine` モード（AIによる回答生成）を使用する場合に必要です。設定しない場合は、検索結果のリストのみが返されます。

## 使い方

### 1. サーバーの起動確認（オプション）
開発モードで起動して動作確認ができます。
```bash
fastmcp dev server.py
```

### 2. インデックスの作成（初回必須）
Clineからツール **`refresh_index`** を実行してください。
- Mutagenリポジトリをスキャンし、ベクトルインデックスを作成します。
- 初回は数分かかる場合があります。
- 完了すると、除外されたファイル数などが表示されます。

### 3. 検索
ツール **`search_repository`** を使用して質問できます。
例:
- "How do I create a new NPC record?"
- "Explain the logic for handling FormLinks."

### 4. 統計確認
ツール **`get_index_stats`** で現在のインデックス状況（ドキュメント数など）を確認できます。

## トラブルシューティング

- **"Index does not exist" エラー**:
  - `refresh_index` を実行してインデックスを作成してください。
- **検索結果が空、またはエラー**:
  - `MUTAGEN_REPO_PATH` が正しいか確認してください。
  - `uv run test_server.py` を実行して、自己診断テストを行ってください。
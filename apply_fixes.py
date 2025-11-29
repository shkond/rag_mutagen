#!/usr/bin/env python3
"""
Apply fixes for user feedback:
1. Fix REPO_ROOT definition order
2. Add CodeSplitter fallback
3. Update transformations to use variable
"""

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: REPO_ROOT definition
# Find where logger is initialized and add REPO_ROOT before LOG_FILE usage
old_logging = '''# server.py に追加（ファイル先を Desktop に固定）
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
 # 例: server.py の logging 初期化のすぐ後に追加
logger = logging.getLogger("mutagen-rag")
LOG_FILE = os.getenv("MCP_LOG_FILE", str(REPO_ROOT / "mcp_server.log"))'''

new_logging = '''# server.py に追加（ファイル先を Desktop に固定）
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# ワークスペース直下（このファイルが存在するフォルダ）をルートにする
REPO_ROOT = Path(__file__).resolve().parent
# ロガー初期化
logger = logging.getLogger("mutagen-rag")
LOG_FILE = os.getenv("MCP_LOG_FILE", str(REPO_ROOT / "mcp_server.log"))'''

content = content.replace(old_logging, new_logging)

# Fix 2: CodeSplitter fallback
old_codesplitter = '''# Configuration
# Set chunk size to 2048 and overlap to 200 for better code context
Settings.chunk_size = 2048
Settings.chunk_overlap = 200'''

new_codesplitter = '''# Configuration
# Code splitter for C# - chunk by semantic code blocks rather than tokens
# Falls back to default splitting if tree-sitter is unavailable
try:
    from llama_index.core.node_parser import CodeSplitter
    code_splitter = CodeSplitter(
        language="c_sharp",
        chunk_lines=40,  # Roughly 40 lines per chunk
        chunk_lines_overlap=15,  # Overlap to maintain context
        max_chars=2048,  # Safety limit
    )
    transformations_list = [code_splitter]
    logger.info("CodeSplitter (C#) initialized successfully.")
except ImportError as e:
    logger.warning(f"Tree-sitter or CodeSplitter not available: {e}. Falling back to default splitting.")
    transformations_list = []  # Use default LlamaIndex splitting'''

content = content.replace(old_codesplitter, new_codesplitter)

# Write
with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixes applied successfully!")

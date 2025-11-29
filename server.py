"""
Mutagen RAG MCP Server

Provides semantic code search over the Mutagen codebase using:
- Vector search (dense retrieval) with BAAI/bge-small-en-v1.5
- BM25 (sparse retrieval) for keyword matching
- Hybrid fusion and reranking for optimal results

Refactored for improved maintainability and testability.
"""
import asyncio

from fastmcp import FastMCP
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

# Import refactored modules
from config import (
    MUTAGEN_REPO_PATH,
    STORAGE_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    CHUNK_LINES,
    CHUNK_OVERLAP_LINES,
    MAX_CHARS
)
from logging_config import setup_logging, get_logger
from index_manager import IndexManager
from search_engine import HybridSearchEngine

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# ============================================================================
# Code Splitter Configuration
# ============================================================================

# Try to use CodeSplitter for C#-aware chunking
# Falls back to default splitting if tree-sitter is unavailable
try:
    from llama_index.core.node_parser import CodeSplitter
    
    code_splitter = CodeSplitter(
        language="c_sharp",
        chunk_lines=CHUNK_LINES,
        chunk_lines_overlap=CHUNK_OVERLAP_LINES,
        max_chars=MAX_CHARS,
    )
    transformations_list = [code_splitter]
    logger.info("CodeSplitter (C#) initialized successfully")
except ImportError as e:
    logger.warning(
        f"Tree-sitter or CodeSplitter not available: {e}. "
        "Falling back to default splitting."
    )
    transformations_list = []  # Use default LlamaIndex splitting

# ============================================================================
# Initialize Components
# ============================================================================

# Initialize FastMCP server
mcp = FastMCP(
    "Mutagen Helper",
    dependencies=["fastmcp", "llama-index", "chromadb"]
)

# Initialize embedding model
embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_NAME)

# Initialize ChromaDB client (persistent)
chroma_client = chromadb.PersistentClient(path=STORAGE_PATH)

# Initialize index manager
index_manager = IndexManager(
    chroma_client=chroma_client,
    embed_model=embed_model,
    transformations_list=transformations_list,
    storage_path=STORAGE_PATH,
    collection_name=COLLECTION_NAME
)

# Initialize search engine
search_engine = HybridSearchEngine(
    chroma_client=chroma_client,
    embed_model=embed_model,
    storage_path=STORAGE_PATH,
    collection_name=COLLECTION_NAME
)

# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def refresh_index(repo_path: str = MUTAGEN_REPO_PATH) -> str:
    """
    Scans the Mutagen repository and rebuilds the vector index.
    Filters out auto-generated files.
    
    Args:
        repo_path: Path to the Mutagen src directory.
        
    Returns:
        Status message with statistics
    """
    logger.info(f"Starting index refresh for: {repo_path}")
    
    # Clear search engine cache
    search_engine.clear_cache()
    
    # Perform index refresh
    result = index_manager.refresh_index(repo_path)
    
    # Format response
    if result["success"]:
        return (
            f"✅ Index refresh complete.\n"
            f"- Time taken: {result['elapsed_time']:.2f}s\n"
            f"- Handwritten files registered: {result['indexed_files']}\n"
            f"- Excluded generated files: {result['excluded_files']}\n"
            f"- Storage path: {result['storage_path']}"
        )
    else:
        return f"❌ Index refresh failed: {result.get('error', 'Unknown error')}"


@mcp.tool()
def search_repository(query: str, top_k: int = 10) -> str:
    """
    Searches the Mutagen repository index for relevant code snippets.
    
    Uses hybrid search combining:
    - Vector similarity (semantic search)
    - BM25 keyword matching
    - Cross-encoder reranking
    
    Args:
        query: The search query
        top_k: Number of results to return (default: 10)
        
    Returns:
        Formatted search results with source files
    """
    logger.info(f"Searching for: {query} (top_k={top_k})")
    
    # Perform search
    result = search_engine.search(query, top_k)
    
    # Format and return results
    return search_engine.format_search_results(result)


@mcp.tool()
def get_index_stats() -> str:
    """
    Returns statistics about the current index.
    
    Returns:
        Index statistics including document count and storage info
    """
    try:
        chroma_collection = chroma_client.get_collection(COLLECTION_NAME)
        count = chroma_collection.count()
        return (
            f"📊 Index Statistics\n"
            f"- Total Documents: {count}\n"
            f"- Collection Name: {COLLECTION_NAME}\n"
            f"- Storage Path: {STORAGE_PATH}"
        )
    except Exception as e:
        return f"❌ Failed to get stats: {str(e)}"


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        logger.info("Starting Mutagen RAG MCP Server...")
        mcp.run()
    except asyncio.CancelledError:
        logger.info("Shutdown requested (CancelledError). Exiting cleanly.")
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down MCP server.")
    except Exception as e:
        logger.exception("MCP server terminated with exception: %s", e)

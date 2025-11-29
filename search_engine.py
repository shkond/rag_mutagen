"""
Search engine module for Mutagen RAG system.
Implements hybrid search combining BM25 (sparse) and vector (dense) retrieval with reranking.
"""
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

from llama_index.core import (
    load_index_from_storage,
    StorageContext,
    QueryBundle
)
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.postprocessor import SentenceTransformerRerank
import chromadb

from config import (
    STORAGE_PATH,
    COLLECTION_NAME,
    DEFAULT_TOP_K,
    BM25_MULTIPLIER,
    VECTOR_MULTIPLIER,
    RERANKER_MODEL_NAME,
    RERANK_TOP_N_RATIO
)
from logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """
    Container for search results.
    """
    response_text: str
    source_nodes: List[NodeWithScore]
    success: bool
    error: Optional[str] = None


class HybridSearchEngine:
    """
    Hybrid search engine combining BM25 and vector retrieval with reranking.
    
    Manages:
    - BM25 retriever caching for performance
    - Hybrid fusion of sparse and dense retrieval
    - Reranking for improved relevance
    - Graceful fallbacks when components are unavailable
    """
    
    def __init__(
        self,
        chroma_client: chromadb.PersistentClient,
        embed_model,
        storage_path: str = None,
        collection_name: str = None,
        reranker_model: str = None
    ):
        """
        Initialize the hybrid search engine.
        
        Args:
            chroma_client: ChromaDB persistent client instance
            embed_model: Embedding model for vector search
            storage_path: Path to stored index metadata
            collection_name: Name of the ChromaDB collection
            reranker_model: Name of the reranker model
        """
        self.chroma_client = chroma_client
        self.embed_model = embed_model
        self.storage_path = storage_path or STORAGE_PATH
        self.collection_name = collection_name or COLLECTION_NAME
        self.reranker_model = reranker_model or RERANKER_MODEL_NAME
        
        # Cached BM25 retriever (replaces global variable)
        self._bm25_retriever: Optional[BM25Retriever] = None
        
        logger.info("HybridSearchEngine initialized")
    
    def clear_cache(self) -> None:
        """
        Clear the BM25 retriever cache.
        Should be called when the index is refreshed.
        """
        self._bm25_retriever = None
        logger.info("Cleared BM25 retriever cache")
    
    def _build_bm25_retriever(
        self,
        index,
        chroma_collection,
        top_k: int
    ) -> Optional[BM25Retriever]:
        """
        Build or retrieve cached BM25 retriever.
        
        Args:
            index: VectorStoreIndex instance
            chroma_collection: ChromaDB collection
            top_k: Number of top results to fetch
            
        Returns:
            BM25Retriever instance or None if building fails
        """
        # Return cached retriever if available
        if self._bm25_retriever is not None:
            logger.info("Using cached BM25 retriever")
            return self._bm25_retriever
        
        # Build new BM25 retriever
        logger.info("Building new BM25 retriever...")
        
        try:
            # Try to get nodes from docstore first
            nodes = list(index.docstore.docs.values())
            
            # If docstore is empty, fetch from ChromaDB
            if not nodes:
                logger.info("Docstore empty, fetching nodes from ChromaDB for BM25...")
                data = chroma_collection.get()
                
                if data and data.get('documents'):
                    for i, text in enumerate(data['documents']):
                        node = TextNode(
                            text=text,
                            id_=data['ids'][i],
                            metadata=data.get('metadatas', [{}])[i] if data.get('metadatas') else {}
                        )
                        nodes.append(node)
            
            # Build BM25 index from nodes
            if nodes:
                logger.info(f"Building BM25 index from {len(nodes)} nodes...")
                self._bm25_retriever = BM25Retriever.from_defaults(
                    nodes=nodes,
                    similarity_top_k=top_k * BM25_MULTIPLIER
                )
                logger.info("BM25 retriever cached successfully")
                return self._bm25_retriever
            else:
                logger.warning("No nodes found for BM25")
                return None
        
        except Exception as e:
            logger.error(f"Failed to initialize BM25Retriever: {e}")
            return None
    
    def _get_retrievers(
        self,
        index,
        chroma_collection,
        top_k: int
    ) -> Tuple[Any, Optional[BM25Retriever]]:
        """
        Get vector and BM25 retrievers.
        
        Args:
            index: VectorStoreIndex instance
            chroma_collection: ChromaDB collection
            top_k: Number of top results
            
        Returns:
            Tuple of (vector_retriever, bm25_retriever)
        """
        # Vector retriever (dense search)
        retriever_vector = index.as_retriever(
            similarity_top_k=top_k * VECTOR_MULTIPLIER
        )
        
        # BM25 retriever (sparse search)
        retriever_bm25 = self._build_bm25_retriever(index, chroma_collection, top_k)
        
        return retriever_vector, retriever_bm25
    
    def _create_fusion_retriever(
        self,
        retriever_vector,
        retriever_bm25: Optional[BM25Retriever],
        top_k: int
    ):
        """
        Create fusion retriever combining vector and BM25.
        
        Args:
            retriever_vector: Vector retriever instance
            retriever_bm25: BM25 retriever instance (optional)
            top_k: Number of top results
            
        Returns:
            Fusion retriever or vector retriever if BM25 is unavailable
        """
        if retriever_bm25 is None:
            logger.warning("Falling back to Vector Search only (BM25 missing)")
            return retriever_vector
        
        try:
            # Combine results from both retrievers using reciprocal rank fusion
            retriever_fusion = QueryFusionRetriever(
                [retriever_vector, retriever_bm25],
                similarity_top_k=top_k * VECTOR_MULTIPLIER,  # Fetch candidates for reranking
                num_queries=1,
                mode="reciprocal_rank",
                use_async=False,
                verbose=True
            )
            return retriever_fusion
        except Exception as e:
            logger.warning(f"Failed to create fusion retriever: {e}. Using vector only.")
            return retriever_vector
    
    def _create_reranker(self, top_k: int):
        """
        Create reranker for post-processing results.
        
        Args:
            top_k: Number of final results after reranking
            
        Returns:
            SentenceTransformerRerank instance or None if creation fails
        """
        try:
            reranker = SentenceTransformerRerank(
                model=self.reranker_model,
                top_n=int(top_k * RERANK_TOP_N_RATIO)
            )
            return reranker
        except Exception as e:
            logger.warning(f"Failed to create reranker: {e}")
            return None
    
    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> SearchResult:
        """
        Perform hybrid search on the indexed repository.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            SearchResult object with response and source nodes
        """
        try:
            # Check if collection exists
            try:
                chroma_collection = self.chroma_client.get_collection(self.collection_name)
            except ValueError:
                return SearchResult(
                    response_text="",
                    source_nodes=[],
                    success=False,
                    error="Index does not exist. Please run 'refresh_index' first."
                )
            
            # Load index
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                persist_dir=self.storage_path
            )
            
            index = load_index_from_storage(
                storage_context,
                embed_model=self.embed_model
            )
            
            # Get retrievers
            retriever_vector, retriever_bm25 = self._get_retrievers(
                index,
                chroma_collection,
                top_k
            )
            
            # Create fusion retriever
            final_retriever = self._create_fusion_retriever(
                retriever_vector,
                retriever_bm25,
                top_k
            )
            
            # Create reranker
            reranker = self._create_reranker(top_k)
            
            # Try to use query engine
            try:
                query_engine = index.as_query_engine(
                    retriever=final_retriever,
                    node_postprocessors=[reranker] if reranker else [],
                    response_mode="refine"
                )
                response = query_engine.query(query)
                response_text = str(response)
                source_nodes = response.source_nodes
            
            except Exception as e:
                # Fallback to direct retrieval if query engine fails
                logger.warning(
                    f"Query engine failed (likely missing LLM): {e}. "
                    "Returning retrieval results only."
                )
                source_nodes = retriever_vector.retrieve(query)
                
                # Apply reranker manually if available
                if reranker and source_nodes:
                    source_nodes = reranker.postprocess_nodes(
                        source_nodes,
                        query_bundle=QueryBundle(query)
                    )
                
                response_text = "⚠️ LLM not configured or failed. Showing retrieved documents only."
            
            return SearchResult(
                response_text=response_text,
                source_nodes=source_nodes,
                success=True
            )
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return SearchResult(
                response_text="",
                source_nodes=[],
                success=False,
                error=str(e)
            )
    
    def format_search_results(self, result: SearchResult) -> str:
        """
        Format search results for display.
        
        Args:
            result: SearchResult object
            
        Returns:
            Formatted string with response and sources
        """
        if not result.success:
            return f"❌ Error during search: {result.error}"
        
        # Build sources list
        sources_list = []
        for node in result.source_nodes:
            # Handle NodeWithScore or TextNode
            n = node.node if hasattr(node, 'node') else node
            score = f"{node.score:.4f}" if hasattr(node, 'score') and node.score is not None else "N/A"
            
            file_path = n.metadata.get('file_path', 'Unknown')
            types = n.metadata.get('defined_types', '')
            
            sources_list.append(
                f"- {file_path} (Score: {score}) {f'[{types}]' if types else ''}"
            )
        
        sources = "\n".join(sources_list)
        
        return f"{result.response_text}\n\n📂 Source Files:\n{sources}"

"""
Index management module for Mutagen RAG system.
Handles vector index creation, updating, and persistence.
"""
import time
from pathlib import Path
from typing import List, Dict, Any

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
)
from llama_index.core.schema import Document
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from config import (
    STORAGE_PATH,
    COLLECTION_NAME,
    DEFAULT_BATCH_SIZE,
    MAX_BATCH_SIZE,
    BATCH_SIZE_DIVISOR
)
from file_filters import FileFilterer
from metadata_extractor import MetadataExtractor
from logging_config import get_logger

logger = get_logger(__name__)


class IndexManager:
    """
    Manages vector index creation, updates, and persistence.
    
    Orchestrates the multi-step process of:
    1. Scanning and filtering files
    2. Loading documents
    3. Extracting metadata
    4. Building vector index
    5. Persisting to disk
    """
    
    def __init__(
        self,
        chroma_client: chromadb.PersistentClient,
        embed_model,
        transformations_list: List = None,
        storage_path: str = None,
        collection_name: str = None
    ):
        """
        Initialize the index manager.
        
        Args:
            chroma_client: ChromaDB persistent client instance
            embed_model: Embedding model for vector generation
            transformations_list: List of transformations (e.g., CodeSplitter) to apply
            storage_path: Path to store index metadata
            collection_name: Name of the ChromaDB collection
        """
        self.chroma_client = chroma_client
        self.embed_model = embed_model
        self.transformations_list = transformations_list or []
        self.storage_path = storage_path or STORAGE_PATH
        self.collection_name = collection_name or COLLECTION_NAME
        
        # Initialize helper classes
        self.file_filterer = FileFilterer()
        self.metadata_extractor = MetadataExtractor()
        
        # Calculate safe batch size for ChromaDB
        self.batch_size = self._calculate_batch_size()
        
        logger.info(f"IndexManager initialized with batch size: {self.batch_size}")
    
    def _calculate_batch_size(self) -> int:
        """
        Calculate safe batch size for ChromaDB insertions.
        
        Returns:
            Safe batch size integer
        """
        try:
            max_batch = getattr(self.chroma_client, "max_batch_size", MAX_BATCH_SIZE)
            safe_batch = min(MAX_BATCH_SIZE, max_batch // BATCH_SIZE_DIVISOR)
            logger.info(f"ChromaDB max_batch_size: {max_batch}, using: {safe_batch}")
            return safe_batch
        except Exception as e:
            logger.warning(f"Failed to get max_batch_size: {e}. Using fallback: {DEFAULT_BATCH_SIZE}")
            return DEFAULT_BATCH_SIZE
    
    def scan_and_filter_files(self, repo_path: str) -> List[str]:
        """
        Scan repository and return filtered file paths.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            List of file paths that passed the fast filter
            
        Raises:
            ValueError: If repo path doesn't exist or no files found
        """
        repo_path_obj = Path(repo_path)
        
        if not repo_path_obj.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        logger.info(f"Scanning repository at: {repo_path}")
        
        # Use FileFilterer to scan with fast pre-filtering
        all_files = self.file_filterer.scan_files(repo_path_obj, extension=".cs")
        
        if not all_files:
            raise ValueError(f"No .cs files found after pre-filtering in {repo_path}")
        
        return all_files
    
    def load_documents(self, file_paths: List[str]) -> List[Document]:
        """
        Load documents from file paths.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            List of loaded Document objects
            
        Raises:
            RuntimeError: If document loading fails
        """
        reader = SimpleDirectoryReader(
            input_files=file_paths,
            filename_as_id=True
        )
        
        try:
            all_docs = reader.load_data()
            logger.info(f"Loaded {len(all_docs)} documents")
        except Exception as e:
            raise RuntimeError(f"Error loading data: {e}")
        
        return all_docs
    
    def filter_and_add_metadata(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents by content and add metadata.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of filtered documents with metadata
            
        Raises:
            ValueError: If no documents remain after filtering
        """
        logger.info(f"Applying header-based filtering to {len(documents)} documents...")
        
        # Filter by content (header check)
        filtered_docs = self.file_filterer.filter_documents_by_content(documents)
        
        if not filtered_docs:
            raise ValueError("No documents remained after filtering. Check path and filter logic.")
        
        # Add metadata to each document
        for doc in filtered_docs:
            # Basic metadata
            doc.metadata["source"] = "mutagen_handwritten"
            doc.metadata["indexed_at"] = str(Path(doc.metadata["file_path"]).stat().st_mtime)
            
            # Extract C# metadata
            try:
                csharp_metadata = self.metadata_extractor.extract_all(
                    doc.metadata["file_path"],
                    doc.text
                )
                doc.metadata.update(csharp_metadata)
            except Exception as e:
                logger.warning(
                    f"Failed to extract metadata for {doc.metadata.get('file_path', 'unknown')}: {e}"
                )
        
        return filtered_docs
    
    def build_index(self, documents: List[Document]) -> VectorStoreIndex:
        """
        Build vector index from documents.
        
        Args:
            documents: List of Document objects with metadata
            
        Returns:
            Created VectorStoreIndex
        """
        # Initialize ChromaDB collection
        chroma_collection = self.chroma_client.get_or_create_collection(self.collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create index with configured transformations
        logger.info(f"Building index with {len(documents)} documents...")
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=self.embed_model,
            transformations=self.transformations_list,
            show_progress=True,
            insert_batch_size=self.batch_size
        )
        
        logger.info("Index built successfully")
        return index
    
    def persist_index(self, index: VectorStoreIndex) -> None:
        """
        Persist index to disk.
        
        Args:
            index: VectorStoreIndex to persist
        """
        index.storage_context.persist(persist_dir=self.storage_path)
        logger.info(f"Index persisted to {self.storage_path}")
    
    def refresh_index(self, repo_path: str) -> Dict[str, Any]:
        """
        Complete index refresh workflow.
        
        Orchestrates all steps:
        1. Scan and filter files
        2. Load documents
        3. Filter by content and add metadata
        4. Build index
        5. Persist to disk
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary with statistics:
            - success: bool
            - elapsed_time: float
            - total_files: int
            - indexed_files: int
            - excluded_files: int
            - storage_path: str
            - error: str (if failed)
        """
        start_time = time.time()
        
        try:
            # Step 1: Scan and filter files
            file_paths = self.scan_and_filter_files(repo_path)
            total_files = len(file_paths)
            
            # Step 2: Load documents
            documents = self.load_documents(file_paths)
            
            # Step 3: Filter by content and add metadata
            filtered_docs = self.filter_and_add_metadata(documents)
            indexed_files = len(filtered_docs)
            excluded_files = total_files - indexed_files + (len(documents) - indexed_files)
            
            # Step 4: Build index
            index = self.build_index(filtered_docs)
            
            # Step 5: Persist to disk
            self.persist_index(index)
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "elapsed_time": elapsed_time,
                "total_files": total_files,
                "indexed_files": indexed_files,
                "excluded_files": excluded_files,
                "storage_path": self.storage_path
            }
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Index refresh failed: {e}")
            return {
                "success": False,
                "elapsed_time": elapsed_time,
                "error": str(e)
            }

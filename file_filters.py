"""
File filtering module for Mutagen RAG system.
Handles filtering of generated files and directory scanning.
"""
import os
from pathlib import Path
from typing import List

from config import (
    GENERATED_SUFFIXES,
    EXCLUDED_DIRS,
    GENERATED_MARKERS,
    HEADER_CHECK_CHARS
)
from logging_config import get_logger

logger = get_logger(__name__)


class FileFilterer:
    """
    Handles file filtering and scanning for the Mutagen codebase.
    
    Provides two-stage filtering:
    1. Fast path-based filtering (no file I/O) - checks extensions and directories
    2. Slow content-based filtering (reads file headers) - checks for generated markers
    """
    
    def __init__(
        self,
        generated_suffixes: List[str] = None,
        excluded_dirs: set = None,
        generated_markers: List[str] = None,
        header_check_chars: int = None
    ):
        """
        Initialize the file filterer with configurable parameters.
        
        Args:
            generated_suffixes: File name suffixes indicating generated files
            excluded_dirs: Directory names to exclude from scanning
            generated_markers: Content markers indicating auto-generated files
            header_check_chars: Number of characters to check in file header
        """
        self.generated_suffixes = generated_suffixes or GENERATED_SUFFIXES
        self.excluded_dirs = excluded_dirs or EXCLUDED_DIRS
        self.generated_markers = generated_markers or GENERATED_MARKERS
        self.header_check_chars = header_check_chars or HEADER_CHECK_CHARS
    
    def is_generated_file_fast(self, file_path: Path) -> bool:
        """
        Fast path-based filtering without file I/O.
        Checks file extensions and directory names only.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file appears to be generated, False otherwise
        """
        path_str = str(file_path)
        
        # 1. Check file name patterns
        if any(path_str.endswith(suffix) for suffix in self.generated_suffixes):
            return True
        
        # 2. Check directory names
        if any(excluded_dir in file_path.parts for excluded_dir in self.excluded_dirs):
            return True
        
        return False
    
    def is_header_generated(self, text: str) -> bool:
        """
        Check if file content has auto-generated markers.
        This is the slow check that reads file content.
        
        Args:
            text: File content
            
        Returns:
            True if the file content indicates it's auto-generated, False otherwise
        """
        # Only check first N chars for performance
        header = text[:self.header_check_chars]
        return any(marker in header for marker in self.generated_markers)
    
    def scan_files(self, repo_path: Path, extension: str = ".cs") -> List[str]:
        """
        Scan repository and return list of non-generated files.
        
        This performs FAST pre-filtering before loading files into memory,
        dramatically reducing memory usage and I/O for large codebases.
        
        Args:
            repo_path: Path to the repository root
            extension: File extension to filter (default: ".cs")
            
        Returns:
            List of absolute file paths (as strings) that passed the fast filter
        """
        if not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            return []
        
        all_files = []
        
        for root, dirs, files in os.walk(str(repo_path)):
            # Modify dirs in-place to skip excluded directories
            # This prevents os.walk from descending into them
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                if file.endswith(extension):
                    full_path = Path(root) / file
                    
                    # Fast path-based filtering (no file I/O)
                    if not self.is_generated_file_fast(full_path):
                        all_files.append(str(full_path))
        
        logger.info(f"Pre-filtered to {len(all_files)} {extension} files before loading")
        return all_files
    
    def filter_documents_by_content(self, documents: List) -> List:
        """
        Filter documents by checking their content for generated markers.
        
        This is the second-stage filtering that reads file content.
        Should only be called on documents that already passed the fast filter.
        
        Args:
            documents: List of LlamaIndex Document objects
            
        Returns:
            Filtered list of documents without generated content
        """
        filtered_docs = [
            d for d in documents
            if not self.is_header_generated(d.text)
        ]
        
        excluded_count = len(documents) - len(filtered_docs)
        logger.info(
            f"Filtered down to {len(filtered_docs)} documents. "
            f"Excluded {excluded_count} files with generated headers."
        )
        
        return filtered_docs

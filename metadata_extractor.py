"""
Metadata extraction module for Mutagen RAG system.
Extracts C# specific metadata from source files.
"""
import re
from typing import Optional, List, Dict

from config import MAX_METADATA_LENGTH
from logging_config import get_logger

logger = get_logger(__name__)


class MetadataExtractor:
    """
    Extracts C# specific metadata from source code files.
    
    Supports extraction of:
    - Namespace names
    - Type definitions (class, interface, struct, enum, record)
    - Public method names
    """
    
    def __init__(self, max_length: int = None):
        """
        Initialize the metadata extractor.
        
        Args:
            max_length: Maximum length for joined metadata strings to avoid overflow
        """
        self.max_length = max_length or MAX_METADATA_LENGTH
    
    def extract_namespace(self, content: str) -> Optional[str]:
        """
        Extract namespace from C# code.
        
        Args:
            content: C# source code content
            
        Returns:
            Namespace name if found, None otherwise
        """
        namespace_match = re.search(r'namespace\s+([\w\.]+)', content)
        if namespace_match:
            return namespace_match.group(1)
        return None
    
    def extract_types(self, content: str) -> List[str]:
        """
        Extract type definitions (class, interface, struct, enum, record) from C# code.
        
        Args:
            content: C# source code content
            
        Returns:
            List of type definitions in format "type:Name"
        """
        types = []
        for match in re.finditer(
            r'(class|interface|struct|enum|record)\s+([\w]+)',
            content
        ):
            types.append(f"{match.group(1)}:{match.group(2)}")
        return types
    
    def extract_methods(self, content: str) -> List[str]:
        """
        Extract public method names from C# code.
        
        Pattern matches: public [modifiers] ReturnType MethodName(
        This is used for BM25 keyword matching to improve search accuracy.
        
        Args:
            content: C# source code content
            
        Returns:
            List of unique public method names
        """
        method_pattern = r'public\s+(?:static\s+|virtual\s+|override\s+|async\s+)?[\w<>\[\]]+\s+([\w]+)\s*\('
        methods = re.findall(method_pattern, content)
        
        # Remove duplicates while preserving order
        unique_methods = list(dict.fromkeys(methods))
        return unique_methods
    
    def _truncate_if_needed(self, text: str) -> str:
        """
        Truncate text if it exceeds maximum length.
        
        Args:
            text: Text to truncate
            
        Returns:
            Truncated text with "..." suffix if needed
        """
        if len(text) > self.max_length:
            return text[:self.max_length - 3] + "..."
        return text
    
    def extract_all(self, file_path: str, content: str) -> Dict[str, str]:
        """
        Extract all metadata from C# source file.
        
        Args:
            file_path: Path to the source file (for logging)
            content: C# source code content
            
        Returns:
            Dictionary containing extracted metadata (namespace, defined_types, methods)
        """
        metadata = {}
        
        try:
            # Extract namespace
            namespace = self.extract_namespace(content)
            if namespace:
                metadata["namespace"] = namespace
            
            # Extract type definitions
            types = self.extract_types(content)
            if types:
                joined_types = ", ".join(types)
                metadata["defined_types"] = self._truncate_if_needed(joined_types)
            
            # Extract public methods
            methods = self.extract_methods(content)
            if methods:
                joined_methods = ", ".join(methods)
                metadata["methods"] = self._truncate_if_needed(joined_methods)
        
        except Exception as e:
            logger.warning(f"Failed to extract metadata for {file_path}: {e}")
        
        return metadata

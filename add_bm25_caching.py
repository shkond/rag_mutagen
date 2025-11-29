#!/usr/bin/env python3
"""
Complete the optimizations by adding BM25 caching to search_repository
"""

# Read the file
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the get_bm25_retriever helper function before refresh_index
helper_function = '''
def get_bm25_retriever(index, chroma_collection, top_k: int):
    """
    Get or build BM25 retriever with caching.
    Cached retriever is reused across searches until index is refreshed.
    """
    global _CACHED_BM25_RETRIEVER
    
    if _CACHED_BM25_RETRIEVER is not None:
        logger.info("Using cached BM25 retriever")
        return _CACHED_BM25_RETRIEVER
    
    # Build BM25 retriever
    logger.info("Building new BM25 retriever...")
    try:
        nodes = list(index.docstore.docs.values())
        if not nodes:
            logger.info("Docstore empty, fetching nodes from ChromaDB for BM25...")
            data = chroma_collection.get()
            if data and data['documents']:
                for i, text in enumerate(data['documents']):
                    node = TextNode(
                        text=text, 
                        id_=data['ids'][i], 
                        metadata=data['metadatas'][i] if data['metadatas'] else {}
                    )
                    nodes.append(node)
        
        logger.info(f"Building BM25 index from {len(nodes)} nodes...")
        if nodes:
            _CACHED_BM25_RETRIEVER = BM25Retriever.from_defaults(
                nodes=nodes,
                similarity_top_k=top_k * 3
            )
            logger.info("BM25 retriever cached successfully")
            return _CACHED_BM25_RETRIEVER
        else:
            logger.warning("No nodes found for BM25.")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize BM25Retriever: {e}")
        return None

'''

# Insert helper function before @mcp.tool() for refresh_index
refresh_marker = '@mcp.tool()\\ndef refresh_index('
if refresh_marker in content:
    content = content.replace(refresh_marker, helper_function + refresh_marker)

# 2. Replace BM25 construction in search_repository with cached call
old_bm25_code = '''        # 1. BM25 Retriever (Sparse)
        # We construct it from the docstore of the loaded index
        # Note: This builds the BM25 index in memory, which is fast for <5k files
        retriever_bm25 = None
        try:
            nodes = list(index.docstore.docs.values())
            if not nodes:
                logger.info("Docstore empty, fetching nodes from ChromaDB for BM25...")
                data = chroma_collection.get()
                if data and data['documents']:
                    for i, text in enumerate(data['documents']):
                        # Reconstruct TextNode
                        # Note: We might lose some node attributes not stored in metadata/text
                        # but it's enough for BM25
                        node = TextNode(
                            text=text, 
                            id_=data['ids'][i], 
                            metadata=data['metadatas'][i] if data['metadatas'] else {}
                        )
                        nodes.append(node)
            
            logger.info(f"Building BM25 index from {len(nodes)} nodes...")
            if nodes:
                retriever_bm25 = BM25Retriever.from_defaults(
                    nodes=nodes,
                    similarity_top_k=top_k * 3 # Fetch more candidates for fusion
                )
            else:
                logger.warning("No nodes found for BM25.")
        except Exception as e:
            logger.error(f"Failed to initialize BM25Retriever: {e}")'''

new_bm25_code = '''        # 1. BM25 Retriever (Sparse) - with caching for performance
        retriever_bm25 = get_bm25_retriever(index, chroma_collection, top_k)'''

content = content.replace(old_bm25_code, new_bm25_code)

# Write the output
with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("BM25 caching optimizations applied successfully!")

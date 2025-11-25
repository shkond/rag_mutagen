import sys
import os
from pathlib import Path

# Add current directory to sys.path
sys.path.append(os.getcwd())

from server import refresh_index, search_repository

def main():
    print("=== Verifying RAG Improvements ===")
    
    # 1. Refresh Index
    print("\n[1] Running refresh_index...")
    repo_path = "./Mutagen/Mutagen.Bethesda.Core"
    if not os.path.exists(repo_path):
        print(f"Warning: {repo_path} does not exist. Using ./Mutagen if available or skipping.")
        if os.path.exists("./Mutagen"):
             repo_path = "./Mutagen"
        else:
             print("Error: No Mutagen directory found.")
             return

    try:
        # FastMCP tools might be callable directly
        result = refresh_index(repo_path=repo_path)
        print("Result:", result)
    except Exception as e:
        print(f"Error calling refresh_index: {e}")
        # Try accessing original function if it's a wrapper
        if hasattr(refresh_index, 'fn'):
            try:
                result = refresh_index.fn(repo_path=repo_path)
                print("Result (via .fn):", result)
            except Exception as e2:
                print(f"Error calling refresh_index.fn: {e2}")

    # 2. Search Repository
    print("\n[2] Running search_repository (Hybrid + Rerank)...")
    query = "FormLink implementation"
    try:
        result = search_repository(query=query, top_k=3)
        print("Result:", result)
    except Exception as e:
        print(f"Error calling search_repository: {e}")
        if hasattr(search_repository, 'fn'):
            try:
                result = search_repository.fn(query=query, top_k=3)
                print("Result (via .fn):", result)
            except Exception as e2:
                print(f"Error calling search_repository.fn: {e2}")

if __name__ == "__main__":
    main()

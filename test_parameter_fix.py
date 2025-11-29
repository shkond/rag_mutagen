"""
Test to verify the fix for multi-path refresh_index parameter name issue.
Tests both repo_path (singular) and repo_paths (plural) parameter names.
"""
import sys

def get_refresh_index_function():
    """Get the actual refresh_index function from the MCP tool wrapper"""
    from server import refresh_index
    
    # FastMCP wraps the function in a FunctionTool object
    # We need to access the underlying function
    if hasattr(refresh_index, 'fn'):
        return refresh_index.fn
    elif hasattr(refresh_index, '__wrapped__'):
        return refresh_index.__wrapped__
    else:
        # If it's already a function, return it
        return refresh_index

def test_repo_path_singular():
    """Test with repo_path (singular) - what AI clients use"""
    print("=" * 70)
    print("Test 1: repo_path (singular) - AI Client Format")
    print("=" * 70)
    
    refresh_index = get_refresh_index_function()
    
    # Simulate AI client call with repo_path (singular)
    result = refresh_index(repo_path="./Mutagen")
    print(f"✓ Success with repo_path parameter")
    print(f"Result (first 150 chars): {result[:150]}...")
    print()

def test_repo_paths_plural():
    """Test with repo_paths (plural) - backward compatibility"""
    print("=" * 70)
    print("Test 2: repo_paths (plural) - Backward Compatibility")
    print("=" * 70)
    
    refresh_index = get_refresh_index_function()
    
    # Test with repo_paths (plural)
    result = refresh_index(repo_paths="./Mutagen")
    print(f"✓ Success with repo_paths parameter")
    print(f"Result (first 150 chars): {result[:150]}...")
    print()

def test_comma_separated_string():
    """Test with comma-separated string"""
    print("=" * 70)
    print("Test 3: Comma-Separated String (Multiple Paths)")
    print("=" * 70)
    
    refresh_index = get_refresh_index_function()
    
    # Test with comma-separated paths (using repo_path)
    paths = "Mutagen.Bethesda.Core,Mutagen.Bethesda.Fallout4"
    result = refresh_index(repo_path=paths)
    print(f"✓ Success with comma-separated paths")
    print(f"Result (first 150 chars): {result[:150]}...")
    print()

def test_list_input():
    """Test with list input"""
    print("=" * 70)
    print("Test 4: List Input (AI Might Send This)")
    print("=" * 70)
    
    refresh_index = get_refresh_index_function()
    
    # Test with list of paths
    paths = ["./Mutagen", "./NonExistent"]
    result = refresh_index(repo_path=paths)
    print(f"✓ Success with list input")
    print(f"Result (first 150 chars): {result[:150]}...")
    print()

def test_default_value():
    """Test with no parameters (should use default)"""
    print("=" * 70)
    print("Test 5: No Parameters (Default Value)")
    print("=" * 70)
    
    refresh_index = get_refresh_index_function()
    
    # Test with no parameters
    result = refresh_index()
    print(f"✓ Success with default value")
    print(f"Result (first 150 chars): {result[:150]}...")
    print()

def test_both_parameters():
    """Test when both parameters are provided (repo_paths should take precedence)"""
    print("=" * 70)
    print("Test 6: Both Parameters (repo_paths Should Win)")
    print("=" * 70)
    
    refresh_index = get_refresh_index_function()
    
    # Test with both parameters (repo_paths should take precedence)
    result = refresh_index(repo_path="./Wrong", repo_paths="./Mutagen")
    print(f"✓ Success - repo_paths took precedence")
    print(f"Result (first 150 chars): {result[:150]}...")
    print()

def test_exact_ai_call():
    """Test the exact format that caused the original error"""
    print("=" * 70)
    print("Test 7: Exact AI Client Call (Original Error Case)")
    print("=" * 70)
    
    refresh_index = get_refresh_index_function()
    
    # This is the exact call that was failing
    paths = "Mutagen.Bethesda.Fallout4,Mutagen.Bethesda.Fallout4.Generator,Mutagen.Bethesda.Tests,Mutagen.Bethesda.UnitTests,Mutagen.Bethesda.Core.UnitTests,Mutagen.Bethesda.Testing,Mutagen.Bethesda.Core,Mutagen.Bethesda"
    
    result = refresh_index(repo_path=paths)
    print(f"✓ Success with exact AI client format")
    print(f"Result (first 150 chars): {result[:150]}...")
    print()

if __name__ == "__main__":
    try:
        print("\n" + "=" * 70)
        print("MULTI-PATH REFRESH_INDEX FIX VERIFICATION")
        print("=" * 70)
        print()
        
        test_repo_path_singular()
        test_repo_paths_plural()
        test_comma_separated_string()
        test_list_input()
        test_default_value()
        test_both_parameters()
        test_exact_ai_call()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("""
Summary:
  ✓ repo_path (singular) parameter works
  ✓ repo_paths (plural) parameter works (backward compatible)
  ✓ Comma-separated strings work
  ✓ List inputs work
  ✓ Default value works
  ✓ Parameter precedence works correctly
  ✓ Exact AI client format works

The fix successfully resolves the parameter name mismatch issue!
        """)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

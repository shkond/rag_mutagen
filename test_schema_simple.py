"""
Simplified test to check MCP tool schema for refresh_index
"""
import sys
import json

def check_tool_schema():
    """Check the MCP tool schema"""
    print("=" * 70)
    print("Checking MCP Tool Schema for refresh_index")
    print("=" * 70)
    
    # Import after printing header to see any import errors
    from server import refresh_index
    import inspect
    
    # Get function signature
    sig = inspect.signature(refresh_index)
    print(f"\nFunction Signature:")
    print(f"  {refresh_index.__name__}{sig}")
    
    # Get parameters
    print(f"\nParameters:")
    for param_name, param in sig.parameters.items():
        print(f"  - {param_name}:")
        print(f"      Type annotation: {param.annotation}")
        print(f"      Default: {param.default}")
        print(f"      Kind: {param.kind}")
    
    # Get docstring
    print(f"\nDocstring:")
    print(f"  {refresh_index.__doc__}")
    
    return sig

def test_string_input():
    """Test with string input (correct)"""
    print("\n" + "=" * 70)
    print("Test 1: String Input (Single Path)")
    print("=" * 70)
    
    from server import refresh_index
    
    input_val = "./Mutagen"
    print(f"Input: {repr(input_val)}")
    print(f"Type: {type(input_val).__name__}")
    
    try:
        result = refresh_index(input_val)
        print(f"✓ Success")
        print(f"Result (first 150 chars): {result[:150]}...")
    except Exception as e:
        print(f"✗ Error: {e}")

def test_comma_separated_string():
    """Test with comma-separated string (correct)"""
    print("\n" + "=" * 70)
    print("Test 2: Comma-Separated String (Multiple Paths)")
    print("=" * 70)
    
    from server import refresh_index
    
    input_val = "./Mutagen,./NonExistent"
    print(f"Input: {repr(input_val)}")
    print(f"Type: {type(input_val).__name__}")
    
    try:
        result = refresh_index(input_val)
        print(f"✓ Success")
        print(f"Result (first 150 chars): {result[:150]}...")
    except Exception as e:
        print(f"✗ Error: {e}")

def test_list_input():
    """Test with list input (WRONG - this is what AI might try)"""
    print("\n" + "=" * 70)
    print("Test 3: List Input (POTENTIAL ERROR CASE)")
    print("=" * 70)
    
    from server import refresh_index
    
    input_val = ["./Mutagen", "./NonExistent"]
    print(f"Input: {repr(input_val)}")
    print(f"Type: {type(input_val).__name__}")
    
    try:
        result = refresh_index(input_val)
        print(f"✓ Success (unexpected!)")
        print(f"Result (first 150 chars): {result[:150]}...")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        print(f"\n💡 This is likely the issue!")
        print(f"   AI is passing a list instead of a comma-separated string")

if __name__ == "__main__":
    try:
        # Check schema
        check_tool_schema()
        
        # Test different input types
        test_string_input()
        test_comma_separated_string()
        test_list_input()
        
        print("\n" + "=" * 70)
        print("CONCLUSION")
        print("=" * 70)
        print("""
The refresh_index function expects a STRING parameter (repo_paths: str).

For multiple paths, the string should be:
  - Comma-separated: "path1,path2,path3"
  - OR Newline-separated: "path1\\npath2\\npath3"

If an AI client passes a LIST instead of a STRING, it will fail.

Possible solutions:
  1. Update the function to accept Union[str, List[str]]
  2. Update the MCP tool description to be more explicit
  3. Add input validation that converts lists to comma-separated strings
        """)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

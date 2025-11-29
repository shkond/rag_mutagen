#!/usr/bin/env python3
"""
Test metadata extraction function without full dependencies
"""
import re

def extract_metadata(file_path: str, content: str) -> dict:
    """
    Extracts C# specific metadata (namespace, class, method names, etc.)
    """
    metadata = {}
    
    # Extract Namespace
    namespace_match = re.search(r'namespace\s+([\w\.]+)', content)
    if namespace_match:
        metadata["namespace"] = namespace_match.group(1)
        
    # Extract Class/Interface/Struct names
    types = []
    for match in re.finditer(r'(class|interface|struct|enum|record)\s+([\w]+)', content):
        types.append(f"{match.group(1)}:{match.group(2)}")
    
    if types:
        joined_types = ", ".join(types)
        if len(joined_types) > 500:
            joined_types = joined_types[:497] + "..."
        metadata["defined_types"] = joined_types
    
    # Extract Method Names (public methods for BM25 keyword matching)
    method_pattern = r'public\s+(?:static\s+|virtual\s+|override\s+|async\s+)?[\w<>\[\]]+\s+([\w]+)\s*\('
    methods = re.findall(method_pattern, content)
    
    if methods:
        # Remove duplicates and limit size to avoid metadata overflow
        unique_methods = list(set(methods))
        joined_methods = ", ".join(unique_methods)
        if len(joined_methods) > 500:
            joined_methods = joined_methods[:497] + "..."
        metadata["methods"] = joined_methods
        
    return metadata

# Test cases
test_code = '''
namespace Mutagen.Bethesda.Skyrim
{
    public class LoadOrder
    {
        public static void Initialize() { }
        
        public virtual int Calculate(int value) { 
            return value * 2; 
        }
        
        public override string ToString() { 
            return "LoadOrder"; 
        }
        
        public async Task<bool> ProcessAsync() { 
            return true; 
        }
        
        private void InternalMethod() { }
    }
    
    public interface IWeapon
    {
        public void Attack();
    }
}
'''

result = extract_metadata('test.cs', test_code)

print("✅ Metadata Extraction Test Results:")
print(f"Namespace: {result.get('namespace', 'N/A')}")
print(f"Defined Types: {result.get('defined_types', 'N/A')}")
print(f"Public Methods: {result.get('methods', 'N/A')}")

expected_methods = {'Initialize', 'Calculate', 'ToString', 'ProcessAsync', 'Attack'}
extracted_methods = set(result.get('methods', '').split(', '))

print(f"\n✅ Expected methods found: {expected_methods.intersection(extracted_methods)}")
if 'InternalMethod' in extracted_methods:
    print("⚠️  Warning: Private method detected (should be filtered)")
else:
    print("✅ Private methods correctly excluded")

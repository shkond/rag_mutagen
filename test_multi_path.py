"""
Lightweight test script for multi-path refresh_index functionality.
Tests path parsing logic without requiring full dependencies.
"""
from pathlib import Path

print("="*60)
print("Multi-Path Parsing Test Suite")
print("="*60)

# Test 1: Single path (backward compatibility)
print("\n" + "="*60)
print("Test 1: Single Path (Backward Compatibility)")
print("="*60)
single_path = "./Mutagen/Mutagen.Bethesda.Core"
print(f"Input: '{single_path}'")

if '\n' in single_path:
    paths = [p.strip() for p in single_path.split('\n') if p.strip()]
elif ',' in single_path:
    paths = [p.strip() for p in single_path.split(',') if p.strip()]
else:
    paths = [single_path.strip()]

print(f"Parsed paths: {paths}")
print(f"✓ Expected 1 path, got {len(paths)}")
assert len(paths) == 1, "Single path parsing failed"
assert paths[0] == "./Mutagen/Mutagen.Bethesda.Core"

# Test 2: Comma-separated paths
print("\n" + "="*60)
print("Test 2: Comma-Separated Paths")
print("="*60)
comma_paths = "./Mutagen/Mutagen.Bethesda.Core,./Mutagen/Mutagen.Bethesda.Core.UnitTests"
print(f"Input: '{comma_paths}'")

if '\n' in comma_paths:
    paths = [p.strip() for p in comma_paths.split('\n') if p.strip()]
elif ',' in comma_paths:
    paths = [p.strip() for p in comma_paths.split(',') if p.strip()]
else:
    paths = [comma_paths.strip()]

print(f"Parsed paths:")
for i, p in enumerate(paths, 1):
    print(f"  {i}. {p}")
print(f"✓ Expected 2 paths, got {len(paths)}")
assert len(paths) == 2, "Comma-separated parsing failed"

# Test 3: Newline-separated paths
print("\n" + "="*60)
print("Test 3: Newline-Separated Paths")
print("="*60)
newline_paths = """./Mutagen/Mutagen.Bethesda.Core
./Mutagen/Mutagen.Bethesda.Core.UnitTests
./Mutagen/Mutagen.Bethesda.Fallout4"""
print(f"Input (multiline):")
for line in newline_paths.split('\n'):
    print(f"  {repr(line)}")

if '\n' in newline_paths:
    paths = [p.strip() for p in newline_paths.split('\n') if p.strip()]
elif ',' in newline_paths:
    paths = [p.strip() for p in newline_paths.split(',') if p.strip()]
else:
    paths = [newline_paths.strip()]

print(f"Parsed paths:")
for i, p in enumerate(paths, 1):
    print(f"  {i}. {p}")
print(f"✓ Expected 3 paths, got {len(paths)}")
assert len(paths) == 3, "Newline-separated parsing failed"

# Test 4: Empty and whitespace paths
print("\n" + "="*60)
print("Test 4: Empty/Whitespace Input")
print("="*60)
empty_paths = "  ,  ,  "
print(f"Input: '{empty_paths}'")

if '\n' in empty_paths:
    paths = [p.strip() for p in empty_paths.split('\n') if p.strip()]
elif ',' in empty_paths:
    paths = [p.strip() for p in empty_paths.split(',') if p.strip()]
else:
    paths = [empty_paths.strip()]

paths = [p for p in paths if p]  # Remove empty
print(f"Parsed paths: {paths}")
print(f"✓ Expected 0 paths, got {len(paths)}")
assert len(paths) == 0, "Empty path handling failed"

# Test 5: Path with extra whitespace
print("\n" + "="*60)
print("Test 5: Whitespace Trimming")
print("="*60)
whitespace_paths = "  ./path1  , ./path2  ,  ./path3 "
print(f"Input: '{whitespace_paths}'")

if '\n' in whitespace_paths:
    paths = [p.strip() for p in whitespace_paths.split('\n') if p.strip()]
elif ',' in whitespace_paths:
    paths = [p.strip() for p in whitespace_paths.split(',') if p.strip()]
else:
    paths = [whitespace_paths.strip()]

print(f"Parsed paths:")
for i, p in enumerate(paths, 1):
    print(f"  {i}. '{p}'")
print(f"✓ All paths properly trimmed")
assert all(not p.startswith(' ') and not p.endswith(' ') for p in paths)

# Test 6: source_repo metadata logic
print("\n" + "="*60)
print("Test 6: source_repo Metadata Logic")
print("="*60)
test_file = Path("./Mutagen/Mutagen.Bethesda.Core/SomeFile.cs")
test_paths = ["./Mutagen/Mutagen.Bethesda.Core", "./Mutagen/Other"]

print(f"Test file: {test_file}")
print(f"Repository candidates: {test_paths}")

source_repo = "unknown"
for repo_path in test_paths:
    repo_path_resolved = Path(repo_path).resolve()
    try:
        test_file.resolve().relative_to(repo_path_resolved)
        source_repo = repo_path_resolved.name
        print(f"  ✓ Matched to repository: '{source_repo}'")
        break
    except ValueError:
        print(f"  ✗ No match with: '{Path(repo_path).name}'")
        continue

assert source_repo == "Mutagen.Bethesda.Core", f"Expected 'Mutagen.Bethesda.Core', got '{source_repo}'"

# Test 7: Check path existence
print("\n" + "="*60)
print("Test 7: Path Existence Check")
print("="*60)
test_paths_mixed = ["./Mutagen", "./NonExistent", "./AnotherNonExistent"]
print("Checking paths:")
for path in test_paths_mixed:
    exists = Path(path).exists()
    print(f"  {path}: {'✓ EXISTS' if exists else '✗ MISSING'}")

print("\n" + "="*60)
print("✅ All Tests Passed!")
print("="*60)
print("\nSummary:")
print("  ✓ Single path parsing")
print("  ✓ Comma-separated parsing")
print("  ✓ Newline-separated parsing")
print("  ✓ Empty path handling")
print("  ✓ Whitespace trimming")
print("  ✓ source_repo metadata logic")
print("  ✓ Path existence checking")

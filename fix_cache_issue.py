#!/usr/bin/env python3
"""
🔧 Script to diagnose and fix Python cache issues

This script:
1. Checks which file is being imported
2. Removes cache files (.pyc, __pycache__)
3. Forces a clean module re-import
4. Tests if the new code is working
"""

import os
import sys
import shutil
from pathlib import Path

def print_section(title: str):
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")

def remove_cache_files(project_root: Path):
    """Remove all Python cache files."""
    print("🧹 Removing cache files...")

    cache_removed = 0

    # Remove __pycache__ directories
    for pycache in project_root.rglob("__pycache__"):
        if pycache.is_dir():
            print(f"   Removing: {pycache}")
            shutil.rmtree(pycache)
            cache_removed += 1

    # Remove .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        if pyc_file.is_file():
            print(f"   Removing: {pyc_file}")
            pyc_file.unlink()
            cache_removed += 1

    if cache_removed == 0:
        print("   ✅ No cache files found")
    else:
        print(f"   ✅ {cache_removed} cache file(s) removed")

def verify_code_version(project_root: Path):
    """Check if the current code has the correct implementation."""
    print("🔍 Checking code version...")

    faq_file = project_root / "simple_faq_rag.py"

    with open(faq_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for new code (iloc)
    has_new_code = "df.iloc[:, 0]" in content and "df.iloc[:, 1]" in content

    # Ensure the old mapping code is not present
    has_old_code = "column_mapping = {}" in content or "'Questions': 'question'" in content

    print(f"   New code (iloc): {'✅ Present' if has_new_code else '❌ MISSING'}")
    print(f"   Old code (mapping): {'❌ PRESENT' if has_old_code else '✅ Absent'}")

    if has_new_code and not has_old_code:
        print("\n   ✅ File has the CORRECT version of the code!")
        return True
    else:
        print("\n   ❌ PROBLEM: File does not have the expected version!")
        return False

def clear_module_from_memory():
    """Remove module from Python memory."""
    print("🧠 Clearing module from memory...")

    if 'simple_faq_rag' in sys.modules:
        del sys.modules['simple_faq_rag']
        print("   ✅ Module removed from memory")
    else:
        print("   ✅ Module was not in memory")

def test_import(project_root: Path):
    """Test importing the module."""
    print("📦 Testing import...")

    # Ensure the project root is on the path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        # Import module
        from simple_faq_rag import SimpleFAQSystem

        # Check which file was imported
        import simple_faq_rag
        imported_file = simple_faq_rag.__file__
        print(f"   ✅ Module imported from: {imported_file}")

        # Validate import path
        expected_file = str(project_root / "simple_faq_rag.py")
        if os.path.abspath(imported_file) == os.path.abspath(expected_file):
            print("   ✅ Correct file is being imported!")
            return True
        else:
            print("   ❌ PROBLEM: Importing the wrong file!")
            print(f"      Expected: {expected_file}")
            print(f"      Actual: {imported_file}")
            return False

    except Exception as e:
        print(f"   ❌ Error importing: {e}")
        return False

def test_load_csv(project_root: Path):
    """Test if load_csv is using the new code."""
    print("🧪 Testing load_csv function...")

    try:
        # Check if example CSV exists
        csv_path = project_root / "data" / "faq_example.csv"
        if not csv_path.exists():
            print(f"   ⚠️  Test CSV not found: {csv_path}")
            print("   Skipping functional test...")
            return None

        # Import and test
        from dotenv import load_dotenv
        load_dotenv()

        from simple_faq_rag import SimpleFAQSystem

        project_id = os.getenv('PROJECT_ID')
        if not project_id:
            print("   ⚠️  PROJECT_ID not configured in .env")
            print("   Skipping functional test...")
            return None

        # Create system and test
        print("   Initializing system...")
        faq = SimpleFAQSystem(project_id=project_id)

        print(f"   Loading CSV: {csv_path}")
        faq.load_csv(str(csv_path))

        print("   ✅ CSV loaded successfully!")
        print(f"   ✅ {len(faq.df)} questions processed")

        # Validate standardized columns
        if 'question' in faq.df.columns and 'answer' in faq.df.columns:
            print("   ✅ Columns standardized correctly!")
            return True
        else:
            print(f"   ❌ PROBLEM: Unexpected columns: {list(faq.df.columns)}")
            return False

    except Exception as e:
        print(f"   ❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""

    print_section("🔧 PYTHON CACHE DIAGNOSIS AND FIX")

    # Determine project directory
    project_root = Path(__file__).parent
    print(f"📁 Project directory: {project_root}\n")

    # STEP 1: Remove cache
    print_section("STEP 1: Clearing Cache")
    remove_cache_files(project_root)

    # STEP 2: Verify code in file
    print_section("STEP 2: Verifying Code in File")
    code_ok = verify_code_version(project_root)

    if not code_ok:
        print("\n⚠️  WARNING: The file does not have the expected code version!")
        print("   Run: git pull origin claude/simple-faq-rag-34uUC")
        return

    # STEP 3: Clear memory
    print_section("STEP 3: Clearing Python Memory")
    clear_module_from_memory()

    # STEP 4: Test import
    print_section("STEP 4: Testing Import")
    import_ok = test_import(project_root)

    if not import_ok:
        print("\n⚠️  PROBLEM: Module is not being imported correctly!")
        return

    # STEP 5: Functional test
    print_section("STEP 5: Functional Test")
    test_ok = test_load_csv(project_root)

    # SUMMARY
    print_section("📊 SUMMARY")

    if code_ok and import_ok and test_ok:
        print("✅ EVERYTHING OK! The system is working correctly!")
        print("\n🎯 Next steps:")
        print("   python simple_scripts/03_use_bucket.py")
    elif test_ok is None:
        print("⚠️  Code and import OK, but functional test was skipped")
        print("   (missing .env or example CSV)")
        print("\n🎯 Try running:")
        print("   python simple_scripts/03_use_bucket.py")
    else:
        print("❌ There are still problems. See details above.")
        print("\n💡 Suggestions:")
        print("   1. Restart the terminal completely")
        print("   2. Run: git pull")
        print("   3. Run this script again")

if __name__ == "__main__":
    main()

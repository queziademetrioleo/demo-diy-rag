#!/usr/bin/env python3
"""
Script 00: Setup Validation
Checks if everything is configured correctly BEFORE running.
Always run this before the other scripts.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv


def validate_env():
    """Validate environment variables."""
    load_dotenv()

    required_vars = {
        "PROJECT_ID": "Google Cloud project ID",
        "BUCKET_NAME": "Cloud Storage bucket name",
        "LOCATION": "Google Cloud region"
    }

    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  - {var}: {description}")
        else:
            print(f"  ✓ {var}: {value}")

    if missing:
        print("\n❌ Missing variables in .env:")
        for m in missing:
            print(m)
        print("\n📝 How to fix:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("\n2. Edit .env and fill the variables:")
        print("   nano .env")
        return False

    return True


def validate_gcloud_auth():
    """Validate gcloud authentication."""
    import subprocess

    try:
        result = subprocess.run(
            ["gcloud", "auth", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and "ACTIVE" in result.stdout:
            # Extract active email
            for line in result.stdout.split('\n'):
                if '*' in line or 'ACTIVE' in line:
                    print("  ✓ Authenticated")
                    break
            return True
        else:
            print("  ✗ Not authenticated")
            print("\n📝 How to fix:")
            print("  gcloud auth login")
            print("  gcloud auth application-default login")
            return False

    except FileNotFoundError:
        print("  ✗ gcloud CLI not found")
        print("\n📝 Install gcloud CLI:")
        print("  https://cloud.google.com/sdk/docs/install")
        return False
    except Exception as e:
        print(f"  ⚠️  Error checking auth: {e}")
        return False


def validate_project_access():
    """Validate project access."""
    import subprocess
    from dotenv import load_dotenv

    load_dotenv()
    project_id = os.getenv("PROJECT_ID")

    if not project_id:
        print("  ⚠️  PROJECT_ID not defined, skipping validation")
        return True

    try:
        result = subprocess.run(
            ["gcloud", "config", "set", "project", project_id],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"  ✓ Access to project: {project_id}")
            return True
        else:
            print(f"  ✗ No access to project: {project_id}")
            print("\n📝 Make sure the project exists and you have permission")
            return False

    except Exception as e:
        print(f"  ⚠️  Error checking project: {e}")
        return True


def validate_apis_enabled():
    """Validate that required APIs are enabled."""
    import subprocess
    from dotenv import load_dotenv

    load_dotenv()
    project_id = os.getenv("PROJECT_ID")

    if not project_id:
        print("  ⚠️  PROJECT_ID not defined, skipping validation")
        return True

    required_apis = [
        "aiplatform.googleapis.com",
        "storage-api.googleapis.com"
    ]

    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--enabled", f"--project={project_id}"],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            print("  ⚠️  Could not verify APIs")
            return True

        missing_apis = []
        for api in required_apis:
            if api in result.stdout:
                print(f"  ✓ {api}")
            else:
                print(f"  ✗ {api}")
                missing_apis.append(api)

        if missing_apis:
            print("\n📝 Enable missing APIs:")
            print(f"  gcloud services enable {' '.join(missing_apis)} --project={project_id}")
            return False

        return True

    except Exception as e:
        print(f"  ⚠️  Error checking APIs: {e}")
        return True


def validate_python_packages():
    """Validate that Python packages are installed."""
    required_packages = {
        "google-cloud-aiplatform": "google.cloud.aiplatform",
        "google-cloud-storage": "google.cloud.storage",
        "pandas": "pandas",
        "numpy": "numpy",
        "loguru": "loguru",
        "python-dotenv": "dotenv",
        "streamlit": "streamlit",
        "tqdm": "tqdm"
    }

    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name}")
            missing.append(package_name)

    if missing:
        print("\n📝 Install missing packages:")
        print("  pip install -r requirements.txt")
        return False

    return True


def validate_file_structure():
    """Validate file structure."""
    required_files = [
        "README.md",
        "requirements.txt",
        ".env.example",
        "src/data_loader.py",
        "src/embeddings.py",
        "src/vector_search.py",
        "src/rag_system.py",
        "scripts/01_download_data.py",
        "scripts/02_create_embeddings.py",
        "scripts/03_setup_vector_search.py",
        "scripts/05_test_api.py",
        "app.py"
    ]

    project_root = Path(__file__).parent.parent
    missing = []

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path}")
            missing.append(file_path)

    if missing:
        print("\n⚠️  Some files are missing!")
        print("Make sure the repository is complete.")
        return False

    return True


def main():
    """Run all validations."""
    print("="*70)
    print("🔍 SETUP VALIDATION - Demo DIY RAG")
    print("="*70)
    print("\nThis script checks if everything is configured correctly.")
    print("Run this BEFORE running the other scripts!\n")

    checks = [
        ("📁 File Structure", validate_file_structure),
        ("🔧 Environment Variables (.env)", validate_env),
        ("📦 Python Packages", validate_python_packages),
        ("🔐 gcloud Authentication", validate_gcloud_auth),
        ("🎯 Project Access", validate_project_access),
        ("🌐 Google Cloud APIs", validate_apis_enabled),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{name}")
        print("-" * 70)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            results.append(False)

    print("\n" + "="*70)

    if all(results):
        print("✅ ALL VALIDATIONS PASSED!")
        print("="*70)
        print("\n🎉 Everything is configured correctly!")
        print("\n📋 Next steps:")
        print("  1. python scripts/01_download_data.py")
        print("  2. python scripts/02_create_embeddings.py")
        print("  3. python scripts/03_setup_vector_search.py  (30-45 min)")
        print("  4. python scripts/05_test_api.py")
        print("  5. streamlit run app.py")
        print("\n💡 Tip: Read CRITICAL_FIXES.md for important details!")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("="*70)
        print("\n⚠️  Fix the issues above before continuing.")
        print("\n📖 For detailed help, see:")
        print("  - CRITICAL_FIXES.md")
        print("  - docs/TROUBLESHOOTING.md")
        print("  - README.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
🪣 Script to use the FAQ system with Google Cloud Storage

This script:
1. Downloads the CSV from Cloud Storage
2. Creates the knowledge base (embeddings)
3. Uploads the knowledge base to the bucket
4. Tests the system with example questions
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage
import tempfile

# Add project path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from simple_faq_rag import SimpleFAQSystem


def print_section(title: str):
    """Print a formatted section."""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")


def download_csv_from_bucket(bucket_name: str, csv_path: str) -> str:
    """
    Download CSV from Cloud Storage to a temp file.

    Args:
        bucket_name: Bucket name
        csv_path: CSV path in bucket (e.g., raw_data/faq.csv)

    Returns:
        Local temp file path
    """
    print("📥 Downloading CSV from the bucket...")

    try:
        # Initialize client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Create blob
        blob = bucket.blob(csv_path)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.csv',
            delete=False
        )

        # Download
        blob.download_to_filename(temp_file.name)

        # Get original file name
        filename = os.path.basename(csv_path)

        print(f"✅ CSV downloaded: {filename}")
        print(f"   Local: {temp_file.name}")

        return temp_file.name

    except Exception as e:
        print(f"\n❌ Error downloading CSV: {e}")
        print("\n💡 Tips:")
        print("   - Make sure the file exists in the bucket")
        print(f"   - Expected path: gs://{bucket_name}/{csv_path}")
        print(f"   - Run: gsutil ls gs://{bucket_name}/raw_data/")
        sys.exit(1)


def upload_knowledge_base_to_bucket(
    bucket_name: str,
    embeddings_path: str,
    metadata_path: str
):
    """
    Upload the knowledge base to the bucket.

    Args:
        bucket_name: Bucket name
        embeddings_path: Local path to embeddings (.npy)
        metadata_path: Local path to metadata (.csv)
    """
    print("\n📤 Uploading knowledge base...")

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Upload embeddings
        embeddings_blob = bucket.blob("embeddings/faq_embeddings.npy")
        embeddings_blob.upload_from_filename(embeddings_path)
        print("   ✅ Embeddings uploaded")

        # Upload metadata
        metadata_blob = bucket.blob("knowledge_base/faq_metadata.csv")
        metadata_blob.upload_from_filename(metadata_path)
        print("   ✅ Metadata uploaded")

        print("\n✅ Knowledge base saved in the bucket!")
        print(f"   - gs://{bucket_name}/embeddings/faq_embeddings.npy")
        print(f"   - gs://{bucket_name}/knowledge_base/faq_metadata.csv")

    except Exception as e:
        print(f"\n❌ Error uploading: {e}")
        sys.exit(1)


def main():
    """Main entry point."""

    # Load environment variables
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    bucket_name = os.getenv("BUCKET_NAME")
    raw_data_path = os.getenv("RAW_DATA_PATH")

    # Validate configuration
    if not all([project_id, bucket_name, raw_data_path]):
        print("❌ Error: .env file is not configured!")
        print("\n💡 Create .env with:")
        print("   PROJECT_ID=your-project")
        print("   BUCKET_NAME=your-bucket")
        print("   RAW_DATA_PATH=raw_data/your_file.csv")
        sys.exit(1)

    print_section("🪣 FAQ SYSTEM WITH GOOGLE CLOUD STORAGE")

    print(f"✅ Project: {project_id}")
    print(f"✅ Bucket: gs://{bucket_name}")

    # STEP 1: Download CSV
    print_section("STEP 1: Downloading data from Cloud Storage")

    csv_file = download_csv_from_bucket(bucket_name, raw_data_path)

    # STEP 2: Initialize system
    print_section("STEP 2: Initializing FAQ System")

    try:
        faq = SimpleFAQSystem(
            project_id=project_id,
            location=location
        )
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        print("\n💡 Make sure Vertex AI API is enabled:")
        print(f"   gcloud services enable aiplatform.googleapis.com --project={project_id}")
        sys.exit(1)

    # STEP 3: Load CSV
    print_section("STEP 3: Loading Questions and Answers")

    try:
        faq.load_csv(csv_file)
        print(f"\n📊 Total questions: {len(faq.df)}")
        print("\n📝 First 5 questions:")
        for i, row in faq.df.head(5).iterrows():
            print(f"   {i+1}. {row['question'][:60]}...")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        print("\n💡 Tips:")
        print("   - CSV must have at least 2 columns")
        print("   - Column 1: Questions (any name)")
        print("   - Column 2: Answers (any name)")
        sys.exit(1)

    # STEP 4: Create knowledge base
    print_section("STEP 4: Creating Knowledge Base (Embeddings)")

    print("⏳ This may take a few minutes depending on CSV size...")

    try:
        faq.create_knowledge_base()
    except Exception as e:
        print(f"❌ Error creating knowledge base: {e}")
        sys.exit(1)

    # STEP 5: Save base locally
    print_section("STEP 5: Saving Knowledge Base")

    import numpy as np

    # Create temporary directory
    temp_dir = Path(tempfile.gettempdir()) / "faq_knowledge_base"
    temp_dir.mkdir(exist_ok=True)

    # Save embeddings
    embeddings_file = temp_dir / "faq_embeddings.npy"
    np.save(embeddings_file, faq.embeddings)
    print(f"✅ Embeddings saved: {embeddings_file}")

    # Save metadata
    metadata_file = temp_dir / "faq_metadata.csv"
    faq.df.to_csv(metadata_file, index=False)
    print(f"✅ Metadata saved: {metadata_file}")

    # STEP 6: Upload to bucket
    print_section("STEP 6: Uploading to Cloud Storage")

    upload_knowledge_base_to_bucket(
        bucket_name,
        str(embeddings_file),
        str(metadata_file)
    )

    # STEP 7: Test system
    print_section("STEP 7: Testing System")

    # Use first 3 questions for testing
    test_queries = faq.df['question'].head(3).tolist()

    print("🧪 Running 3 test questions:\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─'*70}")
        print(f"Test {i}: {query}")
        print('─'*70)

        try:
            result = faq.ask(query)

            if result['found']:
                print(f"✅ Answer found (score: {result['score']:.2f}):")
                print(f"\n{result['answer']}\n")
            else:
                print("❌ No answer found")

        except Exception as e:
            print(f"❌ Error: {e}")

    # FINAL
    print_section("✅ PROCESS COMPLETED SUCCESSFULLY!")

    print("📊 Summary:")
    print(f"   • {len(faq.df)} questions processed")
    print("   • Knowledge base created")
    print(f"   • Files saved in bucket: gs://{bucket_name}/")

    print("\n🎯 Next steps:")
    print("   1. Test more questions:")
    print("      python simple_scripts/01_test_system.py")
    print("\n   2. Open web interface:")
    print("      python simple_gradio_app.py")

    print("\n💡 The knowledge base is saved in the bucket!")
    print("   You do NOT need to reprocess every time.")
    print("   To use it, just load the files from the bucket.")

    # Clean up temp file
    os.unlink(csv_file)

    print("\n" + "="*70)
    print("🎉 ALL DONE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

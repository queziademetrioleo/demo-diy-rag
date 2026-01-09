#!/usr/bin/env python3
"""
Script 01: Download and process data
Downloads the Flipkart dataset and prepares it for RAG.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from loguru import logger
from data_loader import DataLoader

def main():
    # Load environment variables
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    bucket_name = os.getenv("BUCKET_NAME")

    if not project_id or not bucket_name:
        logger.error("PROJECT_ID and BUCKET_NAME must be defined in .env")
        sys.exit(1)

    logger.info("="*60)
    logger.info("SCRIPT 01: Download and Process Data")
    logger.info("="*60)

    # Initialize loader
    loader = DataLoader(
        project_id=project_id,
        bucket_name=bucket_name
    )

    # Option 1: Download from Kaggle (requires credentials)
    try:
        logger.info("\nTrying to download dataset from Kaggle...")
        file_path = loader.download_kaggle_dataset()
        df_raw = loader.load_csv(file_path)

    except Exception as e:
        logger.warning(f"Could not download from Kaggle: {e}")
        logger.info("Using sample dataset...")

        # Option 2: Use sample data
        df_raw = loader.get_sample_data(n=1000)

    # Process data
    logger.info("\nProcessing data...")
    df_processed = loader.process_products(df_raw)

    # Upload to GCS
    logger.info("\nUploading to Cloud Storage...")
    gcs_uri = loader.upload_to_gcs(df_processed)

    # Final stats
    logger.info("\n" + "="*60)
    logger.info("✅ DOWNLOAD AND PROCESSING COMPLETE!")
    logger.info("="*60)
    logger.info(f"Total products: {len(df_processed)}")
    logger.info(f"Data saved to: {gcs_uri}")
    logger.info("\nNext step: Run scripts/02_create_embeddings.py")
    logger.info("="*60)

if __name__ == "__main__":
    main()

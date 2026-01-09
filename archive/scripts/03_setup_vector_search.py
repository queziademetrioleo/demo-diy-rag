#!/usr/bin/env python3
"""
Script 03: Vector Search setup
Creates index and endpoint, then deploys.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from loguru import logger
from vector_search import VectorSearchManager

def main():
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    bucket_name = os.getenv("BUCKET_NAME")
    location = os.getenv("LOCATION", "us-central1")
    index_name = os.getenv("VECTOR_SEARCH_INDEX_NAME", "products-index")
    endpoint_name = os.getenv("VECTOR_SEARCH_ENDPOINT_NAME", "products-endpoint")
    dimensions = int(os.getenv("VECTOR_DIMENSIONS", "768"))

    embeddings_uri = f"gs://{bucket_name}/embeddings/vector_search_data.jsonl"

    logger.info("="*60)
    logger.info("SCRIPT 03: Vector Search Setup")
    logger.info("="*60)

    # Initialize manager
    manager = VectorSearchManager(
        project_id=project_id,
        location=location,
        index_display_name=index_name,
        endpoint_display_name=endpoint_name
    )

    # Create index
    logger.info("\nCreating index...")
    index = manager.get_or_create_index(
        embeddings_gcs_uri=embeddings_uri,
        dimensions=dimensions
    )

    # Create endpoint
    logger.info("\nCreating endpoint...")
    endpoint = manager.get_or_create_endpoint()

    # Deploy
    logger.info("\nDeploying (WARNING: may take 30-45 minutes)...")
    manager.deploy_index(
        index=index,
        endpoint=endpoint,
        machine_type="e2-standard-2"
    )

    logger.info("\n" + "="*60)
    logger.info("✅ VECTOR SEARCH CONFIGURED!")
    logger.info("="*60)
    logger.info(f"Index: {index.resource_name}")
    logger.info(f"Endpoint: {endpoint.resource_name}")
    logger.info("\n⏰ Deployment in progress - wait 30-45 minutes")
    logger.info("Track at: https://console.cloud.google.com/vertex-ai/matching-engine")
    logger.info("\nNext step (after deploy): Run scripts/05_test_api.py")
    logger.info("="*60)

if __name__ == "__main__":
    main()

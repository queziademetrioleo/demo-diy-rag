#!/usr/bin/env python3
"""
Script 03: Setup do Vector Search
Cria índice e endpoint, faz deploy.
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
    index_name = os.getenv("VECTOR_SEARCH_INDEX_NAME", "produtos-index")
    endpoint_name = os.getenv("VECTOR_SEARCH_ENDPOINT_NAME", "produtos-endpoint")
    dimensions = int(os.getenv("VECTOR_DIMENSIONS", "768"))

    embeddings_uri = f"gs://{bucket_name}/embeddings/vector_search_data.jsonl"

    logger.info("="*60)
    logger.info("SCRIPT 03: Setup Vector Search")
    logger.info("="*60)

    # Inicializar manager
    manager = VectorSearchManager(
        project_id=project_id,
        location=location,
        index_display_name=index_name,
        endpoint_display_name=endpoint_name
    )

    # Criar índice
    logger.info("\nCriando índice...")
    index = manager.get_or_create_index(
        embeddings_gcs_uri=embeddings_uri,
        dimensions=dimensions
    )

    # Criar endpoint
    logger.info("\nCriando endpoint...")
    endpoint = manager.get_or_create_endpoint()

    # Deploy
    logger.info("\nFazendo deploy (ATENÇÃO: pode levar 30-45 minutos!)...")
    manager.deploy_index(
        index=index,
        endpoint=endpoint,
        machine_type="e2-standard-2"
    )

    logger.info("\n" + "="*60)
    logger.info("✅ VECTOR SEARCH CONFIGURADO!")
    logger.info("="*60)
    logger.info(f"Índice: {index.resource_name}")
    logger.info(f"Endpoint: {endpoint.resource_name}")
    logger.info(f"\n⏰ Deploy em andamento - aguarde 30-45 minutos")
    logger.info(f"Acompanhe em: https://console.cloud.google.com/vertex-ai/matching-engine")
    logger.info(f"\nPróximo passo (após deploy): Execute scripts/05_test_api.py")
    logger.info("="*60)

if __name__ == "__main__":
    main()

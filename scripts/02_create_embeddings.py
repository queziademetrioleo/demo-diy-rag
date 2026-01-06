#!/usr/bin/env python3
"""
Script 02: Criação de embeddings
Gera embeddings usando Vertex AI para todos os produtos.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from loguru import logger
from data_loader import DataLoader
from embeddings import EmbeddingGenerator

def main():
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    bucket_name = os.getenv("BUCKET_NAME")
    location = os.getenv("LOCATION", "us-central1")
    data_path = os.getenv("RAW_DATA_PATH", "raw_data/flipkart_products.csv")
    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

    logger.info("="*60)
    logger.info("SCRIPT 02: Criação de Embeddings")
    logger.info("="*60)

    # Carregar dados
    logger.info("\nCarregando dados do GCS...")
    loader = DataLoader(project_id=project_id, bucket_name=bucket_name)
    df = loader.download_from_gcs(data_path)

    # Inicializar gerador
    logger.info(f"\nInicializando {model_name}...")
    generator = EmbeddingGenerator(
        project_id=project_id,
        location=location,
        model_name=model_name
    )

    # Criar embeddings
    logger.info("\nGerando embeddings (isso pode demorar)...")
    embeddings, metadata = generator.create_embeddings_dataset(df)

    # Salvar
    logger.info("\nSalvando embeddings...")
    uris = generator.save_embeddings_to_gcs(
        embeddings=embeddings,
        metadata=metadata,
        bucket_name=bucket_name
    )

    vector_search_uri = generator.save_for_vector_search(
        embeddings=embeddings,
        metadata=metadata,
        bucket_name=bucket_name
    )

    logger.info("\n" + "="*60)
    logger.info("✅ EMBEDDINGS CRIADOS COM SUCESSO!")
    logger.info("="*60)
    logger.info(f"Total: {len(embeddings)} embeddings")
    logger.info(f"Dimensão: {embeddings.shape[1]}")
    logger.info(f"\nArquivos salvos:")
    logger.info(f"  - {uris['embeddings_uri']}")
    logger.info(f"  - {uris['metadata_uri']}")
    logger.info(f"  - {vector_search_uri}")
    logger.info(f"\nPróximo passo: Execute scripts/03_setup_vector_search.py")
    logger.info("="*60)

if __name__ == "__main__":
    main()

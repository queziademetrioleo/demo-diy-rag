#!/usr/bin/env python3
"""
Script 01: Download e processamento de dados
Faz download do dataset Flipkart e processa para uso no RAG.
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from loguru import logger
from data_loader import DataLoader

def main():
    # Carregar variáveis de ambiente
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    bucket_name = os.getenv("BUCKET_NAME")

    if not project_id or not bucket_name:
        logger.error("PROJECT_ID e BUCKET_NAME devem estar definidos no .env")
        sys.exit(1)

    logger.info("="*60)
    logger.info("SCRIPT 01: Download e Processamento de Dados")
    logger.info("="*60)

    # Inicializar loader
    loader = DataLoader(
        project_id=project_id,
        bucket_name=bucket_name
    )

    # Opção 1: Tentar baixar do Kaggle (requer credenciais)
    try:
        logger.info("\nTentando baixar dataset do Kaggle...")
        file_path = loader.download_kaggle_dataset()
        df_raw = loader.load_csv(file_path)

    except Exception as e:
        logger.warning(f"Não foi possível baixar do Kaggle: {e}")
        logger.info("Usando dataset de exemplo...")

        # Opção 2: Usar dados de exemplo
        df_raw = loader.get_sample_data(n=1000)

    # Processar dados
    logger.info("\nProcessando dados...")
    df_processed = loader.process_products(df_raw)

    # Upload para GCS
    logger.info("\nFazendo upload para Cloud Storage...")
    gcs_uri = loader.upload_to_gcs(df_processed)

    # Estatísticas finais
    logger.info("\n" + "="*60)
    logger.info("✅ DOWNLOAD E PROCESSAMENTO CONCLUÍDOS!")
    logger.info("="*60)
    logger.info(f"Total de produtos: {len(df_processed)}")
    logger.info(f"Dados salvos em: {gcs_uri}")
    logger.info(f"\nPróximo passo: Execute scripts/02_create_embeddings.py")
    logger.info("="*60)

if __name__ == "__main__":
    main()

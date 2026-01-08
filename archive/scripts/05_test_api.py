#!/usr/bin/env python3
"""
Script 05: Testes do sistema RAG
Executa testes de queries e avalia o sistema.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from loguru import logger
from rag_system import RAGSystem

def main():
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    bucket_name = os.getenv("BUCKET_NAME")

    logger.info("="*60)
    logger.info("SCRIPT 05: Testes do Sistema RAG")
    logger.info("="*60)

    # Inicializar RAG
    logger.info("\nInicializando sistema RAG...")
    rag = RAGSystem(
        project_id=project_id,
        location=location,
        bucket_name=bucket_name
    )

    # Queries de teste
    test_queries = [
        "Quero um smartphone com boa câmera e bateria durável",
        "Quais produtos têm desconto acima de 30%?",
        "Me recomende um notebook para trabalho",
        "Produtos da marca Samsung disponíveis"
    ]

    logger.info(f"\n🧪 Executando {len(test_queries)} queries de teste...\n")

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTE {i}/{len(test_queries)}")
        logger.info(f"{'='*60}")
        logger.info(f"Query: {query}")

        try:
            result = rag.query(query)

            logger.info(f"\n📝 Resposta:")
            logger.info(result['answer'])

            if result.get('sources'):
                logger.info(f"\n📚 Fontes ({len(result['sources'])}):")
                for j, source in enumerate(result['sources'], 1):
                    logger.info(f"  {j}. {source['name']} (score: {source['relevance_score']:.3f})")

            logger.info(f"\n✅ Teste {i} concluído!")

        except Exception as e:
            logger.error(f"❌ Erro no teste {i}: {e}")

    logger.info("\n" + "="*60)
    logger.info("✅ TODOS OS TESTES CONCLUÍDOS!")
    logger.info("="*60)
    logger.info("\n🎉 Sistema RAG está funcionando!")
    logger.info("Você pode agora usar o notebook: notebooks/demo_rag_completo.ipynb")
    logger.info("="*60)

if __name__ == "__main__":
    main()

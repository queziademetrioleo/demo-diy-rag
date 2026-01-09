#!/usr/bin/env python3
"""
Script 05: RAG system tests
Runs query tests and evaluates the system.
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
    logger.info("SCRIPT 05: RAG System Tests")
    logger.info("="*60)

    # Initialize RAG
    logger.info("\nInitializing RAG system...")
    rag = RAGSystem(
        project_id=project_id,
        location=location,
        bucket_name=bucket_name
    )

    # Test queries
    test_queries = [
        "I want a smartphone with a good camera and long battery",
        "Which products have discounts above 30%?",
        "Recommend a laptop for work",
        "Samsung brand products available"
    ]

    logger.info(f"\n🧪 Running {len(test_queries)} test queries...\n")

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST {i}/{len(test_queries)}")
        logger.info(f"{'='*60}")
        logger.info(f"Query: {query}")

        try:
            result = rag.query(query)

            logger.info("\n📝 Answer:")
            logger.info(result['answer'])

            if result.get('sources'):
                logger.info(f"\n📚 Sources ({len(result['sources'])}):")
                for j, source in enumerate(result['sources'], 1):
                    logger.info(f"  {j}. {source['name']} (score: {source['relevance_score']:.3f})")

            logger.info(f"\n✅ Test {i} completed!")

        except Exception as e:
            logger.error(f"❌ Error in test {i}: {e}")

    logger.info("\n" + "="*60)
    logger.info("✅ ALL TESTS COMPLETED!")
    logger.info("="*60)
    logger.info("\n🎉 RAG system is working!")
    logger.info("You can now use the notebook: notebooks/demo_rag_completo.ipynb")
    logger.info("="*60)

if __name__ == "__main__":
    main()

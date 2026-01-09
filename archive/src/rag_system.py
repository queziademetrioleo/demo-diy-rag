"""
Full RAG (Retrieval Augmented Generation) system.

This module integrates:
- Retrieval
- LLM generation
- Answer evaluation
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
from google.cloud import aiplatform
from loguru import logger
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, HarmCategory, HarmBlockThreshold

from embeddings import EmbeddingGenerator


@dataclass
class RAGConfig:
    """RAG system configuration."""
    top_k: int = 5
    similarity_threshold: float = 0.6
    max_tokens: int = 512
    temperature: float = 0.2


class RAGSystem:
    """
    Full RAG system for retrieval and answer generation.
    """

    def __init__(
        self,
        project_id: str,
        location: str,
        bucket_name: str,
        config: Optional[RAGConfig] = None,
        deployed_index_id: Optional[str] = None,
        endpoint_name: Optional[str] = None
    ):
        """
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            bucket_name: Cloud Storage bucket name
            config: RAG configuration
            deployed_index_id: Deployed index ID
            endpoint_name: Endpoint display name
        """
        self.project_id = project_id
        self.location = location
        self.bucket_name = bucket_name
        self.config = config or RAGConfig()
        self.deployed_index_id = deployed_index_id
        self.endpoint_name = endpoint_name

        vertexai.init(project=project_id, location=location)
        aiplatform.init(project=project_id, location=location)

        # Embedding generator
        self.embedding_generator = EmbeddingGenerator(project_id=project_id, location=location)

        # LLM configuration
        self.llm = GenerativeModel("gemini-2.5-flash")
        self.generation_config = GenerationConfig(
            max_output_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )

        # Load metadata (if available)
        self.metadata = None
        self._load_metadata()

    def _load_metadata(self):
        """Load metadata from GCS if available."""
        try:
            embeddings, metadata = self.embedding_generator.load_embeddings_from_gcs(
                self.bucket_name,
                prefix="embeddings"
            )
            self.metadata = metadata
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Retrieve top-k relevant documents.

        Args:
            query: User query
            top_k: Number of results

        Returns:
            List of document dicts
        """
        if top_k is None:
            top_k = self.config.top_k

        if self.metadata is None:
            logger.warning("Metadata not available")
            return []

        query_embedding = self.embedding_generator.generate_query_embedding(query)

        # Compute similarity
        embeddings, _ = self.embedding_generator.load_embeddings_from_gcs(
            self.bucket_name,
            prefix="embeddings"
        )

        similarities = np.dot(embeddings, query_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top-k
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < self.config.similarity_threshold:
                continue

            result = self.metadata.iloc[idx].to_dict()
            result['relevance_score'] = score
            results.append(result)

        logger.info(f"Retrieval completed: {len(results)}/{len(top_indices)} results")
        return results

    def _build_prompt(self, query: str, documents: List[Dict]) -> str:
        """
        Build prompt for LLM.

        Args:
            query: User query
            documents: Retrieved documents

        Returns:
            Prompt string
        """
        prompt = """You are an assistant specialized in e-commerce products.
Your job is to answer questions about the catalog.

Rules:
1. Use ONLY the information in the products below
2. If the answer is not in the products, say "I couldn't find that information"
3. If there are prices, mention them in USD

AVAILABLE PRODUCTS:
"""

        for i, doc in enumerate(documents, 1):
            prompt += f"\n[Product {i}]\n"
            prompt += f"- Name: {doc.get('name', '')}\n"
            prompt += f"- Category: {doc.get('category', '')}\n"
            prompt += f"- Brand: {doc.get('brand', '')}\n"
            prompt += f"- Price: ${doc.get('discounted_price', 0):.2f}\n"
            prompt += f"- Rating: {doc.get('rating', '')}\n"
            prompt += f"- Description: {doc.get('description', '')[:200]}...\n"

        prompt += f"\nUSER QUESTION: {query}\n"
        prompt += "ANSWER:"

        return prompt

    def generate_answer(self, query: str, documents: List[Dict]) -> str:
        """
        Generate an answer based on retrieved documents.

        Args:
            query: User query
            documents: Retrieved documents

        Returns:
            Generated answer
        """
        prompt = self._build_prompt(query, documents)

        try:
            response = self.llm.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            answer = response.text
            logger.info(f"Generated answer: {len(answer)} characters")
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Sorry, I couldn't generate an answer right now."

    def query(self, query: str, top_k: Optional[int] = None) -> Dict:
        """
        Run a full query: retrieve + generate.

        Args:
            query: User query
            top_k: Number of documents to retrieve

        Returns:
            Dictionary with answer and metadata
        """
        documents = self.retrieve(query, top_k=top_k)

        if not documents:
            return {
                "answer": "Sorry, I couldn't find relevant products for your question.",
                "sources": []
            }

        answer = self.generate_answer(query, documents)

        return {
            "answer": answer,
            "sources": documents
        }

    def batch_query(self, queries: List[str]) -> List[Dict]:
        """
        Process multiple queries in batch.

        Args:
            queries: List of user queries

        Returns:
            List of results
        """
        results = []
        for query in queries:
            results.append(self.query(query))
        return results

    def is_grounded(self, answer: str, documents: List[Dict]) -> bool:
        """
        Check if the answer is grounded in the documents.

        Args:
            answer: Generated answer
            documents: Retrieved documents

        Returns:
            True if grounded, False otherwise
        """
        # Simplified implementation
        important_keywords = ["product", "category", "brand", "price", "rating"]
        return any(keyword in answer.lower() for keyword in important_keywords)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAG system for products")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--bucket-name", required=True, help="Cloud Storage Bucket name")
    parser.add_argument("--location", default="us-central1", help="Google Cloud region")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    args = parser.parse_args()

    rag = RAGSystem(
        project_id=args.project_id,
        location=args.location,
        bucket_name=args.bucket_name
    )

    query = "Looking for a laptop"
    result = rag.query(query)
    logger.info("Answer:")
    logger.info(result['answer'])

"""
Module for generating embeddings using Vertex AI.

This module is responsible for:
- Processing embeddings in batches for efficiency
"""

import json
import tempfile
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
from google.cloud import storage
from loguru import logger
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput


class EmbeddingGenerator:
    """Generates embeddings for text data."""

    def __init__(self, project_id: str, location: str = "us-central1", model_name: str = "text-embedding-004", batch_size: int = 250):
        """
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            model_name: Embedding model name
            batch_size: Batch size (max 250 for text-embedding-004)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.batch_size = batch_size

        vertexai.init(project=project_id, location=location)
        self.model = TextEmbeddingModel.from_pretrained(model_name)

    def get_embedding_dimension(self) -> int:
        """Return embedding dimension for the model."""
        # text-embedding-004 returns 768-dimensional vectors
        return 768

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of input strings

        Returns:
            Embeddings array
        """
        embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            inputs = [TextEmbeddingInput(text=text, task_type="RETRIEVAL_DOCUMENT") for text in batch]
            batch_embeddings = self.model.get_embeddings(inputs)
            batch_vectors = [emb.values for emb in batch_embeddings]
            embeddings.extend(batch_vectors)

            logger.info(f"Processed batch {i//self.batch_size + 1}/{(len(texts)-1)//self.batch_size + 1}")

        return np.array(embeddings, dtype=np.float32)

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.

        Args:
            query: Query string

        Returns:
            Query embedding vector
        """
        try:
            query_input = TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")
            query_emb = self.model.get_embeddings([query_input])[0]
            return np.array(query_emb.values, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    def create_embeddings_dataset(self, df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Create embeddings and metadata from a product DataFrame.

        Args:
            df: DataFrame with product data

        Returns:
            Tuple of embeddings and metadata DataFrame
        """
        if 'embedding_text' not in df.columns:
            df = df.copy()
            df['embedding_text'] = df.apply(
                lambda row: f"{row.get('name', '')} {row.get('description', '')}",
                axis=1
            )

        texts = df['embedding_text'].tolist()
        embeddings = self.generate_embeddings(texts)

        metadata = df[['name', 'category', 'description', 'discounted_price', 'rating', 'brand']].copy()
        metadata['id'] = [f"prod_{i}" for i in range(len(metadata))]

        return embeddings, metadata

    def save_embeddings_to_gcs(
        self,
        embeddings: np.ndarray,
        metadata: pd.DataFrame,
        bucket_name: str,
        output_prefix: str = "embeddings"
    ) -> Dict[str, str]:
        """
        Save embeddings and metadata to GCS.

        Args:
            embeddings: Embeddings array
            metadata: Metadata DataFrame
            bucket_name: Bucket name
            output_prefix: Prefix path in bucket

        Returns:
            Dictionary with GCS URIs
        """
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Save embeddings
        embeddings_file = tempfile.NamedTemporaryFile(delete=False, suffix='.npy')
        np.save(embeddings_file.name, embeddings)

        embeddings_blob = bucket.blob(f"{output_prefix}/embeddings.npy")
        embeddings_blob.upload_from_filename(embeddings_file.name)

        # Save metadata
        metadata_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        metadata.to_csv(metadata_file.name, index=False)

        metadata_blob = bucket.blob(f"{output_prefix}/metadata.csv")
        metadata_blob.upload_from_filename(metadata_file.name)

        # Clean up
        embeddings_file.close()
        metadata_file.close()

        logger.info(f"Saved embeddings and metadata to gs://{bucket_name}/{output_prefix}/")

        return {
            "embeddings_uri": f"gs://{bucket_name}/{output_prefix}/embeddings.npy",
            "metadata_uri": f"gs://{bucket_name}/{output_prefix}/metadata.csv"
        }

    def save_for_vector_search(
        self,
        embeddings: np.ndarray,
        metadata: pd.DataFrame,
        bucket_name: str,
        output_prefix: str = "embeddings"
    ) -> str:
        """
        Save embeddings in Vector Search format (JSONL).

        Args:
            embeddings: Embeddings array
            metadata: Metadata DataFrame
            bucket_name: Bucket name
            output_prefix: Prefix path in bucket

        Returns:
            GCS URI of the JSONL file
        """
        jsonl_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl')

        for i, embedding in enumerate(embeddings):
            record = {
                "id": f"prod_{i}",
                "embedding": embedding.tolist(),
                "metadata": {
                    "name": metadata.iloc[i]['name'],
                    "category": metadata.iloc[i]['category'],
                    "price": metadata.iloc[i].get('discounted_price', None),
                    "rating": metadata.iloc[i].get('rating', None),
                    "brand": metadata.iloc[i].get('brand', None)
                }
            }
            jsonl_file.write((json.dumps(record) + "\n").encode('utf-8'))

        jsonl_file.flush()

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{output_prefix}/vector_search_data.jsonl")
        blob.upload_from_filename(jsonl_file.name)

        jsonl_file.close()

        logger.info(f"Saved Vector Search data to gs://{bucket_name}/{output_prefix}/vector_search_data.jsonl")

        return f"gs://{bucket_name}/{output_prefix}/vector_search_data.jsonl"

    def load_embeddings_from_gcs(self, bucket_name: str, prefix: str = "embeddings") -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Load embeddings and metadata from GCS.

        Args:
            bucket_name: Bucket name
            prefix: Prefix path in bucket

        Returns:
            Tuple of embeddings and metadata DataFrame
        """
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Download embeddings
        embeddings_blob = bucket.blob(f"{prefix}/embeddings.npy")
        embeddings_file = tempfile.NamedTemporaryFile(delete=False, suffix='.npy')
        embeddings_blob.download_to_filename(embeddings_file.name)
        embeddings = np.load(embeddings_file.name)

        # Download metadata
        metadata_blob = bucket.blob(f"{prefix}/metadata.csv")
        metadata_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        metadata_blob.download_to_filename(metadata_file.name)
        metadata = pd.read_csv(metadata_file.name)

        embeddings_file.close()
        metadata_file.close()

        logger.info(f"Loaded embeddings from gs://{bucket_name}/{prefix}/")
        return embeddings, metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embedding generation")
    parser.add_argument("--bucket-name", required=True, help="Cloud Storage Bucket name")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--location", default="us-central1", help="Google Cloud region")
    parser.add_argument("--model-name", default="text-embedding-004", help="Embedding model")
    parser.add_argument("--batch-size", type=int, default=250, help="Batch size")
    args = parser.parse_args()

    generator = EmbeddingGenerator(
        project_id=args.project_id,
        location=args.location,
        model_name=args.model_name,
        batch_size=args.batch_size
    )

    logger.info("Generating sample embeddings...")
    sample_texts = ["Sample product 1", "Sample product 2"]
    embeddings = generator.generate_embeddings(sample_texts)

    logger.info("EMBEDDINGS GENERATED")
    logger.info(f"Dimension: {embeddings.shape[1]}")

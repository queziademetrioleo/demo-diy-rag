"""
Module for loading and processing the Flipkart dataset.

This module is responsible for:
- Preparing data for embedding generation
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from google.cloud import storage
from loguru import logger


class DataLoader:
    """Loads and processes dataset data."""

    def __init__(self, project_id: str, bucket_name: str, local_data_path: str = "./data"):
        """
        Args:
            project_id: Google Cloud project ID
            bucket_name: Cloud Storage bucket name
            local_data_path: Local path for data (default: ./data)
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.local_data_path = Path(local_data_path)

        # Create local directory if it doesn't exist
        self.local_data_path.mkdir(parents=True, exist_ok=True)

        # Initialize Cloud Storage client
        self.storage_client = storage.Client(project=project_id)

    def create_bucket_if_not_exists(self) -> storage.Bucket:
        """Create a bucket in Cloud Storage if it doesn't exist."""
        bucket = self.storage_client.bucket(self.bucket_name)
        if bucket.exists():
            logger.info(f"Bucket '{self.bucket_name}' already exists")
            return bucket

        bucket.location = "us-central1"
        bucket = self.storage_client.create_bucket(bucket)
        logger.info(f"Bucket '{self.bucket_name}' created successfully")
        return bucket

    def download_kaggle_dataset(self, dataset: str = "retailrocket/ecommerce-dataset") -> str:
        """
        Download the dataset from Kaggle.

        Note: Requires Kaggle credentials in ~/.kaggle/kaggle.json

        Args:
            dataset: Kaggle dataset identifier

        Returns:
            Path to the downloaded file
        """
        import kaggle

        try:
            # Download dataset
            kaggle.api.dataset_download_files(dataset, path=self.local_data_path, unzip=True)

            # Locate CSV file
            csv_files = list(self.local_data_path.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError("No CSV file found after download")

            return str(csv_files[0])

        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            raise

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load CSV into a DataFrame.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with data
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise

    def process_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process raw product data into a standard format.

        Args:
            df: Raw product DataFrame

        Returns:
            Processed DataFrame
        """
        # Normalize whitespace
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        # Create copy to avoid modifying original
        df_processed = df.copy()

        # Rename columns to standard
        column_mapping = {
            'product_name': 'name',
            'product_category_tree': 'category',
            'description': 'description',
            'retail_price': 'retail_price',
            'discounted_price': 'discounted_price',
            'brand': 'brand',
            'overall_rating': 'rating',
            'product_rating': 'rating'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in df_processed.columns:
                df_processed = df_processed.rename(columns={old_col: new_col})

        # Check required columns
        required_cols = ['name', 'category', 'description']
        for col in required_cols:
            if col not in df_processed.columns:
                logger.warning(f"Required column '{col}' not found")

        # Extract first category
        if 'category' in df_processed.columns:
            df_processed['category'] = df_processed['category'].apply(
                lambda x: x.split('>>')[0].strip() if isinstance(x, str) else x
            )

        # Process prices
        if 'discounted_price' in df_processed.columns:
            df_processed['discounted_price'] = df_processed['discounted_price'].astype(str)
            df_processed['discounted_price'] = df_processed['discounted_price'].str.replace('[₹,]', '', regex=True)
            df_processed['discounted_price'] = pd.to_numeric(df_processed['discounted_price'], errors='coerce')

        if 'retail_price' in df_processed.columns:
            df_processed['retail_price'] = df_processed['retail_price'].astype(str)
            df_processed['retail_price'] = df_processed['retail_price'].str.replace('[₹,]', '', regex=True)
            df_processed['retail_price'] = pd.to_numeric(df_processed['retail_price'], errors='coerce')

        # Drop rows missing critical data
        df_processed = df_processed.dropna(subset=['name', 'description'])

        logger.info(f"Processing complete: {len(df_processed)} valid products")
        return df_processed

    def create_embeddings_text(self, df: pd.DataFrame) -> pd.Series:
        """
        Create combined text for embeddings.

        Args:
            df: Processed DataFrame

        Returns:
            Series with combined text
        """
        texts = []
        for _, row in df.iterrows():
            parts = []

            # Name
            if pd.notna(row.get('name')):
                parts.append(f"Product: {row['name']}")

            # Brand
            if pd.notna(row.get('brand')):
                parts.append(f"Brand: {row['brand']}")

            # Category
            if pd.notna(row.get('category')):
                parts.append(f"Category: {row['category']}")

            # Description
            desc = row.get('description')
            if pd.notna(desc):
                # Limit description length
                desc = str(desc)[:500]
                parts.append(f"Description: {desc}")

            # Price
            if pd.notna(row.get('discounted_price')):
                parts.append(f"Price: ${row['discounted_price']:.2f}")

            # Rating
            if pd.notna(row.get('rating')):
                parts.append(f"Rating: {row['rating']}")

            texts.append("\n".join(parts))

        return pd.Series(texts)

    def upload_to_gcs(self, df: pd.DataFrame, output_filename: str = "products_processed.csv") -> str:
        """
        Upload processed data to GCS.

        Args:
            df: Processed DataFrame
            output_filename: Output CSV name

        Returns:
            GCS URI
        """
        # Ensure bucket exists
        bucket = self.create_bucket_if_not_exists()

        # Save to local temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        df.to_csv(temp_file.name, index=False)

        # Upload to GCS
        blob = bucket.blob(f"processed_data/{output_filename}")
        blob.upload_from_filename(temp_file.name)

        # Clean up temp file
        os.unlink(temp_file.name)

        gcs_uri = f"gs://{self.bucket_name}/processed_data/{output_filename}"
        logger.info(f"Upload completed: {gcs_uri}")

        return gcs_uri

    def download_from_gcs(self, gcs_path: str) -> pd.DataFrame:
        """
        Download CSV from GCS.

        Args:
            gcs_path: Path in bucket

        Returns:
            DataFrame with downloaded data
        """
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(gcs_path)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        blob.download_to_filename(temp_file.name)

        df = pd.read_csv(temp_file.name)
        os.unlink(temp_file.name)

        logger.info(f"Download from GCS complete: {len(df)} rows")
        return df

    def create_sample_data(self, n: int = 100) -> pd.DataFrame:
        """Create sample data for quick tests."""
        categories = ["Electronics", "Apparel", "Home", "Books", "Sports"]
        data = {
            'name': [f"Sample Product {i}" for i in range(n)],
            'description': [f"Detailed description for product {i}" for i in range(n)],
            'category': [categories[i % len(categories)] for i in range(n)],
            'discounted_price': [round(10 + i * 0.5, 2) for i in range(n)],
            'rating': [round(3.5 + (i % 5) * 0.3, 1) for i in range(n)],
            'brand': [f"Brand {i % 10}" for i in range(n)]
        }
        return pd.DataFrame(data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Data loader and processor")
    parser.add_argument("--bucket-name", required=True, help="Cloud Storage Bucket name")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--local-path", default="./data", help="Local data path")
    args = parser.parse_args()

    loader = DataLoader(project_id=args.project_id, bucket_name=args.bucket_name, local_data_path=args.local_path)
    df = loader.create_sample_data(n=100)
    gcs_uri = loader.upload_to_gcs(df)
    logger.info("DATASET STATISTICS")
    logger.info(f"Rows: {len(df)}")
    logger.info(f"Saved to: {gcs_uri}")

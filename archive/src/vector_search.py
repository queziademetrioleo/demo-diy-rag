"""
Module for configuring and using Vertex AI Vector Search.

This module is responsible for:
- Creating and configuring Vector Search indexes
- Deploying indexes to endpoints
- Managing filters and restrictions
"""

import time
from typing import List, Dict, Optional

from google.cloud import aiplatform
from loguru import logger


class VectorSearchManager:
    """Manage Vertex AI Vector Search resources."""

    def __init__(
        self,
        project_id: str,
        location: str,
        index_display_name: str,
        endpoint_display_name: str
    ):
        """
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            index_display_name: Index display name
            endpoint_display_name: Endpoint display name
        """
        self.project_id = project_id
        self.location = location
        self.index_display_name = index_display_name
        self.endpoint_display_name = endpoint_display_name

        aiplatform.init(project=project_id, location=location)

    def create_index(
        self,
        embeddings_gcs_uri: str,
        dimensions: int,
        distance_measure: str = "COSINE_DISTANCE",
        algorithm_config: Optional[Dict] = None,
        description: str = "FAQ vector search index"
    ):
        """
        Create a Vector Search index.

        Args:
            embeddings_gcs_uri: GCS path to embeddings
            dimensions: Vector dimensions
            distance_measure: Distance metric
            algorithm_config: Algorithm configuration (optional)
            description: Index description

        Returns:
            Created index
        """
        logger.info(f"Creating index: {self.index_display_name}")

        # Default algorithm configuration (Tree-AH)
        if algorithm_config is None:
            algorithm_config = {
                "tree_ah_config": {
                    "leaf_node_embedding_count": 500,
                    "leaf_nodes_to_search_percent": 7
                }
            }

        try:
            index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
                display_name=self.index_display_name,
                contents_delta_uri=embeddings_gcs_uri,
                dimensions=dimensions,
                distance_measure_type=distance_measure,
                description=description,
                algorithm_config=algorithm_config
            )

            logger.info(f"Index created successfully: {index.resource_name}")
            logger.info("Waiting for creation to complete...")
            index.wait()

            return index

        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def get_or_create_index(
        self,
        embeddings_gcs_uri: str,
        dimensions: int,
        distance_measure: str = "COSINE_DISTANCE"
    ):
        """
        Get existing index or create a new one.

        Args:
            embeddings_gcs_uri: GCS path to embeddings
            dimensions: Vector dimensions
            distance_measure: Distance metric

        Returns:
            Index resource
        """
        # Try to find existing index
        try:
            indexes = aiplatform.MatchingEngineIndex.list(
                filter=f"display_name={self.index_display_name}"
            )
            if indexes:
                index = indexes[0]
                logger.info(f"Existing index found: {index.resource_name}")
                return index
        except Exception as e:
            logger.warning(f"Error finding existing index: {e}")

        # Create new index
        return self.create_index(
            embeddings_gcs_uri=embeddings_gcs_uri,
            dimensions=dimensions,
            distance_measure=distance_measure
        )

    def create_endpoint(self, description: str = "Vector Search endpoint", public_endpoint: bool = True):
        """
        Create a Vector Search endpoint.

        Args:
            description: Endpoint description
            public_endpoint: If True, create a public endpoint

        Returns:
            Endpoint resource
        """
        try:
            endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
                display_name=self.endpoint_display_name,
                description=description,
                public_endpoint_enabled=public_endpoint
            )

            logger.info(f"Endpoint created successfully: {endpoint.resource_name}")
            return endpoint

        except Exception as e:
            logger.error(f"Error creating endpoint: {e}")
            raise

    def get_or_create_endpoint(self, public_endpoint: bool = True):
        """
        Get existing endpoint or create a new one.

        Args:
            public_endpoint: If True, create a public endpoint

        Returns:
            Endpoint resource
        """
        # Try to find existing endpoint
        try:
            endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
                filter=f"display_name={self.endpoint_display_name}"
            )
            if endpoints:
                endpoint = endpoints[0]
                logger.info(f"Existing endpoint found: {endpoint.resource_name}")
                return endpoint
        except Exception as e:
            logger.warning(f"Error finding existing endpoint: {e}")

        # Create new endpoint
        return self.create_endpoint(public_endpoint=public_endpoint)

    def deploy_index(
        self,
        index,
        endpoint,
        deployed_index_id: str = "faq-index",
        machine_type: str = "e2-standard-2",
        min_replica_count: int = 1,
        max_replica_count: int = 1
    ):
        """
        Deploy an index to an endpoint.

        Args:
            index: Index to deploy
            endpoint: Endpoint to deploy to
            deployed_index_id: Deployed index ID
            machine_type: Machine type
            min_replica_count: Minimum replicas
            max_replica_count: Maximum replicas
        """
        try:
            logger.info("Deploying index to endpoint...")

            endpoint.deploy_index(
                index=index,
                deployed_index_id=deployed_index_id,
                machine_type=machine_type,
                min_replica_count=min_replica_count,
                max_replica_count=max_replica_count
            )

            logger.info("You can check status in the Google Cloud Console.")

        except Exception as e:
            logger.error(f"Error deploying index: {e}")
            raise

    def find_neighbors(
        self,
        endpoint,
        deployed_index_id: str,
        queries: List[List[float]],
        num_neighbors: int = 10,
        filter_: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for nearest neighbors.

        Args:
            endpoint: Endpoint where index is deployed
            deployed_index_id: Deployed index ID
            queries: List of embedding vectors
            num_neighbors: Number of neighbors to return
            filter_: Optional filter

        Returns:
            List of results with IDs and distances
        """
        try:
            response = endpoint.find_neighbors(
                deployed_index_id=deployed_index_id,
                queries=queries,
                num_neighbors=num_neighbors,
                filter=filter_
            )

            results = []
            for query_idx, neighbors in enumerate(response):
                for neighbor in neighbors:
                    results.append({
                        "query_index": query_idx,
                        "id": neighbor.id,
                        "distance": neighbor.distance
                    })

            return results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise

    def get_index_stats(self, index) -> Dict:
        """Get index statistics."""
        try:
            stats = index.to_dict()
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def update_index(self, index, embeddings_gcs_uri: str):
        """
        Update index with new embeddings.

        Args:
            index: Index to update
            embeddings_gcs_uri: GCS path to new embeddings

        Returns:
            Updated index
        """
        logger.info("Updating index with new embeddings...")
        try:
            index = index.update(embeddings_gcs_uri=embeddings_gcs_uri)
            logger.info("Update started successfully!")
            return index
        except Exception as e:
            logger.error(f"Error updating index: {e}")
            raise

    def undeploy_index(self, endpoint, deployed_index_id: str):
        """
        Remove an index deployment.

        Args:
            endpoint: Endpoint to remove from
            deployed_index_id: Deployed index ID
        """
        logger.info(f"Removing index deployment: {deployed_index_id}")
        try:
            endpoint.undeploy_index(deployed_index_id=deployed_index_id)
            logger.info("Index undeployed successfully!")
        except Exception as e:
            logger.error(f"Error undeploying index: {e}")
            raise

    def delete_index(self, index):
        """
        Delete an index.

        WARNING: This operation is irreversible!

        Args:
            index: Index to delete
        """
        logger.warning(f"DELETING index: {index.display_name}")
        try:
            index.delete()
            logger.info("Index deleted successfully!")
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            raise

    def delete_endpoint(self, endpoint):
        """
        Delete an endpoint.

        WARNING: This operation is irreversible!
        Ensure no indexes are deployed before deleting.

        Args:
            endpoint: Endpoint to delete
        """
        try:
            endpoint.delete()
            logger.info("Endpoint deleted successfully!")
        except Exception as e:
            logger.error(f"Error deleting endpoint: {e}")
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Configure Vector Search")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--bucket-name", required=True, help="Cloud Storage Bucket name")
    parser.add_argument("--dimensions", type=int, default=768, help="Embedding dimensions")
    parser.add_argument("--index-name", default="products-index", help="Index name")
    parser.add_argument("--endpoint-name", default="products-endpoint", help="Endpoint name")
    parser.add_argument("--machine-type", default="e2-standard-2", help="Machine type")

    args = parser.parse_args()

    manager = VectorSearchManager(
        project_id=args.project_id,
        location="us-central1",
        index_display_name=args.index_name,
        endpoint_display_name=args.endpoint_name
    )

    # Create or get index
    logger.info("Creating index...")
    index = manager.get_or_create_index(
        embeddings_gcs_uri=f"gs://{args.bucket_name}/embeddings/vector_search_data.jsonl",
        dimensions=args.dimensions
    )

    # Create or get endpoint
    logger.info("Creating endpoint...")
    endpoint = manager.get_or_create_endpoint()

    # Deploy
    logger.info("Deploying index...")
    manager.deploy_index(
        index=index,
        endpoint=endpoint,
        machine_type=args.machine_type
    )

    # Summary
    logger.info("VECTOR SEARCH CONFIGURATION COMPLETE")
    logger.info(f"Index: {index.resource_name}")
    logger.info(f"Endpoint: {endpoint.resource_name}")
    logger.info("Wait 30-45 minutes for deployment to complete.")

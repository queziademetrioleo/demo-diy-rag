"""
Módulo para configuração e uso do Vertex AI Vector Search.

Este módulo é responsável por:
- Criar e configurar índices de Vector Search
- Criar e gerenciar endpoints
- Fazer deploy de índices em endpoints
- Realizar buscas vetoriais eficientes
- Gerenciar filtros e restrições
"""

import time
from typing import List, Dict, Optional, Tuple
from google.cloud import aiplatform
from google.cloud import storage
from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint
from loguru import logger
import numpy as np


class VectorSearchManager:
    """
    Classe para gerenciar Vector Search no Vertex AI.

    Attributes:
        project_id: ID do projeto Google Cloud
        location: Região do Google Cloud
        index_display_name: Nome do índice
        endpoint_display_name: Nome do endpoint
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        index_display_name: str = "produtos-index",
        endpoint_display_name: str = "produtos-endpoint"
    ):
        """
        Inicializa o VectorSearchManager.

        Args:
            project_id: ID do projeto Google Cloud
            location: Região do Google Cloud
            index_display_name: Nome para exibição do índice
            endpoint_display_name: Nome para exibição do endpoint
        """
        self.project_id = project_id
        self.location = location
        self.index_display_name = index_display_name
        self.endpoint_display_name = endpoint_display_name

        # Inicializar Vertex AI
        aiplatform.init(project=project_id, location=location)

        self.storage_client = storage.Client(project=project_id)

        logger.info(f"VectorSearchManager inicializado: projeto {project_id}")

    def create_index(
        self,
        embeddings_gcs_uri: str,
        dimensions: int = 768,
        distance_measure: str = "DOT_PRODUCT_DISTANCE",
        algorithm_config: Optional[Dict] = None,
        description: str = "Index de produtos para RAG"
    ) -> MatchingEngineIndex:
        """
        Cria um índice de Vector Search.

        Args:
            embeddings_gcs_uri: URI do GCS com embeddings (formato JSONL)
            dimensions: Dimensão dos vetores
            distance_measure: Métrica de distância
                - DOT_PRODUCT_DISTANCE (para embeddings normalizados)
                - COSINE_DISTANCE
                - SQUARED_L2_DISTANCE
            algorithm_config: Configuração do algoritmo (opcional)
            description: Descrição do índice

        Returns:
            Objeto MatchingEngineIndex criado
        """
        logger.info(f"Criando índice: {self.index_display_name}")

        # Configuração padrão do algoritmo (Tree-AH)
        if algorithm_config is None:
            algorithm_config = {
                "treeAhConfig": {
                    "leafNodeEmbeddingCount": 1000,
                    "leafNodesToSearchPercent": 7
                }
            }

        try:
            # Criar índice
            index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
                display_name=self.index_display_name,
                contents_delta_uri=embeddings_gcs_uri,
                dimensions=dimensions,
                approximate_neighbors_count=10,
                distance_measure_type=distance_measure,
                leaf_node_embedding_count=algorithm_config["treeAhConfig"]["leafNodeEmbeddingCount"],
                leaf_nodes_to_search_percent=algorithm_config["treeAhConfig"]["leafNodesToSearchPercent"],
                description=description
            )

            logger.info(f"Índice criado com sucesso: {index.resource_name}")
            logger.info(f"Aguardando conclusão da criação...")

            # Aguardar conclusão (pode levar vários minutos)
            # O índice é criado de forma assíncrona
            return index

        except Exception as e:
            logger.error(f"Erro ao criar índice: {e}")
            raise

    def get_or_create_index(
        self,
        embeddings_gcs_uri: str,
        dimensions: int = 768,
        distance_measure: str = "DOT_PRODUCT_DISTANCE"
    ) -> MatchingEngineIndex:
        """
        Obtém índice existente ou cria novo.

        Args:
            embeddings_gcs_uri: URI do GCS com embeddings
            dimensions: Dimensão dos vetores
            distance_measure: Métrica de distância

        Returns:
            Objeto MatchingEngineIndex
        """
        # Tentar encontrar índice existente
        try:
            indexes = aiplatform.MatchingEngineIndex.list(
                filter=f'display_name="{self.index_display_name}"'
            )

            if indexes:
                index = indexes[0]
                logger.info(f"Índice existente encontrado: {index.resource_name}")
                return index

        except Exception as e:
            logger.warning(f"Erro ao buscar índice existente: {e}")

        # Criar novo índice
        return self.create_index(
            embeddings_gcs_uri=embeddings_gcs_uri,
            dimensions=dimensions,
            distance_measure=distance_measure
        )

    def create_endpoint(
        self,
        description: str = "Endpoint para busca de produtos",
        public_endpoint: bool = True
    ) -> MatchingEngineIndexEndpoint:
        """
        Cria um endpoint para servir o índice.

        Args:
            description: Descrição do endpoint
            public_endpoint: Se True, cria endpoint público

        Returns:
            Objeto MatchingEngineIndexEndpoint criado
        """
        logger.info(f"Criando endpoint: {self.endpoint_display_name}")

        try:
            endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
                display_name=self.endpoint_display_name,
                description=description,
                public_endpoint_enabled=public_endpoint
            )

            logger.info(f"Endpoint criado com sucesso: {endpoint.resource_name}")

            return endpoint

        except Exception as e:
            logger.error(f"Erro ao criar endpoint: {e}")
            raise

    def get_or_create_endpoint(
        self,
        public_endpoint: bool = True
    ) -> MatchingEngineIndexEndpoint:
        """
        Obtém endpoint existente ou cria novo.

        Args:
            public_endpoint: Se True, cria endpoint público

        Returns:
            Objeto MatchingEngineIndexEndpoint
        """
        # Tentar encontrar endpoint existente
        try:
            endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
                filter=f'display_name="{self.endpoint_display_name}"'
            )

            if endpoints:
                endpoint = endpoints[0]
                logger.info(f"Endpoint existente encontrado: {endpoint.resource_name}")
                return endpoint

        except Exception as e:
            logger.warning(f"Erro ao buscar endpoint existente: {e}")

        # Criar novo endpoint
        return self.create_endpoint(public_endpoint=public_endpoint)

    def deploy_index(
        self,
        index: MatchingEngineIndex,
        endpoint: MatchingEngineIndexEndpoint,
        deployed_index_id: str = "deployed_produtos_index",
        machine_type: str = "e2-standard-2",
        min_replica_count: int = 1,
        max_replica_count: int = 2
    ) -> None:
        """
        Faz deploy de um índice em um endpoint.

        Args:
            index: Índice a ser deployado
            endpoint: Endpoint onde fazer deploy
            deployed_index_id: ID do índice deployado
            machine_type: Tipo de máquina (e2-standard-2, e2-standard-16, etc)
            min_replica_count: Número mínimo de réplicas
            max_replica_count: Número máximo de réplicas
        """
        logger.info(f"Fazendo deploy do índice no endpoint...")
        logger.info(f"  Machine type: {machine_type}")
        logger.info(f"  Replicas: {min_replica_count}-{max_replica_count}")

        try:
            # Deploy do índice
            endpoint.deploy_index(
                index=index,
                deployed_index_id=deployed_index_id,
                display_name=deployed_index_id,
                machine_type=machine_type,
                min_replica_count=min_replica_count,
                max_replica_count=max_replica_count,
            )

            logger.info("Deploy iniciado com sucesso!")
            logger.info("AVISO: O deploy pode levar 30-45 minutos para completar.")
            logger.info("Você pode verificar o status no console do Google Cloud.")

        except Exception as e:
            logger.error(f"Erro ao fazer deploy: {e}")
            raise

    def search(
        self,
        endpoint: MatchingEngineIndexEndpoint,
        query_embedding: np.ndarray,
        deployed_index_id: str = "deployed_produtos_index",
        num_neighbors: int = 5,
        filter_restrictions: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Realiza busca vetorial.

        Args:
            endpoint: Endpoint onde o índice está deployado
            query_embedding: Vetor de embedding da query
            deployed_index_id: ID do índice deployado
            num_neighbors: Número de vizinhos a retornar
            filter_restrictions: Filtros a aplicar (opcional)

        Returns:
            Lista de resultados com IDs e distâncias
        """
        try:
            # Converter embedding para lista
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()

            # Fazer busca
            response = endpoint.find_neighbors(
                deployed_index_id=deployed_index_id,
                queries=[query_embedding],
                num_neighbors=num_neighbors,
                filter=filter_restrictions
            )

            # Processar resultados
            results = []
            if response and len(response) > 0:
                for neighbor in response[0]:
                    results.append({
                        "id": neighbor.id,
                        "distance": neighbor.distance
                    })

            logger.info(f"Busca retornou {len(results)} resultados")

            return results

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []

    def get_index_stats(self, index: MatchingEngineIndex) -> Dict:
        """
        Obtém estatísticas do índice.

        Args:
            index: Índice para obter estatísticas

        Returns:
            Dicionário com estatísticas
        """
        try:
            stats = {
                "display_name": index.display_name,
                "resource_name": index.resource_name,
                "created_time": str(index.create_time),
                "updated_time": str(index.update_time),
                "index_stats": index.index_stats if hasattr(index, 'index_stats') else None
            }

            return stats

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def update_index(
        self,
        index: MatchingEngineIndex,
        new_embeddings_gcs_uri: str
    ) -> MatchingEngineIndex:
        """
        Atualiza índice com novos embeddings.

        Args:
            index: Índice a ser atualizado
            new_embeddings_gcs_uri: URI do GCS com novos embeddings

        Returns:
            Índice atualizado
        """
        logger.info(f"Atualizando índice com novos embeddings...")

        try:
            # Atualizar índice
            updated_index = index.update_embeddings(
                contents_delta_uri=new_embeddings_gcs_uri
            )

            logger.info("Atualização iniciada com sucesso!")

            return updated_index

        except Exception as e:
            logger.error(f"Erro ao atualizar índice: {e}")
            raise

    def undeploy_index(
        self,
        endpoint: MatchingEngineIndexEndpoint,
        deployed_index_id: str = "deployed_produtos_index"
    ) -> None:
        """
        Remove deploy de um índice.

        Args:
            endpoint: Endpoint do qual remover o índice
            deployed_index_id: ID do índice deployado
        """
        logger.info(f"Removendo deploy do índice: {deployed_index_id}")

        try:
            endpoint.undeploy_index(deployed_index_id=deployed_index_id)
            logger.info("Deploy removido com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao remover deploy: {e}")
            raise

    def delete_index(self, index: MatchingEngineIndex) -> None:
        """
        Deleta um índice.

        AVISO: Esta operação é irreversível!

        Args:
            index: Índice a ser deletado
        """
        logger.warning(f"DELETANDO índice: {index.display_name}")

        try:
            index.delete()
            logger.info("Índice deletado com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao deletar índice: {e}")
            raise

    def delete_endpoint(self, endpoint: MatchingEngineIndexEndpoint) -> None:
        """
        Deleta um endpoint.

        AVISO: Esta operação é irreversível!
        Certifique-se de que não há índices deployados antes de deletar.

        Args:
            endpoint: Endpoint a ser deletado
        """
        logger.warning(f"DELETANDO endpoint: {endpoint.display_name}")

        try:
            endpoint.delete()
            logger.info("Endpoint deletado com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao deletar endpoint: {e}")
            raise


def main():
    """Função principal para execução standalone."""
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="Configurar Vector Search")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--location", default="us-central1", help="GCP location")
    parser.add_argument("--embeddings-uri", required=True, help="GCS URI dos embeddings (JSONL)")
    parser.add_argument("--dimensions", type=int, default=768, help="Dimensão dos embeddings")
    parser.add_argument("--index-name", default="produtos-index", help="Nome do índice")
    parser.add_argument("--endpoint-name", default="produtos-endpoint", help="Nome do endpoint")
    parser.add_argument("--deploy", action="store_true", help="Fazer deploy automaticamente")
    parser.add_argument("--machine-type", default="e2-standard-2", help="Tipo de máquina")

    args = parser.parse_args()

    # Inicializar manager
    manager = VectorSearchManager(
        project_id=args.project_id,
        location=args.location,
        index_display_name=args.index_name,
        endpoint_display_name=args.endpoint_name
    )

    # Criar ou obter índice
    logger.info("Criando índice...")
    index = manager.get_or_create_index(
        embeddings_gcs_uri=args.embeddings_uri,
        dimensions=args.dimensions
    )

    # Criar ou obter endpoint
    logger.info("Criando endpoint...")
    endpoint = manager.get_or_create_endpoint()

    # Deploy se solicitado
    if args.deploy:
        logger.info("Fazendo deploy do índice...")
        manager.deploy_index(
            index=index,
            endpoint=endpoint,
            machine_type=args.machine_type
        )

    # Resumo
    logger.info("\n" + "="*50)
    logger.info("CONFIGURAÇÃO DE VECTOR SEARCH CONCLUÍDA")
    logger.info("="*50)
    logger.info(f"Índice: {index.resource_name}")
    logger.info(f"Endpoint: {endpoint.resource_name}")

    if args.deploy:
        logger.info("\nDeploy iniciado!")
        logger.info("Aguarde 30-45 minutos para conclusão.")
        logger.info("Verifique status em: https://console.cloud.google.com/vertex-ai/matching-engine/indexes")
    else:
        logger.info("\nPara fazer deploy, execute novamente com --deploy")

    logger.info("="*50)


if __name__ == "__main__":
    main()

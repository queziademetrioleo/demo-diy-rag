"""
Módulo para geração de embeddings usando Vertex AI.

Este módulo é responsável por:
- Gerar embeddings de texto usando modelos do Vertex AI
- Processar embeddings em lotes para eficiência
- Salvar embeddings em formato otimizado para Vector Search
- Gerenciar metadata de embeddings
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from google.cloud import aiplatform
from google.cloud import storage
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from loguru import logger
from tqdm import tqdm
import time


class EmbeddingGenerator:
    """
    Classe para gerar embeddings usando Vertex AI.

    Attributes:
        project_id: ID do projeto Google Cloud
        location: Região do Google Cloud (ex: us-central1)
        model_name: Nome do modelo de embeddings
        batch_size: Tamanho do lote para processamento
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "text-embedding-004",
        batch_size: int = 250
    ):
        """
        Inicializa o EmbeddingGenerator.

        Args:
            project_id: ID do projeto Google Cloud
            location: Região do Google Cloud
            model_name: Nome do modelo de embeddings
            batch_size: Tamanho do lote (máx 250 para text-embedding-004)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.batch_size = min(batch_size, 250)  # Limite da API

        # Inicializar Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Carregar modelo
        self.model = TextEmbeddingModel.from_pretrained(model_name)

        self.storage_client = storage.Client(project=project_id)

        logger.info(
            f"EmbeddingGenerator inicializado: {model_name} "
            f"(batch_size={self.batch_size})"
        )

    def get_embedding_dimension(self) -> int:
        """
        Retorna a dimensão dos embeddings do modelo.

        Returns:
            Dimensão dos vetores de embedding
        """
        # text-embedding-004 retorna vetores de 768 dimensões
        dimension_map = {
            "text-embedding-004": 768,
            "textembedding-gecko@003": 768,
            "textembedding-gecko@002": 768,
            "textembedding-gecko@001": 768
        }

        return dimension_map.get(self.model_name, 768)

    def generate_embeddings(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Gera embeddings para uma lista de textos.

        Args:
            texts: Lista de textos para gerar embeddings
            task_type: Tipo de tarefa (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc)
            show_progress: Mostrar barra de progresso

        Returns:
            Array numpy com embeddings (shape: [n_texts, embedding_dim])
        """
        embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        logger.info(
            f"Gerando embeddings para {len(texts)} textos "
            f"em {total_batches} lotes..."
        )

        # Processar em lotes
        iterator = range(0, len(texts), self.batch_size)
        if show_progress:
            iterator = tqdm(iterator, desc="Gerando embeddings", total=total_batches)

        for i in iterator:
            batch_texts = texts[i:i + self.batch_size]

            # Criar inputs com task type
            inputs = [
                TextEmbeddingInput(text=text, task_type=task_type)
                for text in batch_texts
            ]

            try:
                # Gerar embeddings
                batch_embeddings = self.model.get_embeddings(inputs)

                # Extrair valores dos embeddings
                batch_vectors = [emb.values for emb in batch_embeddings]
                embeddings.extend(batch_vectors)

                # Rate limiting (evitar throttling)
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Erro ao processar lote {i//self.batch_size}: {e}")
                # Adicionar vetores zero em caso de erro
                dim = self.get_embedding_dimension()
                embeddings.extend([np.zeros(dim).tolist()] * len(batch_texts))

        # Converter para numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)

        logger.info(f"Embeddings gerados: shape {embeddings_array.shape}")

        return embeddings_array

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Gera embedding para uma query de busca.

        Args:
            query: Texto da query

        Returns:
            Vetor de embedding
        """
        input_obj = TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")

        try:
            embeddings = self.model.get_embeddings([input_obj])
            return np.array(embeddings[0].values, dtype=np.float32)

        except Exception as e:
            logger.error(f"Erro ao gerar embedding da query: {e}")
            # Retornar vetor zero em caso de erro
            dim = self.get_embedding_dimension()
            return np.zeros(dim, dtype=np.float32)

    def create_embeddings_dataset(
        self,
        df: pd.DataFrame,
        text_column: str = "combined_text",
        id_column: str = "product_id"
    ) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Cria dataset de embeddings a partir de DataFrame.

        Args:
            df: DataFrame com dados
            text_column: Nome da coluna com texto
            id_column: Nome da coluna com ID único

        Returns:
            Tupla (embeddings_array, metadata_df)
        """
        logger.info(f"Criando dataset de embeddings de {len(df)} itens...")

        # Validar colunas
        if text_column not in df.columns:
            raise ValueError(f"Coluna '{text_column}' não encontrada no DataFrame")

        if id_column not in df.columns:
            raise ValueError(f"Coluna '{id_column}' não encontrada no DataFrame")

        # Gerar embeddings
        texts = df[text_column].tolist()
        embeddings = self.generate_embeddings(texts)

        # Criar metadata
        metadata_df = df.copy()
        metadata_df['embedding_id'] = range(len(df))

        # Adicionar informações do embedding
        metadata_df['embedding_dimension'] = self.get_embedding_dimension()
        metadata_df['embedding_model'] = self.model_name

        logger.info(
            f"Dataset criado: {len(embeddings)} embeddings, "
            f"{len(metadata_df)} metadatas"
        )

        return embeddings, metadata_df

    def save_embeddings_to_gcs(
        self,
        embeddings: np.ndarray,
        metadata: pd.DataFrame,
        bucket_name: str,
        embeddings_path: str = "embeddings/vectors.npy",
        metadata_path: str = "embeddings/metadata.csv"
    ) -> Dict[str, str]:
        """
        Salva embeddings e metadata no Cloud Storage.

        Args:
            embeddings: Array numpy com embeddings
            metadata: DataFrame com metadata
            bucket_name: Nome do bucket
            embeddings_path: Caminho para salvar embeddings
            metadata_path: Caminho para salvar metadata

        Returns:
            Dicionário com URIs dos arquivos salvos
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # Salvar embeddings
            # Criar arquivo temporário local
            local_embeddings = Path("./temp_embeddings.npy")
            np.save(local_embeddings, embeddings)

            blob_embeddings = bucket.blob(embeddings_path)
            blob_embeddings.upload_from_filename(str(local_embeddings))

            embeddings_uri = f"gs://{bucket_name}/{embeddings_path}"
            logger.info(f"Embeddings salvos: {embeddings_uri}")

            # Salvar metadata
            local_metadata = Path("./temp_metadata.csv")
            metadata.to_csv(local_metadata, index=False)

            blob_metadata = bucket.blob(metadata_path)
            blob_metadata.upload_from_filename(str(local_metadata))

            metadata_uri = f"gs://{bucket_name}/{metadata_path}"
            logger.info(f"Metadata salva: {metadata_uri}")

            # Limpar arquivos temporários
            local_embeddings.unlink()
            local_metadata.unlink()

            return {
                "embeddings_uri": embeddings_uri,
                "metadata_uri": metadata_uri
            }

        except Exception as e:
            logger.error(f"Erro ao salvar no GCS: {e}")
            raise

    def save_for_vector_search(
        self,
        embeddings: np.ndarray,
        metadata: pd.DataFrame,
        bucket_name: str,
        output_path: str = "embeddings/vector_search_data.jsonl",
        id_column: str = "product_id"
    ) -> str:
        """
        Salva embeddings no formato JSONL para Vector Search.

        Formato esperado pelo Vector Search:
        {"id": "item1", "embedding": [0.1, 0.2, ...], "metadata": {...}}

        Args:
            embeddings: Array numpy com embeddings
            metadata: DataFrame com metadata
            bucket_name: Nome do bucket
            output_path: Caminho de saída
            id_column: Nome da coluna de ID

        Returns:
            GCS URI do arquivo criado
        """
        logger.info("Preparando dados para Vector Search...")

        # Criar arquivo JSONL local
        local_file = Path("./temp_vector_search.jsonl")

        with open(local_file, 'w', encoding='utf-8') as f:
            for idx, (embedding, (_, row)) in enumerate(zip(embeddings, metadata.iterrows())):
                # Criar objeto JSON
                item = {
                    "id": str(row[id_column]),
                    "embedding": embedding.tolist(),
                    "restricts": {
                        "category": str(row.get('category', '')),
                        "brand": str(row.get('brand', ''))
                    }
                }

                # Adicionar metadata seletiva (campos mais importantes)
                item_metadata = {
                    "name": str(row.get('name', '')),
                    "description": str(row.get('description', ''))[:200],  # Limitar tamanho
                    "category": str(row.get('category', '')),
                    "brand": str(row.get('brand', '')),
                    "price": float(row.get('discounted_price', 0)),
                    "rating": float(row.get('rating', 0)) if pd.notna(row.get('rating')) else None
                }

                # Remover campos nulos
                item_metadata = {k: v for k, v in item_metadata.items() if v is not None and v != ''}

                item["metadata"] = item_metadata

                # Escrever linha JSON
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        # Upload para GCS
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.blob(output_path)
            blob.upload_from_filename(str(local_file))

            gcs_uri = f"gs://{bucket_name}/{output_path}"
            logger.info(f"Dados para Vector Search salvos: {gcs_uri}")

            # Limpar arquivo temporário
            local_file.unlink()

            return gcs_uri

        except Exception as e:
            logger.error(f"Erro ao salvar dados para Vector Search: {e}")
            raise

    def load_embeddings_from_gcs(
        self,
        bucket_name: str,
        embeddings_path: str = "embeddings/vectors.npy",
        metadata_path: str = "embeddings/metadata.csv"
    ) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Carrega embeddings e metadata do Cloud Storage.

        Args:
            bucket_name: Nome do bucket
            embeddings_path: Caminho dos embeddings
            metadata_path: Caminho da metadata

        Returns:
            Tupla (embeddings_array, metadata_df)
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)

            # Baixar embeddings
            local_embeddings = Path("./temp_embeddings_load.npy")
            blob_embeddings = bucket.blob(embeddings_path)
            blob_embeddings.download_to_filename(str(local_embeddings))

            embeddings = np.load(local_embeddings)
            local_embeddings.unlink()

            logger.info(f"Embeddings carregados: shape {embeddings.shape}")

            # Baixar metadata
            local_metadata = Path("./temp_metadata_load.csv")
            blob_metadata = bucket.blob(metadata_path)
            blob_metadata.download_to_filename(str(local_metadata))

            metadata = pd.read_csv(local_metadata)
            local_metadata.unlink()

            logger.info(f"Metadata carregada: {len(metadata)} linhas")

            return embeddings, metadata

        except Exception as e:
            logger.error(f"Erro ao carregar do GCS: {e}")
            raise


def main():
    """Função principal para execução standalone."""
    import argparse
    from dotenv import load_dotenv
    from data_loader import DataLoader

    load_dotenv()

    parser = argparse.ArgumentParser(description="Gerar embeddings com Vertex AI")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--bucket-name", required=True, help="Cloud Storage Bucket name")
    parser.add_argument("--location", default="us-central1", help="GCP location")
    parser.add_argument("--data-path", default="raw_data/flipkart_products.csv", help="Caminho dos dados no GCS")
    parser.add_argument("--model", default="text-embedding-004", help="Modelo de embedding")
    parser.add_argument("--batch-size", type=int, default=250, help="Tamanho do batch")

    args = parser.parse_args()

    # Carregar dados
    logger.info("Carregando dados...")
    loader = DataLoader(
        project_id=args.project_id,
        bucket_name=args.bucket_name
    )
    df = loader.download_from_gcs(args.data_path)

    # Gerar embeddings
    logger.info("Inicializando gerador de embeddings...")
    generator = EmbeddingGenerator(
        project_id=args.project_id,
        location=args.location,
        model_name=args.model,
        batch_size=args.batch_size
    )

    # Criar dataset de embeddings
    embeddings, metadata = generator.create_embeddings_dataset(df)

    # Salvar em múltiplos formatos
    logger.info("Salvando embeddings...")

    # Formato 1: Arrays separados
    uris = generator.save_embeddings_to_gcs(
        embeddings=embeddings,
        metadata=metadata,
        bucket_name=args.bucket_name
    )

    # Formato 2: JSONL para Vector Search
    vector_search_uri = generator.save_for_vector_search(
        embeddings=embeddings,
        metadata=metadata,
        bucket_name=args.bucket_name
    )

    # Resumo
    logger.info("\n" + "="*50)
    logger.info("GERAÇÃO DE EMBEDDINGS CONCLUÍDA")
    logger.info("="*50)
    logger.info(f"Total de embeddings: {len(embeddings)}")
    logger.info(f"Dimensão: {embeddings.shape[1]}")
    logger.info(f"Modelo: {args.model}")
    logger.info(f"\nArquivos salvos:")
    logger.info(f"  - Embeddings: {uris['embeddings_uri']}")
    logger.info(f"  - Metadata: {uris['metadata_uri']}")
    logger.info(f"  - Vector Search: {vector_search_uri}")
    logger.info("="*50)


if __name__ == "__main__":
    main()

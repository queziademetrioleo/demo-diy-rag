"""
Módulo para carregamento e processamento de dados do dataset Flipkart.

Este módulo é responsável por:
- Download do dataset do Kaggle
- Limpeza e processamento dos dados
- Upload para Google Cloud Storage
- Preparação dos dados para geração de embeddings
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from google.cloud import storage
from loguru import logger
import re


class DataLoader:
    """
    Classe para carregar e processar dados de produtos.

    Attributes:
        project_id: ID do projeto Google Cloud
        bucket_name: Nome do bucket no Cloud Storage
        local_data_path: Caminho local para armazenar dados
    """

    def __init__(
        self,
        project_id: str,
        bucket_name: str,
        local_data_path: str = "./data"
    ):
        """
        Inicializa o DataLoader.

        Args:
            project_id: ID do projeto Google Cloud
            bucket_name: Nome do bucket no Cloud Storage
            local_data_path: Caminho local para dados (padrão: ./data)
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.local_data_path = Path(local_data_path)
        self.storage_client = storage.Client(project=project_id)

        # Criar diretório local se não existir
        self.local_data_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"DataLoader inicializado para projeto: {project_id}")

    def create_bucket_if_not_exists(self) -> storage.Bucket:
        """
        Cria bucket no Cloud Storage se não existir.

        Returns:
            Objeto Bucket do Cloud Storage
        """
        try:
            bucket = self.storage_client.get_bucket(self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' já existe")
        except Exception:
            bucket = self.storage_client.create_bucket(
                self.bucket_name,
                location="us-central1"
            )
            logger.info(f"Bucket '{self.bucket_name}' criado com sucesso")

        return bucket

    def download_kaggle_dataset(
        self,
        dataset_name: str = "PromptCloudHQ/flipkart-products",
        output_filename: str = "flipkart_com-ecommerce_sample.csv"
    ) -> Path:
        """
        Baixa dataset do Kaggle.

        NOTA: Requer configuração de credenciais Kaggle em ~/.kaggle/kaggle.json

        Args:
            dataset_name: Nome do dataset no Kaggle
            output_filename: Nome do arquivo de saída

        Returns:
            Path para o arquivo baixado
        """
        try:
            import kaggle

            logger.info(f"Baixando dataset: {dataset_name}")

            # Download para pasta local
            kaggle.api.dataset_download_files(
                dataset_name,
                path=str(self.local_data_path),
                unzip=True
            )

            file_path = self.local_data_path / output_filename

            if file_path.exists():
                logger.info(f"Dataset baixado com sucesso: {file_path}")
                return file_path
            else:
                raise FileNotFoundError(
                    f"Arquivo {output_filename} não encontrado após download"
                )

        except Exception as e:
            logger.error(f"Erro ao baixar dataset: {e}")
            raise

    def load_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Carrega arquivo CSV em DataFrame.

        Args:
            file_path: Caminho para o arquivo CSV

        Returns:
            DataFrame com os dados
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"CSV carregado: {len(df)} linhas, {len(df.columns)} colunas")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar CSV: {e}")
            raise

    def clean_text(self, text: str) -> str:
        """
        Limpa texto removendo caracteres especiais e normalizando.

        Args:
            text: Texto a ser limpo

        Returns:
            Texto limpo
        """
        if pd.isna(text):
            return ""

        # Converter para string
        text = str(text)

        # Remover HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remover caracteres especiais excessivos
        text = re.sub(r'[^\w\s\.,!?-]', ' ', text)

        # Normalizar espaços
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def process_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de produtos.

        Args:
            df: DataFrame com dados brutos

        Returns:
            DataFrame processado
        """
        logger.info("Iniciando processamento de produtos...")

        # Criar cópia para não modificar original
        df_processed = df.copy()

        # Renomear colunas para padrão
        column_mapping = {
            'uniq_id': 'product_id',
            'product_name': 'name',
            'description': 'description',
            'retail_price': 'price',
            'discounted_price': 'discounted_price',
            'product_category_tree': 'category',
            'brand': 'brand',
            'product_rating': 'rating',
            'overall_rating': 'overall_rating',
            'image': 'image_url'
        }

        # Renomear apenas colunas que existem
        existing_columns = {k: v for k, v in column_mapping.items() if k in df_processed.columns}
        df_processed = df_processed.rename(columns=existing_columns)

        # Garantir que colunas essenciais existem
        essential_columns = ['product_id', 'name', 'description']
        for col in essential_columns:
            if col not in df_processed.columns:
                logger.warning(f"Coluna essencial '{col}' não encontrada")

        # Limpar textos
        if 'name' in df_processed.columns:
            df_processed['name'] = df_processed['name'].apply(self.clean_text)

        if 'description' in df_processed.columns:
            df_processed['description'] = df_processed['description'].apply(self.clean_text)

        # Processar categoria (extrair primeira categoria)
        if 'category' in df_processed.columns:
            df_processed['category'] = df_processed['category'].apply(
                lambda x: self.clean_text(x).split('>>')[0] if pd.notna(x) else "Sem categoria"
            )

        # Processar preços
        for price_col in ['price', 'discounted_price']:
            if price_col in df_processed.columns:
                # Remover símbolos de moeda e converter para float
                df_processed[price_col] = df_processed[price_col].apply(
                    lambda x: float(re.sub(r'[^\d.]', '', str(x))) if pd.notna(x) else 0.0
                )

        # Calcular desconto percentual
        if 'price' in df_processed.columns and 'discounted_price' in df_processed.columns:
            df_processed['discount_percent'] = (
                (df_processed['price'] - df_processed['discounted_price']) /
                df_processed['price'] * 100
            ).round(2)
            df_processed['discount_percent'] = df_processed['discount_percent'].fillna(0)

        # Criar texto combinado para embeddings
        df_processed['combined_text'] = self._create_combined_text(df_processed)

        # Remover linhas com textos vazios
        df_processed = df_processed[df_processed['combined_text'].str.len() > 10]

        # Reset index
        df_processed = df_processed.reset_index(drop=True)

        logger.info(f"Processamento concluído: {len(df_processed)} produtos válidos")

        return df_processed

    def _create_combined_text(self, df: pd.DataFrame) -> pd.Series:
        """
        Cria texto combinado para geração de embeddings.

        Args:
            df: DataFrame com dados do produto

        Returns:
            Series com textos combinados
        """
        combined_texts = []

        for _, row in df.iterrows():
            parts = []

            # Nome do produto
            if 'name' in row and pd.notna(row['name']):
                parts.append(f"Produto: {row['name']}")

            # Categoria
            if 'category' in row and pd.notna(row['category']):
                parts.append(f"Categoria: {row['category']}")

            # Marca
            if 'brand' in row and pd.notna(row['brand']):
                parts.append(f"Marca: {row['brand']}")

            # Descrição
            if 'description' in row and pd.notna(row['description']):
                # Limitar tamanho da descrição
                desc = str(row['description'])[:500]
                parts.append(f"Descrição: {desc}")

            # Preço
            if 'discounted_price' in row and pd.notna(row['discounted_price']):
                parts.append(f"Preço: R$ {row['discounted_price']:.2f}")

            # Rating
            if 'rating' in row and pd.notna(row['rating']):
                parts.append(f"Avaliação: {row['rating']}")

            combined_texts.append(" | ".join(parts))

        return pd.Series(combined_texts)

    def upload_to_gcs(
        self,
        df: pd.DataFrame,
        blob_name: str = "raw_data/flipkart_products.csv"
    ) -> str:
        """
        Faz upload do DataFrame para Cloud Storage.

        Args:
            df: DataFrame a ser enviado
            blob_name: Nome do blob (caminho) no bucket

        Returns:
            GCS URI do arquivo
        """
        try:
            bucket = self.create_bucket_if_not_exists()
            blob = bucket.blob(blob_name)

            # Salvar localmente primeiro
            local_file = self.local_data_path / "processed_data.csv"
            df.to_csv(local_file, index=False)

            # Upload
            blob.upload_from_filename(str(local_file))

            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
            logger.info(f"Upload concluído: {gcs_uri}")

            return gcs_uri

        except Exception as e:
            logger.error(f"Erro no upload para GCS: {e}")
            raise

    def download_from_gcs(self, blob_name: str) -> pd.DataFrame:
        """
        Baixa dados do Cloud Storage.

        Args:
            blob_name: Nome do blob no bucket

        Returns:
            DataFrame com os dados
        """
        try:
            bucket = self.storage_client.get_bucket(self.bucket_name)
            blob = bucket.blob(blob_name)

            # Download para arquivo local
            local_file = self.local_data_path / "downloaded_data.csv"
            blob.download_to_filename(str(local_file))

            # Carregar em DataFrame
            df = pd.read_csv(local_file)
            logger.info(f"Download do GCS concluído: {len(df)} linhas")

            return df

        except Exception as e:
            logger.error(f"Erro no download do GCS: {e}")
            raise

    def get_sample_data(self, n: int = 1000) -> pd.DataFrame:
        """
        Cria dataset de exemplo para testes rápidos.

        Args:
            n: Número de amostras

        Returns:
            DataFrame com dados de exemplo
        """
        logger.info(f"Criando dataset de exemplo com {n} produtos...")

        categories = ["Eletrônicos", "Vestuário", "Casa", "Livros", "Esportes"]
        brands = ["Samsung", "Apple", "Nike", "Adidas", "Dell", "HP"]

        data = {
            'product_id': [f"PROD{i:06d}" for i in range(n)],
            'name': [f"Produto Exemplo {i}" for i in range(n)],
            'description': [f"Descrição detalhada do produto {i}" for i in range(n)],
            'category': np.random.choice(categories, n),
            'brand': np.random.choice(brands, n),
            'price': np.random.uniform(50, 5000, n).round(2),
            'discounted_price': np.random.uniform(30, 4000, n).round(2),
            'rating': np.random.uniform(3.0, 5.0, n).round(1)
        }

        df = pd.DataFrame(data)
        df = self.process_products(df)

        return df


def main():
    """Função principal para execução standalone."""
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="Carregar e processar dados de produtos")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--bucket-name", required=True, help="Cloud Storage Bucket name")
    parser.add_argument("--download-kaggle", action="store_true", help="Baixar dataset do Kaggle")
    parser.add_argument("--sample-only", action="store_true", help="Usar apenas dados de exemplo")
    parser.add_argument("--sample-size", type=int, default=1000, help="Tamanho do sample")

    args = parser.parse_args()

    # Inicializar DataLoader
    loader = DataLoader(
        project_id=args.project_id,
        bucket_name=args.bucket_name
    )

    if args.sample_only:
        # Usar dados de exemplo
        df = loader.get_sample_data(n=args.sample_size)
    else:
        # Baixar do Kaggle se solicitado
        if args.download_kaggle:
            file_path = loader.download_kaggle_dataset()
        else:
            # Procurar arquivo local
            file_path = loader.local_data_path / "flipkart_com-ecommerce_sample.csv"
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {file_path}. "
                    "Use --download-kaggle para baixar."
                )

        # Carregar e processar
        df_raw = loader.load_csv(file_path)
        df = loader.process_products(df_raw)

    # Upload para GCS
    gcs_uri = loader.upload_to_gcs(df)

    # Estatísticas
    logger.info("\n" + "="*50)
    logger.info("ESTATÍSTICAS DO DATASET")
    logger.info("="*50)
    logger.info(f"Total de produtos: {len(df)}")
    logger.info(f"Colunas: {list(df.columns)}")
    if 'category' in df.columns:
        logger.info(f"\nCategorias:")
        logger.info(df['category'].value_counts().head())
    logger.info(f"\nDados salvos em: {gcs_uri}")
    logger.info("="*50)


if __name__ == "__main__":
    main()

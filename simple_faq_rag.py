"""
🤖 Sistema FAQ Simples com RAG

Sistema SIMPLIFICADO para buscar respostas em um CSV usando IA.

Como funciona:
1. Você tem um CSV com perguntas e respostas
2. O sistema transforma as perguntas em vetores (embeddings)
3. Quando você faz uma pergunta, ele busca a mais similar
4. Retorna a resposta correspondente

SEM complexidade! SEM LLM! Só busca semântica simples.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from google.cloud import aiplatform
from google.cloud import storage
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity
import json


class SimpleFAQSystem:
    """
    Sistema FAQ simples com busca semântica.

    Não usa LLM! Só busca a pergunta mais similar e retorna a resposta.
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        csv_path: Optional[str] = None
    ):
        """
        Inicializa o sistema FAQ.

        Args:
            project_id: ID do projeto Google Cloud
            location: Região (padrão: us-central1)
            csv_path: Caminho para o CSV com perguntas/respostas
        """
        self.project_id = project_id
        self.location = location
        self.csv_path = csv_path

        # Dados
        self.df = None  # DataFrame com perguntas/respostas
        self.embeddings = None  # Vetores das perguntas

        # Inicializar Vertex AI
        logger.info("Inicializando Vertex AI...")
        vertexai.init(project=project_id, location=location)
        aiplatform.init(project=project_id, location=location)

        # Modelo de embeddings
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

        logger.info("✅ Sistema FAQ inicializado!")

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Carrega CSV com perguntas e respostas.

        O CSV deve ter as colunas: 'pergunta' e 'resposta'

        Args:
            csv_path: Caminho para o arquivo CSV

        Returns:
            DataFrame carregado
        """
        logger.info(f"📂 Carregando CSV: {csv_path}")

        df = pd.read_csv(csv_path)

        # Validar colunas
        required_cols = ['pergunta', 'resposta']
        missing = [col for col in required_cols if col not in df.columns]

        if missing:
            raise ValueError(
                f"CSV deve ter colunas 'pergunta' e 'resposta'. "
                f"Faltando: {missing}"
            )

        # Remover linhas vazias
        df = df.dropna(subset=['pergunta', 'resposta'])

        # Adicionar ID
        df['id'] = [f"FAQ_{i:04d}" for i in range(len(df))]

        self.df = df

        logger.info(f"✅ {len(df)} perguntas carregadas")
        return df

    def generate_embeddings(self, texts: List[str], batch_size: int = 250) -> np.ndarray:
        """
        Gera embeddings para uma lista de textos.

        Args:
            texts: Lista de textos
            batch_size: Tamanho do lote (máx 250)

        Returns:
            Array numpy com embeddings
        """
        logger.info(f"🔄 Gerando embeddings para {len(texts)} textos...")

        embeddings = []

        # Processar em lotes
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Criar inputs
            inputs = [
                TextEmbeddingInput(text=text, task_type="RETRIEVAL_DOCUMENT")
                for text in batch
            ]

            # Gerar embeddings
            batch_embeddings = self.embedding_model.get_embeddings(inputs)
            batch_vectors = [emb.values for emb in batch_embeddings]

            embeddings.extend(batch_vectors)

            logger.info(f"  Processado lote {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

        embeddings_array = np.array(embeddings, dtype=np.float32)

        logger.info(f"✅ Embeddings gerados: {embeddings_array.shape}")

        return embeddings_array

    def create_knowledge_base(self):
        """
        Cria a base de conhecimento gerando embeddings de todas as perguntas.

        Isso precisa ser executado UMA vez antes de fazer buscas.
        """
        if self.df is None:
            raise ValueError("CSV não carregado! Execute load_csv() primeiro.")

        logger.info("🧠 Criando base de conhecimento...")

        # Gerar embeddings das perguntas
        perguntas = self.df['pergunta'].tolist()
        self.embeddings = self.generate_embeddings(perguntas)

        logger.info("✅ Base de conhecimento criada!")

    def search(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Busca perguntas similares à query.

        Args:
            query: Pergunta do usuário
            top_k: Quantas respostas retornar
            threshold: Score mínimo de similaridade (0-1)

        Returns:
            Lista de dicionários com pergunta, resposta e score
        """
        if self.embeddings is None:
            raise ValueError(
                "Base de conhecimento não criada! "
                "Execute create_knowledge_base() primeiro."
            )

        logger.info(f"🔍 Buscando: '{query}'")

        # Gerar embedding da query
        query_input = TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")
        query_emb = self.embedding_model.get_embeddings([query_input])[0]
        query_vector = np.array(query_emb.values, dtype=np.float32).reshape(1, -1)

        # Calcular similaridade com todas as perguntas
        similarities = cosine_similarity(query_vector, self.embeddings)[0]

        # Pegar top K
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Montar resultados
        results = []
        for idx in top_indices:
            score = float(similarities[idx])

            # Filtrar por threshold
            if score < threshold:
                continue

            results.append({
                'id': self.df.iloc[idx]['id'],
                'pergunta': self.df.iloc[idx]['pergunta'],
                'resposta': self.df.iloc[idx]['resposta'],
                'score': score,
                'confidence': self._score_to_confidence(score)
            })

        logger.info(f"✅ Encontradas {len(results)} respostas acima do threshold")

        return results

    def ask(self, query: str) -> Dict:
        """
        Faz uma pergunta e retorna a melhor resposta.

        Este é o método principal para usar o sistema!

        Args:
            query: Sua pergunta

        Returns:
            Dicionário com resposta, score, etc
        """
        results = self.search(query, top_k=1)

        if not results:
            return {
                'pergunta_encontrada': None,
                'resposta': "Desculpe, não encontrei uma resposta para essa pergunta.",
                'score': 0.0,
                'confidence': 'baixa',
                'found': False
            }

        best = results[0]
        return {
            'pergunta_encontrada': best['pergunta'],
            'resposta': best['resposta'],
            'score': best['score'],
            'confidence': best['confidence'],
            'found': True
        }

    def _score_to_confidence(self, score: float) -> str:
        """Converte score numérico em texto."""
        if score >= 0.9:
            return 'muito alta'
        elif score >= 0.8:
            return 'alta'
        elif score >= 0.7:
            return 'média'
        else:
            return 'baixa'

    def save_knowledge_base(self, output_path: str):
        """
        Salva a base de conhecimento em arquivo.

        Args:
            output_path: Caminho para salvar (sem extensão)
        """
        if self.embeddings is None or self.df is None:
            raise ValueError("Base de conhecimento não criada!")

        logger.info(f"💾 Salvando base de conhecimento...")

        # Salvar embeddings
        np.save(f"{output_path}_embeddings.npy", self.embeddings)

        # Salvar DataFrame
        self.df.to_csv(f"{output_path}_data.csv", index=False)

        logger.info(f"✅ Salvo em: {output_path}")

    def load_knowledge_base(self, input_path: str):
        """
        Carrega base de conhecimento salva.

        Args:
            input_path: Caminho base (sem extensão)
        """
        logger.info(f"📂 Carregando base de conhecimento...")

        # Carregar embeddings
        self.embeddings = np.load(f"{input_path}_embeddings.npy")

        # Carregar DataFrame
        self.df = pd.read_csv(f"{input_path}_data.csv")

        logger.info(f"✅ Base carregada: {len(self.df)} perguntas")

    def get_stats(self) -> Dict:
        """Retorna estatísticas da base de conhecimento."""
        if self.df is None:
            return {"status": "Nenhum dado carregado"}

        return {
            'total_perguntas': len(self.df),
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else None,
            'base_criada': self.embeddings is not None,
            'tamanho_memoria_mb': self.embeddings.nbytes / 1024 / 1024 if self.embeddings is not None else 0
        }


def demo():
    """Demonstração de uso do sistema."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("="*60)
    print("🤖 DEMO - Sistema FAQ Simples")
    print("="*60)

    # Configurar
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("❌ Configure PROJECT_ID no .env")
        return

    # Inicializar sistema
    print("\n1️⃣ Inicializando sistema...")
    faq = SimpleFAQSystem(project_id=project_id)

    # Carregar CSV (você precisa ter um!)
    csv_path = "data/faq_example.csv"
    if not Path(csv_path).exists():
        print(f"❌ CSV não encontrado: {csv_path}")
        print("Crie um CSV com colunas 'pergunta' e 'resposta'")
        return

    print(f"\n2️⃣ Carregando CSV...")
    faq.load_csv(csv_path)

    print(f"\n3️⃣ Criando base de conhecimento...")
    faq.create_knowledge_base()

    print(f"\n4️⃣ Fazendo perguntas de teste...")

    test_queries = [
        "Como redefinir senha?",
        "Qual o prazo de entrega?",
        "Como cancelar pedido?"
    ]

    for query in test_queries:
        print(f"\n❓ Pergunta: {query}")
        result = faq.ask(query)

        if result['found']:
            print(f"✅ Resposta ({result['confidence']} confiança):")
            print(f"   {result['resposta']}")
            print(f"   Score: {result['score']:.2%}")
        else:
            print("❌ Resposta não encontrada")

    print("\n" + "="*60)
    print("✅ Demo concluída!")
    print("="*60)


if __name__ == "__main__":
    demo()

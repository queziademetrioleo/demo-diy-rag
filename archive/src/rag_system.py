"""
Sistema RAG (Retrieval Augmented Generation) completo.

Este módulo integra:
- Vector Search para retrieval
- Gemini Pro para generation
- Prompt engineering e chain-of-thought
- Grounding e fact-checking
- Avaliação de resposta
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.language_models import TextGenerationModel
from loguru import logger

from embeddings import EmbeddingGenerator
from vector_search import VectorSearchManager


@dataclass
class RAGConfig:
    """Configuração do sistema RAG."""
    top_k: int = 5
    similarity_threshold: float = 0.7
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048
    llm_top_p: float = 0.8
    llm_top_k: int = 40
    enable_safety: bool = True
    enable_grounding_check: bool = True


class RAGSystem:
    """
    Sistema RAG completo para busca e geração de respostas.

    Attributes:
        project_id: ID do projeto Google Cloud
        location: Região do Google Cloud
        config: Configuração do RAG
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        bucket_name: str = None,
        endpoint_name: str = "produtos-endpoint",
        deployed_index_id: str = "deployed_produtos_index",
        llm_model: str = "gemini-1.5-pro",
        config: Optional[RAGConfig] = None
    ):
        """
        Inicializa o sistema RAG.

        Args:
            project_id: ID do projeto Google Cloud
            location: Região do Google Cloud
            bucket_name: Nome do bucket com dados
            endpoint_name: Nome do endpoint do Vector Search
            deployed_index_id: ID do índice deployado
            llm_model: Modelo LLM a usar (gemini-1.5-pro, gemini-pro, etc)
            config: Configuração do RAG
        """
        self.project_id = project_id
        self.location = location
        self.bucket_name = bucket_name or f"{project_id}-data"
        self.endpoint_name = endpoint_name
        self.deployed_index_id = deployed_index_id
        self.llm_model_name = llm_model

        # Configuração
        self.config = config or RAGConfig()

        # Inicializar Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Inicializar componentes
        self.embedding_generator = EmbeddingGenerator(
            project_id=project_id,
            location=location
        )

        self.vector_search_manager = VectorSearchManager(
            project_id=project_id,
            location=location,
            endpoint_display_name=endpoint_name
        )

        # Carregar endpoint
        self.endpoint = self._load_endpoint()

        # Inicializar LLM
        self.llm = self._initialize_llm()

        # Carregar metadata (se disponível)
        self.metadata_df = None
        try:
            self._load_metadata()
        except Exception as e:
            logger.warning(f"Não foi possível carregar metadata: {e}")

        logger.info(f"RAGSystem inicializado com modelo: {llm_model}")

    def _load_endpoint(self):
        """Carrega endpoint do Vector Search."""
        try:
            endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
                filter=f'display_name="{self.endpoint_name}"'
            )

            if not endpoints:
                raise ValueError(
                    f"Endpoint '{self.endpoint_name}' não encontrado. "
                    "Execute o setup do Vector Search primeiro."
                )

            endpoint = endpoints[0]
            logger.info(f"Endpoint carregado: {endpoint.resource_name}")
            return endpoint

        except Exception as e:
            logger.error(f"Erro ao carregar endpoint: {e}")
            raise

    def _initialize_llm(self):
        """Inicializa modelo de linguagem."""
        try:
            if "gemini" in self.llm_model_name.lower():
                # Usar Gemini
                model = GenerativeModel(self.llm_model_name)
                logger.info(f"Modelo Gemini carregado: {self.llm_model_name}")
            else:
                # Usar modelos Text (text-bison, etc)
                model = TextGenerationModel.from_pretrained(self.llm_model_name)
                logger.info(f"Modelo Text carregado: {self.llm_model_name}")

            return model

        except Exception as e:
            logger.error(f"Erro ao inicializar LLM: {e}")
            raise

    def _load_metadata(self):
        """Carrega metadata dos produtos."""
        try:
            _, metadata = self.embedding_generator.load_embeddings_from_gcs(
                bucket_name=self.bucket_name
            )
            self.metadata_df = metadata
            logger.info(f"Metadata carregada: {len(metadata)} itens")

        except Exception as e:
            logger.warning(f"Metadata não disponível: {e}")
            self.metadata_df = None

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Busca documentos relevantes usando Vector Search.

        Args:
            query: Query de busca
            top_k: Número de resultados (usa config se None)
            filters: Filtros adicionais (ex: categoria, marca)

        Returns:
            Lista de documentos relevantes com metadata
        """
        top_k = top_k or self.config.top_k

        logger.info(f"Buscando documentos para: '{query[:50]}...'")

        # Gerar embedding da query
        query_embedding = self.embedding_generator.generate_query_embedding(query)

        # Preparar filtros
        filter_restrictions = None
        if filters:
            filter_restrictions = [
                {"namespace": key, "allow_list": [value]}
                for key, value in filters.items()
            ]

        # Buscar no Vector Search
        results = self.vector_search_manager.search(
            endpoint=self.endpoint,
            query_embedding=query_embedding,
            deployed_index_id=self.deployed_index_id,
            num_neighbors=top_k,
            filter_restrictions=filter_restrictions
        )

        # Enriquecer com metadata
        enriched_results = self._enrich_with_metadata(results)

        # Filtrar por threshold de similaridade
        filtered_results = [
            r for r in enriched_results
            if r['distance'] >= self.config.similarity_threshold
        ]

        logger.info(
            f"Retrieval concluído: {len(filtered_results)}/{len(results)} "
            f"documentos acima do threshold"
        )

        return filtered_results

    def _enrich_with_metadata(self, results: List[Dict]) -> List[Dict]:
        """
        Enriquece resultados com metadata.

        Args:
            results: Resultados do Vector Search

        Returns:
            Resultados enriquecidos
        """
        if self.metadata_df is None:
            return results

        enriched = []
        for result in results:
            product_id = result['id']

            # Buscar metadata
            metadata_row = self.metadata_df[
                self.metadata_df['product_id'] == product_id
            ]

            if not metadata_row.empty:
                metadata = metadata_row.iloc[0].to_dict()

                enriched.append({
                    **result,
                    'metadata': metadata
                })
            else:
                enriched.append(result)

        return enriched

    def generate_prompt(
        self,
        query: str,
        context_docs: List[Dict],
        instruction: Optional[str] = None
    ) -> str:
        """
        Gera prompt para o LLM com contexto RAG.

        Args:
            query: Query do usuário
            context_docs: Documentos de contexto
            instruction: Instrução adicional (opcional)

        Returns:
            Prompt formatado
        """
        # Instrução base
        base_instruction = instruction or """
Você é um assistente especializado em produtos de e-commerce. Sua função é ajudar
clientes a encontrar produtos e responder perguntas sobre o catálogo.

REGRAS IMPORTANTES:
1. Use APENAS informações dos produtos fornecidos abaixo
2. Se a informação não estiver nos produtos, diga "Não encontrei essa informação"
3. Seja preciso e objetivo
4. Cite os produtos relevantes quando apropriado
5. Se houver preços, sempre mencione em Reais (R$)
"""

        # Formatar documentos de contexto
        context_text = "\n\n".join([
            self._format_document(doc, idx + 1)
            for idx, doc in enumerate(context_docs)
        ])

        # Montar prompt completo
        prompt = f"""{base_instruction.strip()}

PRODUTOS DISPONÍVEIS:
{context_text}

PERGUNTA DO CLIENTE:
{query}

RESPOSTA:"""

        return prompt

    def _format_document(self, doc: Dict, index: int) -> str:
        """
        Formata documento para inclusão no prompt.

        Args:
            doc: Documento com metadata
            index: Índice do documento

        Returns:
            Texto formatado
        """
        metadata = doc.get('metadata', {})

        # Extrair campos principais
        name = metadata.get('name', 'Produto sem nome')
        description = metadata.get('description', '')
        category = metadata.get('category', 'N/A')
        brand = metadata.get('brand', 'N/A')
        price = metadata.get('price', metadata.get('discounted_price', 0))
        rating = metadata.get('rating', 'N/A')

        # Formatar
        formatted = f"""[{index}] {name}
- Categoria: {category}
- Marca: {brand}
- Preço: R$ {price:.2f}
- Avaliação: {rating}
- Descrição: {description[:200]}..."""

        return formatted

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Gera resposta usando LLM.

        Args:
            prompt: Prompt de entrada
            temperature: Temperature para sampling (usa config se None)
            max_tokens: Máximo de tokens (usa config se None)

        Returns:
            Resposta gerada
        """
        temperature = temperature or self.config.llm_temperature
        max_tokens = max_tokens or self.config.llm_max_tokens

        logger.info("Gerando resposta com LLM...")

        try:
            if "gemini" in self.llm_model_name.lower():
                # Usar Gemini
                generation_config = GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=self.config.llm_top_p,
                    top_k=self.config.llm_top_k
                )

                response = self.llm.generate_content(
                    prompt,
                    generation_config=generation_config
                )

                answer = response.text

            else:
                # Usar modelos Text
                response = self.llm.predict(
                    prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=self.config.llm_top_p,
                    top_k=self.config.llm_top_k
                )

                answer = response.text

            logger.info(f"Resposta gerada: {len(answer)} caracteres")

            return answer

        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return "Desculpe, ocorreu um erro ao gerar a resposta."

    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict] = None,
        return_sources: bool = True
    ) -> Dict:
        """
        Executa query RAG completa (retrieve + generate).

        Args:
            query: Pergunta do usuário
            top_k: Número de documentos a recuperar
            filters: Filtros de busca
            return_sources: Incluir fontes na resposta

        Returns:
            Dicionário com resposta e metadata
        """
        logger.info(f"Query RAG: '{query}'")

        # 1. Retrieve
        context_docs = self.retrieve(
            query=query,
            top_k=top_k,
            filters=filters
        )

        if not context_docs:
            return {
                "answer": "Desculpe, não encontrei produtos relevantes para sua pergunta.",
                "sources": [],
                "context_used": 0
            }

        # 2. Generate prompt
        prompt = self.generate_prompt(
            query=query,
            context_docs=context_docs
        )

        # 3. Generate answer
        answer = self.generate(prompt)

        # 4. Preparar resposta
        response = {
            "answer": answer,
            "context_used": len(context_docs)
        }

        if return_sources:
            response["sources"] = [
                {
                    "product_id": doc.get('id'),
                    "name": doc.get('metadata', {}).get('name'),
                    "relevance_score": doc.get('distance')
                }
                for doc in context_docs[:3]  # Top 3 apenas
            ]

        return response

    def batch_query(self, queries: List[str]) -> List[Dict]:
        """
        Processa múltiplas queries em lote.

        Args:
            queries: Lista de queries

        Returns:
            Lista de respostas
        """
        logger.info(f"Processando {len(queries)} queries em lote...")

        responses = []
        for query in queries:
            response = self.query(query)
            responses.append(response)

        return responses

    def evaluate_response(
        self,
        query: str,
        answer: str,
        ground_truth: Optional[str] = None
    ) -> Dict:
        """
        Avalia qualidade da resposta.

        Args:
            query: Query original
            answer: Resposta gerada
            ground_truth: Resposta esperada (opcional)

        Returns:
            Métricas de avaliação
        """
        metrics = {
            "answer_length": len(answer),
            "has_content": len(answer.strip()) > 0,
            "contains_apology": "desculpe" in answer.lower()
        }

        # Avaliar grounding (se tiver contexto)
        if self.config.enable_grounding_check:
            metrics["grounding_score"] = self._check_grounding(answer)

        return metrics

    def _check_grounding(self, answer: str) -> float:
        """
        Verifica se resposta está fundamentada nos documentos.

        Args:
            answer: Resposta a verificar

        Returns:
            Score de grounding (0-1)
        """
        # Implementação simplificada
        # Em produção, usar técnicas mais sofisticadas
        keywords_found = 0
        important_keywords = ["r$", "produto", "categoria", "marca", "preço"]

        for keyword in important_keywords:
            if keyword in answer.lower():
                keywords_found += 1

        return keywords_found / len(important_keywords)


def main():
    """Função principal para demonstração."""
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="Sistema RAG para produtos")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--location", default="us-central1", help="GCP location")
    parser.add_argument("--query", required=True, help="Query de busca")
    parser.add_argument("--top-k", type=int, default=5, help="Número de resultados")

    args = parser.parse_args()

    # Inicializar sistema
    rag = RAGSystem(
        project_id=args.project_id,
        location=args.location
    )

    # Executar query
    result = rag.query(
        query=args.query,
        top_k=args.top_k
    )

    # Exibir resultado
    logger.info("\n" + "="*50)
    logger.info("RESULTADO DA QUERY RAG")
    logger.info("="*50)
    logger.info(f"\nQuery: {args.query}")
    logger.info(f"\nResposta:\n{result['answer']}")

    if result.get('sources'):
        logger.info(f"\nFontes utilizadas:")
        for idx, source in enumerate(result['sources'], 1):
            logger.info(
                f"  {idx}. {source['name']} "
                f"(score: {source['relevance_score']:.3f})"
            )

    logger.info(f"\nContexto usado: {result['context_used']} documentos")
    logger.info("="*50)


if __name__ == "__main__":
    main()

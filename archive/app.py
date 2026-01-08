"""
🤖 Chat App Interativo - Sistema RAG de Produtos

Aplicação web para testar o sistema RAG de forma interativa.
Interface tipo ChatGPT para fazer perguntas sobre produtos.

Uso:
    streamlit run app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path
from typing import Optional
import time

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.rag_system import RAGSystem, RAGConfig
from loguru import logger

# Configuração da página
st.set_page_config(
    page_title="RAG Product Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
    }
    .chat-message.assistant {
        background-color: #f5f5f5;
    }
    .source-box {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-top: 0.5rem;
        font-size: 0.9em;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Inicializa variáveis de sessão."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None

    if 'initialized' not in st.session_state:
        st.session_state.initialized = False

    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0


def initialize_rag_system(
    project_id: str,
    location: str,
    bucket_name: str,
    temperature: float,
    top_k: int
) -> Optional[RAGSystem]:
    """Inicializa o sistema RAG."""
    try:
        with st.spinner("🔄 Inicializando sistema RAG... (pode levar alguns segundos)"):
            config = RAGConfig(
                top_k=top_k,
                llm_temperature=temperature,
                similarity_threshold=0.7
            )

            rag = RAGSystem(
                project_id=project_id,
                location=location,
                bucket_name=bucket_name,
                config=config
            )

            st.success("✅ Sistema RAG inicializado com sucesso!")
            return rag

    except Exception as e:
        st.error(f"❌ Erro ao inicializar sistema RAG: {e}")
        st.info("💡 Verifique se o Vector Search foi deployado e se as credenciais estão corretas.")
        logger.error(f"Erro na inicialização: {e}")
        return None


def display_message(role: str, content: str, sources: Optional[list] = None):
    """Exibe uma mensagem no chat."""

    icon = "👤" if role == "user" else "🤖"
    css_class = "user" if role == "user" else "assistant"

    with st.container():
        st.markdown(f"""
        <div class="chat-message {css_class}">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5em; margin-right: 0.5rem;">{icon}</span>
                <strong>{"Você" if role == "user" else "Assistente"}</strong>
            </div>
            <div>{content}</div>
        </div>
        """, unsafe_allow_html=True)

        # Exibir fontes se disponíveis
        if sources and role == "assistant":
            with st.expander("📚 Ver fontes utilizadas", expanded=False):
                for idx, source in enumerate(sources, 1):
                    st.markdown(f"""
                    **{idx}. {source.get('name', 'N/A')}**
                    - Relevância: {source.get('relevance_score', 0):.2%}
                    - ID: `{source.get('product_id', 'N/A')}`
                    """)


def main():
    """Função principal da aplicação."""

    # Carregar variáveis de ambiente
    load_dotenv()

    # Inicializar session state
    initialize_session_state()

    # Header
    st.title("🛍️ Assistente de Produtos com IA")
    st.markdown("Faça perguntas sobre nosso catálogo de produtos usando linguagem natural!")

    # Sidebar - Configurações
    with st.sidebar:
        st.header("⚙️ Configurações")

        # Configurações do GCP
        st.subheader("Google Cloud")
        project_id = st.text_input(
            "Project ID",
            value=os.getenv("PROJECT_ID", ""),
            help="ID do projeto Google Cloud"
        )

        location = st.text_input(
            "Location",
            value=os.getenv("LOCATION", "us-central1"),
            help="Região do Google Cloud"
        )

        bucket_name = st.text_input(
            "Bucket Name",
            value=os.getenv("BUCKET_NAME", ""),
            help="Nome do bucket no Cloud Storage"
        )

        st.divider()

        # Configurações do RAG
        st.subheader("Parâmetros do RAG")

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.1,
            help="Controla a criatividade das respostas. Menor = mais consistente."
        )

        top_k = st.slider(
            "Top K Produtos",
            min_value=1,
            max_value=10,
            value=5,
            help="Número de produtos a buscar"
        )

        st.divider()

        # Botão de inicialização
        if st.button("🚀 Inicializar Sistema", type="primary", use_container_width=True):
            if not project_id or not bucket_name:
                st.error("⚠️ Por favor, preencha Project ID e Bucket Name")
            else:
                st.session_state.rag_system = initialize_rag_system(
                    project_id=project_id,
                    location=location,
                    bucket_name=bucket_name,
                    temperature=temperature,
                    top_k=top_k
                )
                st.session_state.initialized = True

        # Status
        st.divider()
        st.subheader("📊 Status")

        if st.session_state.initialized and st.session_state.rag_system:
            st.success("✅ Sistema Online")
            st.metric("Queries Realizadas", st.session_state.query_count)
        else:
            st.warning("⚠️ Sistema Offline")
            st.info("👆 Clique em 'Inicializar Sistema' para começar")

        # Exemplos de perguntas
        st.divider()
        st.subheader("💡 Exemplos de Perguntas")
        st.markdown("""
        - Quero um smartphone com boa câmera
        - Notebooks até R$ 3000
        - Produtos da marca Samsung
        - Quais tênis de corrida você tem?
        - Me recomende um presente de tecnologia
        """)

        # Limpar chat
        if st.button("🗑️ Limpar Conversa", use_container_width=True):
            st.session_state.messages = []
            st.session_state.query_count = 0
            st.rerun()

    # Área principal - Chat

    # Container de mensagens
    messages_container = st.container()

    with messages_container:
        # Exibir histórico de mensagens
        for message in st.session_state.messages:
            display_message(
                role=message["role"],
                content=message["content"],
                sources=message.get("sources")
            )

    # Input de query
    st.divider()

    # Verificar se sistema está inicializado
    if not st.session_state.initialized or not st.session_state.rag_system:
        st.info("ℹ️ Configure e inicialize o sistema na barra lateral para começar.")

        # Mostrar instruções
        with st.expander("📖 Como usar", expanded=True):
            st.markdown("""
            ### Passo a Passo:

            1. **Configure o Google Cloud** na barra lateral:
               - Preencha o Project ID
               - Confirme a Location (us-central1)
               - Preencha o Bucket Name

            2. **Ajuste os parâmetros** (opcional):
               - Temperature: controla criatividade
               - Top K: quantos produtos buscar

            3. **Clique em "Inicializar Sistema"**
               - Aguarde a inicialização (pode levar alguns segundos)

            4. **Comece a conversar!**
               - Digite sua pergunta na caixa abaixo
               - Pressione Enter ou clique em Enviar

            ### Requisitos:
            - ✅ Vector Search deployado
            - ✅ Embeddings criados
            - ✅ Autenticação configurada (`gcloud auth`)
            """)
    else:
        # Chat input
        query = st.chat_input("Digite sua pergunta sobre produtos...")

        if query:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({
                "role": "user",
                "content": query
            })

            # Exibir mensagem do usuário
            with messages_container:
                display_message("user", query)

            # Processar query
            try:
                with st.spinner("🤔 Pensando..."):
                    start_time = time.time()

                    # Executar RAG
                    result = st.session_state.rag_system.query(
                        query=query,
                        top_k=top_k,
                        return_sources=True
                    )

                    elapsed_time = time.time() - start_time

                    # Adicionar resposta do assistente
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result.get("sources", [])
                    })

                    # Incrementar contador
                    st.session_state.query_count += 1

                    # Exibir resposta
                    with messages_container:
                        display_message(
                            "assistant",
                            result["answer"],
                            sources=result.get("sources")
                        )

                    # Exibir métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("⏱️ Tempo de Resposta", f"{elapsed_time:.2f}s")
                    with col2:
                        st.metric("📚 Documentos Usados", result.get("context_used", 0))
                    with col3:
                        st.metric("🎯 Fontes Citadas", len(result.get("sources", [])))

                    # Rerun para atualizar interface
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Erro ao processar query: {e}")
                logger.error(f"Erro na query: {e}")

                # Mostrar detalhes técnicos em expander
                with st.expander("🔍 Detalhes Técnicos do Erro"):
                    st.code(str(e))
                    st.markdown("**Possíveis causas:**")
                    st.markdown("""
                    - Vector Search não está deployado
                    - Endpoint não foi encontrado
                    - Problemas de autenticação
                    - Quota excedida
                    """)


if __name__ == "__main__":
    main()

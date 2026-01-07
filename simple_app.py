"""
🤖 Chat App SIMPLES - Sistema FAQ

Interface web simplificada para testar o sistema FAQ.
Sem complexidade! Fácil de entender e usar.
"""

import streamlit as st
import sys
from pathlib import Path
import os
import time

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from simple_faq_rag import SimpleFAQSystem

# Configuração da página
st.set_page_config(
    page_title="FAQ Assistant - Simples",
    page_icon="💬",
    layout="wide"
)

# CSS simples
st.markdown("""
<style>
    .user-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .bot-message {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .confidence-high { color: #4caf50; font-weight: bold; }
    .confidence-medium { color: #ff9800; font-weight: bold; }
    .confidence-low { color: #f44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inicializa variáveis de sessão."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'faq_system' not in st.session_state:
        st.session_state.faq_system = None

    if 'initialized' not in st.session_state:
        st.session_state.initialized = False

    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0


def initialize_system(project_id: str, csv_path: str):
    """Inicializa o sistema FAQ."""
    try:
        with st.spinner("🔄 Inicializando sistema..."):
            # Criar sistema
            faq = SimpleFAQSystem(project_id=project_id)

            # Carregar CSV
            faq.load_csv(csv_path)

            # Criar base de conhecimento
            st.info("⏳ Criando base de conhecimento... (1-2 minutos)")
            faq.create_knowledge_base()

            st.success("✅ Sistema pronto!")
            return faq

    except Exception as e:
        st.error(f"❌ Erro: {e}")
        return None


def display_message(role: str, content: str, metadata: dict = None):
    """Exibe mensagem no chat."""

    if role == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>👤 Você:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)

    else:  # assistant
        confidence_class = f"confidence-{metadata.get('confidence', 'low').replace(' ', '-')}"

        st.markdown(f"""
        <div class="bot-message">
            <strong>🤖 Assistente:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)

        if metadata and metadata.get('found'):
            with st.expander("📊 Detalhes da resposta", expanded=False):
                st.write(f"**Confiança:** {metadata.get('confidence', 'N/A')}")
                st.write(f"**Score:** {metadata.get('score', 0):.1%}")
                st.write(f"**Pergunta original:** {metadata.get('pergunta_encontrada', 'N/A')}")


def main():
    """Função principal do app."""

    load_dotenv()
    init_session_state()

    # Header
    st.title("💬 FAQ Assistant - Versão Simples")
    st.markdown("Faça perguntas e receba respostas da base de conhecimento!")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuração")

        # Configurações
        project_id = st.text_input(
            "Project ID",
            value=os.getenv("PROJECT_ID", ""),
            help="ID do projeto Google Cloud"
        )

        csv_path = st.text_input(
            "Caminho do CSV",
            value="data/faq_example.csv",
            help="Caminho para o arquivo CSV com perguntas/respostas"
        )

        st.divider()

        # Botão inicializar
        if st.button("🚀 Inicializar Sistema", type="primary"):
            if not project_id:
                st.error("⚠️ Preencha o Project ID")
            elif not Path(csv_path).exists():
                st.error(f"⚠️ CSV não encontrado: {csv_path}")
            else:
                st.session_state.faq_system = initialize_system(project_id, csv_path)
                if st.session_state.faq_system:
                    st.session_state.initialized = True
                    st.rerun()

        # Status
        st.divider()
        st.subheader("📊 Status")

        if st.session_state.initialized:
            st.success("✅ Sistema Online")
            st.metric("Perguntas Feitas", st.session_state.total_queries)

            if st.session_state.faq_system:
                stats = st.session_state.faq_system.get_stats()
                st.metric("Base de Dados", f"{stats['total_perguntas']} perguntas")
        else:
            st.warning("⚠️ Sistema Offline")
            st.info("👆 Clique em 'Inicializar Sistema'")

        # Exemplos
        st.divider()
        st.subheader("💡 Exemplos")
        st.markdown("""
        - Como redefinir senha?
        - Qual o prazo de entrega?
        - Vocês aceitam PIX?
        - Como rastrear pedido?
        """)

        # Limpar
        if st.button("🗑️ Limpar Chat"):
            st.session_state.messages = []
            st.session_state.total_queries = 0
            st.rerun()

    # Área principal
    if not st.session_state.initialized:
        st.info("ℹ️ Configure e inicialize o sistema na barra lateral")

        with st.expander("📖 Como usar", expanded=True):
            st.markdown("""
            ### Passo a Passo:

            1. **Configure o Project ID** na barra lateral
            2. **Verifique o caminho do CSV** (padrão já incluso!)
            3. **Clique em "Inicializar Sistema"**
            4. **Aguarde** a criação da base (1-2 minutos)
            5. **Comece a perguntar!**

            ### Formato do CSV:

            Seu CSV deve ter duas colunas:
            - `pergunta`: A pergunta
            - `resposta`: A resposta correspondente

            Exemplo incluído em: `data/faq_example.csv`
            """)

    else:
        # Container de mensagens
        messages_container = st.container()

        with messages_container:
            for message in st.session_state.messages:
                display_message(
                    role=message["role"],
                    content=message["content"],
                    metadata=message.get("metadata")
                )

        # Input
        st.divider()

        question = st.chat_input("Digite sua pergunta...")

        if question:
            # Adicionar pergunta do usuário
            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            # Exibir pergunta
            with messages_container:
                display_message("user", question)

            # Processar
            try:
                with st.spinner("🤔 Pensando..."):
                    start_time = time.time()

                    result = st.session_state.faq_system.ask(question)

                    elapsed = time.time() - start_time

                # Adicionar resposta
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result['resposta'],
                    "metadata": result
                })

                # Incrementar contador
                st.session_state.total_queries += 1

                # Exibir resposta
                with messages_container:
                    display_message(
                        "assistant",
                        result['resposta'],
                        metadata=result
                    )

                # Métricas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⏱️ Tempo", f"{elapsed:.2f}s")
                with col2:
                    st.metric("🎯 Confiança", result.get('confidence', 'N/A'))
                with col3:
                    st.metric("📊 Score", f"{result.get('score', 0):.0%}")

                st.rerun()

            except Exception as e:
                st.error(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()

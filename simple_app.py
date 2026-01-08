"""
🤖 Chat App SIMPLES - Sistema FAQ
Carrega automaticamente do Cloud Storage - PRONTO PARA USO!
"""

import streamlit as st
import sys
from pathlib import Path
import os
import tempfile
import numpy as np
from google.cloud import storage
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Adicionar diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

from simple_faq_rag import SimpleFAQSystem

# ============================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================

st.set_page_config(
    page_title="FAQ Assistant",
    page_icon="💬",
    layout="centered"
)

# ============================================
# CARREGAR SISTEMA AUTOMATICAMENTE (CACHE)
# ============================================

# Versão do código (incrementar quando atualizar simple_faq_rag.py)
CODE_VERSION = "2.0.0-llm"

@st.cache_resource(show_spinner="🚀 Carregando FAQ do Cloud Storage...")
def load_faq_system(_version):
    """
    Carrega o sistema FAQ automaticamente do Cloud Storage.
    Usa cache para não recarregar toda vez.

    Args:
        _version: Versão do código (força reload quando muda)
    """
    project_id = os.getenv("PROJECT_ID")
    bucket_name = os.getenv("BUCKET_NAME")

    if not project_id or not bucket_name:
        st.error("❌ Configure .env com PROJECT_ID e BUCKET_NAME")
        st.stop()

    # Inicializar Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Download embeddings
    embeddings_blob = bucket.blob("embeddings/faq_embeddings.npy")
    temp_embeddings = tempfile.NamedTemporaryFile(delete=False, suffix='.npy')
    embeddings_blob.download_to_filename(temp_embeddings.name)

    # Download metadata
    metadata_blob = bucket.blob("knowledge_base/faq_metadata.csv")
    temp_metadata = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    metadata_blob.download_to_filename(temp_metadata.name)

    # Criar sistema
    faq = SimpleFAQSystem(project_id=project_id)
    faq.load_csv(temp_metadata.name)
    faq.embeddings = np.load(temp_embeddings.name)

    return faq

# Carregar sistema (só executa 1 vez graças ao cache)
# Passa CODE_VERSION para forçar reload quando código muda
faq_system = load_faq_system(CODE_VERSION)

# ============================================
# HEADER
# ============================================

st.title("💬 FAQ Assistant com IA")
st.markdown(f"*RAG com Gemini • {len(faq_system.df)} perguntas na base*")
st.markdown("---")

# ============================================
# SESSION STATE
# ============================================

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ============================================
# SIDEBAR - INFO
# ============================================

with st.sidebar:
    st.header("ℹ️ Informações")

    st.success("🟢 Sistema Online")
    st.metric("Perguntas disponíveis", len(faq_system.df))

    st.markdown("---")
    st.caption("**Project ID:**")
    st.code(os.getenv("PROJECT_ID", "N/A"))

    st.markdown("---")

    # Botão para limpar conversa
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

    # Botão para recarregar sistema (limpar cache)
    if st.button("🔄 Recarregar Sistema", help="Limpa cache e recarrega código atualizado"):
        st.cache_resource.clear()
        st.rerun()

    st.markdown("---")

    # Info sobre RAG
    with st.expander("ℹ️ Como funciona"):
        st.markdown("""
**RAG (Retrieval Augmented Generation):**

1. **Retrieval** 🔍
   - Busca FAQs relevantes usando embeddings

2. **Generation** 🤖
   - Gemini gera resposta baseada nos FAQs
   - Grounded em dados reais
   - Prompt engineering aplicado

3. **Output Filtering** ✅
   - Filtra informações sensíveis
   - Safety settings ativados
        """)

    st.markdown("---")
    st.caption("☁️ Powered by Vertex AI + Gemini")

# ============================================
# CHAT PRINCIPAL
# ============================================

# Mostrar histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "score" in msg:
            score = msg["score"]
            if score >= 0.8:
                st.markdown(f"**Confiança:** :green[{score:.0%}]")
            elif score >= 0.6:
                st.markdown(f"**Confiança:** :orange[{score:.0%}]")
            else:
                st.markdown(f"**Confiança:** :red[{score:.0%}]")

# Input do usuário
if prompt := st.chat_input("Digite sua pergunta..."):

    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Buscar resposta
    with st.chat_message("assistant"):
        with st.spinner("🤖 Processando com IA..."):
            try:
                # Usar RAG completo com LLM (Gemini)
                result = faq_system.ask_with_llm(prompt)

                if result['found']:
                    # Resposta gerada pelo LLM
                    resposta_gerada = result['resposta_gerada']
                    score = result['score']

                    # Mostrar resposta gerada
                    st.markdown(resposta_gerada)

                    # Mostrar fonte (FAQ original) em expander
                    with st.expander("📚 Ver FAQ original"):
                        st.markdown(f"**Pergunta encontrada:** {result['pergunta_encontrada']}")
                        st.markdown(f"**Resposta original:** {result['resposta_original']}")
                        st.caption(f"✨ Resposta reformulada por IA (Gemini)")

                    # Mostrar confiança
                    if score >= 0.8:
                        st.markdown(f"**Confiança:** :green[{score:.0%}]")
                    elif score >= 0.6:
                        st.markdown(f"**Confiança:** :orange[{score:.0%}]")
                    else:
                        st.markdown(f"**Confiança:** :red[{score:.0%}]")

                    # Salvar no histórico
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": resposta_gerada,
                        "score": score
                    })
                else:
                    msg = result.get('resposta_gerada', "Desculpe, não encontrei uma resposta relevante para essa pergunta. 😕")
                    st.markdown(msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": msg
                    })

            except Exception as e:
                error_msg = f"❌ Erro ao buscar resposta: {e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.caption("🤖 RAG (Retrieval Augmented Generation) • Powered by Vertex AI + Gemini 1.5 Flash")

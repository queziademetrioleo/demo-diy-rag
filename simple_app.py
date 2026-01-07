"""
🤖 Chat App SIMPLES - Sistema FAQ
Interface web que carrega TUDO do Cloud Storage automaticamente
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

st.title("💬 Sistema FAQ Simples")
st.markdown("*Carrega automaticamente do Cloud Storage*")
st.markdown("---")

# ============================================
# SESSION STATE
# ============================================

if 'faq_system' not in st.session_state:
    st.session_state.faq_system = None

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ============================================
# FUNÇÕES DE CLOUD STORAGE
# ============================================

def download_from_bucket(bucket_name: str, blob_path: str) -> str:
    """Baixa arquivo do bucket para arquivo temporário"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    blob.download_to_filename(temp_file.name)

    return temp_file.name

def load_from_bucket_processed(bucket_name: str, project_id: str):
    """
    Carrega base de conhecimento JÁ PROCESSADA do bucket.
    Muito mais rápido que processar do zero!
    """
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

    # Carregar dados processados
    faq.load_csv(temp_metadata.name)
    faq.embeddings = np.load(temp_embeddings.name)

    return faq

# ============================================
# SIDEBAR - CONFIGURAÇÃO
# ============================================

with st.sidebar:
    st.header("⚙️ Configuração")

    # Inputs (do .env)
    project_id = st.text_input(
        "Project ID",
        value=os.getenv("PROJECT_ID", ""),
        help="ID do projeto Google Cloud"
    )

    bucket_name = st.text_input(
        "Bucket Name",
        value=os.getenv("BUCKET_NAME", ""),
        help="Nome do bucket do Cloud Storage"
    )

    st.markdown("---")

    # Opções de carregamento
    load_option = st.radio(
        "Modo de carregamento:",
        ["🚀 Base Processada (Rápido)", "📄 CSV do Zero (Lento)"],
        help="Base processada usa embeddings já salvos"
    )

    st.markdown("---")

    # Botão de inicialização
    if st.button("🚀 Inicializar Sistema", type="primary"):
        if not project_id or not bucket_name:
            st.error("❌ Configure PROJECT_ID e BUCKET_NAME!")
            st.stop()

        try:
            if load_option == "🚀 Base Processada (Rápido)":
                with st.spinner("📥 Baixando base processada do bucket..."):
                    faq = load_from_bucket_processed(bucket_name, project_id)

                st.success(f"✅ {len(faq.df)} perguntas carregadas do bucket!")
                st.info("⚡ Base de conhecimento já estava processada!")

            else:  # CSV do zero
                with st.spinner("📥 Baixando CSV do bucket..."):
                    raw_data_path = os.getenv("RAW_DATA_PATH", "raw_data/faq_demo.csv")
                    csv_file = download_from_bucket(bucket_name, raw_data_path)

                with st.spinner("🧠 Criando sistema..."):
                    faq = SimpleFAQSystem(project_id=project_id)
                    faq.load_csv(csv_file)

                st.success(f"✅ {len(faq.df)} perguntas carregadas")

                with st.spinner("⏳ Criando embeddings (2-3 min)..."):
                    faq.create_knowledge_base()

                st.success("✅ Embeddings criados!")

            # Salvar na sessão
            st.session_state.faq_system = faq
            st.balloons()

        except Exception as e:
            st.error(f"❌ Erro: {e}")
            st.session_state.faq_system = None

    # Status
    st.markdown("---")
    if st.session_state.faq_system is not None:
        st.success("🟢 Sistema Online")
        st.info(f"📊 {len(st.session_state.faq_system.df)} perguntas")
    else:
        st.warning("🔴 Sistema Offline")
        st.info("👆 Clique em 'Inicializar'")

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
    # Verificar se sistema está inicializado
    if st.session_state.faq_system is None:
        st.error("⚠️ Sistema não inicializado! Use o botão na sidebar.")
        st.stop()

    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Buscar resposta
    with st.chat_message("assistant"):
        with st.spinner("Buscando..."):
            try:
                result = st.session_state.faq_system.ask(prompt)

                if result['found']:
                    resposta = result['resposta']
                    score = result['score']

                    st.markdown(resposta)

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
                        "content": resposta,
                        "score": score
                    })
                else:
                    msg = "Desculpe, não encontrei uma resposta relevante. 😕"
                    st.markdown(msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": msg
                    })

            except Exception as e:
                error_msg = f"❌ Erro: {e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.caption("☁️ Powered by Google Cloud Storage + Vertex AI")

"""
🤖 Chat App SIMPLES - Sistema FAQ
Interface web para testar o sistema FAQ
"""

import streamlit as st
import sys
from pathlib import Path
import os

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
st.markdown("---")

# ============================================
# SESSION STATE
# ============================================

if 'faq_system' not in st.session_state:
    st.session_state.faq_system = None

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ============================================
# SIDEBAR - CONFIGURAÇÃO
# ============================================

with st.sidebar:
    st.header("⚙️ Configuração")

    # Inputs
    project_id = st.text_input(
        "Project ID",
        value=os.getenv("PROJECT_ID", "teste-de-big-query-472216"),
        help="ID do projeto Google Cloud"
    )

    csv_path = st.text_input(
        "Caminho do CSV",
        value="data/faq_example.csv",
        help="Caminho para o arquivo CSV com perguntas/respostas"
    )

    st.markdown("---")

    # Botão de inicialização
    if st.button("🚀 Inicializar Sistema", type="primary"):
        with st.spinner("Inicializando sistema..."):
            try:
                # Criar sistema
                faq = SimpleFAQSystem(project_id=project_id)

                # Carregar CSV
                faq.load_csv(csv_path)
                st.success(f"✅ {len(faq.df)} perguntas carregadas")

                # Criar base de conhecimento
                with st.spinner("Criando base de conhecimento (embeddings)..."):
                    faq.create_knowledge_base()

                # Salvar na sessão
                st.session_state.faq_system = faq
                st.success("✅ Sistema pronto!")
                st.balloons()

            except Exception as e:
                st.error(f"❌ Erro: {e}")
                st.session_state.faq_system = None

    # Status
    st.markdown("---")
    if st.session_state.faq_system is not None:
        st.success("🟢 Sistema Online")
        st.info(f"📊 {len(st.session_state.faq_system.df)} perguntas disponíveis")
    else:
        st.warning("🔴 Sistema Offline")
        st.info("👆 Clique em 'Inicializar Sistema'")

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
                    msg = "Desculpe, não encontrei uma resposta relevante para sua pergunta. 😕"
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
st.caption("💡 Sistema FAQ com IA - Vertex AI Embeddings")

#!/usr/bin/env python3
"""
Sistema FAQ com Gradio - Interface de Chat Simples e Moderna
Carrega automaticamente do Cloud Storage e responde perguntas usando RAG + LLM
"""

import gradio as gr
import os
import tempfile
import numpy as np
from dotenv import load_dotenv
from google.cloud import storage
from simple_faq_rag import SimpleFAQSystem

# Versão do código (para forçar reload se necessário)
VERSION = "3.0.0-gradio"

def load_faq_from_bucket():
    """Carrega FAQ automaticamente do Cloud Storage."""
    load_dotenv()

    project_id = os.getenv('PROJECT_ID')
    bucket_name = os.getenv('BUCKET_NAME')

    if not project_id or not bucket_name:
        raise ValueError("❌ Configure PROJECT_ID e BUCKET_NAME no arquivo .env")

    print(f"🚀 Carregando FAQ do bucket: gs://{bucket_name}")

    # Inicializar sistema
    faq = SimpleFAQSystem(project_id=project_id)

    # Cliente do Cloud Storage
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Download embeddings
    print("📥 Baixando embeddings...")
    embeddings_blob = bucket.blob("embeddings/faq_embeddings.npy")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.npy') as tmp_emb:
        embeddings_blob.download_to_filename(tmp_emb.name)
        faq.embeddings = np.load(tmp_emb.name)
        print(f"   ✅ {faq.embeddings.shape[0]} embeddings carregados")

    # Download metadata
    print("📥 Baixando metadados...")
    metadata_blob = bucket.blob("knowledge_base/faq_metadata.csv")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_meta:
        metadata_blob.download_to_filename(tmp_meta.name)
        faq.load_csv(tmp_meta.name)
        print(f"   ✅ {len(faq.faqs)} perguntas carregadas")

    print("✅ Sistema FAQ pronto para uso!\n")
    return faq


def chat_function(message, history):
    """
    Função de chat que processa mensagens do usuário.

    Args:
        message: Mensagem do usuário
        history: Histórico do chat (gerenciado automaticamente pelo Gradio)

    Returns:
        Resposta do sistema
    """
    try:
        # Usar RAG completo com LLM
        result = faq_system.ask_with_llm(message)

        if result['found']:
            # Resposta gerada pelo LLM
            response = result['resposta_gerada']

            # Adicionar informações extras
            confidence = result['confidence']
            score = result['score']
            pergunta_original = result['pergunta_encontrada']

            # Formatar resposta com metadados
            response_formatted = f"{response}\n\n"
            response_formatted += f"---\n"
            response_formatted += f"📊 **Confiança:** {confidence} ({score:.0%})\n"
            response_formatted += f"📚 **Fonte:** {pergunta_original}"

            return response_formatted
        else:
            # Sem resultados relevantes
            return result['resposta_gerada']

    except Exception as e:
        return f"❌ Erro ao processar pergunta: {str(e)}\n\nTente novamente ou reformule sua pergunta."


# Inicializar sistema FAQ (carrega do bucket)
print("\n" + "="*70)
print("💬 SISTEMA FAQ COM IA - GRADIO")
print("="*70 + "\n")

try:
    faq_system = load_faq_from_bucket()
except Exception as e:
    print(f"❌ Erro ao carregar FAQ: {e}")
    print("\n💡 Verifique:")
    print("   1. Arquivo .env está configurado")
    print("   2. Bucket existe e tem os arquivos")
    print("   3. APIs estão habilitadas")
    raise


# Criar interface Gradio
with gr.Blocks(title="FAQ Inteligente", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # 💬 FAQ Inteligente com IA

    Sistema RAG (Retrieval Augmented Generation) usando:
    - 🔍 **Vertex AI Embeddings** (text-embedding-004)
    - 🤖 **Gemini 1.5 Flash** (geração de respostas)
    - ☁️ **Google Cloud Storage** (dados organizados)

    Faça suas perguntas abaixo!
    """)

    # Interface de Chat
    chatbot = gr.ChatInterface(
        fn=chat_function,
        examples=[
            "Olá!",
            "Como resetar minha senha?",
            "Qual o prazo de entrega?",
            "Vocês aceitam PIX?",
            "Como funciona a política de devolução?",
        ],
        title="",  # Título já está no Markdown acima
        description="",
        retry_btn="🔄 Tentar Novamente",
        undo_btn="↩️ Desfazer",
        clear_btn="🗑️ Limpar Conversa",
        submit_btn="📤 Enviar",
        chatbot=gr.Chatbot(
            height=500,
            show_label=False,
            avatar_images=(None, "https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg"),
        ),
    )

    # Footer com informações
    gr.Markdown("""
    ---

    ### ℹ️ Sobre o Sistema

    - **Versão:** """ + VERSION + """
    - **Modelo LLM:** Gemini 1.5 Flash
    - **Embeddings:** text-embedding-004 (768 dimensões)
    - **Retrieval:** Cosine similarity (top 3 resultados)
    - **Safety:** Output filtering + Gemini safety settings

    ---

    🎓 **Desenvolvido para Google Cloud Gen AI Specialization**
    """)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌐 INICIANDO SERVIDOR GRADIO")
    print("="*70 + "\n")

    demo.launch(
        server_name="0.0.0.0",
        server_port=8080,
        share=False,
        show_error=True,
        favicon_path=None,
    )

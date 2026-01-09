#!/usr/bin/env python3
"""
Minimal FAQ chatbot with RAG
Loads from Cloud Storage and answers questions
"""

import gradio as gr
import os
import tempfile
import numpy as np
import traceback
from dotenv import load_dotenv
from google.cloud import storage
from simple_faq_rag import SimpleFAQSystem

VERSION = "3.1.0"

def load_faq_from_bucket():
    """Load FAQ from Cloud Storage."""
    load_dotenv()

    project_id = os.getenv('PROJECT_ID')
    bucket_name = os.getenv('BUCKET_NAME')

    if not project_id or not bucket_name:
        raise ValueError("Configure PROJECT_ID and BUCKET_NAME in .env file")

    print(f"Loading FAQ from bucket: gs://{bucket_name}")

    # Initialize system
    faq = SimpleFAQSystem(project_id=project_id)

    # Cloud Storage client
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Download embeddings
    print("Downloading embeddings...")
    embeddings_blob = bucket.blob("embeddings/faq_embeddings.npy")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.npy') as tmp_emb:
        embeddings_blob.download_to_filename(tmp_emb.name)
        faq.embeddings = np.load(tmp_emb.name)
        print(f"   ✓ {faq.embeddings.shape[0]} embeddings loaded")

    # Download metadata
    print("Downloading metadata...")
    metadata_blob = bucket.blob("knowledge_base/faq_metadata.csv")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_meta:
        metadata_blob.download_to_filename(tmp_meta.name)
        faq.load_csv(tmp_meta.name)
        print(f"   ✓ {len(faq.df)} questions loaded")

    print("✓ FAQ system ready!\n")
    return faq


def chat_function(message, history):
    """
    Process user messages.

    Args:
        message: User message
        history: Chat history (managed by Gradio)

    Returns:
        Response string
    """
    try:
        # Use RAG with LLM
        result = faq_system.ask_with_llm(message)

        # Return response only (no metadata)
        return result['generated_answer']

    except Exception as e:
        # Log full error for debugging
        print(f"ERROR processing query: {message}")
        print(traceback.format_exc())
        return "Sorry, an error occurred. Please try again."


# Initialize FAQ system
print("\n" + "="*70)
print("FAQ CHATBOT - LOADING")
print("="*70 + "\n")

try:
    faq_system = load_faq_from_bucket()
except Exception as e:
    print(f"Error loading FAQ: {e}")
    print("\nCheck:")
    print("   1. .env file configured")
    print("   2. Bucket exists with files")
    print("   3. APIs enabled")
    raise


# Create Gradio interface
with gr.Blocks(title="FAQ Chatbot") as demo:

    gr.Markdown("# FAQ Chatbot")

    # Chat interface
    chatbot = gr.ChatInterface(
        fn=chat_function,
        examples=[
            "Hello!",
            "How do I reset my password?",
            "What's the delivery time?",
            "Do you accept credit cards?",
            "What's your return policy?",
        ],
        chatbot=gr.Chatbot(
            height=600,
            show_label=False,
        ),
    )


if __name__ == "__main__":
    print("\n" + "="*70)
    print("STARTING GRADIO SERVER")
    print("="*70 + "\n")

    demo.launch(
        server_name="0.0.0.0",
        server_port=8080,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
    )

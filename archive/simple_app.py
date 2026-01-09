"""
🤖 Simple Chat App - FAQ System
Auto-loads from Cloud Storage - READY TO USE!
"""

import streamlit as st
import sys
from pathlib import Path
import os
import tempfile
import numpy as np
from google.cloud import storage
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simple_faq_rag import SimpleFAQSystem

# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title="FAQ Assistant",
    page_icon="💬",
    layout="centered"
)

# ============================================
# AUTO-LOAD SYSTEM (CACHE)
# ============================================

# Code version (increment when updating simple_faq_rag.py)
CODE_VERSION = "2.0.0-llm"

@st.cache_resource(show_spinner="🚀 Loading FAQ from Cloud Storage...")
def load_faq_system(_version):
    """
    Load the FAQ system automatically from Cloud Storage.
    Uses cache so it doesn't reload every time.

    Args:
        _version: Code version (forces reload when it changes)
    """
    project_id = os.getenv("PROJECT_ID")
    bucket_name = os.getenv("BUCKET_NAME")

    if not project_id or not bucket_name:
        st.error("❌ Configure .env with PROJECT_ID and BUCKET_NAME")
        st.stop()

    # Initialize Cloud Storage
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

    # Create system
    faq = SimpleFAQSystem(project_id=project_id)
    faq.load_csv(temp_metadata.name)
    faq.embeddings = np.load(temp_embeddings.name)

    return faq

# Load system (only runs once thanks to cache)
# Pass CODE_VERSION to force reload when code changes
faq_system = load_faq_system(CODE_VERSION)

# ============================================
# HEADER
# ============================================

st.title("💬 FAQ Assistant with AI")
st.markdown(f"*RAG with Gemini • {len(faq_system.df)} questions in the base*")
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
    st.header("ℹ️ Information")

    st.success("🟢 System Online")
    st.metric("Available questions", len(faq_system.df))

    st.markdown("---")
    st.caption("**Project ID:**")
    st.code(os.getenv("PROJECT_ID", "N/A"))

    st.markdown("---")

    # Button to clear conversation
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    # Button to reload system (clear cache)
    if st.button("🔄 Reload System", help="Clears cache and reloads updated code"):
        st.cache_resource.clear()
        st.rerun()

    st.markdown("---")

    # Info about RAG
    with st.expander("ℹ️ How it works"):
        st.markdown("""
**RAG (Retrieval Augmented Generation):**

1. **Retrieval** 🔍
   - Finds relevant FAQs using embeddings

2. **Generation** 🤖
   - Gemini generates the answer based on FAQs
   - Grounded in real data
   - Prompt engineering applied

3. **Output Filtering** ✅
   - Filters sensitive information
   - Safety settings enabled
        """)

    st.markdown("---")
    st.caption("☁️ Powered by Vertex AI + Gemini")

# ============================================
# MAIN CHAT
# ============================================

# Show history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "score" in msg:
            score = msg["score"]
            if score >= 0.8:
                st.markdown(f"**Confidence:** :green[{score:.0%}]")
            elif score >= 0.6:
                st.markdown(f"**Confidence:** :orange[{score:.0%}]")
            else:
                st.markdown(f"**Confidence:** :red[{score:.0%}]")

# User input
if prompt := st.chat_input("Type your question..."):

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Fetch answer
    with st.chat_message("assistant"):
        with st.spinner("🤖 Processing with AI..."):
            try:
                # Use full RAG with LLM (Gemini)
                result = faq_system.ask_with_llm(prompt)

                if result['found']:
                    # LLM-generated answer
                    generated_answer = result['generated_answer']
                    score = result['score']

                    # Display answer
                    st.markdown(generated_answer)

                    # Show source (original FAQ) in expander
                    with st.expander("📚 View original FAQ"):
                        st.markdown(f"**Matched question:** {result['question_found']}")
                        st.markdown(f"**Original answer:** {result['original_answer']}")
                        st.caption("✨ Answer rewritten by AI (Gemini)")

                    # Show confidence
                    if score >= 0.8:
                        st.markdown(f"**Confidence:** :green[{score:.0%}]")
                    elif score >= 0.6:
                        st.markdown(f"**Confidence:** :orange[{score:.0%}]")
                    else:
                        st.markdown(f"**Confidence:** :red[{score:.0%}]")

                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": generated_answer,
                        "score": score
                    })
                else:
                    msg = result.get('generated_answer', "Sorry, I couldn't find a relevant answer to that question. 😕")
                    st.markdown(msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": msg
                    })

            except Exception as e:
                error_msg = f"❌ Error fetching answer: {e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.caption("🤖 RAG (Retrieval Augmented Generation) • Powered by Vertex AI + Gemini 2.5 Flash")

#!/usr/bin/env python3
"""
REST API for FAQ Chatbot
Simple Flask API endpoint for testing
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import numpy as np
from dotenv import load_dotenv
from google.cloud import storage
from simple_faq_rag import SimpleFAQSystem

app = Flask(__name__)
CORS(app)  # Enable CORS for testing

# Load FAQ system
print("Loading FAQ system...")
load_dotenv()

project_id = os.getenv('PROJECT_ID')
bucket_name = os.getenv('BUCKET_NAME')

faq_system = SimpleFAQSystem(project_id=project_id)

# Load from bucket
client = storage.Client()
bucket = client.bucket(bucket_name)

# Download embeddings
embeddings_blob = bucket.blob("embeddings/faq_embeddings.npy")
with tempfile.NamedTemporaryFile(delete=False, suffix='.npy') as tmp_emb:
    embeddings_blob.download_to_filename(tmp_emb.name)
    faq_system.embeddings = np.load(tmp_emb.name)

# Download metadata
metadata_blob = bucket.blob("knowledge_base/faq_metadata.csv")
with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_meta:
    metadata_blob.download_to_filename(tmp_meta.name)
    faq_system.load_csv(tmp_meta.name)

print(f"FAQ system ready with {len(faq_system.df)} questions!")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'total_questions': len(faq_system.df),
        'model': 'gemini-2.5-flash',
        'embeddings': 'text-embedding-004'
    })


@app.route('/ask', methods=['POST'])
def ask():
    """
    Main endpoint to ask questions

    Request body:
    {
        "question": "How do I reset my password?"
    }

    Response:
    {
        "answer": "To reset your password...",
        "confidence": "high",
        "score": 0.85
    }
    """
    try:
        data = request.get_json()

        if not data or 'question' not in data:
            return jsonify({
                'error': 'Missing "question" field in request body'
            }), 400

        question = data['question']

        # Get answer from FAQ system
        result = faq_system.ask_with_llm(question)

        return jsonify({
            'answer': result['resposta_gerada'],
            'confidence': result.get('confidence', 'unknown'),
            'score': float(result.get('score', 0.0)),
            'found': result.get('found', False)
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/search', methods=['POST'])
def search():
    """
    Search endpoint (without LLM generation)

    Request body:
    {
        "query": "password",
        "top_k": 3
    }

    Response:
    {
        "results": [
            {
                "question": "How do I reset my password?",
                "answer": "...",
                "score": 0.85
            }
        ]
    }
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing "query" field in request body'
            }), 400

        query = data['query']
        top_k = data.get('top_k', 3)

        # Search FAQs
        results = faq_system.search(query, top_k=top_k)

        return jsonify({
            'results': [
                {
                    'question': r['pergunta'],
                    'answer': r['resposta'],
                    'score': float(r['score']),
                    'confidence': r['confidence']
                }
                for r in results
            ],
            'total': len(results)
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("FAQ CHATBOT - REST API")
    print("="*70)
    print("\nEndpoints:")
    print("  GET  /health              - Health check")
    print("  POST /ask                 - Ask question (with LLM)")
    print("  POST /search              - Search FAQs (no LLM)")
    print("\n" + "="*70 + "\n")

    # Get port from environment (Cloud Run compatibility)
    port = int(os.getenv('PORT', 8080))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )

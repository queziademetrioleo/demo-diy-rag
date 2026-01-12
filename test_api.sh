#!/bin/bash
# Test script for FAQ Chatbot API

API_URL="http://localhost:8081"

echo "======================================================================"
echo "FAQ CHATBOT API - TEST SCRIPT"
echo "======================================================================"

# Health check
echo -e "\n1️⃣  Testing /health endpoint..."
curl -s $API_URL/health | jq '.'

# Ask question (with LLM)
echo -e "\n2️⃣  Testing /ask endpoint (with LLM)..."
curl -s -X POST $API_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I reset my password?"
  }' | jq '.'

# Search (without LLM)
echo -e "\n3️⃣  Testing /search endpoint (no LLM)..."
curl -s -X POST $API_URL/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "payment",
    "top_k": 3
  }' | jq '.'

# Test greeting
echo -e "\n4️⃣  Testing greeting..."
curl -s -X POST $API_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Hello!"
  }' | jq '.'

echo -e "\n======================================================================"
echo "TESTS COMPLETED"
echo "======================================================================"

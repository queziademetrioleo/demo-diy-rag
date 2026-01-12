# 🌐 FAQ Chatbot - API Endpoints

## Quick Start

### Option 1: Gradio API (Automatic)
```bash
# Start Gradio (includes automatic API)
python simple_gradio_app.py

# Test endpoint
curl -X POST http://localhost:8080/api/predict \
  -H "Content-Type: application/json" \
  -d '{"data": ["How do I reset my password?"]}'
```

### Option 2: Flask REST API
```bash
# Install dependencies
pip install flask flask-cors

# Start Flask API
python api_rest.py

# Test endpoint
curl -X POST http://localhost:8081/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my password?"}'
```

---

## 📡 Available Endpoints

### **1. Gradio Endpoints** (Port 8080)

#### POST `/api/predict`
Ask a question (with LLM generation)

**Request:**
```json
{
  "data": ["How do I reset my password?"]
}
```

**Response:**
```json
{
  "data": ["To reset your password, go to Settings > Security..."],
  "duration": 2.5
}
```

#### GET `/info`
API information

**Response:**
```json
{
  "named_endpoints": {...},
  "unnamed_endpoints": {...}
}
```

---

### **2. Flask REST Endpoints** (Port 8081)

#### GET `/health`
Health check

**Response:**
```json
{
  "status": "healthy",
  "total_questions": 25,
  "model": "gemini-2.5-flash",
  "embeddings": "text-embedding-004"
}
```

#### POST `/ask`
Ask a question with LLM generation

**Request:**
```json
{
  "question": "How do I reset my password?"
}
```

**Response:**
```json
{
  "answer": "To reset your password, go to Settings > Security...",
  "confidence": "high",
  "score": 0.85,
  "found": true
}
```

#### POST `/search`
Search FAQs without LLM (faster, no generation)

**Request:**
```json
{
  "query": "password",
  "top_k": 3
}
```

**Response:**
```json
{
  "results": [
    {
      "question": "How do I reset my password?",
      "answer": "To reset your password...",
      "score": 0.85,
      "confidence": "high"
    }
  ],
  "total": 3
}
```

---

## 🧪 Testing

### Using curl

```bash
# Health check
curl http://localhost:8081/health

# Ask question
curl -X POST http://localhost:8081/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What payment methods do you accept?"}'

# Search FAQs
curl -X POST http://localhost:8081/search \
  -H "Content-Type: application/json" \
  -d '{"query": "delivery", "top_k": 5}'
```

### Using test script

```bash
# Run automated tests
./test_api.sh
```

### Using Python

```python
import requests

# Ask question
response = requests.post(
    'http://localhost:8081/ask',
    json={'question': 'How do I reset my password?'}
)

print(response.json()['answer'])
```

### Using JavaScript

```javascript
// Ask question
fetch('http://localhost:8081/ask', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    question: 'How do I reset my password?'
  })
})
.then(res => res.json())
.then(data => console.log(data.answer));
```

---

## 🔒 Production Considerations

### Security
- Add authentication (API keys, JWT, etc.)
- Enable rate limiting
- Use HTTPS in production
- Validate input to prevent injection

### Performance
- Add caching for common questions
- Use async endpoints for better concurrency
- Consider load balancing for high traffic

### Monitoring
- Add logging for all requests
- Track response times
- Monitor error rates
- Set up alerts for API health

---

## 📊 Comparison

| Feature | Gradio API | Flask API |
|---------|-----------|-----------|
| **Port** | 8080 | 8081 |
| **UI Included** | ✅ Yes | ❌ No |
| **Request Format** | `{"data": [...]}` | `{"question": "..."}` |
| **Response Format** | `{"data": [...]}` | `{"answer": "..."}` |
| **Best For** | Quick demos, prototyping | Production, integrations |
| **Setup** | Automatic (no config) | Manual (Flask app) |

---

## 🚀 Deployment

### Cloud Run (Recommended)

```bash
# Deploy Gradio version
gcloud run deploy faq-chatbot \
  --source . \
  --port 8080 \
  --allow-unauthenticated

# Deploy Flask API version
gcloud run deploy faq-api \
  --source . \
  --port 8081 \
  --allow-unauthenticated
```

### App Engine

```yaml
# app.yaml
runtime: python312
entrypoint: python api_rest.py

env_variables:
  PROJECT_ID: "your-project-id"
  BUCKET_NAME: "your-bucket-name"
```

---

## 📝 Example Integration

### From another Python service

```python
# faq_client.py
import requests

class FAQClient:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url

    def ask(self, question: str) -> str:
        response = requests.post(
            f"{self.base_url}/ask",
            json={"question": question}
        )
        return response.json()["answer"]

# Usage
client = FAQClient()
answer = client.ask("How do I reset my password?")
print(answer)
```

### From a web app

```html
<script>
async function askFAQ(question) {
  const response = await fetch('http://localhost:8081/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  });
  const data = await response.json();
  return data.answer;
}

// Usage
askFAQ('How do I reset my password?')
  .then(answer => console.log(answer));
</script>
```

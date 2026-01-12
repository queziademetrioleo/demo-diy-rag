# 🚀 Deployment Guide - Google Cloud Gen AI Certification

## ⚠️ IMPORTANTE para Certificação

Para o Google Cloud Gen AI Specialization, você **NÃO PODE** usar localhost.

**Requisitos obrigatórios:**
- ✅ Deployed on Google Cloud
- ✅ Network-accessible endpoint (HTTPS)
- ✅ Uses Vertex AI (Gemini + Embeddings)
- ✅ IAM authentication (recommended)

---

## 🎯 Opção 1: Cloud Run (Recomendado - Mais Fácil)

### **Com IAM Authentication** (Melhor para certificação)

```bash
# Deploy with IAM authentication
./deploy_cloud_run_iam.sh
```

**Resultado:**
- URL: `https://faq-chatbot-api-xxxxx-uc.a.run.app`
- Autenticação: IAM (Service Account)
- ✅ **VÁLIDO para certificação**

**Como testar:**
```bash
# 1. Get token
TOKEN=$(gcloud auth print-identity-token)

# 2. Test endpoint
curl https://faq-chatbot-api-xxxxx-uc.a.run.app/health \
  -H "Authorization: Bearer $TOKEN"

# 3. Ask question
curl -X POST https://faq-chatbot-api-xxxxx-uc.a.run.app/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my password?"}'
```

**Dar acesso para outros:**
```bash
gcloud run services add-iam-policy-binding faq-chatbot-api \
  --region=us-central1 \
  --member='user:estagiaria@example.com' \
  --role='roles/run.invoker'
```

---

### **Sem autenticação** (Apenas para testes)

```bash
# Deploy without authentication (public)
./deploy_cloud_run.sh
```

**Resultado:**
- URL: `https://faq-chatbot-api-xxxxx-uc.a.run.app`
- Autenticação: Nenhuma (público)
- ⚠️ **Menos seguro, mas também válido**

**Como testar:**
```bash
# Direct access (no token needed)
curl https://faq-chatbot-api-xxxxx-uc.a.run.app/health

curl -X POST https://faq-chatbot-api-xxxxx-uc.a.run.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my password?"}'
```

---

## 🏆 Opção 2: Vertex AI Endpoint (Padrão Ouro)

Esta é a **MELHOR opção** para certificação, mas mais complexa.

### Passo 1: Criar Custom Container

```bash
# Build container for Vertex AI
gcloud builds submit --tag gcr.io/${PROJECT_ID}/faq-chatbot-vertex
```

### Passo 2: Upload do Model

```bash
# Create model
gcloud ai models upload \
  --region=us-central1 \
  --display-name=faq-chatbot-model \
  --container-image-uri=gcr.io/${PROJECT_ID}/faq-chatbot-vertex \
  --container-health-route=/health \
  --container-predict-route=/ask \
  --container-ports=8080
```

### Passo 3: Deploy Endpoint

```bash
# Create endpoint
gcloud ai endpoints create \
  --region=us-central1 \
  --display-name=faq-chatbot-endpoint

# Deploy model to endpoint
gcloud ai endpoints deploy-model ENDPOINT_ID \
  --region=us-central1 \
  --model=MODEL_ID \
  --display-name=faq-chatbot-deployment \
  --machine-type=n1-standard-4 \
  --min-replica-count=1 \
  --max-replica-count=3
```

### Testar Vertex AI Endpoint

```bash
# Using gcloud
gcloud ai endpoints predict ENDPOINT_ID \
  --region=us-central1 \
  --json-request='{"instances": [{"question": "How do I reset my password?"}]}'

# Using Python
from google.cloud import aiplatform

endpoint = aiplatform.Endpoint('projects/PROJECT_ID/locations/us-central1/endpoints/ENDPOINT_ID')
response = endpoint.predict(instances=[{"question": "How do I reset my password?"}])
print(response.predictions[0])
```

**Vantagens:**
- ✅ Gerenciamento automático de versões
- ✅ Autoscaling nativo
- ✅ Monitoramento integrado
- ✅ **Melhor pontuação na certificação**

---

## 📊 Comparação

| Feature | Cloud Run (IAM) | Cloud Run (Public) | Vertex AI Endpoint |
|---------|----------------|-------------------|-------------------|
| **Setup** | Fácil | Muito fácil | Complexo |
| **Autenticação** | IAM ✅ | Nenhuma ⚠️ | IAM ✅ |
| **Custo** | Baixo | Baixo | Médio-Alto |
| **Certificação** | ✅ Válido | ✅ Válido | ⭐ Recomendado |
| **Tempo deploy** | 5 min | 5 min | 15-20 min |

---

## 🧪 Verificar Deployment

### Checklist para Certificação

- [ ] Serviço rodando no GCP (não localhost)
- [ ] Endpoint HTTPS acessível
- [ ] Usa Vertex AI (Gemini 2.5 Flash)
- [ ] Usa Vertex AI Embeddings (text-embedding-004)
- [ ] Autenticação configurada (IAM ou pública)
- [ ] Health check funcionando
- [ ] Predict/Ask endpoint funcionando

### Comandos de Verificação

```bash
# 1. Check service status
gcloud run services describe faq-chatbot-api \
  --region=us-central1 \
  --format=json

# 2. Test health endpoint
TOKEN=$(gcloud auth print-identity-token)
curl https://YOUR-SERVICE-URL/health \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
# {
#   "status": "healthy",
#   "model": "gemini-2.5-flash",
#   "embeddings": "text-embedding-004"
# }

# 3. Test ask endpoint
curl -X POST https://YOUR-SERVICE-URL/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'
```

---

## 🎓 Submeter para Certificação

### O que enviar:

1. **Service URL:**
   ```
   https://faq-chatbot-api-xxxxx-uc.a.run.app
   ```

2. **Prova de uso do Vertex AI:**
   - Screenshot do `/health` endpoint mostrando:
     - `"model": "gemini-2.5-flash"`
     - `"embeddings": "text-embedding-004"`

3. **Exemplo de request/response:**
   ```bash
   # Request
   POST /ask
   {"question": "How do I reset my password?"}

   # Response
   {"answer": "To reset your password, go to Settings...", "confidence": "high"}
   ```

4. **Logs mostrando Vertex AI usage:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=faq-chatbot-api" --limit=50
   ```

---

## 💰 Estimativa de Custos

### Cloud Run (IAM authenticated)
- Request: $0.40 per million
- Memory: $0.0000025 per GB-second
- CPU: $0.00002400 per vCPU-second

**Estimativa mensal:**
- 10,000 requests/mês: ~$5-10
- Baixo uso: Quase grátis (free tier)

### Vertex AI Endpoint
- Deployment: ~$50-100/mês (sempre ligado)
- Predictions: Cobrança por request
- Recomendado apenas para produção

---

## 🔒 Segurança

### Cloud Run com IAM

```bash
# Grant access to specific user
gcloud run services add-iam-policy-binding faq-chatbot-api \
  --region=us-central1 \
  --member='user:email@example.com' \
  --role='roles/run.invoker'

# Grant access to service account
gcloud run services add-iam-policy-binding faq-chatbot-api \
  --region=us-central1 \
  --member='serviceAccount:sa@project.iam.gserviceaccount.com' \
  --role='roles/run.invoker'

# Remove public access (if deployed as public)
gcloud run services remove-iam-policy-binding faq-chatbot-api \
  --region=us-central1 \
  --member='allUsers' \
  --role='roles/run.invoker'
```

---

## 🐛 Troubleshooting

### "Permission denied" errors
```bash
# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='user:YOUR_EMAIL' \
  --role='roles/run.admin'

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='user:YOUR_EMAIL' \
  --role='roles/iam.serviceAccountUser'
```

### "Service not found" errors
```bash
# List all Cloud Run services
gcloud run services list --region=us-central1

# Check service logs
gcloud logging read "resource.type=cloud_run_revision" --limit=100
```

### Container build fails
```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Check build logs
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

---

## 📝 Próximos Passos

1. ✅ Deploy no Cloud Run com IAM
2. ✅ Testar endpoint com autenticação
3. ✅ Dar acesso para estagiária
4. ✅ Fazer screenshots para certificação
5. ✅ Submeter URL para avaliação

**Recomendação:** Comece com **Cloud Run + IAM** (mais fácil, rápido e válido para certificação).

# 🚀 GUIA RÁPIDO: Deploy no Cloud Run para Certificação

## ⚡ TL;DR - Como Obter seu Endpoint

```bash
# 1. Fazer deploy (5 minutos)
./deploy_cloud_run_iam.sh

# 2. Obter URL
SERVICE_URL=$(gcloud run services describe faq-chatbot-api \
  --region=us-central1 --format='value(status.url)')
echo "Seu endpoint: $SERVICE_URL"

# 3. Testar
TOKEN=$(gcloud auth print-identity-token)
curl $SERVICE_URL/health -H "Authorization: Bearer $TOKEN"
```

**Pronto! Você tem um endpoint para a certificação.**

---

## 🎯 Por que preciso disso?

**Google Cloud Gen AI Certification exige:**
- ❌ Localhost NÃO é aceito
- ✅ Endpoint deployado no GCP
- ✅ HTTPS acessível via rede
- ✅ Usa Vertex AI (provado no /health)
- ✅ Autenticação IAM

---

## 📋 Passo a Passo Detalhado

### Passo 1: Deploy

```bash
# No Cloud Shell
./deploy_cloud_run_iam.sh
```

**Aguarde 5-7 minutos**. O script vai:
1. Habilitar APIs necessárias
2. Criar container Docker
3. Deploy no Cloud Run
4. Configurar autenticação IAM

**Saída esperada:**
```
✅ DEPLOYMENT SUCCESSFUL (IAM AUTHENTICATED)!
Service URL: https://faq-chatbot-api-abc123-uc.a.run.app
```

---

### Passo 2: Salvar URL

```bash
SERVICE_URL=$(gcloud run services describe faq-chatbot-api \
  --region=us-central1 \
  --format='value(status.url)')

echo $SERVICE_URL
```

**Copie esse URL** - você vai precisar para a certificação!

---

### Passo 3: Testar

```bash
# Obter token
TOKEN=$(gcloud auth print-identity-token)

# Testar health
curl $SERVICE_URL/health -H "Authorization: Bearer $TOKEN"
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "total_questions": 25,
  "model": "gemini-2.5-flash",
  "embeddings": "text-embedding-004"
}
```

**✅ Se viu isso, está funcionando!**

---

### Passo 4: Fazer Pergunta

```bash
curl -X POST $SERVICE_URL/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my password?"}'
```

**Resposta esperada:**
```json
{
  "answer": "To reset your password...",
  "confidence": "high",
  "score": 0.95,
  "found": true
}
```

---

## 👥 Dar Acesso para Outros

```bash
# Dar acesso para estagiária/avaliador
gcloud run services add-iam-policy-binding faq-chatbot-api \
  --region=us-central1 \
  --member='user:EMAIL_AQUI@example.com' \
  --role='roles/run.invoker'
```

**Instruções para a pessoa:**
```bash
# 1. Login
gcloud auth login

# 2. Obter token
TOKEN=$(gcloud auth print-identity-token)

# 3. Testar
curl https://faq-chatbot-api-abc123-uc.a.run.app/health \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎓 Submeter para Certificação

**Você precisa fornecer:**

### 1. URL do Endpoint
```
https://faq-chatbot-api-abc123-uc.a.run.app
```

### 2. Screenshot do /health

**Como fazer:**
```bash
TOKEN=$(gcloud auth print-identity-token)
curl $SERVICE_URL/health -H "Authorization: Bearer $TOKEN" | jq '.'
```

**Tire screenshot mostrando:**
```json
{
  "model": "gemini-2.5-flash",
  "embeddings": "text-embedding-004"
}
```

### 3. Exemplo Request/Response

**Request:**
```bash
curl -X POST $SERVICE_URL/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my password?"}'
```

**Screenshot da resposta**

---

## 💰 Quanto Custa?

**Cloud Run:**
- ✅ 2 milhões requests/mês: **GRÁTIS**
- ✅ 180k vCPU-seconds/mês: **GRÁTIS**
- ✅ 360k GiB-seconds/mês: **GRÁTIS**

**Para este projeto:**
- Uso leve: **$0** (free tier cobre)
- Uso moderado: **$2-5/mês**

**Você provavelmente não vai pagar nada!**

---

## 🔍 Verificar Status

```bash
# Ver serviços
gcloud run services list --region=us-central1

# Ver logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=faq-chatbot-api" \
  --limit=20

# Abrir console
echo "https://console.cloud.google.com/run/detail/us-central1/faq-chatbot-api"
```

---

## 🗑️ Deletar Serviço

**Se quiser parar de usar:**

```bash
gcloud run services delete faq-chatbot-api --region=us-central1
```

**Custos param imediatamente.**

---

## ❓ Troubleshooting

### Erro: "Permission denied"

```bash
# Dar permissões
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='user:SEU_EMAIL' \
  --role='roles/run.admin'
```

### Erro: "Service not found"

```bash
# Verificar região
gcloud run services list --region=us-central1

# Deploy novamente
./deploy_cloud_run_iam.sh
```

### Token expirado

```bash
# Gerar novo token
TOKEN=$(gcloud auth print-identity-token)
```

---

## ✅ Checklist Final

Antes de submeter para certificação:

- [ ] Serviço deployado no Cloud Run
- [ ] URL funciona: `https://faq-chatbot-api-xxx.run.app`
- [ ] `/health` retorna `"model": "gemini-2.5-flash"`
- [ ] `/ask` responde perguntas corretamente
- [ ] Screenshot do `/health` feito
- [ ] Exemplo de request/response documentado

**Tudo checado? Você está pronto! 🎉**

---

## 📚 Mais Informações

- **Documentação completa:** `DEPLOYMENT.md`
- **Checklist certificação:** `CERTIFICATION_CHECKLIST.md`
- **Tutorial completo:** `PASSO_A_PASSO.md` (Seção 11)

---

**Dúvidas?** Veja os arquivos de documentação ou execute os scripts com `-h` para ajuda.

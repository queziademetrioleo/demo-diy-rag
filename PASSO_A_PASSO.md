# 🚀 Guia Passo a Passo - Sistema FAQ RAG

**Do Cloud Shell ao Sistema Funcionando em 15 Minutos**

Este guia te leva do zero a um sistema FAQ inteligente rodando, sem erros.

## 📋 Índice Rápido

1. [Pré-requisitos](#1-pré-requisitos)
2. [Cloud Shell e Projeto](#2-cloud-shell-e-projeto)
3. [Clonar Código](#3-clonar-código)
4. [Habilitar APIs](#4-habilitar-apis)
5. [Criar Bucket e Estrutura](#5-criar-bucket-e-estrutura)
6. [Upload do CSV](#6-upload-do-csv)
7. [Configurar .env](#7-configurar-env-importante)
8. [Instalar Dependências](#8-instalar-dependências)
9. [Processar FAQ](#9-processar-faq)
10. [Rodar Interface Web](#10-rodar-interface-web)
11. [Troubleshooting](#troubleshooting)

---

## 1. Pré-requisitos

**Você precisa ter:**
- Conta Google (Gmail)
- Projeto Google Cloud criado
- Billing habilitado (pode usar free tier!)

**Não precisa instalar nada!** Tudo roda no Cloud Shell (navegador).

---

## 2. Cloud Shell e Projeto

### 2.1 Abrir Cloud Shell

1. Vá para https://console.cloud.google.com
2. Clique no ícone **">_"** no topo direito
3. Janela de terminal abre (Cloud Shell)

### 2.2 Configurar Projeto

```bash
# Ver projeto atual
gcloud config get-value project

# Se não aparecer ou estiver errado, configurar:
gcloud config set project SEU-PROJECT-ID

# Anotar o PROJECT_ID! Você vai usar várias vezes
```

**✅ Checkpoint:** Comando `gcloud config get-value project` retorna seu projeto

---

## 3. Clonar Código

```bash
# Clonar repositório
git clone https://github.com/queziademetrioleo/demo-diy-rag.git
cd demo-diy-rag

# Mudar para branch do sistema simples
git checkout claude/simple-faq-rag-34uUC

# Verificar arquivos
ls -la
```

**Você deve ver:**
- `simple_faq_rag.py` - Sistema RAG
- `simple_gradio_app.py` - Interface Gradio
- `simple_scripts/` - Scripts auxiliares
- `data/faq_example.csv` - CSV de exemplo
- `requirements.txt` - Dependências

**✅ Checkpoint:** Arquivo `simple_faq_rag.py` existe

---

## 4. Habilitar APIs

```bash
# Habilitar Vertex AI e Cloud Storage
gcloud services enable \
  aiplatform.googleapis.com \
  storage-api.googleapis.com

# Aguardar ativação (30 segundos)
sleep 30 && echo "✅ APIs habilitadas!"
```

**✅ Checkpoint:** Comando termina sem erros

---

## 5. Criar Bucket e Estrutura

### 5.1 Criar Bucket

```bash
# Criar bucket (substitui SEU-PROJECT-ID automaticamente)
gsutil mb -l us-central1 gs://$(gcloud config get-value project)-data
```

**⚠️ Se der erro "bucket exists":** Tudo bem! Continue.

### 5.2 Criar Pastas Organizadas

```bash
# Criar estrutura de pastas no bucket
echo "" | gsutil cp - gs://$(gcloud config get-value project)-data/raw_data/.keep
echo "" | gsutil cp - gs://$(gcloud config get-value project)-data/embeddings/.keep
echo "" | gsutil cp - gs://$(gcloud config get-value project)-data/knowledge_base/.keep

echo "✅ Estrutura criada!"
```

**Estrutura criada:**
```
seu-projeto-data/
├── raw_data/          # CSV original
├── embeddings/        # Vetores de IA (.npy)
└── knowledge_base/    # Metadata (.csv)
```

**✅ Checkpoint:** `gsutil ls gs://$(gcloud config get-value project)-data` mostra as 3 pastas

---

## 6. Upload do CSV

**⚠️ CRÍTICO:** Nome do arquivo **NÃO PODE** ter espaços ou caracteres especiais!

### Opção A: Usar CSV de Exemplo (Recomendado)

```bash
# Copiar CSV de exemplo para bucket
gsutil cp data/faq_example.csv gs://$(gcloud config get-value project)-data/raw_data/
```

### Opção B: Usar Seu Próprio CSV

**Regra do CSV:**
- Mínimo **2 colunas**
- **1ª coluna:** Perguntas (qualquer nome: Questions, pergunta, Q, etc.)
- **2ª coluna:** Respostas (qualquer nome: Answers, resposta, A, etc.)

**PASSO 1: Renomear arquivo (se necessário)**

Se seu arquivo tem espaços, renomeie ANTES de subir:

```bash
# Exemplo: "FAQ - DEMO (v1).csv" → "faq_demo.csv"
# ❌ ERRADO: Arquivo com espaços quebra!
# ✅ CORRETO: Apenas letras, números, _ e -
```

**PASSO 2: Upload pelo Cloud Shell**

1. Clique no menu **⋮** (três pontos) no Cloud Shell
2. Selecione **Upload**
3. Escolha seu arquivo CSV (já renomeado!)
4. Aguarde "Upload completed"

**PASSO 3: Copiar para bucket**

```bash
# Substitua "faq_demo.csv" pelo nome do seu arquivo
gsutil cp ~/faq_demo.csv gs://$(gcloud config get-value project)-data/raw_data/
```

### Verificar Upload

```bash
# Listar arquivos no bucket
gsutil ls gs://$(gcloud config get-value project)-data/raw_data/

# Deve mostrar seu CSV
```

**✅ Checkpoint:** Seu CSV aparece na listagem

---

## 7. Configurar .env (IMPORTANTE!)

**⚠️ CRÍTICO:** Arquivo .env NÃO PODE ter comentários decorativos!

```bash
# Copiar exemplo
cp .env.example .env

# Editar
nano .env
```

**No editor nano:**

1. Pressione `Ctrl+K` várias vezes até apagar TUDO
2. Cole EXATAMENTE isto (substituindo SEU-PROJECT-ID):

```bash
PROJECT_ID=SEU-PROJECT-ID
LOCATION=us-central1
BUCKET_NAME=SEU-PROJECT-ID-data
RAW_DATA_PATH=raw_data/faq_example.csv
```

**❌ NÃO FAÇA ISTO:**
```bash
# ============================================
# CONFIGURAÇÃO (comentários decorativos!)
# ============================================
PROJECT_ID=...  # Isso quebra o parser!
```

**✅ FAÇA ASSIM:**
```bash
PROJECT_ID=teste-de-big-query-472216
LOCATION=us-central1
BUCKET_NAME=teste-de-big-query-472216-data
RAW_DATA_PATH=raw_data/faq_example.csv
```

**Se usou seu próprio CSV, atualize a linha `RAW_DATA_PATH`:**
```bash
RAW_DATA_PATH=raw_data/seu_arquivo.csv
```

**Salvar:**
1. `Ctrl+O` → `Enter`
2. `Ctrl+X`

**Verificar:**
```bash
cat .env
```

**✅ Checkpoint:** .env mostra suas 4 linhas sem comentários decorativos

---

## 8. Instalar Dependências

### 8.1 Criar Ambiente Virtual

```bash
# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate
```

**O prompt muda para:**
```
(venv) usuario@cloudshell:~/demo-diy-rag$
```

**⚠️ Importante:** O `(venv)` deve aparecer! Se não aparecer, rode `source venv/bin/activate` novamente.

### 8.2 Instalar Pacotes

```bash
# Atualizar pip
pip install --upgrade pip

# Instalar todas as dependências (~3 minutos)
pip install -r requirements.txt
```

**☕ Aguarde ~3 minutos...**

**Verificar instalação:**
```bash
pip list | grep google-cloud
```

**Deve mostrar:**
```
google-cloud-aiplatform    1.38.1
google-cloud-storage       2.14.0
```

**✅ Checkpoint:** Dependências instaladas sem erros

---

## 9. Processar FAQ

Este script vai:
1. Baixar CSV do bucket
2. Criar embeddings com Vertex AI
3. Salvar base de conhecimento no bucket

```bash
# Executar processamento
python simple_scripts/03_use_bucket.py
```

**Vai aparecer:**

```
======================================================================
🪣 SISTEMA FAQ COM GOOGLE CLOUD STORAGE
======================================================================

✅ Projeto: seu-projeto-id
✅ Bucket: gs://seu-projeto-data

======================================================================
ETAPA 1: Baixando dados do Cloud Storage
======================================================================
📥 Baixando CSV do bucket...
✅ Baixado: [arquivo temporário]

======================================================================
ETAPA 2: Inicializando Sistema FAQ
======================================================================
✅ Sistema inicializado!

======================================================================
ETAPA 3: Carregando Perguntas e Respostas
======================================================================
📊 Total de perguntas: 25

======================================================================
ETAPA 4: Criando Base de Conhecimento (Embeddings)
======================================================================
⏳ Isso pode levar alguns minutos...
```

**⏰ AGUARDE 2-5 MINUTOS** - Está criando embeddings com IA!

**Quando terminar:**

```
✅ Base de conhecimento criada!

======================================================================
ETAPA 5: Salvando Base de Conhecimento
======================================================================
✅ Embeddings salvos
✅ Metadados salvos

======================================================================
ETAPA 6: Enviando para Cloud Storage
======================================================================
📤 Fazendo upload da base de conhecimento...
   ✅ Embeddings enviados
   ✅ Metadados enviados

✅ Base de conhecimento salva no bucket!

======================================================================
ETAPA 7: Testando Sistema
======================================================================
🧪 Fazendo 3 perguntas de teste:

[Testes aparecem aqui...]

======================================================================
✅ PROCESSO CONCLUÍDO COM SUCESSO!
======================================================================
```

**Verificar que funcionou:**
```bash
# Listar arquivos criados
gsutil ls -r gs://$(gcloud config get-value project)-data/
```

**Deve mostrar:**
```
gs://seu-projeto-data/embeddings/:
gs://seu-projeto-data/embeddings/faq_embeddings.npy

gs://seu-projeto-data/knowledge_base/:
gs://seu-projeto-data/knowledge_base/faq_metadata.csv

gs://seu-projeto-data/raw_data/:
gs://seu-projeto-data/raw_data/faq_example.csv
```

**✅ Checkpoint:** 3 pastas com arquivos criados

---

## 10. Rodar Interface Web

### 10.1 Iniciar Gradio

```bash
# Rodar app Gradio (simples!)
python simple_gradio_app.py
```

**Vai aparecer:**
```
💬 SISTEMA FAQ COM IA - GRADIO
======================================================================

🚀 Carregando FAQ do bucket: gs://seu-projeto-data
📥 Baixando embeddings...
   ✅ 25 embeddings carregados
📥 Baixando metadados...
   ✅ 25 perguntas carregadas
✅ Sistema FAQ pronto para uso!

🌐 INICIANDO SERVIDOR GRADIO
======================================================================

Running on local URL:  http://0.0.0.0:8080

To create a public link, set `share=True` in `launch()`.
```

### 10.2 Abrir no Navegador

**No Cloud Shell:**
1. Procure botão **"Web Preview"** no topo
2. Clique → **"Preview on port 8080"**
3. Nova aba abre com a interface de chat!

### 10.3 Usar o Sistema

**Interface Gradio pronta para usar:**

1. **Chat moderno** aparece automaticamente
2. **Exemplos prontos** para clicar:
   - "Olá!"
   - "Como resetar minha senha?"
   - "Qual o prazo de entrega?"
   - "Vocês aceitam PIX?"

3. **Digite suas perguntas** no campo de texto
4. **Pressione Enter** ou clique "📤 Enviar"

**Recursos da interface:**
- 💬 **Chat com histórico** (mantém conversa)
- 📊 **Metadados inclusos** (confiança, score, fonte)
- 🔄 **Tentar Novamente** (re-enviar mensagem)
- ↩️ **Desfazer** (voltar mensagem)
- 🗑️ **Limpar Conversa** (resetar chat)
- 🎨 **Design moderno** (tema Gradio Soft)

**✅ Checkpoint:** Sistema responde perguntas corretamente

**💡 Gradio é MUITO mais simples:**
- ✅ Sem problemas de cache
- ✅ Auto-reload funciona melhor
- ✅ Apenas 150 linhas vs. 200+ do Streamlit
- ✅ Interface de chat nativa (não precisa implementar)

---

## 📡 PASSO 11: Deploy no Cloud Run (Endpoint para Certificação)

**⚠️ IMPORTANTE:** Para a certificação Google Cloud Gen AI, você **NÃO PODE** usar localhost. Precisa de um **endpoint deployado no GCP**.

### 11.1 Por que preciso disso?

**Requisitos da certificação:**
- ✅ Serviço rodando no GCP (não localhost)
- ✅ Endpoint HTTPS acessível via rede
- ✅ Usa Vertex AI (Gemini + Embeddings)
- ✅ Autenticação IAM

**Cloud Run oferece tudo isso automaticamente!**

---

### 11.2 Deploy com IAM Authentication (Recomendado)

**Este é o método RECOMENDADO para a certificação.**

```bash
# No Cloud Shell, execute:
./deploy_cloud_run_iam.sh
```

**O que esse script faz:**

1. ✅ Habilita APIs necessárias (Cloud Build, Cloud Run)
2. ✅ Cria imagem Docker do seu sistema
3. ✅ Faz deploy no Cloud Run
4. ✅ Configura autenticação IAM
5. ✅ Retorna o URL do endpoint

**Tempo estimado:** 5-7 minutos

**Saída esperada:**
```
======================================================================
✅ DEPLOYMENT SUCCESSFUL (IAM AUTHENTICATED)!
======================================================================

Service URL: https://faq-chatbot-api-abc123-uc.a.run.app

⚠️  This service requires authentication!

To test, you need to:

1. Get authentication token:
   TOKEN=$(gcloud auth print-identity-token)

2. Test with token:
   curl https://faq-chatbot-api-abc123-uc.a.run.app/health \
     -H "Authorization: Bearer $TOKEN"
```

---

### 11.3 Testar o Endpoint Deployado

**Passo 1: Obter token de autenticação**
```bash
TOKEN=$(gcloud auth print-identity-token)
```

**Passo 2: Salvar URL do serviço**
```bash
SERVICE_URL=$(gcloud run services describe faq-chatbot-api \
  --region=us-central1 \
  --format='value(status.url)')

echo "Seu endpoint: $SERVICE_URL"
```

**Passo 3: Testar health check**
```bash
curl $SERVICE_URL/health \
  -H "Authorization: Bearer $TOKEN"
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

**Passo 4: Fazer uma pergunta**
```bash
curl -X POST $SERVICE_URL/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my password?"}'
```

**Resposta esperada:**
```json
{
  "answer": "To reset your password, go to Settings > Security > Reset Password. You'll receive an email with instructions.",
  "confidence": "high",
  "score": 0.95,
  "found": true
}
```

**✅ Checkpoint:** Endpoint responde com sucesso e mostra uso do Vertex AI

---

### 11.4 Dar Acesso para Outras Pessoas

**Para dar acesso à estagiária ou avaliador:**

```bash
# Substituir pelo email real
gcloud run services add-iam-policy-binding faq-chatbot-api \
  --region=us-central1 \
  --member='user:estagiaria@example.com' \
  --role='roles/run.invoker'
```

**Depois disso, a pessoa pode acessar assim:**

```bash
# Ela precisa fazer login primeiro
gcloud auth login

# Obter token
TOKEN=$(gcloud auth print-identity-token)

# Testar endpoint
curl https://faq-chatbot-api-abc123-uc.a.run.app/health \
  -H "Authorization: Bearer $TOKEN"
```

---

### 11.5 Verificar Custos

**Cloud Run - Free tier:**
- ✅ Primeiros 2 milhões de requests: GRÁTIS
- ✅ 180k vCPU-seconds por mês: GRÁTIS
- ✅ 360k GiB-seconds por mês: GRÁTIS

**Vertex AI:**
- Gemini 2.5 Flash: ~$0.00025 por 1K caracteres
- Embeddings: ~$0.00002 por 1K caracteres

**Custo total estimado:**
- Uso leve (1k requests): **GRÁTIS** (free tier)
- Uso moderado (10k requests): **$2-5/mês**
- Uso intenso (100k requests): **$20-30/mês**

---

### 11.6 Monitorar o Serviço

**Ver logs:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=faq-chatbot-api" \
  --limit=50 \
  --format=json
```

**Ver métricas:**
```bash
# Abrir no navegador
echo "https://console.cloud.google.com/run/detail/us-central1/faq-chatbot-api/metrics"
```

**Deletar serviço (se necessário):**
```bash
gcloud run services delete faq-chatbot-api --region=us-central1
```

---

### 11.7 Alternativa: Deploy Público (Sem Autenticação)

**⚠️ Menos seguro, mas também válido para certificação**

Se você quiser um endpoint **público** (sem necessidade de token):

```bash
./deploy_cloud_run.sh
```

**Diferença:**
- Qualquer pessoa pode acessar (sem token)
- Útil para demos rápidas
- Menos pontos na certificação (sem IAM)

**Testar (sem token):**
```bash
curl https://faq-chatbot-api-abc123-uc.a.run.app/health
```

---

### 11.8 O que Submeter para Certificação

**Você precisa fornecer:**

1. **URL do serviço:**
   ```
   https://faq-chatbot-api-abc123-uc.a.run.app
   ```

2. **Screenshot do /health endpoint:**
   - Mostrando `"model": "gemini-2.5-flash"`
   - Mostrando `"embeddings": "text-embedding-004"`

3. **Exemplo de request/response:**
   - Pergunta feita
   - Resposta gerada

4. **Prova de deployment no GCP:**
   - URL com domínio `.run.app` (Cloud Run)
   - OU screenshot do console GCP

**✅ Pronto! Você tem um endpoint válido para certificação.**

---

## 🎉 Parabéns!

Você criou um sistema RAG completo:
- ✅ Embeddings com Vertex AI
- ✅ LLM com Gemini
- ✅ Dados organizados no Cloud Storage
- ✅ Interface web funcional
- ✅ Prompt engineering + grounding
- ✅ Output filtering + safety

---

## Troubleshooting

### Erro: `CommandException: No URLs matched`

**Causa:** Nome de arquivo com espaços/caracteres especiais

**Solução:**
```bash
# Renomear arquivo no bucket
python
from google.cloud import storage
client = storage.Client()
bucket = client.bucket("seu-bucket-name")
old_blob = bucket.blob("raw_data/arquivo com espaços.csv")
new_blob_name = "raw_data/arquivo_sem_espacos.csv"
bucket.copy_blob(old_blob, bucket, new_blob_name)
old_blob.delete()
exit()
```

---

### Erro: `python-dotenv could not parse statement`

**Causa:** Comentários decorativos no .env

**Solução:**
```bash
# Editar .env
nano .env

# Remover TODOS os comentários decorativos (linhas com ====)
# Deixar APENAS linhas KEY=value
# Salvar: Ctrl+O, Enter, Ctrl+X
```

---

### Erro: `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`

**Causa:** numpy incompatível com Python 3.12

**Solução:** Já corrigido no requirements.txt! Se aparecer:
```bash
pip install --upgrade numpy scikit-learn
```

---

### Erro: `Permission Denied` ou `API not enabled`

**Solução:**
```bash
# Re-habilitar APIs
gcloud services enable \
  aiplatform.googleapis.com \
  storage-api.googleapis.com

# Re-autenticar
gcloud auth application-default login

# Aguardar 1 minuto
sleep 60

# Tentar novamente
python simple_scripts/03_use_bucket.py
```

---

### Erro: Git push retorna 403

**Causa:** Branch não tem prefixo `claude/`

**Solução:**
```bash
# Criar branch com nome correto
git checkout -b claude/sua-feature-34uUC

# Push com upstream
git push -u origin claude/sua-feature-34uUC
```

---

### Cloud Shell desconectou

**Solução:**
```bash
# Voltar para pasta
cd demo-diy-rag

# Reativar ambiente virtual
source venv/bin/activate

# Verificar projeto
gcloud config get-value project

# Continuar de onde parou
```

---

### Sistema muito lento

**É normal!** Criação de embeddings demora:
- 25 perguntas: ~2 minutos
- 100 perguntas: ~5 minutos
- 1000 perguntas: ~30 minutos

**Dica:** Após criar uma vez, os embeddings ficam salvos no bucket. Próximas execuções são rápidas (só carrega)!

---

## Próximos Passos

### 1. Usar Seu Próprio CSV

Edite seu CSV com perguntas/respostas reais, suba para o bucket (sem espaços no nome!), atualize `.env` e rode novamente `03_use_bucket.py`.

### 2. Customizar Respostas

Edite o prompt template em `simple_faq_rag.py:371` para mudar o tom das respostas.

### 3. Ajustar Parâmetros

No `.env`, ajuste:
- `TOP_K_RESULTS`: Quantos FAQs buscar (padrão: 3)
- `SIMILARITY_THRESHOLD`: Quão similar deve ser (padrão: 0.5)

### 4. Integrar no Seu Sistema

```python
from simple_faq_rag import SimpleFAQSystem
import os
from dotenv import load_dotenv

load_dotenv()
faq = SimpleFAQSystem(project_id=os.getenv('PROJECT_ID'))

# Carregar do bucket
# (implementar load_from_bucket se necessário)

# Ou carregar local
faq.load_csv('seu_faq.csv')
faq.embeddings = np.load('embeddings.npy')

# Usar
result = faq.ask_with_llm("Como criar conta?")
print(result['resposta_gerada'])
```

---

## Resumo do Que Foi Criado

**Arquitetura:**
1. CSV → Cloud Storage (raw_data/)
2. Vertex AI cria embeddings (768 dimensões)
3. Embeddings salvos no Cloud Storage (embeddings/)
4. Gradio carrega automaticamente ao iniciar
5. Usuário pergunta → Busca embeddings similares → Gemini gera resposta → Output filtering → Resposta final

**Requisitos da Certificação Atendidos:**
- ✅ Prompt engineering (template com instruções)
- ✅ Chain-of-thought (opcional, desabilitado)
- ✅ Grounding (respostas baseadas em FAQs)
- ✅ Output filtering (remove dados sensíveis)
- ✅ Safety settings (Gemini filters)
- ✅ Retrieval (embeddings + cosine similarity)
- ✅ Generation (Gemini 1.5 Flash)

---

## Custos Estimados

**Para 1000 perguntas/mês:**
- Embeddings: ~$0.05
- LLM: ~$0.10
- Storage: ~$0.02

**Total: ~$0.20/mês**



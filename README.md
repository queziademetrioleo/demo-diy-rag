# 💬 Sistema FAQ com RAG Simples

**Demo DIY RAG para Certificação Google Cloud Gen AI Specialization**

Sistema FAQ inteligente usando **RAG (Retrieval Augmented Generation)** com:
- 🔍 **Embeddings** (Vertex AI text-embedding-004)
- 🤖 **LLM** (Gemini 1.5 Flash)
- ☁️ **Cloud Storage** (dados organizados em buckets)
- 🎨 **Interface Web** (Streamlit)

## 🎯 O Que Este Sistema Faz

Responde perguntas de usuários usando uma base de conhecimento FAQ:

1. **Retrieval (Busca):** Encontra FAQs relevantes usando embeddings e similaridade de cosseno
2. **Generation (Geração):** Gemini reformula a resposta de forma natural
3. **Output Filtering:** Remove informações sensíveis (emails, telefones, CPFs)

**Exemplo:**
```
Usuário: "Como faço para resetar minha senha?"
Sistema:
  1. Busca FAQs similares (embeddings)
  2. Gemini gera resposta baseada nos FAQs encontrados
  3. Filtra dados sensíveis antes de exibir
```

## 📁 Arquivos Principais

```
demo-diy-rag/
├── simple_faq_rag.py          # Sistema RAG completo (embeddings + LLM)
├── simple_app.py              # Interface Streamlit (auto-load do bucket)
├── requirements.txt           # Dependências Python
├── .env                       # Configurações (não commitar!)
├── .env.example              # Exemplo de configuração
│
├── simple_scripts/
│   ├── 01_test_system.py     # Testar sistema localmente
│   ├── 02_save_knowledge_base.py  # Salvar embeddings
│   └── 03_use_bucket.py      # Processar CSV e enviar ao bucket
│
└── data/
    └── faq_example.csv       # CSV de exemplo (Questions/Answers)
```

## 🚀 Quick Start (5 Minutos)

### Pré-requisitos
- Projeto Google Cloud com billing habilitado
- Cloud Shell (já tem Python 3.12, gcloud, tudo pronto!)

### Passo 1: Clonar e Configurar

```bash
# No Cloud Shell
git clone https://github.com/seu-usuario/demo-diy-rag.git
cd demo-diy-rag

# Instalar dependências
pip install -r requirements.txt
```

### Passo 2: Configurar .env

**IMPORTANTE:** Sem comentários decorativos! Apenas `KEY=value`

```bash
# Copiar exemplo
cp .env.example .env

# Editar (use nano ou editor do Cloud Shell)
nano .env
```

Conteúdo do `.env`:
```bash
PROJECT_ID=seu-projeto-id
LOCATION=us-central1
BUCKET_NAME=seu-projeto-id-data
RAW_DATA_PATH=raw_data/faq_demo.csv
```

### Passo 3: Criar Bucket e Upload CSV

```bash
# Habilitar APIs
gcloud services enable aiplatform.googleapis.com storage-api.googleapis.com

# Criar bucket
gsutil mb gs://seu-projeto-id-data

# Upload do CSV (SEM ESPAÇOS NO NOME!)
# Use Cloud Shell Editor (3 pontos > Upload) para enviar seu CSV
# Depois:
gsutil cp ~/faq_demo.csv gs://seu-projeto-id-data/raw_data/
```

**⚠️ ERRO COMUM:** Nomes de arquivo com espaços quebram gsutil!
- ❌ ERRADO: `FAC - DEMO1 (DIY RAG) - Página1.csv`
- ✅ CORRETO: `faq_demo.csv`

### Passo 4: Processar FAQ e Criar Embeddings

```bash
# Baixa CSV, cria embeddings, sobe para bucket
python simple_scripts/03_use_bucket.py
```

Isso vai:
- ✅ Baixar CSV do bucket
- ✅ Criar embeddings (text-embedding-004)
- ✅ Salvar no bucket: `embeddings/faq_embeddings.npy` e `knowledge_base/faq_metadata.csv`

⏰ **Tempo:** ~5-10 minutos (depende do tamanho do CSV)

### Passo 5: Rodar Interface Web

```bash
# Streamlit no Cloud Shell (portas específicas!)
streamlit run simple_app.py \
  --server.port=8080 \
  --server.address=0.0.0.0 \
  --browser.serverAddress=localhost \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
```

Clique em "Web Preview" (porta 8080) no Cloud Shell.

**⚠️ Se código não atualiza:** Clique no botão "🔄 Recarregar Sistema" na sidebar!

## 📊 Formato do CSV

Seu CSV precisa ter colunas de perguntas e respostas. O sistema aceita:

**Inglês:**
```csv
Questions,Answers
"How to reset password?","Go to Settings > Account > Reset Password..."
"What is the return policy?","You can return items within 30 days..."
```

**Português:**
```csv
pergunta,resposta
"Como resetar senha?","Vá em Configurações > Conta > Resetar Senha..."
"Qual a política de devolução?","Você pode devolver itens em até 30 dias..."
```

O código detecta automaticamente e mapeia para formato interno.

## 🏗️ Arquitetura

```
┌─────────────────┐
│   CSV FAQ       │  ← Perguntas e Respostas
│  (Cloud Storage)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vertex AI       │  ← Criar embeddings (vetores 768D)
│ text-embedding  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Embeddings     │  ← Salvar no bucket
│ (.npy + .csv)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Streamlit App  │  ← Auto-load ao iniciar
│ (simple_app.py) │
└────────┬────────┘
         │
    User Query
         │
         ▼
┌─────────────────┐
│   RETRIEVAL     │  ← Busca por similaridade (cosine)
│  (Top 3 FAQs)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   GENERATION    │  ← Gemini reformula resposta
│ (Gemini 1.5)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OUTPUT FILTER   │  ← Remove dados sensíveis
│  (Regex)        │
└────────┬────────┘
         │
         ▼
    📤 Resposta
```

## 🔧 Tecnologias

| Componente | Tecnologia | Por Quê |
|------------|-----------|---------|
| **Embeddings** | Vertex AI text-embedding-004 | 768 dimensões, SOTA performance |
| **LLM** | Gemini 1.5 Flash | Rápido, barato, boa qualidade |
| **Busca** | scikit-learn cosine_similarity | Simples, sem infra Vector Search |
| **Storage** | Cloud Storage | Organizado, escalável |
| **Interface** | Streamlit | Rápido de desenvolver, bom UX |
| **Python** | 3.12 (Cloud Shell) | Versão default do ambiente |

## ✅ Requisitos da Certificação

Este projeto atende todos os requisitos do **Demo #1**:

- [x] **Prompt Engineering:** Template com instruções de grounding
- [x] **Chain-of-Thought:** Opcional via parâmetro (desabilitado por padrão)
- [x] **Grounding:** Respostas baseadas apenas nos FAQs recuperados
- [x] **Output Filtering:** Remove emails, telefones, CPFs
- [x] **Safety Settings:** Block harmful content (Gemini safety filters)
- [x] **Retrieval:** Embeddings + cosine similarity
- [x] **Generation:** Gemini 1.5 Flash
- [x] **Cloud Storage:** Dados organizados em buckets

## 🐛 Erros Comuns e Soluções

### 1. Erro: `CommandException: No URLs matched`
**Causa:** Nome de arquivo com espaços
**Solução:** Renomear arquivo sem espaços/caracteres especiais

```bash
# Se arquivo já está no bucket com espaços, renomeie:
python
from google.cloud import storage
client = storage.Client()
bucket = client.bucket("seu-bucket")
blob = bucket.blob("raw_data/arquivo com espaços.csv")
bucket.copy_blob(blob, bucket, "raw_data/arquivo_sem_espacos.csv")
blob.delete()
```

### 2. Erro: `python-dotenv could not parse statement`
**Causa:** Comentários decorativos no .env
**Solução:** Remova todos os comentários decorativos!

❌ **ERRADO:**
```bash
# ============================================
# CONFIGURAÇÃO
# ============================================
PROJECT_ID=meu-projeto
```

✅ **CORRETO:**
```bash
PROJECT_ID=meu-projeto
LOCATION=us-central1
BUCKET_NAME=meu-bucket
```

### 3. Erro: `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`
**Causa:** numpy incompatível com Python 3.12
**Solução:** Já corrigido no requirements.txt (numpy>=1.26.0)

### 4. Streamlit não atualiza código
**Causa:** Cache (@st.cache_resource) mantém versão antiga
**Solução:**
1. Incrementar `CODE_VERSION` em `simple_app.py` (linha 38)
2. OU clicar em "🔄 Recarregar Sistema" na sidebar

### 5. Git push retorna 403
**Causa:** Branch sem prefixo `claude/`
**Solução:**
```bash
git checkout -b claude/sua-feature-34uUC
git push -u origin claude/sua-feature-34uUC
```

## 📚 Mais Informações

- **Guia Passo-a-Passo Detalhado:** `PASSO_A_PASSO.md`
- **Documentação antiga (referência):** `archive/`

## 💰 Custos Estimados

Para 1000 perguntas/mês:

- Embeddings: ~$0.05 (text-embedding-004)
- LLM Generation: ~$0.10 (Gemini 1.5 Flash)
- Cloud Storage: ~$0.02 (poucos MB)

**Total:** ~$0.20/mês (aproximadamente)

## 🎓 Sobre a Certificação

Este projeto foi desenvolvido para a certificação:
**Google Cloud Gen AI Services Specialization - Demo #1**

Requisitos atendidos:
- ✅ Código original documentado
- ✅ Dataset no Cloud Storage
- ✅ Business goal claro (FAQ inteligente)
- ✅ RAG completo (Retrieval + Generation)
- ✅ Prompt engineering
- ✅ Output filtering e safety

## 📞 Suporte

**Issues:** Abra issue neste repositório
**Docs Google Cloud:** https://cloud.google.com/vertex-ai/docs

---

**Desenvolvido para Google Cloud Gen AI Specialization** 🚀

# Guia de Solução de Problemas

## 🔧 Problemas Comuns e Soluções

### 1. Autenticação e Permissões

#### Erro: "Permission Denied" ou "403 Forbidden"

**Sintomas:**
```
ERROR: Permission denied on resource 'projects/PROJECT_ID'
```

**Soluções:**
```bash
# 1. Verificar autenticação atual
gcloud auth list

# 2. Fazer login novamente
gcloud auth login
gcloud auth application-default login

# 3. Verificar projeto ativo
gcloud config get-value project

# 4. Definir projeto correto
gcloud config set project SEU-PROJECT-ID

# 5. Verificar roles da service account
gcloud projects get-iam-policy SEU-PROJECT-ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:demo-rag-sa@*"
```

#### Erro: "API not enabled"

**Sintomas:**
```
ERROR: API aiplatform.googleapis.com is not enabled
```

**Solução:**
```bash
# Habilitar todas as APIs necessárias
gcloud services enable \
    aiplatform.googleapis.com \
    storage-api.googleapis.com \
    storage-component.googleapis.com \
    notebooks.googleapis.com \
    compute.googleapis.com

# Verificar APIs habilitadas
gcloud services list --enabled
```

---

### 2. Problemas com Cloud Storage

#### Erro: "Bucket does not exist"

**Sintomas:**
```
google.cloud.exceptions.NotFound: 404 Bucket not found
```

**Soluções:**
```bash
# 1. Verificar se bucket existe
gsutil ls

# 2. Criar bucket
gsutil mb -l us-central1 gs://SEU-BUCKET-NAME

# 3. Verificar permissões
gsutil iam get gs://SEU-BUCKET-NAME
```

#### Erro: "Access Denied" ao fazer upload

**Soluções:**
```bash
# 1. Dar permissões à service account
gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="serviceAccount:demo-rag-sa@SEU-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# 2. Verificar se arquivo existe localmente
ls -la data/

# 3. Tentar upload manual
gsutil cp data/arquivo.csv gs://SEU-BUCKET-NAME/
```

---

### 3. Problemas com Embeddings

#### Erro: "Quota exceeded"

**Sintomas:**
```
ERROR: Quota exceeded for quota metric 'Requests' and limit 'Requests per minute'
```

**Soluções:**
```python
# Reduzir batch size em src/embeddings.py
batch_size = 100  # era 250

# Adicionar delay entre batches
import time
time.sleep(1)  # aguarda 1 segundo entre batches
```

```bash
# Ou solicitar aumento de quota:
# https://console.cloud.google.com/iam-admin/quotas
```

#### Erro: "Invalid embedding dimension"

**Sintomas:**
```
ERROR: Expected 768 dimensions, got 512
```

**Soluções:**
```python
# Verificar modelo correto em .env
EMBEDDING_MODEL=text-embedding-004  # deve ser 004

# Regenerar embeddings
python scripts/02_create_embeddings.py
```

---

### 4. Problemas com Vector Search

#### Erro: "Index deployment taking too long"

**Sintomas:**
- Deploy não completa após 1 hora

**Soluções:**
```bash
# 1. Verificar status no console
# https://console.cloud.google.com/vertex-ai/matching-engine/indexes

# 2. Verificar logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Index" \
    --limit 50 --format json

# 3. Se travado por >2 horas, cancelar e recriar
# Via console ou código
```

#### Erro: "No deployed index found"

**Sintomas:**
```
ERROR: Deployed index 'deployed_produtos_index' not found
```

**Soluções:**
```python
# 1. Verificar se deploy completou
from vector_search import VectorSearchManager
manager = VectorSearchManager(project_id="SEU-PROJECT-ID")

# Listar endpoints
endpoints = aiplatform.MatchingEngineIndexEndpoint.list()
for ep in endpoints:
    print(ep.display_name, ep.deployed_indexes)

# 2. Refazer deploy se necessário
python scripts/03_setup_vector_search.py
```

---

### 5. Problemas com LLM (Gemini)

#### Erro: "Safety settings blocked response"

**Sintomas:**
```
finish_reason: SAFETY
```

**Soluções:**
```python
# Ajustar safety settings em src/rag_system.py
from vertexai.generative_models import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

response = model.generate_content(prompt, safety_settings=safety_settings)
```

#### Erro: "Token limit exceeded"

**Sintomas:**
```
ERROR: Input too long: X tokens (limit: Y tokens)
```

**Soluções:**
```python
# Reduzir top_k para incluir menos documentos
result = rag.query("sua query", top_k=3)  # era 5

# Ou encurtar descrições em src/rag_system.py
description[:100]  # limita descrição a 100 chars
```

---

### 6. Problemas com Dependências Python

#### Erro: "ModuleNotFoundError"

**Sintomas:**
```
ModuleNotFoundError: No module named 'google.cloud'
```

**Soluções:**
```bash
# 1. Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 2. Reinstalar dependências
pip install -r requirements.txt

# 3. Verificar instalação
pip list | grep google-cloud
```

#### Erro: "Conflicting dependencies"

**Sintomas:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**Soluções:**
```bash
# 1. Criar novo ambiente virtual limpo
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# 2. Instalar com --upgrade
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

---

### 7. Problemas com Kaggle Dataset

#### Erro: "Kaggle credentials not found"

**Sintomas:**
```
OSError: Could not find kaggle.json
```

**Soluções:**
```bash
# 1. Baixar credenciais do Kaggle
# - Ir em https://www.kaggle.com/settings
# - Clicar em "Create New API Token"
# - Baixar kaggle.json

# 2. Configurar credenciais
mkdir -p ~/.kaggle
cp ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# 3. Testar
kaggle datasets list
```

#### Solução Alternativa: Usar dados de exemplo

```bash
# Se não conseguir baixar do Kaggle, use dados de exemplo
# O script detecta automaticamente e cria sample data

python scripts/01_download_data.py
# Vai criar 1000 produtos de exemplo automaticamente
```

---

### 8. Problemas de Performance

#### Lentidão na geração de embeddings

**Soluções:**
```python
# Aumentar batch_size (se não atingir quota)
# Em src/embeddings.py
batch_size = 250  # máximo permitido

# Usar paralelização (avançado)
from concurrent.futures import ThreadPoolExecutor
```

#### Latência alta nas queries

**Soluções:**
```python
# 1. Reduzir top_k
top_k = 3  # em vez de 5

# 2. Implementar cache
from functools import lru_cache

@lru_cache(maxsize=100)
def query_with_cache(query):
    return rag.query(query)

# 3. Aumentar replicas do endpoint
# Em scripts/03_setup_vector_search.py
max_replica_count = 5  # era 2
```

---

### 9. Problemas com Variáveis de Ambiente

#### Erro: "Environment variable not set"

**Sintomas:**
```
KeyError: 'PROJECT_ID'
```

**Soluções:**
```bash
# 1. Verificar se .env existe
ls -la .env

# 2. Se não existir, copiar exemplo
cp .env.example .env

# 3. Editar com seus valores
nano .env
# ou
code .env

# 4. Verificar se está carregando
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('PROJECT_ID'))"
```

---

### 10. Debugging Avançado

#### Habilitar logs detalhados

```python
# Adicionar no início dos scripts
import logging
logging.basicConfig(level=logging.DEBUG)

# Para google-cloud
import google.cloud.logging
client = google.cloud.logging.Client()
client.setup_logging()
```

#### Verificar chamadas de API

```python
# Monitorar requests
import google.cloud.aiplatform as aiplatform
aiplatform.init(project="SEU-PROJECT", location="us-central1")

# Logs vão aparecer no Cloud Console:
# https://console.cloud.google.com/logs
```

#### Executar em modo debug

```bash
# Python debugger
python -m pdb scripts/01_download_data.py

# IPython para debugging interativo
pip install ipython
ipython

# Dentro do IPython:
%run scripts/01_download_data.py
```

---

## 📞 Suporte Adicional

### Documentação Oficial
- [Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)
- [Vector Search Guide](https://cloud.google.com/vertex-ai/docs/matching-engine/overview)
- [Gemini API Docs](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)

### Comunidade
- [Stack Overflow - google-cloud-platform](https://stackoverflow.com/questions/tagged/google-cloud-platform)
- [Google Cloud Community](https://www.googlecloudcommunity.com/)

### Suporte Google Cloud
- [Console de Suporte](https://console.cloud.google.com/support)
- [Status do Serviço](https://status.cloud.google.com/)

---

## 🐛 Reportar Bugs

Se encontrar um problema não listado aqui:

1. Verifique issues existentes no GitHub
2. Colete informações:
   ```bash
   # Versão Python
   python --version

   # Versões de pacotes
   pip freeze > versions.txt

   # Logs de erro completos
   ```
3. Abra uma issue com:
   - Descrição do problema
   - Passos para reproduzir
   - Logs de erro
   - Ambiente (OS, Python version, etc)

---

**Última atualização:** Janeiro 2026

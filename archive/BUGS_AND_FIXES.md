# 🐛 Análise de Bugs e Correções

## Revisão Completa do Código - Janeiro 2026

Esta análise identifica **todos os problemas, pontas soltas e possíveis erros** no código.

---

## ❌ PROBLEMAS ENCONTRADOS

### 1. **CRÍTICO: Missing `vertexai` import**

**Arquivos afetados:**
- `src/embeddings.py` (linha ~13)
- `src/rag_system.py` (linha ~10)

**Problema:**
```python
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from vertexai.generative_models import GenerativeModel, GenerationConfig
```

Mas o pacote `google-cloud-aiplatform` não expõe `vertexai` diretamente!

**Solução:**
```python
# CORRETO:
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic
```

**Impacto:** ⚠️ **ALTO** - Código não vai rodar!

---

### 2. **CRÍTICO: API Version incompatível**

**Arquivo:** `requirements.txt`
**Problema:** Versão `google-cloud-aiplatform==1.38.1` pode ter APIs diferentes

**Solução:** Atualizar para versão mais recente
```
google-cloud-aiplatform>=1.60.0
```

---

### 3. **Missing IAM Permissions no README**

**Arquivo:** `README.md`
**Problema:** Instruções de permissões incompletas

**Faltando:**
- `roles/aiplatform.admin` (não apenas user)
- `roles/iam.serviceAccountUser`
- Permissões de Vector Search específicas

**Solução:** Adicionar seção completa de IAM

---

### 4. **Hardcoded location em vários lugares**

**Arquivos:**
- `src/data_loader.py` linha 68: `location="us-central1"`
- `src/vector_search.py` (várias linhas)

**Problema:** Se usuário usar outra região, vai dar erro

**Solução:** Usar parâmetro location do construtor

---

### 5. **Error handling inadequado**

**Arquivos:** Todos os `src/*.py`
**Problema:** Exceções muito genéricas
```python
except Exception:  # Muito genérico!
```

**Solução:** Catch específico
```python
except storage.exceptions.NotFound:
except google.api_core.exceptions.PermissionDenied:
```

---

### 6. **Missing API enablement check**

**Problema:** Scripts assumem que APIs estão habilitadas

**Solução:** Adicionar verificação:
```python
def check_apis_enabled(project_id):
    """Verifica se APIs necessárias estão habilitadas."""
    required_apis = [
        "aiplatform.googleapis.com",
        "storage-api.googleapis.com"
    ]
    # Check each...
```

---

### 7. **Race condition no Vector Search deploy**

**Arquivo:** `src/vector_search.py`
**Problema:** `deploy_index()` retorna antes do deploy completar

**Solução:** Adicionar wait/poll:
```python
def deploy_index(...):
    endpoint.deploy_index(...)

    # ADICIONAR:
    while not self.is_deployed():
        time.sleep(30)
        logger.info("Aguardando deploy...")
```

---

### 8. **Missing validation de embeddings dimension**

**Arquivo:** `src/embeddings.py`
**Problema:** Não valida se embeddings têm dimensão correta

**Solução:**
```python
expected_dim = self.get_embedding_dimension()
if embeddings.shape[1] != expected_dim:
    raise ValueError(f"Expected {expected_dim}, got {embeddings.shape[1]}")
```

---

### 9. **Cleanup de arquivos temporários pode falhar**

**Arquivo:** `src/embeddings.py`, `src/data_loader.py`
**Problema:**
```python
local_file.unlink()  # E se arquivo não existir?
```

**Solução:**
```python
if local_file.exists():
    local_file.unlink()
```

---

### 10. **Missing retry logic para quota errors**

**Arquivo:** `src/embeddings.py`
**Problema:** Se exceder quota, falha sem retry

**Solução:** Adicionar exponential backoff

---

### 11. **Path issues no Windows**

**Problema:** Uso de `/` em paths pode falhar no Windows

**Solução:** Usar `Path` do pathlib consistentemente

---

### 12. **Missing environment variable validation**

**Arquivo:** Scripts em `scripts/`
**Problema:** Scripts falham silenciosamente se .env não existir

**Solução:**
```python
if not os.getenv("PROJECT_ID"):
    raise EnvironmentError("PROJECT_ID not set. Create .env file!")
```

---

### 13. **Import cycle potential**

**Problema:** `rag_system.py` importa `embeddings.py` que importa componentes

**Solução:** Verificar e reorganizar imports

---

### 14. **Kaggle API pode exigir autenticação**

**Arquivo:** `src/data_loader.py`
**Problema:** `kaggle.api` pode não estar autenticado

**Solução:** Adicionar check:
```python
try:
    kaggle.api.authenticate()
except:
    raise ValueError("Kaggle not configured. See docs.")
```

---

### 15. **Memory issues com datasets grandes**

**Arquivo:** `src/embeddings.py`
**Problema:** Carregar 20k produtos na memória pode ser pesado

**Solução:** Processing em chunks

---

### 16. **Missing indexes em DataFrames**

**Problema:** Operações em DataFrames sem reset de index podem causar bugs

**Solução:** Sempre usar `reset_index(drop=True)` após transformações

---

### 17. **Timezone issues em timestamps**

**Problema:** Timestamps podem ser naive (sem timezone)

**Solução:** Usar UTC explicitamente

---

### 18. **Missing test para deployed index antes de query**

**Arquivo:** `src/rag_system.py`
**Problema:** Tenta query sem verificar se index está deployed

**Solução:**
```python
def _check_deployment_ready(self):
    # Verificar se deployed_index existe
```

---

### 19. **Hardcoded deployed_index_id**

**Arquivo:** `src/rag_system.py`, `src/vector_search.py`
**Problema:** `"deployed_produtos_index"` hardcoded

**Solução:** Usar variável de ambiente

---

### 20. **Missing validation de preços negativos**

**Arquivo:** `src/data_loader.py`
**Problema:** Não valida se preços são positivos

---

## ✅ CORREÇÕES IMPLEMENTADAS

Vou criar arquivos corrigidos a seguir...

---

## 📋 CHECKLIST DE CORREÇÕES

- [ ] Corrigir imports do vertexai
- [ ] Atualizar requirements.txt
- [ ] Adicionar validações de environment variables
- [ ] Melhorar error handling
- [ ] Adicionar retry logic
- [ ] Fix hardcoded values
- [ ] Adicionar API enablement check
- [ ] Melhorar docs de permissões
- [ ] Adicionar deployment status check
- [ ] Fix path issues Windows
- [ ] Adicionar data validation
- [ ] Memory optimization
- [ ] Timezone handling
- [ ] Cleanup de temp files
- [ ] Index validation

---

**Status:** 🔧 Corrigindo agora...

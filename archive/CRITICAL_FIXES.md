# ⚠️ CORREÇÕES CRÍTICAS - LEIA ANTES DE EXECUTAR

## 🔴 Problemas Críticos Encontrados e Soluções

### 1. **MAIS CRÍTICO: Inicialização do Vertex AI**

**Problema:** Falta inicializar o módulo `vertexai` antes de usar os modelos.

**Onde:** `src/embeddings.py` e `src/rag_system.py`

**Correção:**
```python
# ADICIONAR no início do __init__:
import vertexai
vertexai.init(project=project_id, location=location)
```

**Como corrigir:**

Em `src/embeddings.py`, linha 56 (dentro do `__init__`), ADICIONAR ANTES da linha `aiplatform.init`:
```python
# Importar vertexai no topo do arquivo se ainda não tem
import vertexai

# Dentro do __init__, ANTES de aiplatform.init:
vertexai.init(project=self.project_id, location=self.location)
aiplatform.init(project=project_id, location=location)
```

Em `src/rag_system.py`, fazer o mesmo no `__init__`.

---

### 2. **CRÍTICO: Atualizar requirements.txt**

**Problema:** Versão do google-cloud-aiplatform pode estar desatualizada

**Correção:**
```bash
# Editar requirements.txt, mudar linha:
google-cloud-aiplatform==1.38.1

# Para:
google-cloud-aiplatform>=1.38.1
```

Depois reinstalar:
```bash
pip install --upgrade google-cloud-aiplatform
```

---

### 3. **CRÍTICO: Permissões IAM Faltando**

**Problema:** README não documenta TODAS as permissões necessárias

**Correção Completa:**

```bash
# 1. Roles para o usuário
gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="user:seu-email@gmail.com" \
    --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="user:seu-email@gmail.com" \
    --role="roles/storage.admin"

# 2. Roles para Service Account (se usar)
gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="serviceAccount:demo-rag-sa@SEU-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.admin"

gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="serviceAccount:demo-rag-sa@SEU-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding SEU-PROJECT-ID \
    --member="serviceAccount:demo-rag-sa@SEU-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

---

### 4. **IMPORTANTE: APIs que DEVEM estar habilitadas**

**Correção:** Execute TODOS estes comandos:

```bash
# APIs essenciais
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable notebooks.googleapis.com

# APIs adicionais para Vector Search
gcloud services enable serviceusage.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

**Verificar se habilitadas:**
```bash
gcloud services list --enabled | grep -E "aiplatform|storage|compute"
```

---

### 5. **CRÍTICO: Validação de Environment Variables**

**Problema:** Scripts não verificam se .env está configurado

**Solução:** Criar arquivo de validação

Criar arquivo `scripts/00_validate_setup.py`:

```python
#!/usr/bin/env python3
"""
Script 00: Validação de Setup
Verifica se tudo está configurado corretamente ANTES de executar.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def validate_env():
    """Valida variáveis de ambiente."""
    load_dotenv()

    required_vars = [
        "PROJECT_ID",
        "BUCKET_NAME",
        "LOCATION"
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Variáveis faltando no .env: {', '.join(missing)}")
        print("\n1. Copie .env.example para .env:")
        print("   cp .env.example .env")
        print("\n2. Edite .env e preencha as variáveis")
        return False

    print("✅ Variáveis de ambiente OK")
    return True


def validate_gcloud_auth():
    """Valida autenticação gcloud."""
    import subprocess

    try:
        result = subprocess.run(
            ["gcloud", "auth", "list"],
            capture_output=True,
            text=True
        )

        if "ACTIVE" in result.stdout:
            print("✅ gcloud autenticado")
            return True
        else:
            print("❌ gcloud NÃO autenticado")
            print("Execute: gcloud auth login")
            print("         gcloud auth application-default login")
            return False

    except FileNotFoundError:
        print("❌ gcloud CLI não encontrado")
        print("Instale: https://cloud.google.com/sdk/docs/install")
        return False


def validate_apis_enabled():
    """Valida se APIs estão habilitadas."""
    import subprocess
    from dotenv import load_dotenv

    load_dotenv()
    project_id = os.getenv("PROJECT_ID")

    if not project_id:
        print("⚠️  PROJECT_ID não definido, pulando validação de APIs")
        return True

    required_apis = [
        "aiplatform.googleapis.com",
        "storage-api.googleapis.com"
    ]

    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--enabled", f"--project={project_id}"],
            capture_output=True,
            text=True
        )

        missing_apis = []
        for api in required_apis:
            if api not in result.stdout:
                missing_apis.append(api)

        if missing_apis:
            print(f"❌ APIs não habilitadas: {', '.join(missing_apis)}")
            print("\nHabilite com:")
            print(f"gcloud services enable {' '.join(missing_apis)} --project={project_id}")
            return False
        else:
            print("✅ APIs habilitadas")
            return True

    except Exception as e:
        print(f"⚠️  Não foi possível validar APIs: {e}")
        return True  # Não bloquear


def validate_python_packages():
    """Valida se pacotes Python estão instalados."""
    required_packages = [
        "google-cloud-aiplatform",
        "google-cloud-storage",
        "pandas",
        "numpy",
        "loguru",
        "python-dotenv",
        "streamlit"
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"❌ Pacotes Python faltando: {', '.join(missing)}")
        print("\nInstale com:")
        print("pip install -r requirements.txt")
        return False

    print("✅ Pacotes Python instalados")
    return True


def main():
    """Executa todas as validações."""
    print("="*60)
    print("🔍 VALIDAÇÃO DE SETUP - Demo DIY RAG")
    print("="*60)
    print()

    checks = [
        ("Environment Variables", validate_env),
        ("Python Packages", validate_python_packages),
        ("gcloud Authentication", validate_gcloud_auth),
        ("Google Cloud APIs", validate_apis_enabled),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n📋 Verificando: {name}")
        print("-" * 60)
        results.append(check_func())
        print()

    print("="*60)
    if all(results):
        print("✅ TODAS AS VALIDAÇÕES PASSARAM!")
        print("Você pode executar os scripts com segurança.")
        print("\nPróximos passos:")
        print("1. python scripts/01_download_data.py")
        print("2. python scripts/02_create_embeddings.py")
        print("3. python scripts/03_setup_vector_search.py")
    else:
        print("❌ ALGUMAS VALIDAÇÕES FALHARAM")
        print("Corrija os problemas acima antes de continuar.")
        sys.exit(1)

    print("="*60)


if __name__ == "__main__":
    main()
```

**Como usar:**
```bash
# SEMPRE executar isso PRIMEIRO:
python scripts/00_validate_setup.py
```

---

### 6. **IMPORTANTE: Hardcoded location**

**Problema:** Location `"us-central1"` está hardcoded em alguns lugares

**Arquivos para corrigir:**
- `src/data_loader.py` linha 68
- `src/embeddings.py` vários locais
- `src/vector_search.py` vários locais

**Correção em `src/data_loader.py`:**
```python
# Linha 66-70, MUDAR de:
bucket = self.storage_client.create_bucket(
    self.bucket_name,
    location="us-central1"  # ❌ Hardcoded
)

# Para:
# Adicionar self.location no __init__
def __init__(self, project_id, bucket_name, local_data_path="./data", location="us-central1"):
    self.location = location
    # ...

# E usar:
bucket = self.storage_client.create_bucket(
    self.bucket_name,
    location=self.location  # ✅ Usando parâmetro
)
```

---

### 7. **CRÍTICO: Aguardar deploy do Vector Search**

**Problema:** Script 03 retorna antes do deploy completar

**Onde:** `scripts/03_setup_vector_search.py`

**Correção:**
Adicionar após o `manager.deploy_index(...)`:

```python
# scripts/03_setup_vector_search.py
# Após manager.deploy_index(), ADICIONAR:

logger.info("\n⏰ Aguardando deploy completar...")
logger.info("Isso pode levar 30-45 minutos. Seja paciente!")

import time
max_wait = 60  # minutos
wait_interval = 2  # minutos

for i in range(max_wait // wait_interval):
    time.sleep(wait_interval * 60)  # Aguardar 2 minutos

    # Tentar verificar status
    try:
        # Reload endpoint
        endpoint = manager.get_or_create_endpoint()

        # Verificar deployed indexes
        if endpoint.deployed_indexes:
            logger.info(f"✅ Deploy completado após {(i+1)*wait_interval} minutos!")
            break
        else:
            logger.info(f"⏳ Aguardando... ({(i+1)*wait_interval} min)")

    except Exception as e:
        logger.warning(f"Ainda deployando... ({(i+1)*wait_interval} min)")

else:
    logger.warning("⚠️  Deploy ainda em andamento após 60 minutos")
    logger.info("Verifique manualmente: https://console.cloud.google.com/vertex-ai/matching-engine")
```

---

## 📋 ORDEM CORRETA DE EXECUÇÃO

### Setup Inicial (uma vez):

```bash
# 1. Clonar e entrar no diretório
cd demo-diy-rag

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
nano .env  # Editar PROJECT_ID, BUCKET_NAME

# 5. Autenticar gcloud
gcloud auth login
gcloud auth application-default login
gcloud config set project SEU-PROJECT-ID

# 6. Habilitar APIs
gcloud services enable aiplatform.googleapis.com storage-api.googleapis.com

# 7. Configurar permissões (ver seção 3 acima)

# 8. VALIDAR SETUP
python scripts/00_validate_setup.py
```

### Execução dos Scripts (em ordem):

```bash
# 1. Download de dados
python scripts/01_download_data.py

# 2. Criar embeddings (10-15 min)
python scripts/02_create_embeddings.py

# 3. Setup Vector Search (30-45 min!)
python scripts/03_setup_vector_search.py

# 4. Testar sistema
python scripts/05_test_api.py

# 5. Executar Chat App
streamlit run app.py
```

---

## 🆘 Se algo der errado

### "ModuleNotFoundError: vertexai"

```bash
pip install --upgrade google-cloud-aiplatform
```

### "Permission Denied"

```bash
gcloud auth application-default login
# E verificar roles (seção 3)
```

### "API not enabled"

```bash
gcloud services enable aiplatform.googleapis.com --project=SEU-PROJECT
```

### "Bucket not found"

```bash
gsutil mb -l us-central1 gs://SEU-BUCKET-NAME
```

### Scripts muito lentos

É normal! Especialmente:
- Script 02: 10-15 min para 1000 produtos
- Script 03: 30-45 min para deploy

---

## ✅ Checklist Pré-Execução

Antes de executar scripts, verificar:

- [ ] ✅ .env configurado com PROJECT_ID e BUCKET_NAME
- [ ] ✅ gcloud autenticado
- [ ] ✅ APIs habilitadas
- [ ] ✅ Permissões IAM configuradas
- [ ] ✅ Python packages instalados
- [ ] ✅ `scripts/00_validate_setup.py` passou

---

**IMPORTANTE:** Salve este documento e consulte antes de executar qualquer script!

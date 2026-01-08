# 🚀 Guia Rápido de Início

## Setup em 5 Passos (30 minutos + tempo de deploy)

### Passo 1: Configurar Google Cloud (10 min)

```bash
# 1. Fazer login
gcloud auth login
gcloud auth application-default login

# 2. Criar/selecionar projeto
gcloud projects create seu-projeto-rag
gcloud config set project seu-projeto-rag

# 3. Habilitar APIs
gcloud services enable aiplatform.googleapis.com storage-api.googleapis.com

# 4. Anotar PROJECT_ID
export PROJECT_ID=$(gcloud config get-value project)
echo $PROJECT_ID
```

### Passo 2: Setup Local (5 min)

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/demo-diy-rag.git
cd demo-diy-rag

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
nano .env  # edite PROJECT_ID e BUCKET_NAME
```

### Passo 3: Preparar Dados (5 min)

```bash
# Executar script de download
python scripts/01_download_data.py

# Saída esperada:
# ✅ Dataset baixado: 1000 produtos (ou 20k do Kaggle)
# ✅ Upload para GCS completo
```

### Passo 4: Criar Embeddings (10 min)

```bash
# Gerar embeddings
python scripts/02_create_embeddings.py

# Saída esperada:
# ✅ 1000 embeddings criados
# ✅ Salvos no GCS
```

### Passo 5: Setup Vector Search (40 min - maioria é deploy)

```bash
# Criar índice e endpoint
python scripts/03_setup_vector_search.py

# IMPORTANTE: Deploy leva 30-45 minutos!
# ⏰ Aguarde completar antes de testar
```

### Testar o Sistema

```bash
# Após deploy completar, testar:
python scripts/05_test_api.py

# Saída esperada:
# ✅ Resposta: "Encontrei 3 smartphones..."
```

## 🎯 Checklist Rápido

- [ ] Google Cloud projeto criado
- [ ] APIs habilitadas
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] .env configurado
- [ ] Dados carregados
- [ ] Embeddings criados
- [ ] Vector Search deployado (aguarde 30-45 min!)
- [ ] Testes executados com sucesso

## ❓ Problemas?

Veja [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📚 Próximos Passos

1. Explore o notebook: `notebooks/demo_rag_completo.ipynb`
2. Leia o whitepaper: `WHITEPAPER.md`
3. Customize para seu caso de uso

---

**Pronto!** Sistema RAG funcionando em ~1 hora!

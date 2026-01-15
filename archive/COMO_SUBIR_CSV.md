# 📤 COMO SUBIR SEU CSV DO COMPUTADOR PARA O GOOGLE CLOUD

## 🎯 3 Formas Fáceis de Fazer Upload

---

## ✨ FORMA 1: Upload pelo Google Cloud Console (MAIS FÁCIL!)

### **Passo a Passo:**

**1. Abrir Google Cloud Console:**
- Vá para: https://console.cloud.google.com/
- Faça login com sua conta

**2. Ir para Cloud Storage:**
- No menu lateral (☰), clique em **"Cloud Storage"** > **"Buckets"**
- OU busque por "Storage" na barra de pesquisa

**3. Encontrar seu Bucket:**
- Procure o bucket: `seu-project-id-data`
- Clique no nome do bucket

**4. Navegar para a pasta:**
- Clique na pasta **`raw_data/`**
- Se não existir, crie clicando em **"Create folder"** > digite `raw_data`

**5. Fazer Upload:**
- Clique no botão **"UPLOAD FILES"** (no topo)
- Selecione seu arquivo CSV do computador
- Aguarde o upload terminar ✅

**6. Verificar:**
```
✓ Você deve ver: raw_data/seu_arquivo.csv
```

### **📊 Exemplo Visual:**
```
Bucket: seu-project-id-data
  └── raw_data/
      └── meu_faq.csv  ← SEU ARQUIVO AQUI!
```

---

## 🖥️ FORMA 2: Upload pelo Cloud Shell (Mais Técnico)

### **Passo a Passo:**

**1. Abrir Cloud Shell:**
- No Google Cloud Console, clique no ícone **">_"** (canto superior direito)

**2. Fazer Upload do Arquivo Local:**
- No Cloud Shell, clique no **menu ⋮** (três pontinhos)
- Selecione **"Upload"**
- Escolha seu arquivo CSV do computador
- Aguarde aparecer "Upload completed"

**3. Verificar que Subiu:**
```bash
ls ~/*.csv
```

**Vai mostrar:**
```
/home/seu_usuario/meu_faq.csv
```

**4. Copiar para o Bucket:**
```bash
# Copiar para o bucket
gsutil cp ~/meu_faq.csv gs://seu-project-id-data/raw_data/

# OU se preferir mover (apaga do Cloud Shell)
gsutil mv ~/meu_faq.csv gs://seu-project-id-data/raw_data/
```

**5. Verificar no Bucket:**
```bash
gsutil ls gs://seu-project-id-data/raw_data/
```

**Deve mostrar:**
```
gs://seu-project-id-data/raw_data/meu_faq.csv
```

✅ **Pronto! Arquivo no bucket!**

---

## 💻 FORMA 3: Upload via gcloud CLI (Se tiver instalado localmente)

### **Pré-requisito:**
- Ter `gcloud CLI` instalado no seu computador
- Link: https://cloud.google.com/sdk/docs/install

### **Passo a Passo:**

**1. Fazer Login:**
```bash
gcloud auth login
```

**2. Configurar Projeto:**
```bash
gcloud config set project seu-project-id
```

**3. Upload Direto do PC:**
```bash
# Navegue até onde está seu CSV
cd ~/Downloads  # ou onde seu CSV está

# Upload direto para o bucket
gsutil cp meu_faq.csv gs://seu-project-id-data/raw_data/
```

**4. Verificar:**
```bash
gsutil ls gs://seu-project-id-data/raw_data/
```

✅ **Arquivo no bucket!**

---

## 📋 DEPOIS DO UPLOAD - Como Usar no Sistema

### **1. Atualizar arquivo `.env`:**

No Cloud Shell (ou localmente):

```bash
cd ~/demo-diy-rag
nano .env
```

**Altere a linha:**
```bash
# ANTES:
RAW_DATA_PATH=raw_data/faq_example.csv

# DEPOIS (com o nome do SEU arquivo):
RAW_DATA_PATH=raw_data/meu_faq.csv
```

**Salvar:**
- `Ctrl + O` (salvar)
- `Enter` (confirmar)
- `Ctrl + X` (sair)

---

### **2. Executar o Sistema:**

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Rodar com seu CSV
python simple_scripts/03_use_bucket.py
```

**O sistema vai:**
1. ✅ Baixar `meu_faq.csv` do bucket
2. ✅ Processar suas perguntas e respostas
3. ✅ Criar embeddings com IA
4. ✅ Salvar base de conhecimento no bucket

---

## ✅ VERIFICAÇÃO FINAL

### **Conferir se deu certo:**

**No Cloud Shell:**
```bash
# Ver arquivos no bucket
gsutil ls -r gs://seu-project-id-data/

# Deve mostrar:
# gs://seu-project-id-data/raw_data/meu_faq.csv
# gs://seu-project-id-data/embeddings/
# gs://seu-project-id-data/knowledge_base/
```

**OU no Console:**
- Vá para Cloud Storage
- Abra bucket: `seu-project-id-data`
- Veja as pastas:
  - ✅ `raw_data/` → seu CSV
  - ✅ `embeddings/` → arquivos .npy
  - ✅ `knowledge_base/` → metadata.csv

---

## 📝 FORMATO OBRIGATÓRIO DO CSV

Seu CSV **DEVE** ter este formato:

```csv
pergunta,resposta
"Como criar conta?","Clique em Cadastre-se no canto superior direito"
"Esqueci minha senha","Vá em Login > Esqueci Senha > Digite seu email"
"Qual horário de atendimento?","Segunda a sexta, das 8h às 18h"
```

### **Regras Importantes:**

✅ **Primeira linha:** Cabeçalho com `pergunta,resposta`
✅ **Aspas:** Use se tiver vírgulas no texto
✅ **Codificação:** UTF-8 (salvar como UTF-8)
✅ **Quantidade:** Mínimo 5 perguntas, sem limite máximo

❌ **Evitar:**
- Linhas vazias
- Caracteres especiais estranhos
- Múltiplas colunas além de pergunta e resposta

---

## 🎯 EXEMPLO COMPLETO

### **Seu arquivo: `suporte_loja.csv`**

```csv
pergunta,resposta
"Como rastrear pedido?","Acesse Minha Conta > Pedidos > Digite número do pedido"
"Qual prazo de entrega?","5 a 7 dias úteis para todo Brasil"
"Posso trocar produto?","Sim, até 30 dias após recebimento com nota fiscal"
"Aceitam quais pagamentos?","Cartão, PIX, boleto e PayPal"
"Como falar com atendente?","WhatsApp: (11) 99999-9999 ou chat no site"
```

### **Upload:**
```bash
# Opção 1: Pelo Console (arrastar e soltar na pasta raw_data/)

# Opção 2: Pelo Cloud Shell
gsutil cp suporte_loja.csv gs://seu-project-id-data/raw_data/
```

### **Configurar `.env`:**
```bash
RAW_DATA_PATH=raw_data/suporte_loja.csv
```

### **Executar:**
```bash
python simple_scripts/03_use_bucket.py
```

✅ **Sistema funcionando com SEUS dados!**

---

## 🆘 PROBLEMAS COMUNS

### **"Upload failed"**
- Verificar conexão internet
- Arquivo muito grande? (máximo recomendado: 10MB)
- Tentar novamente em alguns minutos

### **"Permission denied"**
- Verificar se está no projeto correto:
  ```bash
  gcloud config get-value project
  # Deve mostrar: seu-project-id
  ```

### **"CSV format error"**
- Verificar se tem cabeçalho `pergunta,resposta`
- Abrir no Excel/Google Sheets e salvar como CSV UTF-8
- Verificar se não tem colunas extras

### **"File not found"**
- Conferir nome do arquivo em `.env`
- Listar arquivos no bucket:
  ```bash
  gsutil ls gs://seu-project-id-data/raw_data/
  ```

---

## 🎉 PRONTO!

Agora você sabe **3 formas diferentes** de subir seu CSV!

**Recomendação:**
- 👍 **Iniciante:** Use FORMA 1 (Console - arrastar e soltar)
- 👨‍💻 **Intermediário:** Use FORMA 2 (Cloud Shell)
- 🚀 **Avançado:** Use FORMA 3 (gcloud local)

**Próximo passo:**
Volte para **PASSO_A_PASSO.md** e siga a partir da FASE 5! 🚀

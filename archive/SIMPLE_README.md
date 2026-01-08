# 🤖 Sistema FAQ Simples com IA

## 💡 O que é isso?

Um sistema **SUPER SIMPLES** para fazer um FAQ inteligente usando IA.

Você tem um CSV com perguntas e respostas? Este sistema encontra a resposta mais similar à pergunta do usuário!

**SEM complexidade!** **SEM LLM caro!** Só busca semântica simples e eficiente.

---

## 🎯 Como Funciona? (Explicação Simples)

```
1. Você tem um CSV:
   pergunta,resposta
   "Como resetar senha?","Vá em Configurações..."
   "Qual o prazo?","5-7 dias úteis"

2. O sistema transforma perguntas em números (vetores):
   "Como resetar senha?" → [0.2, 0.5, 0.1, ...] (768 números)

3. Quando alguém pergunta "esqueci minha senha":
   - Sistema transforma em números
   - Compara com todas as perguntas
   - Acha a mais similar
   - Retorna a resposta correspondente!
```

**Não gera resposta nova!** Só encontra a resposta que já existe no CSV.

---

## 🚀 Começando (Super Rápido!)

### 1. Configurar Projeto

```bash
# 1. Clonar repositório (se ainda não fez)
git clone https://github.com/seu-usuario/demo-diy-rag.git
cd demo-diy-rag

# 2. Mudar para branch simples
git checkout simple-faq-rag

# 3. Configurar .env
cp .env.example .env
nano .env  # Preencher PROJECT_ID

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Autenticar Google Cloud
gcloud auth application-default login
```

### 2. Testar com Exemplo Incluído

```bash
# Executa teste interativo
python simple_scripts/01_test_system.py
```

Isso vai:
- ✅ Carregar 25 perguntas de exemplo
- ✅ Criar base de conhecimento
- ✅ Testar perguntas
- ✅ Abrir modo interativo para você testar!

### 3. Usar Chat App Web

```bash
# Abrir interface web bonita
streamlit run simple_app.py
```

Abre no navegador automaticamente! 🎉

---

## 📁 Seu CSV Deve Ser Assim

**Arquivo:** `data/seu_faq.csv`

```csv
pergunta,resposta
"Como faço para redefinir minha senha?","Vá em Configurações > Segurança > Redefinir Senha"
"Qual o prazo de entrega?","O prazo é de 5-7 dias úteis"
"Vocês aceitam PIX?","Sim! Selecione PIX no checkout"
```

**Regras:**
- ✅ Duas colunas: `pergunta` e `resposta`
- ✅ Primeira linha é cabeçalho
- ✅ Use aspas se tiver vírgulas no texto
- ✅ Pode ter quantas linhas quiser!

---

## 💻 Usando no Código

### Exemplo Básico

```python
from simple_faq_rag import SimpleFAQSystem

# 1. Inicializar
faq = SimpleFAQSystem(project_id="seu-projeto-id")

# 2. Carregar seu CSV
faq.load_csv("data/seu_faq.csv")

# 3. Criar base de conhecimento (demora ~2 min)
faq.create_knowledge_base()

# 4. Fazer perguntas!
result = faq.ask("Como resetar senha?")

if result['found']:
    print(f"Resposta: {result['resposta']}")
    print(f"Confiança: {result['confidence']}")
    print(f"Score: {result['score']:.0%}")
else:
    print("Não encontrei resposta para isso")
```

### Salvar Base para Usar Depois

```python
# Criar e salvar
faq.create_knowledge_base()
faq.save_knowledge_base("data/minha_base")

# Carregar depois (RÁPIDO!)
faq.load_knowledge_base("data/minha_base")
# Pronto! Não precisa reprocessar
```

---

## 📊 Entendendo os Resultados

Quando você faz uma pergunta, recebe:

```python
{
    'pergunta_encontrada': 'Como faço para redefinir minha senha?',
    'resposta': 'Vá em Configurações > Segurança...',
    'score': 0.85,  # 85% de similaridade
    'confidence': 'alta',  # muito alta, alta, média, baixa
    'found': True  # False se não encontrou nada
}
```

**Score:**
- **0.9 - 1.0:** Praticamente idêntica! (muito alta)
- **0.8 - 0.9:** Muito similar (alta)
- **0.7 - 0.8:** Similar (média)
- **< 0.7:** Não retorna (baixa)

---

## 🎨 Chat App - Interface Web

```bash
streamlit run simple_app.py
```

**Funcionalidades:**
- 💬 Chat interativo
- 📊 Mostra confiança e score
- 🔍 Ver pergunta original encontrada
- ⚙️ Configurar facilmente
- 🗑️ Limpar conversa

**Como usar:**
1. Preencher Project ID na sidebar
2. Verificar caminho do CSV
3. Clicar "Inicializar Sistema"
4. Aguardar criação da base (1-2 min)
5. Começar a perguntar!

---

## 🔧 Scripts Incluídos

### `simple_scripts/01_test_system.py`
Teste completo do sistema:
- Carrega CSV
- Cria base de conhecimento
- Testa perguntas exemplo
- Modo interativo

```bash
python simple_scripts/01_test_system.py
```

### `simple_scripts/02_save_knowledge_base.py`
Salva base criada em arquivo:
```bash
python simple_scripts/02_save_knowledge_base.py
```

Útil para não reprocessar sempre!

---

## 📚 Arquivos do Projeto

```
demo-diy-rag/
├── SIMPLE_README.md              ← Você está aqui!
├── simple_faq_rag.py             ← Código principal (1 arquivo!)
├── simple_app.py                 ← Chat web
│
├── simple_scripts/
│   ├── 01_test_system.py         ← Testar sistema
│   └── 02_save_knowledge_base.py ← Salvar base
│
└── data/
    ├── faq_example.csv           ← 25 perguntas exemplo
    └── seu_faq.csv               ← Coloque seu CSV aqui!
```

**Só 3 arquivos principais!** Muito mais simples que a versão completa.

---

## 🤔 Perguntas Frequentes

### **Q: Preciso de LLM (Gemini, GPT)?**
**R:** NÃO! Só usa embeddings. Muito mais barato!

### **Q: Quanto custa?**
**R:** Quase nada! ~$0.01 por 1000 perguntas processadas.
- Criar base de 100 perguntas: ~$0.001
- Fazer 1000 queries: ~$0.01

### **Q: É rápido?**
**R:** SIM! ~100-300ms por resposta.

### **Q: Quantas perguntas posso ter?**
**R:** Quantas quiser! 10, 100, 1000, 10000...
(Mas mais perguntas = demora mais para criar a base inicial)

### **Q: Ele gera respostas novas?**
**R:** NÃO! Só retorna respostas que já estão no CSV.
É um sistema de BUSCA, não de GERAÇÃO.

### **Q: E se a pergunta não existir no CSV?**
**R:** Retorna a mais similar (se score > 0.7)
Se nenhuma for similar o suficiente, diz que não encontrou.

### **Q: Posso usar em produção?**
**R:** SIM! É simples e eficiente para FAQs.

### **Q: Como adicionar mais perguntas?**
**R:** Adicione no CSV e rode `create_knowledge_base()` novamente.

---

## 🆚 Comparação: Simples vs. Completo

| Aspecto | Versão Simples | Versão Completa |
|---------|----------------|-----------------|
| **Arquivos** | 3 principais | 15+ arquivos |
| **Linhas de código** | ~400 linhas | ~3000 linhas |
| **Usa LLM** | ❌ Não | ✅ Sim (Gemini) |
| **Gera respostas** | ❌ Não | ✅ Sim |
| **Custo/mês** | ~$5 | ~$200 |
| **Velocidade** | 0.1-0.3s | 1-2s |
| **Complexidade** | Baixa | Alta |
| **Certificação** | ⚠️ Talvez | ✅ Sim |
| **Aprendizado** | ✅ Fácil | ⚠️ Complexo |
| **FAQ simples** | ✅ Perfeito | ⚠️ Over-engineering |

---

## 🎓 Como Funciona por Dentro?

### 1. **Embeddings (Vetores)**

```python
# Sua pergunta
"Como resetar senha?"

# Vira números (vetor de 768 dimensões)
[0.234, -0.123, 0.567, ..., 0.089]  # 768 números

# Por que? Perguntas similares têm vetores similares!
```

### 2. **Similaridade**

```python
# Compara vetores usando cosseno
query_vector = [0.2, 0.5, 0.1]
pergunta1 = [0.3, 0.4, 0.2]  # Score: 0.95 (muito similar!)
pergunta2 = [0.1, 0.9, 0.8]  # Score: 0.45 (diferente)

# Retorna a pergunta1!
```

### 3. **Fluxo Completo**

```python
# Fase 1: Criar Base (1 vez)
perguntas = ["Como resetar?", "Qual prazo?", ...]
embeddings = gerar_embeddings(perguntas)  # Demora
salvar(embeddings)  # Para não refazer

# Fase 2: Buscar (rápido!)
query = "esqueci senha"
query_emb = gerar_embedding(query)  # Rápido
scores = calcular_similaridade(query_emb, embeddings)  # Rápido
melhor = perguntas[scores.argmax()]  # Acha melhor
resposta = respostas[melhor]  # Retorna
```

---

## 🚀 Próximos Passos

### 1. **Testar com Exemplo**
```bash
python simple_scripts/01_test_system.py
```

### 2. **Usar Seu CSV**
- Crie seu CSV com perguntas/respostas
- Coloque em `data/seu_faq.csv`
- Edite script para usar seu arquivo

### 3. **Salvar Base**
```bash
python simple_scripts/02_save_knowledge_base.py
```

### 4. **Chat App**
```bash
streamlit run simple_app.py
```

### 5. **Integrar em Seu Sistema**
```python
from simple_faq_rag import SimpleFAQSystem
# Use no seu código!
```

---

## 💡 Dicas

### **Performance:**
- Salve a base após criar (não reprocesse)
- Use threshold 0.7+ para boa qualidade
- Top K = 1 para FAQ simples

### **Qualidade:**
- Escreva perguntas de formas variadas no CSV
- Inclua sinônimos e variações
- Teste com perguntas reais de usuários

### **Custos:**
- Embeddings: $0.00002 por 1k tokens
- 100 perguntas médias = ~2k tokens = $0.00004
- Muito barato! 💰

---

## 🆘 Problemas?

### "ModuleNotFoundError: vertexai"
```bash
pip install --upgrade google-cloud-aiplatform
```

### "Permission Denied"
```bash
gcloud auth application-default login
```

### "CSV not found"
```bash
# Verificar caminho
ls data/faq_example.csv
```

### "Embeddings muito lentos"
- Normal! ~1 min para 100 perguntas
- Salve a base depois para não refazer

---

## 📞 Mais Informações

**Arquivos:**
- `simple_faq_rag.py` - Código principal (bem comentado!)
- `simple_app.py` - Chat app (veja como funciona)
- `data/faq_example.csv` - Exemplo real de CSV

**Documentação Google:**
- [Embeddings](https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-text-embeddings)
- [Vertex AI](https://cloud.google.com/vertex-ai/docs)

---

## ✅ Checklist

- [ ] ✅ .env configurado com PROJECT_ID
- [ ] ✅ gcloud auth feito
- [ ] ✅ CSV preparado (ou use exemplo)
- [ ] ✅ Testou com `01_test_system.py`
- [ ] ✅ Chat app funcionando
- [ ] ✅ Entendeu como funciona!

---

**Pronto! Sistema FAQ simples funcionando!** 🎉

Muito mais fácil de entender que a versão completa, né? 😊

---

**Desenvolvido para facilitar o aprendizado de RAG**
**Versão simplificada - Janeiro 2026**

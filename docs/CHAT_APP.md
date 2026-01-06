# 🤖 Chat App Interativo - Guia de Uso

## 📱 O que é o Chat App?

Uma interface web interativa tipo ChatGPT para testar o sistema RAG de produtos. Você pode fazer perguntas em linguagem natural e receber respostas inteligentes baseadas no catálogo de produtos!

## 🚀 Como Executar

### Pré-requisitos

1. Sistema RAG já configurado (scripts 01, 02 e 03 executados)
2. Vector Search deployado e funcionando
3. Dependências instaladas

### Passo a Passo

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Instalar dependências (se ainda não instalou)
pip install -r requirements.txt

# 3. Executar o app
streamlit run app.py
```

O app vai abrir automaticamente no navegador em `http://localhost:8501`

## 📖 Como Usar o App

### 1. Configuração Inicial

Na **barra lateral esquerda**, preencha:

- **Project ID**: Seu ID do projeto Google Cloud
- **Location**: us-central1 (ou sua região)
- **Bucket Name**: Nome do seu bucket (ex: `seu-projeto-data`)

### 2. Ajustar Parâmetros (Opcional)

- **Temperature** (0.0 - 1.0):
  - 0.0 = Respostas mais consistentes e factuais
  - 1.0 = Respostas mais criativas
  - **Recomendado: 0.2**

- **Top K Produtos** (1-10):
  - Quantos produtos buscar antes de gerar resposta
  - Mais produtos = mais contexto, mas mais lento
  - **Recomendado: 5**

### 3. Inicializar o Sistema

1. Clique no botão **"🚀 Inicializar Sistema"**
2. Aguarde alguns segundos (carregando endpoint e modelos)
3. Veja status mudar para "✅ Sistema Online"

### 4. Começar a Conversar!

Digite sua pergunta na caixa de chat na parte inferior e pressione Enter.

## 💡 Exemplos de Perguntas

### Busca por Características
```
Quero um smartphone com boa câmera e bateria durável
```

### Busca por Preço
```
Notebooks até R$ 3000
```

### Busca por Marca
```
Produtos da marca Samsung disponíveis
```

### Busca por Categoria
```
Quais tênis de corrida você tem?
```

### Recomendações
```
Me recomende um presente de tecnologia até R$ 1000
```

### Comparações
```
Qual a diferença entre os smartphones disponíveis?
```

## 🎨 Funcionalidades

### ✨ Interface Interativa
- Design limpo e profissional
- Histórico de conversas
- Mensagens separadas (você vs assistente)

### 📊 Métricas em Tempo Real
- **Tempo de Resposta**: Quanto demorou para processar
- **Documentos Usados**: Quantos produtos foram considerados
- **Fontes Citadas**: Quantos produtos foram mencionados

### 📚 Rastreamento de Fontes
- Expandir "Ver fontes utilizadas"
- Ver quais produtos foram usados na resposta
- Ver scores de relevância
- Ver IDs dos produtos

### ⚙️ Configurações Dinâmicas
- Ajustar parâmetros sem reiniciar
- Ver status do sistema em tempo real
- Contador de queries realizadas

### 🗑️ Limpar Conversa
- Botão para resetar o chat
- Mantém sistema inicializado

## 🔧 Troubleshooting

### Erro: "Sistema Offline"

**Causa:** Sistema não foi inicializado

**Solução:**
1. Preencha Project ID e Bucket Name na sidebar
2. Clique em "Inicializar Sistema"

### Erro: "Endpoint não encontrado"

**Causa:** Vector Search não foi deployado

**Solução:**
```bash
# Verificar status do deploy
python scripts/03_setup_vector_search.py

# Aguardar deploy completar (30-45 min)
```

### Erro: "Permission Denied"

**Causa:** Autenticação não configurada

**Solução:**
```bash
gcloud auth application-default login
```

### App não abre no navegador

**Solução:**
1. Verifique a URL mostrada no terminal
2. Abra manualmente: `http://localhost:8501`
3. Tente mudar a porta:
```bash
streamlit run app.py --server.port 8502
```

### Respostas muito lentas

**Causas possíveis:**
- Top K muito alto
- Endpoint com poucas réplicas
- Região distante

**Soluções:**
- Reduzir Top K para 3
- Aumentar `max_replica_count` no script 03
- Usar região mais próxima

### Erro de importação

**Causa:** Streamlit não instalado

**Solução:**
```bash
pip install streamlit==1.29.0
```

## 📈 Monitoramento

### Ver Logs em Tempo Real

Abra um terminal separado:
```bash
tail -f ~/.streamlit/logs/*.log
```

### Ver Métricas Streamlit

No navegador:
- Menu (≡) → Settings → Show metrics

### Ver Logs do Google Cloud

```bash
gcloud logging read "resource.type=aiplatform.googleapis.com" \
    --limit 50 --format json
```

## 🎯 Dicas para Melhores Resultados

### 1. Seja Específico
❌ "quero um produto bom"
✅ "quero um smartphone com câmera de 48MP e bateria de 5000mAh"

### 2. Mencione Preço
❌ "notebook"
✅ "notebook para programação até R$ 3500"

### 3. Especifique Marca se Importante
❌ "smartphone"
✅ "smartphone Samsung ou Apple"

### 4. Use Comparações
✅ "compare os 3 notebooks mais baratos"
✅ "qual a diferença entre produto X e Y?"

### 5. Peça Recomendações
✅ "me recomende um presente de R$ 500 para quem gosta de tecnologia"

## 🔒 Segurança

### Dados Sensíveis
- ⚠️ **Não compartilhe credenciais** no chat
- ⚠️ **Não insira informações pessoais**
- ✅ Use apenas para queries sobre produtos

### Acesso
- App roda localmente (localhost)
- Sem exposição externa por padrão
- Dados não são salvos permanentemente

### Para Deploy em Produção
```bash
# NÃO recomendado sem configuração adicional
# Requer:
# - Autenticação de usuários
# - HTTPS
# - Rate limiting
# - Firewall
```

## 📊 Avaliação de Respostas

### Indicadores de Qualidade

✅ **Boa Resposta:**
- Cita produtos específicos
- Menciona preços corretos
- Usa informações do catálogo
- Responde diretamente a pergunta

❌ **Resposta Problemática:**
- Muito genérica
- Não cita produtos
- Inventa informações
- Desculpas excessivas ("desculpe...")

### Melhorar Qualidade

Se respostas não estão boas:

1. **Ajustar Temperature**: Reduzir para 0.1
2. **Aumentar Top K**: Para mais contexto
3. **Refazer Pergunta**: Ser mais específico
4. **Verificar Dados**: Embeddings criados corretamente?

## 🎬 Demo em Vídeo

Para criar vídeo de demonstração:

```bash
# 1. Executar app
streamlit run app.py

# 2. Usar ferramenta de gravação de tela:
# - Windows: Xbox Game Bar (Win + G)
# - Mac: QuickTime Player
# - Linux: SimpleScreenRecorder

# 3. Demonstrar:
# - Configuração inicial
# - 3-5 queries diferentes
# - Mostrar fontes e métricas
# - Mostrar diferentes tipos de perguntas
```

## 🚀 Próximos Passos

### Melhorias Possíveis

1. **Filtros Avançados:**
   - Filtro por categoria no sidebar
   - Filtro por faixa de preço
   - Filtro por marca

2. **Histórico Persistente:**
   - Salvar conversas
   - Exportar chat

3. **Visualizações:**
   - Gráficos de produtos
   - Imagens de produtos
   - Comparações visuais

4. **Feedback:**
   - Botões 👍 👎
   - Coletar feedback de qualidade
   - RLHF

## 📞 Suporte

**Problemas com o app:**
- Verifique logs: `~/.streamlit/logs/`
- Documentação: https://docs.streamlit.io/
- Issues: GitHub do projeto

**Problemas com RAG:**
- Consulte: `docs/TROUBLESHOOTING.md`
- Verifique: Vector Search deployado
- Teste: `scripts/05_test_api.py`

---

**Desenvolvido com ❤️ usando Streamlit**

Última atualização: Janeiro 2026

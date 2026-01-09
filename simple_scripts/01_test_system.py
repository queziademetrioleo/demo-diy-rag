#!/usr/bin/env python3
"""
Script 01: Testar Sistema FAQ Simples

Este script testa o sistema FAQ de forma interativa.
É o jeito mais fácil de começar!
"""

import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from simple_faq_rag import SimpleFAQSystem
from loguru import logger


def main():
    """Testa o sistema FAQ."""

    print("="*70)
    print("🤖 TESTE DO SISTEMA FAQ SIMPLES")
    print("="*70)

    # Carregar configurações
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("\n❌ ERRO: PROJECT_ID não configurado no .env")
        print("\n📝 Como corrigir:")
        print("1. Copie .env.example para .env:")
        print("   cp .env.example .env")
        print("2. Edite .env e preencha PROJECT_ID")
        return 1

    print(f"\n✅ Projeto: {project_id}")

    # Verificar CSV
    csv_path = "data/faq_example.csv"
    if not Path(csv_path).exists():
        print(f"\n❌ ERRO: CSV não encontrado: {csv_path}")
        print("\n💡 Use o CSV de exemplo incluído no projeto!")
        return 1

    print(f"✅ CSV encontrado: {csv_path}")

    # Inicializar sistema
    print("\n" + "="*70)
    print("PASSO 1: Inicializando sistema...")
    print("="*70)

    try:
        faq = SimpleFAQSystem(project_id=project_id)
        print("✅ Sistema inicializado!")
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        print("\n💡 Verifique se você está autenticado:")
        print("   gcloud auth application-default login")
        return 1

    # Carregar CSV
    print("\n" + "="*70)
    print("PASSO 2: Carregando Questionss e Answerss...")
    print("="*70)

    try:
        faq.load_csv(csv_path)
        stats = faq.get_stats()
        print(f"✅ {stats['total_Questionss']} Questionss carregadas!")
    except Exception as e:
        print(f"❌ Erro ao carregar CSV: {e}")
        return 1

    # Criar base de conhecimento
    print("\n" + "="*70)
    print("PASSO 3: Criando base de conhecimento...")
    print("="*70)
    print("⏳ Gerando embeddings... (pode levar 1-2 minutos)")

    try:
        faq.create_knowledge_base()
        print("✅ Base de conhecimento criada!")
    except Exception as e:
        print(f"❌ Erro ao criar base: {e}")
        print("\n💡 Verifique se a API está habilitada:")
        print("   gcloud services enable aiplatform.googleapis.com")
        return 1

    # Testar Questionss
    print("\n" + "="*70)
    print("PASSO 4: Testando Questionss...")
    print("="*70)

    test_questions = [
        "Como resetar senha?",
        "Quanto tempo demora a entrega?",
        "Posso devolver?",
        "Aceitam PIX?"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Teste {i}/{len(test_questions)}")
        print(f"❓ Questions: {question}")

        try:
            result = faq.ask(question)

            if result['found']:
                print(f"✅ Answers encontrada (confiança: {result['confidence']})")
                print(f"💬 {result['Answers']}")
                print(f"📊 Score: {result['score']:.1%}")
                print(f"🔗 Questions original: {result['Questions_encontrada']}")
            else:
                print("❌ Nenhuma Answers encontrada")

        except Exception as e:
            print(f"❌ Erro: {e}")

    # Modo interativo
    print("\n" + "="*70)
    print("MODO INTERATIVO - Faça suas Questionss!")
    print("="*70)
    print("Digite 'sair' para encerrar\n")

    while True:
        try:
            question = input("❓ Sua Questions: ").strip()

            if not question:
                continue

            if question.lower() in ['sair', 'exit', 'quit', 'q']:
                print("\n👋 Até logo!")
                break

            result = faq.ask(question)

            if result['found']:
                print(f"\n💬 Answers (confiança: {result['confidence']}):")
                print(f"   {result['Answers']}")
                print(f"   Score: {result['score']:.1%}\n")
            else:
                print("\n❌ Desculpe, não encontrei uma Answers para isso.\n")

        except KeyboardInterrupt:
            print("\n\n👋 Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}\n")

    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*70)
    print("\n📚 Próximos passos:")
    print("1. Use seu próprio CSV com Questionss/Answerss")
    print("2. Execute: python simple_scripts/02_save_knowledge_base.py")
    print("3. Depois: python simple_gradio_app.py")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

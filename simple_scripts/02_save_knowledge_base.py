#!/usr/bin/env python3
"""
Script 02: Salvar Base de Conhecimento

Cria e salva a base de conhecimento para usar depois sem reprocessar.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from simple_faq_rag import SimpleFAQSystem


def main():
    """Salva a base de conhecimento."""

    print("="*70)
    print("💾 SALVANDO BASE DE CONHECIMENTO")
    print("="*70)

    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    csv_path = "data/faq_example.csv"
    output_path = "data/knowledge_base"

    if not project_id:
        print("❌ Configure PROJECT_ID no .env")
        return 1

    # Inicializar
    print("\n1️⃣ Inicializando sistema...")
    faq = SimpleFAQSystem(project_id=project_id)

    # Carregar CSV
    print("\n2️⃣ Carregando CSV...")
    faq.load_csv(csv_path)

    # Criar base
    print("\n3️⃣ Criando base de conhecimento...")
    print("⏳ Aguarde... (1-2 minutos)")
    faq.create_knowledge_base()

    # Salvar
    print("\n4️⃣ Salvando em arquivo...")
    faq.save_knowledge_base(output_path)

    print("\n" + "="*70)
    print("✅ BASE SALVA COM SUCESSO!")
    print("="*70)
    print(f"\nArquivos criados:")
    print(f"  - {output_path}_embeddings.npy")
    print(f"  - {output_path}_data.csv")
    print(f"\n💡 Agora você pode carregar rapidamente com:")
    print(f"   faq.load_knowledge_base('{output_path}')")
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

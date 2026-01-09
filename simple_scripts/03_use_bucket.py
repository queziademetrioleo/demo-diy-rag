#!/usr/bin/env python3
"""
🪣 Script para usar o sistema FAQ com Google Cloud Storage

Este script:
1. Baixa o CSV do Cloud Storage
2. Cria a base de conhecimento (embeddings)
3. Faz upload da base para o bucket
4. Testa o sistema com perguntas de exemplo
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage
import tempfile

# Adicionar path do projeto
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from simple_faq_rag import SimpleFAQSystem


def print_section(title: str):
    """Imprime seção formatada"""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")


def download_csv_from_bucket(bucket_name: str, csv_path: str) -> str:
    """
    Baixa CSV do Cloud Storage para arquivo temporário.

    Args:
        bucket_name: Nome do bucket
        csv_path: Path do CSV no bucket (ex: raw_data/faq.csv)

    Returns:
        Path do arquivo local temporário
    """
    print("📥 Baixando CSV do bucket...")

    try:
        # Inicializar cliente
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Criar blob
        blob = bucket.blob(csv_path)

        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.csv',
            delete=False
        )

        # Download
        blob.download_to_filename(temp_file.name)

        # Pegar nome do arquivo original
        filename = os.path.basename(csv_path)

        print(f"✅ CSV baixado: {filename}")
        print(f"   Local: {temp_file.name}")

        return temp_file.name

    except Exception as e:
        print(f"\n❌ Erro ao baixar CSV: {e}")
        print("\n💡 Dicas:")
        print("   - Verifique se o arquivo existe no bucket")
        print(f"   - Path esperado: gs://{bucket_name}/{csv_path}")
        print("   - Execute: gsutil ls gs://{bucket_name}/raw_data/")
        sys.exit(1)


def upload_knowledge_base_to_bucket(
    bucket_name: str,
    embeddings_path: str,
    metadata_path: str
):
    """
    Faz upload da base de conhecimento para o bucket.

    Args:
        bucket_name: Nome do bucket
        embeddings_path: Path local dos embeddings (.npy)
        metadata_path: Path local dos metadados (.csv)
    """
    print("\n📤 Fazendo upload da base de conhecimento...")

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Upload embeddings
        embeddings_blob = bucket.blob("embeddings/faq_embeddings.npy")
        embeddings_blob.upload_from_filename(embeddings_path)
        print("   ✅ Embeddings enviados")

        # Upload metadata
        metadata_blob = bucket.blob("knowledge_base/faq_metadata.csv")
        metadata_blob.upload_from_filename(metadata_path)
        print("   ✅ Metadados enviados")

        print("\n✅ Base de conhecimento salva no bucket!")
        print(f"   - gs://{bucket_name}/embeddings/faq_embeddings.npy")
        print(f"   - gs://{bucket_name}/knowledge_base/faq_metadata.csv")

    except Exception as e:
        print(f"\n❌ Erro ao fazer upload: {e}")
        sys.exit(1)


def main():
    """Função principal"""

    # Carregar variáveis de ambiente
    load_dotenv()

    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    bucket_name = os.getenv("BUCKET_NAME")
    raw_data_path = os.getenv("RAW_DATA_PATH")

    # Validar configurações
    if not all([project_id, bucket_name, raw_data_path]):
        print("❌ Erro: Arquivo .env não configurado!")
        print("\n💡 Crie o arquivo .env com:")
        print("   PROJECT_ID=seu-projeto")
        print("   BUCKET_NAME=seu-bucket")
        print("   RAW_DATA_PATH=raw_data/seu_arquivo.csv")
        sys.exit(1)

    print_section("🪣 SISTEMA FAQ COM GOOGLE CLOUD STORAGE")

    print(f"✅ Projeto: {project_id}")
    print(f"✅ Bucket: gs://{bucket_name}")

    # ETAPA 1: Download do CSV
    print_section("ETAPA 1: Baixando dados do Cloud Storage")

    csv_file = download_csv_from_bucket(bucket_name, raw_data_path)

    # ETAPA 2: Inicializar sistema
    print_section("ETAPA 2: Inicializando Sistema FAQ")

    try:
        faq = SimpleFAQSystem(
            project_id=project_id,
            location=location
        )
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        print("\n💡 Verifique se Vertex AI API está habilitada:")
        print(f"   gcloud services enable aiplatform.googleapis.com --project={project_id}")
        sys.exit(1)

    # ETAPA 3: Carregar CSV
    print_section("ETAPA 3: Carregando Perguntas e Respostas")

    try:
        faq.load_csv(csv_file)
        print(f"\n📊 Total de perguntas: {len(faq.df)}")
        print("\n📝 Primeiras 5 perguntas:")
        for i, row in faq.df.head(5).iterrows():
            print(f"   {i+1}. {row['pergunta'][:60]}...")
    except Exception as e:
        print(f"❌ Erro ao carregar CSV: {e}")
        print("\n💡 Dicas:")
        print("   - CSV precisa ter pelo menos 2 colunas")
        print("   - Coluna 1: Perguntas (qualquer nome)")
        print("   - Coluna 2: Respostas (qualquer nome)")
        sys.exit(1)

    # ETAPA 4: Criar base de conhecimento
    print_section("ETAPA 4: Criando Base de Conhecimento (Embeddings)")

    print("⏳ Isso pode levar alguns minutos dependendo do tamanho do CSV...")

    try:
        faq.create_knowledge_base()
    except Exception as e:
        print(f"❌ Erro ao criar base: {e}")
        sys.exit(1)

    # ETAPA 5: Salvar base localmente
    print_section("ETAPA 5: Salvando Base de Conhecimento")

    import numpy as np

    # Criar diretório temporário
    temp_dir = Path(tempfile.gettempdir()) / "faq_knowledge_base"
    temp_dir.mkdir(exist_ok=True)

    # Salvar embeddings
    embeddings_file = temp_dir / "faq_embeddings.npy"
    np.save(embeddings_file, faq.embeddings)
    print(f"✅ Embeddings salvos: {embeddings_file}")

    # Salvar metadata
    metadata_file = temp_dir / "faq_metadata.csv"
    faq.df.to_csv(metadata_file, index=False)
    print(f"✅ Metadados salvos: {metadata_file}")

    # ETAPA 6: Upload para bucket
    print_section("ETAPA 6: Enviando para Cloud Storage")

    upload_knowledge_base_to_bucket(
        bucket_name,
        str(embeddings_file),
        str(metadata_file)
    )

    # ETAPA 7: Testar sistema
    print_section("ETAPA 7: Testando Sistema")

    # Pegar primeiras 3 perguntas para testar
    test_queries = faq.df['pergunta'].head(3).tolist()

    print("🧪 Fazendo 3 perguntas de teste:\n")

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─'*70}")
        print(f"Teste {i}: {query}")
        print('─'*70)

        try:
            result = faq.ask(query)

            if result['found']:
                print(f"✅ Resposta encontrada (score: {result['score']:.2f}):")
                print(f"\n{result['resposta']}\n")
            else:
                print("❌ Nenhuma resposta encontrada")

        except Exception as e:
            print(f"❌ Erro: {e}")

    # FINALIZAÇÃO
    print_section("✅ PROCESSO CONCLUÍDO COM SUCESSO!")

    print("📊 Resumo:")
    print(f"   • {len(faq.df)} perguntas processadas")
    print(f"   • Base de conhecimento criada")
    print(f"   • Arquivos salvos no bucket: gs://{bucket_name}/")

    print("\n🎯 Próximos passos:")
    print("   1. Testar mais perguntas:")
    print("      python simple_scripts/01_test_system.py")
    print("\n   2. Abrir interface web:")
    print("      python simple_gradio_app.py")

    print("\n💡 A base de conhecimento está salva no bucket!")
    print("   Você NÃO precisa reprocessar sempre.")
    print("   Para usar, basta carregar os arquivos do bucket.")

    # Limpar arquivo temporário
    os.unlink(csv_file)

    print("\n" + "="*70)
    print("🎉 TUDO PRONTO!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
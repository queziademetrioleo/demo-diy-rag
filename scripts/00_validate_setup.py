#!/usr/bin/env python3
"""
Script 00: Validação de Setup
Verifica se tudo está configurado corretamente ANTES de executar.
Execute SEMPRE antes dos outros scripts!
"""

import os
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv


def validate_env():
    """Valida variáveis de ambiente."""
    load_dotenv()

    required_vars = {
        "PROJECT_ID": "ID do projeto Google Cloud",
        "BUCKET_NAME": "Nome do bucket Cloud Storage",
        "LOCATION": "Região do Google Cloud"
    }

    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  - {var}: {description}")
        else:
            print(f"  ✓ {var}: {value}")

    if missing:
        print(f"\n❌ Variáveis faltando no .env:")
        for m in missing:
            print(m)
        print("\n📝 Como corrigir:")
        print("1. Copie .env.example para .env:")
        print("   cp .env.example .env")
        print("\n2. Edite .env e preencha as variáveis:")
        print("   nano .env")
        return False

    return True


def validate_gcloud_auth():
    """Valida autenticação gcloud."""
    import subprocess

    try:
        result = subprocess.run(
            ["gcloud", "auth", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and "ACTIVE" in result.stdout:
            # Extrair email ativo
            for line in result.stdout.split('\n'):
                if '*' in line or 'ACTIVE' in line:
                    print(f"  ✓ Autenticado")
                    break
            return True
        else:
            print("  ✗ Não autenticado")
            print("\n📝 Como corrigir:")
            print("  gcloud auth login")
            print("  gcloud auth application-default login")
            return False

    except FileNotFoundError:
        print("  ✗ gcloud CLI não encontrado")
        print("\n📝 Instale gcloud CLI:")
        print("  https://cloud.google.com/sdk/docs/install")
        return False
    except Exception as e:
        print(f"  ⚠️  Erro ao verificar: {e}")
        return False


def validate_project_access():
    """Valida acesso ao projeto."""
    import subprocess
    from dotenv import load_dotenv

    load_dotenv()
    project_id = os.getenv("PROJECT_ID")

    if not project_id:
        print("  ⚠️  PROJECT_ID não definido, pulando validação")
        return True

    try:
        result = subprocess.run(
            ["gcloud", "config", "set", "project", project_id],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"  ✓ Acesso ao projeto: {project_id}")
            return True
        else:
            print(f"  ✗ Sem acesso ao projeto: {project_id}")
            print("\n📝 Verifique se o projeto existe e você tem permissão")
            return False

    except Exception as e:
        print(f"  ⚠️  Erro ao verificar projeto: {e}")
        return True


def validate_apis_enabled():
    """Valida se APIs estão habilitadas."""
    import subprocess
    from dotenv import load_dotenv

    load_dotenv()
    project_id = os.getenv("PROJECT_ID")

    if not project_id:
        print("  ⚠️  PROJECT_ID não definido, pulando validação")
        return True

    required_apis = [
        "aiplatform.googleapis.com",
        "storage-api.googleapis.com"
    ]

    try:
        result = subprocess.run(
            ["gcloud", "services", "list", "--enabled", f"--project={project_id}"],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            print(f"  ⚠️  Não foi possível verificar APIs")
            return True

        missing_apis = []
        for api in required_apis:
            if api in result.stdout:
                print(f"  ✓ {api}")
            else:
                print(f"  ✗ {api}")
                missing_apis.append(api)

        if missing_apis:
            print("\n📝 Habilite as APIs faltantes:")
            print(f"  gcloud services enable {' '.join(missing_apis)} --project={project_id}")
            return False

        return True

    except Exception as e:
        print(f"  ⚠️  Erro ao verificar APIs: {e}")
        return True


def validate_python_packages():
    """Valida se pacotes Python estão instalados."""
    required_packages = {
        "google-cloud-aiplatform": "google.cloud.aiplatform",
        "google-cloud-storage": "google.cloud.storage",
        "pandas": "pandas",
        "numpy": "numpy",
        "loguru": "loguru",
        "python-dotenv": "dotenv",
        "streamlit": "streamlit",
        "tqdm": "tqdm"
    }

    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name}")
            missing.append(package_name)

    if missing:
        print("\n📝 Instale os pacotes faltantes:")
        print("  pip install -r requirements.txt")
        return False

    return True


def validate_file_structure():
    """Valida estrutura de arquivos."""
    required_files = [
        "README.md",
        "requirements.txt",
        ".env.example",
        "src/data_loader.py",
        "src/embeddings.py",
        "src/vector_search.py",
        "src/rag_system.py",
        "scripts/01_download_data.py",
        "scripts/02_create_embeddings.py",
        "scripts/03_setup_vector_search.py",
        "scripts/05_test_api.py",
        "app.py"
    ]

    project_root = Path(__file__).parent.parent
    missing = []

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path}")
            missing.append(file_path)

    if missing:
        print("\n⚠️  Alguns arquivos estão faltando!")
        print("Certifique-se de que o repositório está completo.")
        return False

    return True


def main():
    """Executa todas as validações."""
    print("="*70)
    print("🔍 VALIDAÇÃO DE SETUP - Demo DIY RAG")
    print("="*70)
    print("\nEste script verifica se tudo está configurado corretamente.")
    print("Execute isso ANTES de rodar os outros scripts!\n")

    checks = [
        ("📁 Estrutura de Arquivos", validate_file_structure),
        ("🔧 Variáveis de Ambiente (.env)", validate_env),
        ("📦 Pacotes Python", validate_python_packages),
        ("🔐 Autenticação gcloud", validate_gcloud_auth),
        ("🎯 Acesso ao Projeto", validate_project_access),
        ("🌐 APIs do Google Cloud", validate_apis_enabled),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n{name}")
        print("-" * 70)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Erro inesperado: {e}")
            results.append(False)

    print("\n" + "="*70)

    if all(results):
        print("✅ TODAS AS VALIDAÇÕES PASSARAM!")
        print("="*70)
        print("\n🎉 Tudo configurado corretamente!")
        print("\n📋 Próximos passos:")
        print("  1. python scripts/01_download_data.py")
        print("  2. python scripts/02_create_embeddings.py")
        print("  3. python scripts/03_setup_vector_search.py  (30-45 min)")
        print("  4. python scripts/05_test_api.py")
        print("  5. streamlit run app.py")
        print("\n💡 Dica: Leia CRITICAL_FIXES.md para detalhes importantes!")
        return 0
    else:
        print("❌ ALGUMAS VALIDAÇÕES FALHARAM")
        print("="*70)
        print("\n⚠️  Corrija os problemas acima antes de continuar.")
        print("\n📖 Para ajuda detalhada, consulte:")
        print("  - CRITICAL_FIXES.md")
        print("  - docs/TROUBLESHOOTING.md")
        print("  - README.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())

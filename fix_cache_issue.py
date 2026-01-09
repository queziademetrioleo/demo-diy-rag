#!/usr/bin/env python3
"""
🔧 Script para diagnosticar e resolver problemas de cache do Python

Este script:
1. Verifica qual arquivo está sendo importado
2. Remove arquivos de cache (.pyc, __pycache__)
3. Força reimportação limpa do módulo
4. Testa se o novo código está funcionando
"""

import os
import sys
import shutil
from pathlib import Path

def print_section(title: str):
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")

def remove_cache_files(project_root: Path):
    """Remove todos os arquivos de cache Python"""
    print("🧹 Removendo arquivos de cache...")

    cache_removed = 0

    # Remover __pycache__ directories
    for pycache in project_root.rglob("__pycache__"):
        if pycache.is_dir():
            print(f"   Removendo: {pycache}")
            shutil.rmtree(pycache)
            cache_removed += 1

    # Remover .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        if pyc_file.is_file():
            print(f"   Removendo: {pyc_file}")
            pyc_file.unlink()
            cache_removed += 1

    if cache_removed == 0:
        print("   ✅ Nenhum arquivo de cache encontrado")
    else:
        print(f"   ✅ {cache_removed} arquivo(s) de cache removidos")

def verify_code_version(project_root: Path):
    """Verifica se o código atual tem a implementação correta"""
    print("🔍 Verificando versão do código...")

    faq_file = project_root / "simple_faq_rag.py"

    with open(faq_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar se tem o código NOVO (iloc)
    has_new_code = "df.iloc[:, 0]" in content and "df.iloc[:, 1]" in content

    # Verificar se NÃO tem código ANTIGO (column_mapping)
    has_old_code = "column_mapping = {}" in content or "'Questions': 'pergunta'" in content

    print(f"   Código novo (iloc): {'✅ Presente' if has_new_code else '❌ AUSENTE'}")
    print(f"   Código antigo (mapping): {'❌ PRESENTE' if has_old_code else '✅ Ausente'}")

    if has_new_code and not has_old_code:
        print("\n   ✅ Arquivo tem a versão CORRETA do código!")
        return True
    else:
        print("\n   ❌ PROBLEMA: Arquivo não tem a versão esperada!")
        return False

def clear_module_from_memory():
    """Remove módulo da memória do Python"""
    print("🧠 Limpando módulo da memória...")

    if 'simple_faq_rag' in sys.modules:
        del sys.modules['simple_faq_rag']
        print("   ✅ Módulo removido da memória")
    else:
        print("   ✅ Módulo não estava na memória")

def test_import(project_root: Path):
    """Testa importação do módulo"""
    print("📦 Testando importação...")

    # Garantir que o diretório do projeto está no path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        # Importar módulo
        from simple_faq_rag import SimpleFAQSystem

        # Verificar qual arquivo foi importado
        import simple_faq_rag
        imported_file = simple_faq_rag.__file__
        print(f"   ✅ Módulo importado de: {imported_file}")

        # Verificar se o arquivo importado é o correto
        expected_file = str(project_root / "simple_faq_rag.py")
        if os.path.abspath(imported_file) == os.path.abspath(expected_file):
            print("   ✅ Arquivo CORRETO sendo importado!")
            return True
        else:
            print(f"   ❌ PROBLEMA: Importando arquivo ERRADO!")
            print(f"      Esperado: {expected_file}")
            print(f"      Atual: {imported_file}")
            return False

    except Exception as e:
        print(f"   ❌ Erro ao importar: {e}")
        return False

def test_load_csv(project_root: Path):
    """Testa se load_csv está usando o código novo"""
    print("🧪 Testando função load_csv...")

    try:
        # Verificar se existe CSV de exemplo
        csv_path = project_root / "data" / "faq_example.csv"
        if not csv_path.exists():
            print(f"   ⚠️  CSV de teste não encontrado: {csv_path}")
            print("   Pulando teste funcional...")
            return None

        # Importar e testar
        from dotenv import load_dotenv
        load_dotenv()

        from simple_faq_rag import SimpleFAQSystem

        project_id = os.getenv('PROJECT_ID')
        if not project_id:
            print("   ⚠️  PROJECT_ID não configurado no .env")
            print("   Pulando teste funcional...")
            return None

        # Criar sistema e testar
        print("   Inicializando sistema...")
        faq = SimpleFAQSystem(project_id=project_id)

        print(f"   Carregando CSV: {csv_path}")
        faq.load_csv(str(csv_path))

        print(f"   ✅ CSV carregado com sucesso!")
        print(f"   ✅ {len(faq.df)} perguntas processadas")

        # Verificar se as colunas são 'pergunta' e 'resposta'
        if 'pergunta' in faq.df.columns and 'resposta' in faq.df.columns:
            print("   ✅ Colunas padronizadas corretamente!")
            return True
        else:
            print(f"   ❌ PROBLEMA: Colunas inesperadas: {list(faq.df.columns)}")
            return False

    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""

    print_section("🔧 DIAGNÓSTICO E CORREÇÃO DE CACHE DO PYTHON")

    # Determinar diretório do projeto
    project_root = Path(__file__).parent
    print(f"📁 Diretório do projeto: {project_root}\n")

    # ETAPA 1: Remover cache
    print_section("ETAPA 1: Limpando Cache")
    remove_cache_files(project_root)

    # ETAPA 2: Verificar código no arquivo
    print_section("ETAPA 2: Verificando Código no Arquivo")
    code_ok = verify_code_version(project_root)

    if not code_ok:
        print("\n⚠️  ATENÇÃO: O arquivo não tem a versão esperada do código!")
        print("   Execute: git pull origin claude/simple-faq-rag-34uUC")
        return

    # ETAPA 3: Limpar memória
    print_section("ETAPA 3: Limpando Memória do Python")
    clear_module_from_memory()

    # ETAPA 4: Testar importação
    print_section("ETAPA 4: Testando Importação")
    import_ok = test_import(project_root)

    if not import_ok:
        print("\n⚠️  PROBLEMA: Módulo não está sendo importado corretamente!")
        return

    # ETAPA 5: Teste funcional
    print_section("ETAPA 5: Teste Funcional")
    test_ok = test_load_csv(project_root)

    # RESUMO
    print_section("📊 RESUMO")

    if code_ok and import_ok and test_ok:
        print("✅ TUDO OK! O sistema está funcionando corretamente!")
        print("\n🎯 Próximos passos:")
        print("   python simple_scripts/03_use_bucket.py")
    elif test_ok is None:
        print("⚠️  Código e importação OK, mas teste funcional foi pulado")
        print("   (falta .env ou CSV de exemplo)")
        print("\n🎯 Tente executar:")
        print("   python simple_scripts/03_use_bucket.py")
    else:
        print("❌ Ainda há problemas. Veja os detalhes acima.")
        print("\n💡 Sugestões:")
        print("   1. Reinicie completamente o terminal")
        print("   2. Execute: git pull")
        print("   3. Execute este script novamente")

if __name__ == "__main__":
    main()

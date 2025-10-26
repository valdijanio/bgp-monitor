#!/usr/bin/env python3
"""
Script de setup e validação de qualidade do código.
"""
import argparse
import sys
import subprocess


def run_command(command: str, description: str) -> int:
    """
    Executa um comando shell e retorna o código de saída.

    Args:
        command: Comando a ser executado
        description: Descrição do que está sendo executado

    Returns:
        Código de saída do comando
    """
    print(f"\n{'=' * 80}")
    print(f"🔍 {description}")
    print(f"{'=' * 80}\n")

    result = subprocess.run(command, shell=True)
    return result.returncode


def check_quality() -> bool:
    """
    Executa verificações de qualidade de código (Black e Flake8).

    Returns:
        True se todas as verificações passaram, False caso contrário
    """
    success = True

    # Executar Black (verificação)
    black_result = run_command(
        "black . --check --config pyproject.toml",
        "Verificando formatação com Black (100 caracteres)"
    )
    if black_result != 0:
        print("\n❌ Black encontrou problemas de formatação!")
        print("💡 Execute 'black .' para corrigir automaticamente\n")
        success = False
    else:
        print("\n✅ Black: código está formatado corretamente!\n")

    # Executar Flake8
    flake8_result = run_command(
        "flake8 . --config .flake8",
        "Verificando qualidade com Flake8 (120 caracteres)"
    )
    if flake8_result != 0:
        print("\n❌ Flake8 encontrou problemas de qualidade!")
        print("💡 Revise os erros acima e corrija-os\n")
        success = False
    else:
        print("\n✅ Flake8: código está em conformidade!\n")

    return success


def format_code() -> None:
    """Formata o código usando Black."""
    run_command(
        "black . --config pyproject.toml",
        "Formatando código com Black"
    )
    print("\n✅ Código formatado com sucesso!\n")


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Script de setup e validação de qualidade do BGP Monitor"
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Executa verificações de qualidade (Black + Flake8)"
    )
    parser.add_argument(
        "--format",
        action="store_true",
        help="Formata o código usando Black"
    )

    args = parser.parse_args()

    if args.quality:
        success = check_quality()
        sys.exit(0 if success else 1)

    elif args.format:
        format_code()
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

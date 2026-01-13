"""
Script para executar o FileCopy Verifier
Garante que o programa seja executado do diretório correto
"""
import os
import sys
from pathlib import Path

# Muda para o diretório do script
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Adiciona src ao path
sys.path.insert(0, str(script_dir / "src"))

# Executa o programa
if __name__ == "__main__":
    from src.main import main
    main()

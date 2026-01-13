"""
Módulo: helpers.py
Funções auxiliares e utilitárias.
Autor: FileCopy Verifier Team
Data: 2024
"""

from pathlib import Path
from typing import Optional


def validate_path(path: str) -> Optional[Path]:
    """
    Valida e retorna um Path válido.
    
    Args:
        path: String do caminho
        
    Returns:
        Path válido ou None se inválido
    """
    try:
        path_obj = Path(path)
        if path_obj.exists():
            return path_obj
        return None
    except Exception:
        return None


def ensure_directory(path: Path) -> bool:
    """
    Garante que um diretório existe, criando se necessário.
    
    Args:
        path: Caminho do diretório
        
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


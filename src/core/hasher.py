"""
Módulo: hasher.py
Responsável pelo cálculo de hash de arquivos (alias para verifier).
Autor: FileCopy Verifier Team
Data: 2024
"""

from .verifier import IntegrityVerifier

# Alias para compatibilidade
FileHasher = IntegrityVerifier


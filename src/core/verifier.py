"""
Módulo: verifier.py
Responsável pela verificação de integridade de arquivos usando hash.
Autor: FileCopy Verifier Team
Data: 2024
"""

import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional


class IntegrityVerifier:
    """
    Classe responsável por verificar a integridade de arquivos usando hash.
    """
    
    def __init__(self, algorithm: str = "sha256"):
        """
        Inicializa o verificador de integridade.
        
        Args:
            algorithm: Algoritmo de hash a ser usado ('sha256', 'md5', etc.)
        """
        self.algorithm = algorithm
        self.hash_cache: Dict[Path, str] = {}
    
    def calculate_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """
        Calcula o hash de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            chunk_size: Tamanho do chunk para leitura (padrão: 8KB)
            
        Returns:
            Hash hexadecimal do arquivo
        """
        # Verifica cache
        if file_path in self.hash_cache:
            return self.hash_cache[file_path]
        
        # Seleciona algoritmo
        if self.algorithm == "sha256":
            hasher = hashlib.sha256()
        elif self.algorithm == "md5":
            hasher = hashlib.md5()
        else:
            raise ValueError(f"Algoritmo não suportado: {self.algorithm}")
        
        # Calcula hash lendo em chunks
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            
            hash_value = hasher.hexdigest()
            self.hash_cache[file_path] = hash_value
            return hash_value
        except Exception as e:
            raise IOError(f"Erro ao calcular hash de {file_path}: {str(e)}")
    
    def verify_file(self, source_file: Path, dest_file: Path) -> Tuple[bool, Optional[str]]:
        """
        Verifica se dois arquivos são idênticos comparando seus hashes.
        
        Args:
            source_file: Arquivo de origem
            dest_file: Arquivo de destino
            
        Returns:
            Tupla (são_iguais, mensagem_erro)
        """
        try:
            source_hash = self.calculate_hash(source_file)
            dest_hash = self.calculate_hash(dest_file)
            
            if source_hash == dest_hash:
                return True, None
            else:
                return False, f"Hash diferente: origem={source_hash[:16]}..., destino={dest_hash[:16]}..."
        except Exception as e:
            return False, str(e)


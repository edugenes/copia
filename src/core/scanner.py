"""
Módulo: scanner.py
Responsável pela varredura e análise de diretórios.
Autor: FileCopy Verifier Team
Data: 2024
"""

from pathlib import Path
from typing import Dict, List
from collections import defaultdict


class DirectoryScanner:
    """
    Classe responsável por escanear diretórios e coletar estatísticas.
    """
    
    def __init__(self, path: Path):
        """
        Inicializa o scanner de caminho (arquivo ou diretório).
        
        Args:
            path: Caminho a ser escaneado (arquivo ou diretório)
        """
        self.path = Path(path)
        self.files: List[Path] = []
        self.directories: List[Path] = []
        self.stats: Dict = {}
        self.is_file = self.path.is_file()
        self.is_dir = self.path.is_dir()
    
    def scan(self) -> Dict:
        """
        Escaneia o caminho (arquivo ou diretório) coletando informações.
        
        Returns:
            Dicionário com estatísticas
        """
        self.files = []
        self.directories = []
        total_size = 0
        files_by_extension = defaultdict(int)
        size_by_extension = defaultdict(int)
        
        try:
            if self.is_file:
                # Se é um arquivo único
                self.files.append(self.path)
                file_size = self.path.stat().st_size
                total_size = file_size
                
                # Estatísticas por extensão
                ext = self.path.suffix.lower() or 'sem_extensao'
                files_by_extension[ext] = 1
                size_by_extension[ext] = file_size
                
            elif self.is_dir:
                # Se é um diretório, percorre recursivamente
                for item in self.path.rglob('*'):
                    if item.is_file():
                        self.files.append(item)
                        file_size = item.stat().st_size
                        total_size += file_size
                        
                        # Estatísticas por extensão
                        ext = item.suffix.lower() or 'sem_extensao'
                        files_by_extension[ext] += 1
                        size_by_extension[ext] += file_size
                        
                    elif item.is_dir():
                        self.directories.append(item)
            else:
                raise FileNotFoundError(f"Caminho não encontrado: {self.path}")
        
        except PermissionError as e:
            raise PermissionError(f"Sem permissão para acessar {self.path}: {str(e)}")
        
        # Compila estatísticas
        self.stats = {
            'total_files': len(self.files),
            'total_directories': len(self.directories),
            'total_size': total_size,
            'files_by_extension': dict(files_by_extension),
            'size_by_extension': dict(size_by_extension),
            'files': self.files,
            'directories': self.directories
        }
        
        return self.stats
    
    def format_size(self, size_bytes: int) -> str:
        """
        Formata tamanho em bytes para formato legível.
        
        Args:
            size_bytes: Tamanho em bytes
            
        Returns:
            String formatada (ex: "1.5 GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


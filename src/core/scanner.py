"""
Módulo: scanner.py
Responsável pela varredura e análise de diretórios.
Autor: FileCopy Verifier Team
Data: 2024
"""

from pathlib import Path
from typing import Dict, List, Optional, Callable
from collections import defaultdict


class DirectoryScanner:
    """
    Classe responsável por escanear diretórios e coletar estatísticas.
    """
    
    def __init__(self, path: Path, progress_callback: Optional[Callable] = None):
        """
        Inicializa o scanner de caminho (arquivo ou diretório).
        
        Args:
            path: Caminho a ser escaneado (arquivo ou diretório)
            progress_callback: Callback chamado durante o escaneamento
                              Assinatura: callback(files_count, current_file_path, total_size)
        """
        self.path = Path(path)
        self.files: List[Path] = []
        self.directories: List[Path] = []
        self.stats: Dict = {}
        self.is_file = self.path.is_file()
        self.is_dir = self.path.is_dir()
        self.progress_callback = progress_callback
    
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
                file_count = 0
                # Intervalo adaptativo: atualiza mais frequentemente para manter UI responsiva
                update_interval = 50  # Atualiza a cada 50 arquivos (mais frequente)
                
                for item in self.path.rglob('*'):
                    if item.is_file():
                        self.files.append(item)
                        file_size = 0
                        try:
                            file_size = item.stat().st_size
                            # CORREÇÃO: Garante que file_size seja não-negativo e válido
                            if file_size < 0:
                                file_size = 0
                            # CORREÇÃO: Usa soma segura para evitar overflow
                            if total_size + file_size < total_size:  # Detecta overflow
                                # Se houver overflow, mantém o valor atual
                                pass
                            else:
                                total_size += file_size
                        except (OSError, PermissionError):
                            # Ignora arquivos inacessíveis
                            file_size = 0
                        except Exception:
                            # Ignora outros erros
                            file_size = 0
                        
                        file_count += 1
                        
                        # Estatísticas por extensão
                        ext = item.suffix.lower() or 'sem_extensao'
                        files_by_extension[ext] += 1
                        size_by_extension[ext] += file_size
                        
                        # Emite progresso periodicamente para não travar a UI
                        if self.progress_callback and file_count % update_interval == 0:
                            try:
                                # CORREÇÃO: Garante que total_size seja não-negativo antes de emitir
                                safe_total = max(0, total_size)
                                self.progress_callback(file_count, str(item), safe_total)
                            except:
                                pass  # Ignora erros no callback
                    
                    elif item.is_dir():
                        self.directories.append(item)
                
                # Emite progresso final
                if self.progress_callback and file_count > 0:
                    try:
                        # Usa o último arquivo encontrado
                        last_file = self.files[-1] if self.files else None
                        # CORREÇÃO: Garante que total_size seja não-negativo
                        safe_total = max(0, total_size)
                        self.progress_callback(file_count, str(last_file) if last_file else "", safe_total)
                    except:
                        pass
                
                # CORREÇÃO: Garante que total_size final seja não-negativo
                total_size = max(0, total_size)
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


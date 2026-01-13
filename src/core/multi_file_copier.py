"""
Módulo: multi_file_copier.py
Responsável pela cópia de múltiplos arquivos selecionados.
Autor: FileCopy Verifier Team
Data: 2024
"""

from pathlib import Path
from typing import List
import time
from .copier import FileCopier


class MultiFileCopier:
    """
    Classe responsável por copiar múltiplos arquivos selecionados.
    """
    
    def __init__(self, source_files: List[Path], destination: Path, max_retries: int = 3):
        """
        Inicializa o copiador de múltiplos arquivos.
        
        Args:
            source_files: Lista de arquivos de origem
            destination: Diretório de destino
            max_retries: Número máximo de tentativas por arquivo
        """
        self.source_files = [Path(f) for f in source_files]
        self.destination = Path(destination)
        self.progress_callback = None
        self.max_retries = max_retries
        self.paused = False
        self.cancelled = False
    
    def set_progress_callback(self, callback):
        """Define callback de progresso."""
        self.progress_callback = callback
    
    def pause(self):
        """Pausa a cópia."""
        self.paused = True
    
    def resume(self):
        """Retoma a cópia."""
        self.paused = False
    
    def cancel(self):
        """Cancela a cópia."""
        self.cancelled = True
        self.paused = False
    
    def copy_all(self) -> dict:
        """
        Copia todos os arquivos para o diretório de destino.
        
        Returns:
            Dicionário com estatísticas da cópia
        """
        copied_files = []
        failed_files = []
        total_files = len(self.source_files)
        
        for idx, source_file in enumerate(self.source_files, 1):
            # Verifica cancelamento
            if self.cancelled:
                break
            
            # Aguarda se pausado
            while self.paused and not self.cancelled:
                time.sleep(0.1)
            
            if self.cancelled:
                break
            
            try:
                if not source_file.exists() or not source_file.is_file():
                    failed_files.append((source_file, "Arquivo não encontrado"))
                    continue
                
                # Destino é sempre um diretório para múltiplos arquivos
                dest_file = self.destination / source_file.name
                
                # Usa FileCopier para copiar arquivo único
                copier = FileCopier(source_file, dest_file, self.max_retries)
                copier.paused = self.paused
                copier.cancelled = self.cancelled
                
                # Cria callback específico para este arquivo (closure para capturar variáveis)
                def make_callback(file_idx, total, source_f):
                    def callback(curr, tot, fname, fsize, bcopy):
                        if self.progress_callback:
                            self.progress_callback(file_idx, total, source_f, fsize, bcopy)
                    return callback
                
                copier.set_progress_callback(make_callback(idx, total_files, source_file))
                
                if copier.copy_file(source_file, dest_file, idx, total_files):
                    copied_files.append(source_file)
                    if self.progress_callback:
                        # Notifica conclusão do arquivo
                        file_size = source_file.stat().st_size
                        self.progress_callback(idx, total_files, source_file, file_size, file_size)
                else:
                    failed_files.extend(copier.failed_files)
                    
            except Exception as e:
                failed_files.append((source_file, str(e)))
        
        return {
            'total_files': total_files,
            'copied_files': len(copied_files),
            'failed_files': len(failed_files),
            'copied_list': copied_files,
            'failed_list': failed_files
        }
    


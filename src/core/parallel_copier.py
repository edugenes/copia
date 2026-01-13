"""
Módulo: parallel_copier.py
Responsável pela cópia paralela de arquivos usando múltiplas threads.
Autor: FileCopy Verifier Team
Data: 2024
"""

import threading
import queue
import time
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from .copier import FileCopier


class ParallelFileCopier:
    """
    Classe responsável por copiar arquivos em paralelo usando múltiplas threads.
    """
    
    def __init__(self, source: Path, destination: Path, num_threads: int = 4, max_retries: int = 3):
        """
        Inicializa o copiador paralelo de arquivos.
        
        Args:
            source: Caminho de origem (arquivo ou diretório)
            destination: Caminho de destino (arquivo ou diretório)
            num_threads: Número de threads para cópia paralela
            max_retries: Número máximo de tentativas por arquivo
        """
        self.source = Path(source)
        self.destination = Path(destination)
        self.num_threads = max(1, num_threads)
        self.max_retries = max_retries
        self.copied_files: List[Path] = []
        self.failed_files: List[Tuple[Path, str]] = []
        self.progress_callback: Optional[Callable] = None
        self.is_file = self.source.is_file()
        self.is_dir = self.source.is_dir()
        self.paused = False
        self.cancelled = False
        self.lock = threading.Lock()
        self.file_queue = queue.Queue()
        self.copied_count = 0
        self.total_files = 0
    
    def set_progress_callback(self, callback: Callable):
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
    
    def _worker_thread(self):
        """Thread worker que copia arquivos da fila."""
        while not self.cancelled:
            try:
                # Aguarda se pausado
                while self.paused and not self.cancelled:
                    time.sleep(0.1)
                
                if self.cancelled:
                    break
                
                # Obtém arquivo da fila (timeout para verificar cancelamento)
                try:
                    item = self.file_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                file_index, source_file, dest_file = item
                
                # Cria copiador para este arquivo
                copier = FileCopier(source_file, dest_file, self.max_retries)
                # Sincroniza estado de pausa/cancelamento
                if self.paused:
                    copier.pause()
                if self.cancelled:
                    copier.cancel()
                
                # Callback de progresso thread-safe
                def make_callback(idx, total, sf):
                    def callback(curr, tot, fname, fsize, bcopy):
                        if self.progress_callback:
                            # Chama callback sem lock para não bloquear (PyQt signals são thread-safe)
                            try:
                                self.progress_callback(idx, total, sf, fsize, bcopy)
                            except Exception as e:
                                # Log erro mas continua
                                pass
                    return callback
                
                copier.set_progress_callback(make_callback(file_index, self.total_files, source_file))
                
                # Atualiza estado antes de copiar
                if self.paused:
                    copier.pause()
                if self.cancelled:
                    copier.cancel()
                
                # Copia arquivo
                success = copier.copy_file(source_file, dest_file, file_index, self.total_files)
                
                with self.lock:
                    if success:
                        self.copied_files.append(source_file)
                        self.copied_count += 1
                    else:
                        self.failed_files.extend(copier.failed_files)
                
                self.file_queue.task_done()
                
            except Exception as e:
                with self.lock:
                    self.failed_files.append((source_file, str(e)))
                self.file_queue.task_done()
    
    def copy_all(self) -> dict:
        """
        Copia todos os arquivos em paralelo.
        
        Returns:
            Dicionário com estatísticas da cópia
        """
        self.copied_files = []
        self.failed_files = []
        self.copied_count = 0
        
        # Determina lista de arquivos
        source_files = []
        if self.is_file:
            source_files = [self.source]
        elif self.is_dir:
            source_files = [f for f in self.source.rglob('*') if f.is_file()]
        else:
            raise FileNotFoundError(f"Origem não encontrada: {self.source}")
        
        self.total_files = len(source_files)
        
        # Adiciona arquivos à fila
        for idx, source_file in enumerate(source_files, 1):
            if self.is_file:
                if self.destination.is_dir() or not self.destination.exists():
                    dest_file = self.destination / source_file.name if self.destination.is_dir() else self.destination
                else:
                    dest_file = self.destination
            else:
                relative_path = source_file.relative_to(self.source)
                dest_file = self.destination / relative_path
            
            self.file_queue.put((idx, source_file, dest_file))
        
        # Inicia threads worker
        threads = []
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self._worker_thread, daemon=True)
            thread.start()
            threads.append(thread)
        
        # Aguarda conclusão de todos os arquivos
        self.file_queue.join()
        
        # Aguarda threads terminarem
        for thread in threads:
            thread.join(timeout=1.0)
        
        return {
            'total_files': self.total_files,
            'copied_files': len(self.copied_files),
            'failed_files': len(self.failed_files),
            'copied_list': self.copied_files,
            'failed_list': self.failed_files
        }


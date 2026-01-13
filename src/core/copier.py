"""
Módulo: copier.py
Responsável pela lógica principal de cópia de arquivos.
Autor: FileCopy Verifier Team
Data: 2024
"""

import shutil
import time
from pathlib import Path
from typing import List, Tuple, Optional, Callable


class FileCopier:
    """
    Classe responsável por copiar arquivos preservando metadados.
    """
    
    def __init__(self, source: Path, destination: Path, max_retries: int = 3):
        """
        Inicializa o copiador de arquivos.
        
        Args:
            source: Caminho de origem (arquivo ou diretório)
            destination: Caminho de destino (arquivo ou diretório)
            max_retries: Número máximo de tentativas para cada arquivo
        """
        self.source = Path(source)
        self.destination = Path(destination)
        self.copied_files: List[Path] = []
        self.failed_files: List[Tuple[Path, str]] = []
        self.progress_callback: Optional[Callable] = None
        self.is_file = self.source.is_file()
        self.is_dir = self.source.is_dir()
        self.max_retries = max_retries
        self.paused = False
        self.cancelled = False
        
    def set_progress_callback(self, callback: Callable):
        """
        Define callback para atualização de progresso.
        
        Args:
            callback: Função chamada a cada arquivo copiado
                      Assinatura: callback(current_file_index, total_files, filename, file_size, bytes_copied)
        """
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
    
    def copy_file(self, source_file: Path, dest_file: Path, file_index: int = 0, total_files: int = 0) -> bool:
        """
        Copia um único arquivo preservando metadados com retry automático.
        
        Args:
            source_file: Arquivo de origem
            dest_file: Arquivo de destino
            file_index: Índice do arquivo atual (para callback)
            total_files: Total de arquivos (para callback)
            
        Returns:
            True se copiado com sucesso, False caso contrário
        """
        # Retry automático
        for attempt in range(1, self.max_retries + 1):
            # Verifica se foi cancelado
            if self.cancelled:
                return False
            
            # Aguarda se pausado
            while self.paused and not self.cancelled:
                time.sleep(0.1)
            
            if self.cancelled:
                return False
            
            try:
                # Cria diretório de destino se não existir
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                file_size = source_file.stat().st_size
                
                # Se tem callback, copia em chunks para rastrear progresso
                if self.progress_callback and file_size > 0:
                    # Buffer adaptativo baseado no tamanho do arquivo
                    if file_size < 10 * 1024 * 1024:  # < 10MB
                        chunk_size = 512 * 1024  # 512KB
                        update_interval = max(1, file_size // 20)  # Atualiza a cada ~5% do arquivo
                    elif file_size < 100 * 1024 * 1024:  # < 100MB
                        chunk_size = 2 * 1024 * 1024  # 2MB
                        update_interval = max(1, file_size // 10)  # Atualiza a cada ~10% do arquivo
                    else:  # >= 100MB
                        chunk_size = 4 * 1024 * 1024  # 4MB
                        update_interval = max(1, file_size // 100)  # Atualiza a cada ~1% do arquivo
                    
                    bytes_copied = 0
                    bytes_since_update = 0
                    
                    with open(source_file, 'rb') as src, open(dest_file, 'wb') as dst:
                        while True:
                            # Verifica pausa/cancelamento durante cópia
                            if self.cancelled:
                                return False
                            
                            while self.paused and not self.cancelled:
                                time.sleep(0.1)
                            
                            if self.cancelled:
                                return False
                            
                            chunk = src.read(chunk_size)
                            if not chunk:
                                break
                            dst.write(chunk)
                            bytes_copied += len(chunk)
                            bytes_since_update += len(chunk)
                            
                            # Atualiza progresso via callback apenas no intervalo definido
                            if bytes_since_update >= update_interval:
                                if self.progress_callback:
                                    self.progress_callback(file_index, total_files, source_file, file_size, bytes_copied)
                                bytes_since_update = 0
                    
                    # Garante que o último progresso seja atualizado
                    if bytes_since_update > 0 and self.progress_callback:
                        self.progress_callback(file_index, total_files, source_file, file_size, bytes_copied)
                    
                    # Preserva metadados
                    shutil.copystat(source_file, dest_file)
                else:
                    # Copia arquivo preservando metadados (timestamps, permissões)
                    shutil.copy2(source_file, dest_file)
                
                # Sucesso
                return True
                
            except Exception as e:
                # Se foi a última tentativa, registra erro
                if attempt == self.max_retries:
                    error_msg = f"Erro ao copiar {source_file} após {self.max_retries} tentativas: {str(e)}"
                    self.failed_files.append((source_file, error_msg))
                    return False
                else:
                    # Backoff exponencial: espera 2^attempt segundos
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    # Remove arquivo parcial se existir
                    if dest_file.exists():
                        try:
                            dest_file.unlink()
                        except:
                            pass
                    continue
        
        return False
    
    def copy_all(self) -> dict:
        """
        Copia arquivo(s) ou diretório(s) de origem para destino.
        Suporta:
        - Arquivo único
        - Múltiplos arquivos
        - Diretório com subpastas
        
        Returns:
            Dicionário com estatísticas da cópia
        """
        self.copied_files = []
        self.failed_files = []
        
        # Determina lista de arquivos a copiar
        source_files = []
        
        if self.is_file:
            # Se origem é um arquivo único
            source_files = [self.source]
        elif self.is_dir:
            # Se origem é um diretório, lista todos os arquivos recursivamente
            source_files = [f for f in self.source.rglob('*') if f.is_file()]
        else:
            # Origem não existe
            raise FileNotFoundError(f"Origem não encontrada: {self.source}")
        
        total_files = len(source_files)
        copied_count = 0
        
        # Copia cada arquivo
        for idx, source_file in enumerate(source_files, 1):
            # Verifica cancelamento
            if self.cancelled:
                break
            
            # Aguarda se pausado
            while self.paused and not self.cancelled:
                time.sleep(0.1)
            
            if self.cancelled:
                break
            
            try:
                # Determina destino
                if self.is_file:
                    # Se origem é arquivo único, destino pode ser arquivo ou diretório
                    if self.destination.is_dir() or not self.destination.exists():
                        # Se destino é diretório ou não existe, copia mantendo nome
                        dest_file = self.destination / source_file.name if self.destination.is_dir() else self.destination
                    else:
                        # Destino é arquivo específico
                        dest_file = self.destination
                else:
                    # Origem é diretório, mantém estrutura relativa
                    relative_path = source_file.relative_to(self.source)
                    dest_file = self.destination / relative_path
                
                # Copia arquivo (com rastreamento de progresso e retry)
                if self.copy_file(source_file, dest_file, idx, total_files):
                    self.copied_files.append(source_file)
                    copied_count += 1
                    
            except Exception as e:
                error_msg = f"Erro ao processar {source_file}: {str(e)}"
                self.failed_files.append((source_file, error_msg))
        
        # Retorna estatísticas
        return {
            'total_files': total_files,
            'copied_files': len(self.copied_files),
            'failed_files': len(self.failed_files),
            'copied_list': self.copied_files,
            'failed_list': self.failed_files
        }


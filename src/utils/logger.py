"""
Módulo: logger.py
Responsável pelo sistema de logs da aplicação.
Autor: FileCopy Verifier Team
Data: 2024
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class AppLogger:
    """
    Classe responsável pelo gerenciamento de logs da aplicação.
    """
    
    def __init__(self, name: str = "FileCopyVerifier", log_dir: Optional[Path] = None):
        """
        Inicializa o logger.
        
        Args:
            name: Nome do logger
            log_dir: Diretório para salvar logs (None = logs/)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evita duplicação de handlers
        if self.logger.handlers:
            return
        
        # Diretório de logs
        if log_dir is None:
            log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Formato de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para arquivo
        log_file = log_dir / f"filecopy_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Adiciona handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self) -> logging.Logger:
        """
        Retorna o logger configurado.
        
        Returns:
            Logger configurado
        """
        return self.logger


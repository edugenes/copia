"""
Módulo: config.py
Gerenciamento de configurações da aplicação.
Autor: FileCopy Verifier Team
Data: 2024
"""

import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Classe para gerenciar configurações da aplicação."""
    
    def __init__(self, config_file: Path = None):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_file: Caminho do arquivo de configuração
        """
        if config_file is None:
            config_file = Path.home() / ".filecopy_verifier" / "config.json"
        
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings: Dict[str, Any] = self.load()
    
    def load(self) -> Dict[str, Any]:
        """
        Carrega configurações do arquivo.
        
        Returns:
            Dicionário com configurações
        """
        default_config = {
            'hash_algorithm': 'sha256',
            'chunk_size': 8192,
            'log_level': 'INFO',
            'auto_verify': False,
            'preserve_metadata': True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception:
                pass
        
        return default_config
    
    def save(self):
        """Salva configurações no arquivo."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception:
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração.
        
        Args:
            key: Chave da configuração
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Define valor de configuração.
        
        Args:
            key: Chave da configuração
            value: Valor a ser definido
        """
        self.settings[key] = value
        self.save()


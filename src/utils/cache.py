"""
Módulo: cache.py
Responsável pelo cache de estatísticas de escaneamento.
Autor: FileCopy Verifier Team
Data: 2024
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict


class ScanCache:
    """
    Classe responsável por gerenciar cache de estatísticas de escaneamento.
    """
    
    def __init__(self, cache_file: str = ".scan_cache.json", cache_ttl_minutes: int = 5):
        """
        Inicializa o gerenciador de cache.
        
        Args:
            cache_file: Caminho do arquivo de cache
            cache_ttl_minutes: Tempo de vida do cache em minutos
        """
        self.cache_file = Path(cache_file)
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Carrega cache do arquivo."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Converte timestamps de string para datetime
                    for key, entry in data.items():
                        if 'timestamp' in entry:
                            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                    return data
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        """Salva cache no arquivo."""
        try:
            # Converte timestamps para string para JSON
            cache_to_save = {}
            for key, entry in self.cache.items():
                cache_to_save[key] = entry.copy()
                if 'timestamp' in cache_to_save[key]:
                    cache_to_save[key]['timestamp'] = cache_to_save[key]['timestamp'].isoformat()
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_to_save, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Falha silenciosa ao salvar cache
    
    def get_cache_key(self, path: Path, source_files_list: Optional[list] = None) -> str:
        """
        Gera chave única para o caminho.
        
        Args:
            path: Caminho a ser escaneado
            source_files_list: Lista opcional de arquivos (para múltiplos arquivos)
            
        Returns:
            Hash MD5 do caminho + data de modificação
        """
        try:
            if source_files_list:
                # Para múltiplos arquivos, usa hash da lista
                files_str = '|'.join(sorted(source_files_list))
                key_data = f"{files_str}"
            else:
                # Para diretório/arquivo único, usa caminho + data de modificação
                if path.is_file():
                    stat = path.stat()
                    key_data = f"{path}{stat.st_mtime}"
                elif path.is_dir():
                    # Tenta obter data de modificação do diretório
                    try:
                        stat = path.stat()
                        key_data = f"{path}{stat.st_mtime}"
                    except:
                        key_data = str(path)
                else:
                    key_data = str(path)
            
            return hashlib.md5(key_data.encode()).hexdigest()
        except Exception:
            # Fallback: usa apenas o caminho
            return hashlib.md5(str(path).encode()).hexdigest()
    
    def get(self, path: Path, source_files_list: Optional[list] = None) -> Optional[Dict]:
        """
        Obtém cache se válido.
        
        Args:
            path: Caminho escaneado
            source_files_list: Lista opcional de arquivos
            
        Returns:
            Estatísticas em cache se válidas, None caso contrário
        """
        key = self.get_cache_key(path, source_files_list)
        if key in self.cache:
            entry = self.cache[key]
            if 'timestamp' in entry and 'stats' in entry:
                # Verifica se cache ainda é válido
                if datetime.now() - entry['timestamp'] < self.cache_ttl:
                    return entry['stats']
                else:
                    # Remove cache expirado
                    del self.cache[key]
                    self._save_cache()
        return None
    
    def set(self, path: Path, stats: Dict, source_files_list: Optional[list] = None):
        """
        Salva cache.
        
        Args:
            path: Caminho escaneado
            stats: Estatísticas a serem cacheadas
            source_files_list: Lista opcional de arquivos
        """
        key = self.get_cache_key(path, source_files_list)
        self.cache[key] = {
            'stats': stats,
            'timestamp': datetime.now()
        }
        self._save_cache()
    
    def clear(self):
        """Limpa todo o cache."""
        self.cache = {}
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except:
                pass
    
    def clear_expired(self):
        """Remove entradas expiradas do cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if 'timestamp' in entry and now - entry['timestamp'] >= self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            self._save_cache()

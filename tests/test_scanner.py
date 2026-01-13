"""
Testes para o módulo scanner.
"""

import pytest
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.scanner import DirectoryScanner


def test_scanner_basic():
    """Testa escaneamento básico de diretório."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Cria estrutura de teste
        test_dir = Path(tmpdir) / "test"
        test_dir.mkdir()
        
        # Cria alguns arquivos
        (test_dir / "file1.txt").write_text("test content 1")
        (test_dir / "file2.txt").write_text("test content 2")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "file3.txt").write_text("test content 3")
        
        # Escaneia
        scanner = DirectoryScanner(test_dir)
        stats = scanner.scan()
        
        assert stats['total_files'] == 3
        assert stats['total_directories'] >= 1
        assert stats['total_size'] > 0


def test_format_size():
    """Testa formatação de tamanho."""
    scanner = DirectoryScanner(Path("/tmp"))
    
    assert "B" in scanner.format_size(500)
    assert "KB" in scanner.format_size(2048)
    assert "MB" in scanner.format_size(2097152)
    assert "GB" in scanner.format_size(2147483648)


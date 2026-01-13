"""
Testes para o módulo copier.
"""

import pytest
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.copier import FileCopier


def test_copy_single_file():
    """Testa cópia de arquivo único."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        dest_dir = Path(tmpdir) / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        source_file = source_dir / "test.txt"
        source_file.write_text("test content")
        
        copier = FileCopier(source_dir, dest_dir)
        dest_file = dest_dir / "test.txt"
        
        result = copier.copy_file(source_file, dest_file)
        
        assert result is True
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"


def test_copy_all_files():
    """Testa cópia de todos os arquivos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        dest_dir = Path(tmpdir) / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Cria arquivos de teste
        (source_dir / "file1.txt").write_text("content 1")
        (source_dir / "file2.txt").write_text("content 2")
        (source_dir / "subdir").mkdir()
        (source_dir / "subdir" / "file3.txt").write_text("content 3")
        
        copier = FileCopier(source_dir, dest_dir)
        stats = copier.copy_all()
        
        assert stats['total_files'] == 3
        assert stats['copied_files'] == 3
        assert (dest_dir / "file1.txt").exists()
        assert (dest_dir / "file2.txt").exists()
        assert (dest_dir / "subdir" / "file3.txt").exists()


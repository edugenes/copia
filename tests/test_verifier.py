"""
Testes para o módulo verifier.
"""

import pytest
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.verifier import IntegrityVerifier


def test_hash_calculation():
    """Testa cálculo de hash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        
        verifier = IntegrityVerifier()
        hash1 = verifier.calculate_hash(test_file)
        hash2 = verifier.calculate_hash(test_file)
        
        # Hash deve ser consistente
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produz 64 caracteres hex


def test_verify_identical_files():
    """Testa verificação de arquivos idênticos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = Path(tmpdir) / "source.txt"
        dest_file = Path(tmpdir) / "dest.txt"
        
        content = "test content"
        source_file.write_text(content)
        dest_file.write_text(content)
        
        verifier = IntegrityVerifier()
        is_valid, error = verifier.verify_file(source_file, dest_file)
        
        assert is_valid is True
        assert error is None


def test_verify_different_files():
    """Testa verificação de arquivos diferentes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = Path(tmpdir) / "source.txt"
        dest_file = Path(tmpdir) / "dest.txt"
        
        source_file.write_text("content 1")
        dest_file.write_text("content 2")
        
        verifier = IntegrityVerifier()
        is_valid, error = verifier.verify_file(source_file, dest_file)
        
        assert is_valid is False
        assert error is not None


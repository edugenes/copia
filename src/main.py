"""
FileCopy Verifier - Aplicação Principal

Módulo principal que inicia a aplicação FileCopy Verifier.
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow
from utils.logger import AppLogger


def main():
    """Função principal que inicia a aplicação."""
    app = QApplication(sys.argv)
    app.setApplicationName("FileCopy Verifier")
    
    logger = AppLogger().get_logger()
    logger.info("Iniciando FileCopy Verifier")
    
    # Cria e exibe janela principal
    window = MainWindow()
    window.show()
    window.raise_()  # Traz janela para frente
    window.activateWindow()  # Ativa a janela
    
    # Executa aplicação
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


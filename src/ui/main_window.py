"""
Módulo: main_window.py
Janela principal da interface gráfica do FileCopy Verifier.
Autor: FileCopy Verifier Team
Data: 2024
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QProgressBar, QLabel, QFileDialog, QMessageBox,
    QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

from core.scanner import DirectoryScanner
from core.copier import FileCopier
from core.multi_file_copier import MultiFileCopier
from core.parallel_copier import ParallelFileCopier
from core.verifier import IntegrityVerifier
from utils.logger import AppLogger
from utils.cache import ScanCache


class ScanWorker(QThread):
    """Worker thread para executar escaneamento sem travar a GUI."""
    
    finished = pyqtSignal(dict)  # scan statistics
    error = pyqtSignal(str)  # error message
    log = pyqtSignal(str)  # log message
    
    def __init__(self, source_path: Path, source_files_list: List[str] = None):
        super().__init__()
        self.source_path = source_path
        self.source_files_list = source_files_list
    
    def run(self):
        """Executa o escaneamento."""
        try:
            self.log.emit("Iniciando escaneamento...")
            
            # Se tem lista de arquivos múltiplos, escaneia todos
            if self.source_files_list:
                total_size = 0
                total_files = len(self.source_files_list)
                for file_path in self.source_files_list:
                    path = Path(file_path)
                    if path.exists() and path.is_file():
                        total_size += path.stat().st_size
                
                stats = {
                    'total_files': total_files,
                    'total_directories': 0,
                    'total_size': total_size
                }
            else:
                scanner = DirectoryScanner(self.source_path)
                stats = scanner.scan()
            
            self.log.emit(f"Escaneamento concluído: {stats['total_files']} arquivo(s) encontrado(s)")
            self.finished.emit(stats)
        except Exception as e:
            self.error.emit(str(e))


class MultiFileCopyWorker(QThread):
    """Worker thread para executar cópia de múltiplos arquivos sem travar a GUI."""
    
    progress = pyqtSignal(int, int, str, int, int)  # current, total, filename, file_size, bytes_copied
    file_started = pyqtSignal(str, int)  # filename, file_size
    file_finished = pyqtSignal(str, bool)  # filename, success
    finished = pyqtSignal(dict)  # statistics
    error = pyqtSignal(str)  # error message
    log = pyqtSignal(str)  # log message
    
    def __init__(self, source_files: List[Path], destination: Path):
        super().__init__()
        self.source_files = source_files
        self.destination = destination
        self.multi_copier = MultiFileCopier(source_files, destination)
        self.multi_copier.set_progress_callback(self._on_progress)
        self.current_file = None
        self.current_file_size = 0
        self.total_size = 0
        self.start_time = None
    
    def pause(self):
        """Pausa a cópia."""
        if self.multi_copier:
            self.multi_copier.pause()
    
    def resume(self):
        """Retoma a cópia."""
        if self.multi_copier:
            self.multi_copier.resume()
    
    def cancel(self):
        """Cancela a cópia."""
        if self.multi_copier:
            self.multi_copier.cancel()
        self.terminate()
    
    def _on_progress(self, current: int, total: int, filename: Path, file_size: int, bytes_copied: int):
        """Callback de progresso."""
        if self.current_file != filename:
            # Novo arquivo iniciado
            self.current_file_size = file_size
            self.file_started.emit(str(filename), file_size)
            self.current_file = filename
        
        # Emite progresso com informações reais
        self.progress.emit(current, total, str(filename), file_size, bytes_copied)
    
    def run(self):
        """Executa a cópia."""
        try:
            self.start_time = datetime.now()
            self.log.emit(f"Iniciando cópia de {len(self.source_files)} arquivos para {self.destination}")
            
            # Calcula tamanho total
            total_size = 0
            for file_path in self.source_files:
                if file_path.exists() and file_path.is_file():
                    total_size += file_path.stat().st_size
            self.total_size = total_size
            
            stats = self.multi_copier.copy_all()
            
            # Adiciona informações de tamanho
            stats['total_size'] = self.total_size
            stats['start_time'] = self.start_time
            stats['end_time'] = datetime.now()
            
            self.finished.emit(stats)
        except Exception as e:
            self.error.emit(str(e))


class CopyWorker(QThread):
    """Worker thread para executar cópia sem travar a GUI."""
    
    progress = pyqtSignal(int, int, str, int, int)  # current, total, filename, file_size, bytes_copied
    file_started = pyqtSignal(str, int)  # filename, file_size
    file_finished = pyqtSignal(str, bool)  # filename, success
    finished = pyqtSignal(dict)  # statistics
    error = pyqtSignal(str)  # error message
    log = pyqtSignal(str)  # log message
    
    def __init__(self, source: Path, destination: Path, use_parallel: bool = False, num_threads: int = 4):
        super().__init__()
        self.source = source
        self.destination = destination
        self.use_parallel = use_parallel
        self.num_threads = num_threads
        self.copier = None
        self.parallel_copier = None
        self.current_file = None
        self.current_file_size = 0
        self.total_bytes_copied = 0
        self.total_size = 0
        self.start_time = None
    
    def _on_progress(self, current: int, total: int, filename: Path, file_size: int, bytes_copied: int):
        """Callback de progresso."""
        if self.current_file != filename:
            # Novo arquivo iniciado
            self.current_file_size = file_size
            self.file_started.emit(str(filename), file_size)
            self.current_file = filename
        
        # Emite progresso com informações reais
        self.progress.emit(current, total, str(filename), file_size, bytes_copied)
    
    def pause(self):
        """Pausa a cópia."""
        if self.copier:
            self.copier.pause()
        if self.parallel_copier:
            self.parallel_copier.pause()
    
    def resume(self):
        """Retoma a cópia."""
        if self.copier:
            self.copier.resume()
        if self.parallel_copier:
            self.parallel_copier.resume()
    
    def cancel(self):
        """Cancela a cópia."""
        if self.copier:
            self.copier.cancel()
        if self.parallel_copier:
            self.parallel_copier.cancel()
        self.terminate()
    
    def run(self):
        """Executa a cópia."""
        try:
            self.start_time = datetime.now()
            self.log.emit(f"Iniciando cópia de {self.source} para {self.destination}")
            
            # Calcula tamanho total primeiro
            scanner = DirectoryScanner(self.source)
            stats = scanner.scan()
            self.total_size = stats['total_size']
            
            # Usa cópia paralela ou sequencial
            if self.use_parallel and not self.source.is_file():
                self.parallel_copier = ParallelFileCopier(
                    self.source, 
                    self.destination, 
                    num_threads=self.num_threads
                )
                # Cria wrapper para converter callback em sinais PyQt
                def progress_wrapper(file_index, total, source_file, file_size, bytes_copied):
                    # Emite sinal de progresso
                    self.progress.emit(file_index, total, str(source_file), file_size, bytes_copied)
                    # Emite file_started se for novo arquivo
                    if str(source_file) not in getattr(self, '_seen_files', set()):
                        if not hasattr(self, '_seen_files'):
                            self._seen_files = set()
                        self._seen_files.add(str(source_file))
                        self.file_started.emit(str(source_file), file_size)
                        # Log quando inicia novo arquivo
                        self.log.emit(f"Copiando arquivo {file_index}/{total}: {Path(source_file).name}")
                
                self.parallel_copier.set_progress_callback(progress_wrapper)
                self._seen_files = set()
                stats = self.parallel_copier.copy_all()
            else:
                self.copier = FileCopier(self.source, self.destination)
                self.copier.set_progress_callback(self._on_progress)
                stats = self.copier.copy_all()
            
            # Adiciona informações de tamanho
            stats['total_size'] = self.total_size
            stats['start_time'] = self.start_time
            stats['end_time'] = datetime.now()
            
            self.finished.emit(stats)
        except Exception as e:
            self.error.emit(str(e))


class VerifyWorker(QThread):
    """Worker thread para executar verificação sem travar a GUI."""
    
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(dict)  # verification results
    error = pyqtSignal(str)  # error message
    log = pyqtSignal(str)  # log message
    
    def __init__(self, source: Path, destination: Path):
        super().__init__()
        self.source = source
        self.destination = destination
        self.verifier = IntegrityVerifier()
    
    def run(self):
        """Executa a verificação."""
        try:
            self.log.emit("Iniciando verificação de integridade...")
            
            scanner = DirectoryScanner(self.source)
            source_stats = scanner.scan()
            source_files = source_stats['files']
            
            verified = 0
            corrupted = []
            total = len(source_files)
            
            for idx, source_file in enumerate(source_files, 1):
                try:
                    relative_path = source_file.relative_to(self.source)
                    dest_file = self.destination / relative_path
                    
                    if not dest_file.exists():
                        corrupted.append((source_file, "Arquivo não encontrado no destino"))
                        self.progress.emit(verified + len(corrupted), total, str(source_file))
                        continue
                    
                    source_hash = self.verifier.calculate_hash(source_file)
                    dest_hash = self.verifier.calculate_hash(dest_file)
                    
                    if source_hash == dest_hash:
                        verified += 1
                    else:
                        corrupted.append((source_file, "Hash diferente"))
                    
                    self.progress.emit(verified + len(corrupted), total, str(source_file))
                    
                except Exception as e:
                    corrupted.append((source_file, str(e)))
                    self.progress.emit(verified + len(corrupted), total, str(source_file))
            
            result = {
                'total': total,
                'verified': verified,
                'corrupted': len(corrupted),
                'corrupted_list': corrupted
            }
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class FileProgressItem:
    """Classe para gerenciar item de arquivo na tabela."""
    def __init__(self, filename: str, size: int):
        self.filename = filename
        self.size = size
        self.bytes_copied = 0
        self.status = "copiando"  # copiando, concluído, erro
        self.speed = 0.0
        self.start_time = datetime.now()


class MainWindow(QMainWindow):
    """Janela principal da aplicação."""
    
    def __init__(self):
        super().__init__()
        self.logger = AppLogger().get_logger()
        self.copy_worker = None
        self.verify_worker = None
        self.scan_worker = None
        self.file_progress_items = {}  # filename -> FileProgressItem
        self.total_size = 0
        self.total_copied = 0
        self.scan_stats = None
        self.source_files_list = None  # Lista de arquivos selecionados (se múltiplos)
        self.is_paused = False
        # Detecta automaticamente número de threads (CPU count - 1, mínimo 2, máximo 8)
        cpu_count = os.cpu_count() or 4
        self.num_threads = max(2, min(8, cpu_count - 1))
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_file_progress)
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Inicializa a interface gráfica."""
        self.setWindowTitle("FileCopy Verifier")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        central_widget.setLayout(main_layout)
        
        # Grupo: Seleção de Diretórios
        dir_group = QGroupBox("Diretórios")
        dir_layout = QGridLayout()
        
        # Origem
        dir_layout.addWidget(QLabel("Origem:"), 0, 0)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Selecione arquivo(s) ou diretório de origem...")
        dir_layout.addWidget(self.source_edit, 0, 1)
        self.source_btn = QPushButton("Selecionar")
        self.source_btn.clicked.connect(self.select_source)
        dir_layout.addWidget(self.source_btn, 0, 2)
        
        # Destino
        dir_layout.addWidget(QLabel("Destino:"), 1, 0)
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("Selecione arquivo ou diretório de destino...")
        dir_layout.addWidget(self.dest_edit, 1, 1)
        self.dest_btn = QPushButton("Selecionar")
        self.dest_btn.clicked.connect(self.select_destination)
        dir_layout.addWidget(self.dest_btn, 1, 2)
        
        dir_group.setLayout(dir_layout)
        main_layout.addWidget(dir_group)
        
        # Grupo: Estatísticas Globais
        stats_group = QGroupBox("Estatísticas de Progresso")
        stats_layout = QGridLayout()
        
        # Labels de estatísticas
        self.total_label = QLabel("Total: --")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #e0e0e0;")
        stats_layout.addWidget(self.total_label, 0, 0)
        
        self.copied_label = QLabel("Copiado: --")
        self.copied_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #81C784;")
        stats_layout.addWidget(self.copied_label, 0, 1)
        
        self.remaining_label = QLabel("Restante: --")
        self.remaining_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #FFB74D;")
        stats_layout.addWidget(self.remaining_label, 0, 2)
        
        self.speed_label = QLabel("Velocidade: --")
        stats_layout.addWidget(self.speed_label, 1, 0)
        
        self.files_label = QLabel("Arquivos: --")
        stats_layout.addWidget(self.files_label, 1, 1)
        
        self.time_label = QLabel("Tempo: --")
        stats_layout.addWidget(self.time_label, 1, 2)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # Barra de progresso principal (melhorada)
        progress_group = QGroupBox("Progresso Geral")
        progress_layout = QVBoxLayout()
        
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setAlignment(Qt.AlignCenter)
        self.progress_percent_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: #64B5F6;")
        progress_layout.addWidget(self.progress_percent_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3a3a3a;
                border-radius: 5px;
                text-align: center;
                height: 30px;
                font-size: 12pt;
                font-weight: bold;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976D2, stop:1 #64B5F6);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Pronto")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 10pt; color: #b0b0b0;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # Seção de Arquivos em Cópia
        files_group = QGroupBox("Arquivos em Cópia")
        files_layout = QVBoxLayout()
        
        # Tabela de arquivos
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(6)
        self.files_table.setHorizontalHeaderLabels([
            "Arquivo", "Tamanho", "Progresso", "Velocidade", "Tempo Rest.", "Status"
        ])
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.setAlternatingRowColors(True)
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.files_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.files_table.setMaximumHeight(200)
        self.files_table.hide()  # Escondido inicialmente
        
        files_layout.addWidget(self.files_table)
        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("Escanear Origem")
        self.scan_btn.clicked.connect(self.scan_source)
        button_layout.addWidget(self.scan_btn)
        
        self.copy_btn = QPushButton("Iniciar Cópia")
        self.copy_btn.clicked.connect(self.start_copy)
        button_layout.addWidget(self.copy_btn)
        
        self.pause_btn = QPushButton("Pausar")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_operation)
        button_layout.addWidget(self.cancel_btn)
        
        self.verify_btn = QPushButton("Verificar Integridade")
        self.verify_btn.clicked.connect(self.start_verification)
        button_layout.addWidget(self.verify_btn)
        
        main_layout.addLayout(button_layout)
        
        # Área de log
        log_group = QGroupBox("Log de Operações")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Log inicial
        self.log("FileCopy Verifier iniciado. Selecione os diretórios de origem e destino.")
    
    def apply_styles(self):
        """Aplica estilos modernos com tema escuro à interface."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3a3a3a;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #e0e0e0;
                background-color: #252525;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #64B5F6;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #424242;
                color: #757575;
            }
            QLineEdit {
                padding: 5px;
                border: 2px solid #3a3a3a;
                border-radius: 4px;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 2px solid #64B5F6;
            }
            QTableWidget {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                background-color: #252525;
                color: #e0e0e0;
                gridline-color: #3a3a3a;
            }
            QTableWidget::item {
                padding: 5px;
                background-color: #252525;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #1976D2;
                color: white;
            }
            QTableWidget::item:alternate {
                background-color: #2d2d2d;
            }
            QHeaderView::section {
                background-color: #1565C0;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #252525;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
            QProgressBar {
                border: 2px solid #3a3a3a;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976D2, stop:1 #64B5F6);
                border-radius: 3px;
            }
            QLabel {
                color: #e0e0e0;
            }
            QMessageBox {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QMessageBox QLabel {
                color: #e0e0e0;
            }
            QMessageBox QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1565C0;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #3a3a3a;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4a4a4a;
            }
        """)
    
    def format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para formato legível."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def format_time(self, seconds: float) -> str:
        """Formata tempo em segundos para formato legível."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def get_timestamp(self) -> str:
        """Retorna timestamp formatado."""
        return datetime.now().strftime("%H:%M:%S")
    
    def should_use_parallel(self, source_path: Path) -> bool:
        """
        Decide automaticamente se deve usar cópia paralela.
        Usa paralela para diretórios com múltiplos arquivos, não para arquivo único.
        """
        if source_path.is_file():
            return False
        elif source_path.is_dir():
            # Conta arquivos rapidamente
            try:
                file_count = sum(1 for _ in source_path.rglob('*') if _.is_file())
                # Usa paralela se tiver mais de 1 arquivo
                return file_count > 1
            except:
                return True  # Em caso de erro, assume que pode usar paralela
        return False
    
    def select_source(self):
        """Abre diálogo para selecionar arquivo(s) ou diretório de origem."""
        # Diálogo para escolher entre arquivo ou diretório
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Origem")
        dialog.setModal(True)
        layout = QVBoxLayout()
        
        label = QLabel("O que deseja selecionar?")
        layout.addWidget(label)
        
        btn_file = QPushButton("Arquivo(s)")
        btn_file.clicked.connect(lambda: (dialog.accept(), self._select_source_file()))
        layout.addWidget(btn_file)
        
        btn_dir = QPushButton("Diretório/Pasta")
        btn_dir.clicked.connect(lambda: (dialog.accept(), self._select_source_directory()))
        layout.addWidget(btn_dir)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        layout.addWidget(btn_cancel)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _select_source_file(self):
        """Abre diálogo para selecionar arquivo(s)."""
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Selecione arquivo(s) de origem",
            "",
            "Todos os Arquivos (*.*)",
            options=options
        )
        
        if files:
            # Múltiplos arquivos selecionados
            if len(files) == 1:
                self.source_edit.setText(files[0])
                self.log(f"Arquivo de origem selecionado: {files[0]}")
            else:
                # Para múltiplos arquivos, mostra apenas o primeiro e indica quantidade
                self.source_edit.setText(f"{files[0]} (+ {len(files)-1} mais)")
                self.log(f"{len(files)} arquivos selecionados como origem")
            self.source_files_list = files
            self.animate_button(self.source_btn)
    
    def _select_source_directory(self):
        """Abre diálogo para selecionar diretório (incluindo unidades de rede)."""
        # Tenta usar diretório atual ou primeira unidade para mostrar todas as unidades
        import os
        initial_dir = os.getcwd()
        
        # No Windows, tenta começar de um local que mostre todas as unidades
        if os.name == 'nt':  # Windows
            # Tenta usar primeira unidade disponível
            try:
                import string
                drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
                if drives:
                    initial_dir = drives[0]  # Começa da primeira unidade disponível
            except:
                pass
        
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Selecione o diretório de origem",
            initial_dir,  # Começa de um diretório que mostra unidades
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.source_edit.setText(directory)
            self.log(f"Diretório de origem selecionado: {directory}")
            self.source_files_list = None
            self.animate_button(self.source_btn)
    
    def select_destination(self):
        """Abre diálogo para selecionar diretório de destino (incluindo unidades de rede)."""
        import os
        
        # No Windows, o diálogo nativo mostra automaticamente unidades de rede no painel lateral
        # Começa de um diretório raiz para facilitar navegação
        initial_dir = ""
        if os.name == 'nt':  # Windows
            try:
                # Tenta começar de uma unidade local (C:\) para mostrar painel lateral com todas as unidades
                import string
                drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
                if drives:
                    initial_dir = drives[0]  # Começa da primeira unidade (geralmente C:\)
            except:
                initial_dir = os.getcwd()
        else:
            initial_dir = os.getcwd()
        
        # O diálogo nativo do Windows mostra automaticamente:
        # - Unidades locais (C:\, D:\, etc.)
        # - Unidades de rede mapeadas (Z:\, Y:\, etc.) no painel lateral
        # - Pastas de rede não mapeadas podem ser acessadas digitando \\servidor\pasta
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Selecione o diretório de destino\n(Unidades de rede aparecem no painel lateral à esquerda)",
            initial_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            self.dest_edit.setText(directory)
            self.log(f"Diretório de destino selecionado: {directory}")
            self.animate_button(self.dest_btn)
    
    def animate_button(self, button: QPushButton):
        """Anima um botão quando clicado."""
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(100)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        original_geometry = button.geometry()
        animation.setStartValue(original_geometry)
        animation.setEndValue(original_geometry.adjusted(-2, -2, 2, 2))
        animation.finished.connect(lambda: button.setGeometry(original_geometry))
        animation.start()
    
    def scan_source(self):
        """Escaneia o arquivo(s) ou diretório de origem e exibe estatísticas."""
        source_path = self.source_edit.text()
        if not source_path:
            QMessageBox.warning(self, "Aviso", "Selecione o arquivo(s) ou diretório de origem primeiro.")
            return
        
        try:
            # Remove sufixo de múltiplos arquivos se existir
            if " (+ " in source_path:
                source_path = source_path.split(" (+ ")[0]
            
            self.log("Escaneando origem...")
            self.status_label.setText("Escaneando...")
            self.scan_btn.setEnabled(False)
            
            # Cria worker thread para escaneamento
            if self.source_files_list:
                # Para múltiplos arquivos, usa o primeiro como referência
                source_path_obj = Path(self.source_files_list[0]).parent
            else:
                source_path_obj = Path(source_path)
            
            self.scan_worker = ScanWorker(source_path_obj, self.source_files_list)
            self.scan_worker.finished.connect(self.on_scan_finished)
            self.scan_worker.error.connect(self.on_scan_error)
            self.scan_worker.log.connect(self.log)
            self.scan_worker.start()
            
        except Exception as e:
            error_msg = f"Erro ao iniciar escaneamento: {str(e)}"
            self.log(error_msg)
            QMessageBox.critical(self, "Erro", error_msg)
            self.status_label.setText("Erro no escaneamento")
            self.scan_btn.setEnabled(True)
    
    def on_scan_finished(self, stats: dict):
        """Callback quando escaneamento termina."""
        self.scan_stats = stats
        self.total_size = stats['total_size']
        
        # Atualiza labels
        self.total_label.setText(f"Total: {self.format_size(self.total_size)}")
        self.files_label.setText(f"Arquivos: {self.scan_stats['total_files']}")
        
        self.log(f"Escaneamento concluído: {self.scan_stats['total_files']} arquivo(s) encontrado(s)")
        self.log(f"Tamanho total: {self.format_size(self.total_size)}")
        self.status_label.setText("Escaneamento concluído")
        self.scan_btn.setEnabled(True)
    
    def on_scan_error(self, error_msg: str):
        """Callback de erro no escaneamento."""
        self.log(f"ERRO no escaneamento: {error_msg}")
        QMessageBox.critical(self, "Erro", f"Erro durante o escaneamento:\n{error_msg}")
        self.status_label.setText("Erro no escaneamento")
        self.scan_btn.setEnabled(True)
    
    def start_copy(self):
        """Inicia o processo de cópia."""
        source_path = self.source_edit.text()
        dest_path = self.dest_edit.text()
        
        if not source_path or not dest_path:
            QMessageBox.warning(self, "Aviso", "Selecione a origem e destino.")
            return
        
        # Remove sufixo de múltiplos arquivos se existir
        if " (+ " in source_path:
            source_path = source_path.split(" (+ ")[0]
        
        # Se não escaneou ainda, escaneia primeiro
        if not self.scan_stats:
            self.scan_source()
            if not self.scan_stats:
                return
        
        # Confirmação
        if self.source_files_list:
            source_info = f"{len(self.source_files_list)} arquivo(s) selecionado(s)"
            if len(self.source_files_list) <= 5:
                file_list = "\n".join([Path(f).name for f in self.source_files_list])
                source_info = f"Arquivos:\n{file_list}"
        else:
            source_info = source_path
        
        reply = QMessageBox.question(
            self, "Confirmar Cópia",
            f"Copiar:\n{source_info}\n\nPara:\n{dest_path}\n\nDeseja continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.copy_btn.setEnabled(False)
            self.verify_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.is_paused = False
            self.pause_btn.setText("Pausar")
            self.progress_bar.setValue(0)
            self.progress_percent_label.setText("0%")
            self.status_label.setText("Copiando...")
            # CORREÇÃO: Reseta contadores de forma segura
            self.total_copied = 0
            self.file_progress_items = {}
            self.files_table.setRowCount(0)
            self.files_table.show()
            # Garante que valores iniciais sejam válidos
            self.copied_label.setText("Copiado: 0 B")
            self.remaining_label.setText(f"Restante: {self.format_size(self.total_size)}")
            self.speed_label.setText("Velocidade: --")
            
            # Inicia timer de atualização
            self.update_timer.start(200)  # Atualiza a cada 200ms
            
            # Cria worker thread (múltiplos arquivos ou arquivo/diretório único)
            if self.source_files_list:
                self.copy_worker = MultiFileCopyWorker(
                    [Path(f) for f in self.source_files_list], 
                    Path(dest_path)
                )
            else:
                # Detecta automaticamente se deve usar cópia paralela
                source_path_obj = Path(source_path)
                use_parallel = self.should_use_parallel(source_path_obj)
                if use_parallel:
                    self.log(f"Modo paralelo ativado automaticamente ({self.num_threads} threads)")
                else:
                    self.log("Modo sequencial (arquivo único)")
                
                self.copy_worker = CopyWorker(
                    Path(source_path), 
                    Path(dest_path),
                    use_parallel=use_parallel,
                    num_threads=self.num_threads
                )
            
            self.copy_worker.progress.connect(self.on_copy_progress)
            self.copy_worker.file_started.connect(self.on_file_started)
            self.copy_worker.file_finished.connect(self.on_file_finished)
            self.copy_worker.finished.connect(self.on_copy_finished)
            self.copy_worker.error.connect(self.on_copy_error)
            self.copy_worker.log.connect(self.log)
            self.copy_worker.start()
    
    def on_file_started(self, filename: str, file_size: int):
        """Callback quando um arquivo inicia cópia."""
        item = FileProgressItem(filename, file_size)
        self.file_progress_items[filename] = item
        
        # Adiciona linha na tabela
        row = self.files_table.rowCount()
        self.files_table.insertRow(row)
        
        # Nome do arquivo
        name_item = QTableWidgetItem(Path(filename).name)
        self.files_table.setItem(row, 0, name_item)
        
        # Tamanho
        size_item = QTableWidgetItem(self.format_size(file_size))
        self.files_table.setItem(row, 1, size_item)
        
        # Barra de progresso
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("%p%")
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                text-align: center;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976D2, stop:1 #64B5F6);
                border-radius: 2px;
            }
        """)
        self.files_table.setCellWidget(row, 2, progress_bar)
        
        # Velocidade
        speed_item = QTableWidgetItem("--")
        self.files_table.setItem(row, 3, speed_item)
        
        # Tempo restante
        time_item = QTableWidgetItem("--")
        self.files_table.setItem(row, 4, time_item)
        
        # Status
        status_item = QTableWidgetItem("⏳ Copiando")
        status_item.setForeground(QColor("#64B5F6"))
        self.files_table.setItem(row, 5, status_item)
        
        # Scroll para última linha
        self.files_table.scrollToBottom()
    
    def on_file_finished(self, filename: str, success: bool):
        """Callback quando um arquivo termina cópia."""
        if filename in self.file_progress_items:
            item = self.file_progress_items[filename]
            item.status = "concluído" if success else "erro"
            item.bytes_copied = item.size if success else item.bytes_copied
    
    def toggle_pause(self):
        """Alterna entre pausar e retomar."""
        if self.copy_worker and self.copy_worker.isRunning():
            if self.is_paused:
                self.copy_worker.resume()
                self.is_paused = False
                self.pause_btn.setText("Pausar")
                self.status_label.setText("Copiando...")
                self.log("Cópia retomada")
            else:
                self.copy_worker.pause()
                self.is_paused = True
                self.pause_btn.setText("Retomar")
                self.status_label.setText("Pausado")
                self.log("Cópia pausada")
    
    def update_file_progress(self):
        """Atualiza progresso dos arquivos na tabela."""
        # Cria mapeamento de nome de arquivo para linha
        filename_to_row = {}
        for row in range(self.files_table.rowCount()):
            name_item = self.files_table.item(row, 0)
            if name_item:
                filename_to_row[name_item.text()] = row
        
        # Atualiza cada arquivo na lista de progresso
        for filename, item in self.file_progress_items.items():
            file_name = Path(filename).name
            if file_name in filename_to_row:
                row = filename_to_row[file_name]
                
                # Atualiza progresso
                if item.size > 0:
                    # CORREÇÃO: Garante que bytes_copied não exceda size e progresso seja válido
                    valid_bytes = min(max(0, item.bytes_copied), item.size)
                    progress = int((valid_bytes / item.size) * 100)
                    progress = max(0, min(100, progress))  # Limita entre 0 e 100
                    progress_bar = self.files_table.cellWidget(row, 2)
                    if progress_bar:
                        progress_bar.setValue(progress)
                
                # Atualiza velocidade
                speed_item = self.files_table.item(row, 3)
                if speed_item:
                    # CORREÇÃO: Garante velocidade não negativa
                    valid_speed = max(0, item.speed)
                    if valid_speed > 0:
                        speed_item.setText(f"{self.format_size(int(valid_speed))}/s")
                        speed_item.setData(Qt.UserRole, valid_speed)  # Para ordenação
                    else:
                        speed_item.setText("--")
                        speed_item.setData(Qt.UserRole, 0.0)
                
                # Atualiza tempo restante
                time_item = self.files_table.item(row, 4)
                if time_item:
                    # CORREÇÃO: Validações para evitar valores inválidos
                    valid_bytes = min(max(0, item.bytes_copied), item.size)
                    valid_speed = max(0, item.speed)
                    if valid_speed > 0 and item.size > valid_bytes:
                        remaining_bytes = item.size - valid_bytes
                        remaining_time = remaining_bytes / valid_speed
                        # Garante tempo não negativo
                        remaining_time = max(0, remaining_time)
                        time_item.setText(self.format_time(remaining_time))
                    else:
                        time_item.setText("--")
                
                # Atualiza status
                status_item = self.files_table.item(row, 5)
                if status_item:
                    if item.status == "concluído":
                        status_item.setText("✅ Concluído")
                        status_item.setForeground(QColor("#81C784"))
                    elif item.status == "erro":
                        status_item.setText("❌ Erro")
                        status_item.setForeground(QColor("#E57373"))
                    else:
                        status_item.setText("⏳ Copiando")
                        status_item.setForeground(QColor("#64B5F6"))
    
    def cancel_operation(self):
        """Cancela a operação em andamento."""
        if self.copy_worker and self.copy_worker.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar Cancelamento",
                "Deseja realmente cancelar a operação?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.copy_worker.cancel()
                self.update_timer.stop()
                self.copy_btn.setEnabled(True)
                self.verify_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)
                self.cancel_btn.setEnabled(False)
                self.status_label.setText("Operação cancelada")
                self.log("Operação cancelada pelo usuário")
    
    def on_copy_progress(self, current: int, total: int, filename: str, file_size: int, bytes_copied: int):
        """Atualiza progresso da cópia."""
        # CORREÇÃO: Validações para evitar valores inválidos
        if bytes_copied < 0:
            bytes_copied = 0
        if file_size > 0 and bytes_copied > file_size:
            bytes_copied = file_size
        
        # Garante que o arquivo está na lista de progresso
        if filename not in self.file_progress_items:
            self.on_file_started(filename, file_size)
        
        if total > 0:
            # Global progress based on bytes
            if filename in self.file_progress_items:
                item = self.file_progress_items[filename]
                
                # CORREÇÃO: Garante que bytes_copied nunca exceda o tamanho do arquivo
                old_bytes = item.bytes_copied
                # Valida e limita bytes_copied
                if item.size > 0:
                    item.bytes_copied = min(max(0, bytes_copied), item.size)
                else:
                    item.bytes_copied = max(0, bytes_copied)
                
                # CORREÇÃO: Se bytes_copied diminuir (erro de sincronização), mantém valor anterior
                if item.bytes_copied < old_bytes:
                    # Mantém o valor anterior se houver regressão (indica erro de sincronização)
                    item.bytes_copied = old_bytes
                    bytes_delta = 0
                else:
                    bytes_delta = item.bytes_copied - old_bytes
                
                # CORREÇÃO: Calcula velocidade apenas se houver mudança significativa
                elapsed = (datetime.now() - item.start_time).total_seconds()
                if elapsed > 0 and item.bytes_copied > 0:
                    # Usa apenas bytes válidos para calcular velocidade
                    item.speed = max(0, item.bytes_copied / elapsed)
                else:
                    item.speed = 0.0
                
                # CORREÇÃO: Cálculo incremental em vez de recalcular tudo (melhor performance)
                if bytes_delta > 0:  # Apenas incrementa se houver aumento válido
                    self.total_copied += bytes_delta
                    # Garante que total_copied não exceda total_size
                    if self.total_size > 0:
                        self.total_copied = min(self.total_copied, self.total_size)
                # Se bytes_delta == 0 ou negativo, não faz nada (mantém valor atual)
            
            # CORREÇÃO: Validações para evitar valores negativos ou inválidos
            if self.total_size > 0:
                # Garante que total_copied não exceda total_size
                self.total_copied = min(self.total_copied, self.total_size)
                self.total_copied = max(0, self.total_copied)  # Nunca negativo
                
                self.copied_label.setText(f"Copiado: {self.format_size(int(self.total_copied))}")
                remaining = max(0, self.total_size - self.total_copied)
                self.remaining_label.setText(f"Restante: {self.format_size(int(remaining))}")
                
                # CORREÇÃO: Garante que progresso seja entre 0 e 100
                bytes_progress = int((self.total_copied / self.total_size) * 100) if self.total_size > 0 else 0
                bytes_progress = max(0, min(100, bytes_progress))  # Limita entre 0 e 100
                self.progress_bar.setValue(bytes_progress)
                self.progress_percent_label.setText(f"{bytes_progress}%")
                
                if self.copy_worker and hasattr(self.copy_worker, 'start_time') and self.copy_worker.start_time:
                    elapsed_global = (datetime.now() - self.copy_worker.start_time).total_seconds()
                    if elapsed_global > 0 and self.total_copied > 0:
                        avg_speed = self.total_copied / elapsed_global
                        # CORREÇÃO: Garante velocidade não negativa
                        avg_speed = max(0, avg_speed)
                        self.speed_label.setText(f"Velocidade: {self.format_size(int(avg_speed))}/s")
                        
                        # Calcula tempo estimado restante
                        if avg_speed > 0:
                            remaining_bytes = max(0, self.total_size - self.total_copied)
                            remaining_time = remaining_bytes / avg_speed
                            self.time_label.setText(f"Tempo: {self.format_time(elapsed_global)} | Restante: {self.format_time(remaining_time)}")
                        else:
                            self.time_label.setText(f"Tempo: {self.format_time(elapsed_global)}")
                    else:
                        self.speed_label.setText("Velocidade: --")
                        self.time_label.setText("Tempo: --")
            else: # Fallback for file count progress if total_size is 0 (e.g., empty files)
                if total > 0:
                    progress = int((current / total) * 100)
                    progress = max(0, min(100, progress))  # Limita entre 0 e 100
                    self.progress_bar.setValue(progress)
                    self.progress_percent_label.setText(f"{progress}%")
            
            self.files_label.setText(f"Arquivos: {current} / {total}")
            self.status_label.setText(f"Copiando: {Path(filename).name}")
            
            # CORREÇÃO: Não atualiza tabela imediatamente (deixa o timer fazer isso)
            # Isso reduz overhead e melhora performance
            # self.update_file_progress()  # Removido - timer já faz isso
    
    def update_files_table(self):
        """Atualiza tabela de arquivos imediatamente."""
        self.update_file_progress()
    
    def on_copy_finished(self, stats: dict):
        """Callback quando cópia termina."""
        self.update_timer.stop()
        self.copy_btn.setEnabled(True)
        self.verify_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.is_paused = False
        self.pause_btn.setText("Pausar")
        self.progress_bar.setValue(100)
        self.progress_percent_label.setText("100%")
        
        # Calcula tempo total
        if 'start_time' in stats and 'end_time' in stats:
            elapsed = (stats['end_time'] - stats['start_time']).total_seconds()
            self.time_label.setText(f"Tempo: {self.format_time(elapsed)}")
        
        self.status_label.setText("Cópia concluída")
        self.log(f"Cópia concluída: {stats['copied_files']} arquivo(s) copiado(s)")
        
        if stats['failed_files'] > 0:
            self.log(f"Atenção: {stats['failed_files']} arquivo(s) falharam")
        
        success_msg = f"Cópia concluída!\n\n"
        success_msg += f"Arquivos copiados: {stats['copied_files']} de {stats['total_files']}\n"
        if stats['failed_files'] > 0:
            success_msg += f"Arquivos com erro: {stats['failed_files']}\n"
        
        if stats['failed_files'] > 0:
            QMessageBox.warning(self, "Cópia Concluída", success_msg)
        else:
            QMessageBox.information(self, "Sucesso", success_msg)
    
    def on_copy_error(self, error_msg: str):
        """Callback de erro na cópia."""
        self.update_timer.stop()
        self.copy_btn.setEnabled(True)
        self.verify_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.is_paused = False
        self.pause_btn.setText("Pausar")
        self.log(f"ERRO: {error_msg}")
        self.status_label.setText("Erro na cópia")
        QMessageBox.critical(self, "Erro", f"Erro durante a cópia:\n{error_msg}")
    
    def start_verification(self):
        """Inicia a verificação de integridade."""
        source_path = self.source_edit.text()
        dest_path = self.dest_edit.text()
        
        if not source_path or not dest_path:
            QMessageBox.warning(self, "Aviso", "Selecione a origem e destino.")
            return
        
        # Remove sufixo de múltiplos arquivos se existir
        if " (+ " in source_path:
            source_path = source_path.split(" (+ ")[0]
        
        self.verify_btn.setEnabled(False)
        self.status_label.setText("Verificando...")
        self.progress_bar.setValue(0)
        self.log("Iniciando verificação de integridade...")
        
        self.verify_worker = VerifyWorker(Path(source_path), Path(dest_path))
        self.verify_worker.progress.connect(self.on_verify_progress)
        self.verify_worker.finished.connect(self.on_verify_finished)
        self.verify_worker.error.connect(self.on_verify_error)
        self.verify_worker.log.connect(self.log)
        self.verify_worker.start()
    
    def on_verify_progress(self, current: int, total: int, filename: str):
        """Atualiza progresso da verificação."""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_percent_label.setText(f"{progress}%")
            self.status_label.setText(f"Verificando: {Path(filename).name}")
    
    def on_verify_finished(self, result: dict):
        """Callback quando verificação termina."""
        self.verify_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_percent_label.setText("100%")
        self.status_label.setText("Verificação concluída")
        
        msg = f"Verificação concluída!\n\n"
        msg += f"Total de arquivos: {result['total']}\n"
        msg += f"Arquivos verificados: {result['verified']}\n"
        msg += f"Arquivos corrompidos: {result['corrupted']}\n"
        
        if result['corrupted'] > 0:
            msg += f"\nArquivos com problemas:\n"
            for file_path, error in result['corrupted_list'][:10]:  # Mostra até 10
                msg += f"- {Path(file_path).name}: {error}\n"
            if len(result['corrupted_list']) > 10:
                msg += f"... e mais {len(result['corrupted_list']) - 10} arquivo(s)\n"
            
            QMessageBox.warning(self, "Verificação Concluída", msg)
        else:
            QMessageBox.information(self, "Sucesso", msg)
        
        self.log(f"Verificação concluída: {result['verified']} de {result['total']} arquivos verificados")
    
    def on_verify_error(self, error_msg: str):
        """Callback de erro na verificação."""
        self.verify_btn.setEnabled(True)
        self.log(f"ERRO na verificação: {error_msg}")
        self.status_label.setText("Erro na verificação")
        QMessageBox.critical(self, "Erro", f"Erro durante a verificação:\n{error_msg}")
    
    def log(self, message: str):
        """Adiciona mensagem ao log."""
        self.log_text.append(f"[{self.get_timestamp()}] {message}")
        self.logger.info(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
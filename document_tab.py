"""
Módulo de Abas de Documentos (Multi-Tab Document Architecture)
Permite que o Leitor de PDF abra múltiplos arquivos em abas simultâneas,
cada um com visualizador, miniaturas, sumário e estado independentes.
"""

import sys
sys.modules['pymupdf.layout'] = None

import os
import pymupdf
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QPushButton
)

from pdf_viewer import PDFViewer
from thumbnails import SidebarWidget


class DocumentTab(QWidget):
    """Representa uma aba individual contendo um documento PDF completo"""
    pageChanged = pyqtSignal(object, int, int)       # (self, curr_page, total_pages)
    zoomChanged = pyqtSignal(object, float)          # (self, zoom)
    statusMessage = pyqtSignal(object, str)          # (self, msg)
    documentModified = pyqtSignal(object)            # (self)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.file_path = None
        self.doc = None
        self.is_modified = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Divisor da aba: Barra Lateral de Miniaturas/Marcadores + Visualizador
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)

        self.sidebar = SidebarWidget(self)
        self.sidebar.pageSelected.connect(self._on_sidebar_page_selected)
        self.sidebar.exportPagePdfRequested.connect(self.main_window.prompt_export_page_pdf)
        self.sidebar.exportPageImageRequested.connect(self.main_window.prompt_export_page_image)
        self.sidebar.splitPagesRequested.connect(self.main_window.prompt_split_pages)
        self.sidebar.importPdfRequested.connect(self.main_window.prompt_import_pdf)
        self.sidebar.importImageRequested.connect(self.main_window.prompt_import_image)
        self.sidebar.rotatePageRequested.connect(self.main_window._prompt_rotate_specific_page)
        self.sidebar.deletePageRequested.connect(self.main_window._prompt_delete_specific_page)
        self.splitter.addWidget(self.sidebar)

        self.viewer = PDFViewer(self)
        self.viewer.pageChanged.connect(self._on_viewer_page_changed)
        self.viewer.zoomChanged.connect(self._on_viewer_zoom_changed)
        self.viewer.statusMessage.connect(self._on_viewer_status_message)
        self.viewer.documentModified.connect(self._on_viewer_document_modified)
        self.splitter.addWidget(self.viewer)

        self.splitter.setSizes([260, 920])
        layout.addWidget(self.splitter)

    @property
    def tab_name(self):
        if self.file_path:
            return os.path.basename(self.file_path)
        return "Sem Título"

    @property
    def display_title(self):
        mod = "• " if self.is_modified else ""
        return f"{mod}{self.tab_name}"

    def load_file(self, file_path):
        """Abre e carrega um documento a partir do disco"""
        doc = pymupdf.open(file_path)
        self.doc = doc
        self.file_path = file_path
        self.is_modified = False

        self.viewer.load_document(doc)
        self.sidebar.load_document(doc)

    def load_doc(self, doc, file_path=None):
        """Carrega um objeto pymupdf.Document existente (ex: novo ou em memória)"""
        self.doc = doc
        self.file_path = file_path

        self.viewer.load_document(doc)
        self.sidebar.load_document(doc)

    def close_tab(self):
        """Encerra threads em background e fecha recursos do documento"""
        try:
            if self.sidebar.thumbnail_list._worker and self.sidebar.thumbnail_list._worker.isRunning():
                self.sidebar.thumbnail_list._worker.cancel()
                self.sidebar.thumbnail_list._worker.wait()
        except Exception:
            pass

        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass
            self.doc = None

        self.viewer.doc = None
        self.viewer.canvas.pixmap = None

    def _on_sidebar_page_selected(self, page_idx):
        self.viewer.go_to_page(page_idx)

    def _on_viewer_page_changed(self, current_page, total_pages):
        self.sidebar.highlight_page(current_page - 1)
        self.pageChanged.emit(self, current_page, total_pages)

    def _on_viewer_zoom_changed(self, zoom):
        self.zoomChanged.emit(self, zoom)

    def _on_viewer_status_message(self, msg):
        self.statusMessage.emit(self, msg)

    def _on_viewer_document_modified(self):
        self.is_modified = True
        self.documentModified.emit(self)


class WelcomePlaceholderWidget(QWidget):
    """Exibido no centro da janela quando nenhuma aba/documento está aberto"""
    openRequested = pyqtSignal()
    createFromImagesRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)

        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 56px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel("Leitor e Editor de PDF")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e3a8a;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Abra múltiplos arquivos PDF em abas para leitura, anotação e edição rápida.")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 10px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        btn_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_open = QPushButton("📂 Abrir Arquivo PDF...")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 9px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_open.clicked.connect(self.openRequested.emit)
        btn_box.addWidget(btn_open)

        btn_img = QPushButton("🖼️ Criar a partir de Imagens...")
        btn_img.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_img.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                font-weight: 600;
                font-size: 13px;
                padding: 9px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }
        """)
        btn_img.clicked.connect(self.createFromImagesRequested.emit)
        btn_box.addWidget(btn_img)

        layout.addLayout(btn_box)

        hint = QLabel("💡 Dica: Você também pode arrastar e soltar múltiplos arquivos PDF diretamente aqui.")
        hint.setStyleSheet("font-size: 12px; color: #94a3b8; margin-top: 15px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

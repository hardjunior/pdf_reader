"""
Painel lateral com Miniaturas das Páginas (Thumbnails) e Marcadores/Índice (Outline/TOC)
"""

import sys
sys.modules['pymupdf.layout'] = None

import pymupdf
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel, QMenu
)


class ThumbnailWorker(QThread):
    """Gera miniaturas em segundo plano para não travar a interface"""
    thumbnail_ready = pyqtSignal(int, QPixmap)

    def __init__(self, doc, total_pages, target_width=120):
        super().__init__()
        self.doc = doc
        self.total_pages = total_pages
        self.target_width = target_width
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        for page_idx in range(self.total_pages):
            if self._is_cancelled:
                break
            try:
                page = self.doc.load_page(page_idx)
                rect = page.rect
                scale = self.target_width / max(1.0, rect.width)
                matrix = pymupdf.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                qimg = QImage(
                    pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
                )
                pixmap = QPixmap.fromImage(qimg)
                self.thumbnail_ready.emit(page_idx, pixmap)
            except Exception:
                pass


class ThumbnailListWidget(QListWidget):
    """Lista de miniaturas das páginas estilo Adobe Reader com menu contextual"""
    pageSelected = pyqtSignal(int)
    exportPagePdfRequested = pyqtSignal(int)
    exportPageImageRequested = pyqtSignal(int)
    splitPagesRequested = pyqtSignal()
    importPdfRequested = pyqtSignal(int)
    importImageRequested = pyqtSignal(int)
    rotatePageRequested = pyqtSignal(int)
    deletePageRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(110, 150))
        self.setGridSize(QSize(130, 180))
        self.setMovement(QListWidget.Movement.Static)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setSpacing(8)
        self.itemClicked.connect(self._on_item_clicked)
        self._worker = None

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return
        page_idx = item.data(Qt.ItemDataRole.UserRole)
        if page_idx is None:
            return

        self.setCurrentItem(item)
        self.pageSelected.emit(page_idx)

        menu = QMenu(self)

        act_exp_pdf = menu.addAction(f"📤 Exportar Página {page_idx + 1} como PDF...")
        act_exp_pdf.triggered.connect(lambda: self.exportPagePdfRequested.emit(page_idx))

        act_exp_img = menu.addAction(f"🖼️ Exportar Página {page_idx + 1} como Imagem...")
        act_exp_img.triggered.connect(lambda: self.exportPageImageRequested.emit(page_idx))

        act_split = menu.addAction("✂️ Separar / Dividir Páginas...")
        act_split.triggered.connect(self.splitPagesRequested.emit)

        menu.addSeparator()

        act_imp_pdf = menu.addAction(f"➕ Inserir Páginas de PDF aqui...")
        act_imp_pdf.triggered.connect(lambda: self.importPdfRequested.emit(page_idx + 1))

        act_imp_img = menu.addAction(f"🖼️ Inserir Imagem como Página aqui...")
        act_imp_img.triggered.connect(lambda: self.importImageRequested.emit(page_idx + 1))

        menu.addSeparator()

        act_rot = menu.addAction(f"↻ Girar Página {page_idx + 1} Permanentemente")
        act_rot.triggered.connect(lambda: self.rotatePageRequested.emit(page_idx))

        act_del = menu.addAction(f"🗑️ Excluir Página {page_idx + 1}")
        act_del.triggered.connect(lambda: self.deletePageRequested.emit(page_idx))

        menu.exec(event.globalPos())

    def load_document(self, doc):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        self.clear()
        total_pages = len(doc)

        # Cria itens de placeholder inicialmente
        for i in range(total_pages):
            item = QListWidgetItem(f"Página {i + 1}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            self.addItem(item)

        # Inicia renderização em background
        self._worker = ThumbnailWorker(doc, total_pages, target_width=110)
        self._worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        self._worker.start()

    def _on_thumbnail_ready(self, page_idx, pixmap):
        if page_idx < self.count():
            item = self.item(page_idx)
            item.setIcon(QIcon(pixmap))

    def _on_item_clicked(self, item):
        page_idx = item.data(Qt.ItemDataRole.UserRole)
        if page_idx is not None:
            self.pageSelected.emit(page_idx)

    def highlight_page(self, page_idx):
        if 0 <= page_idx < self.count():
            item = self.item(page_idx)
            self.setCurrentItem(item)
            self.scrollToItem(item, QListWidget.ScrollHint.EnsureVisible)


class OutlineTreeWidget(QTreeWidget):
    """Árvore interativa de marcadores / sumário do PDF"""
    pageSelected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.itemClicked.connect(self._on_item_clicked)

    def load_document(self, doc):
        self.clear()
        toc = doc.get_toc()  # [[lvl, title, page, ...], ...]
        if not toc:
            return False

        # Constrói a hierarquia de tópicos
        stack = [(0, self.invisibleRootItem())]

        for item in toc:
            level, title, page_num = item[0], item[1], item[2]
            tree_item = QTreeWidgetItem([title])
            tree_item.setData(0, Qt.ItemDataRole.UserRole, page_num - 1)  # 0-indexed
            
            # Encontra o item pai correspondente ao nível
            while stack and stack[-1][0] >= level:
                stack.pop()

            parent_item = stack[-1][1] if stack else self.invisibleRootItem()
            parent_item.addChild(tree_item)
            stack.append((level, tree_item))

        self.expandAll()
        return True

    def _on_item_clicked(self, item, column):
        page_idx = item.data(0, Qt.ItemDataRole.UserRole)
        if page_idx is not None and page_idx >= 0:
            self.pageSelected.emit(page_idx)


class SidebarWidget(QWidget):
    """Painel lateral com abas para Miniaturas e Sumário"""
    pageSelected = pyqtSignal(int)
    exportPagePdfRequested = pyqtSignal(int)
    exportPageImageRequested = pyqtSignal(int)
    splitPagesRequested = pyqtSignal()
    importPdfRequested = pyqtSignal(int)
    importImageRequested = pyqtSignal(int)
    rotatePageRequested = pyqtSignal(int)
    deletePageRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.thumbnail_list = ThumbnailListWidget()
        self.thumbnail_list.pageSelected.connect(self.pageSelected)
        self.thumbnail_list.exportPagePdfRequested.connect(self.exportPagePdfRequested)
        self.thumbnail_list.exportPageImageRequested.connect(self.exportPageImageRequested)
        self.thumbnail_list.splitPagesRequested.connect(self.splitPagesRequested)
        self.thumbnail_list.importPdfRequested.connect(self.importPdfRequested)
        self.thumbnail_list.importImageRequested.connect(self.importImageRequested)
        self.thumbnail_list.rotatePageRequested.connect(self.rotatePageRequested)
        self.thumbnail_list.deletePageRequested.connect(self.deletePageRequested)

        self.outline_tree = OutlineTreeWidget()
        self.outline_tree.pageSelected.connect(self.pageSelected)

        self.tabs.addTab(self.thumbnail_list, "📑 Miniaturas")
        self.tabs.addTab(self.outline_tree, "🔖 Marcadores")

        self.layout.addWidget(self.tabs)
        self.setMinimumWidth(220)

    def load_document(self, doc):
        self.thumbnail_list.load_document(doc)
        has_toc = self.outline_tree.load_document(doc)
        if not has_toc:
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabText(1, "🔖 Marcadores (Sem índice)")
            self.tabs.setCurrentIndex(0)
        else:
            self.tabs.setTabEnabled(1, True)
            self.tabs.setTabText(1, "🔖 Marcadores")

    def highlight_page(self, page_idx):
        self.thumbnail_list.highlight_page(page_idx)

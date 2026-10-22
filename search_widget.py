"""
Barra de busca de texto integrada estilo Adobe Reader / Chrome PDF
"""

import sys
sys.modules['pymupdf.layout'] = None

import pymupdf
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QCheckBox
)


class SearchBar(QFrame):
    """Barra retrátil de busca com atalhos e contagem de ocorrências"""
    matchSelected = pyqtSignal(int, int, list)  # page_idx, current_idx_on_page, all_matches_on_page
    searchClosed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("search_bar_frame")
        self.doc = None
        self.matches = []          # [(page_idx, rect, idx_in_page), ...]
        self.matches_by_page = {}  # {page_idx: [rect, rect, ...]}
        self.current_match_index = -1

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        icon_label = QLabel("🔍")
        layout.addWidget(icon_label)

        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Localizar no documento...")
        self.input_text.setMinimumWidth(180)
        self.input_text.returnPressed.connect(self.find_next)
        self.input_text.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.input_text)

        self.lbl_count = QLabel("0 de 0")
        self.lbl_count.setStyleSheet("font-size: 12px; font-weight: bold; min-width: 55px;")
        layout.addWidget(self.lbl_count)

        self.btn_prev = QPushButton("▲")
        self.btn_prev.setToolTip("Ocorrência anterior (Shift+Enter)")
        self.btn_prev.setFixedSize(26, 26)
        self.btn_prev.clicked.connect(self.find_prev)
        layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("▼")
        self.btn_next.setToolTip("Próxima ocorrência (Enter)")
        self.btn_next.setFixedSize(26, 26)
        self.btn_next.clicked.connect(self.find_next)
        layout.addWidget(self.btn_next)

        self.chk_case = QCheckBox("Aa")
        self.chk_case.setToolTip("Diferenciar maiúsculas de minúsculas")
        self.chk_case.stateChanged.connect(lambda: self._on_text_changed(self.input_text.text()))
        layout.addWidget(self.chk_case)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Fechar busca (Esc)")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet("border: none; font-weight: bold; font-size: 14px;")
        self.btn_close.clicked.connect(self.close_search)
        layout.addWidget(self.btn_close)

    def set_document(self, doc):
        self.doc = doc
        self.clear_search()

    def show_and_focus(self):
        self.show()
        self.input_text.selectAll()
        self.input_text.setFocus()
        if self.input_text.text():
            self._execute_search(self.input_text.text())

    def close_search(self):
        self.clear_search()
        self.hide()
        self.searchClosed.emit()

    def clear_search(self):
        self.matches = []
        self.matches_by_page = {}
        self.current_match_index = -1
        self.lbl_count.setText("0 de 0")

    def _on_text_changed(self, text):
        if not text.strip():
            self.clear_search()
            self.searchClosed.emit()
            return
        self._execute_search(text.strip())

    def _execute_search(self, query):
        if not self.doc or len(self.doc) == 0 or not query:
            return

        self.matches = []
        self.matches_by_page = {}
        flags = 0
        if not self.chk_case.isChecked():
            flags = pymupdf.TEXT_CASE_INSENSITIVE if hasattr(pymupdf, 'TEXT_CASE_INSENSITIVE') else 0

        for p_idx in range(len(self.doc)):
            page = self.doc.load_page(p_idx)
            try:
                rects = page.search_for(query)
            except Exception:
                rects = []

            if rects:
                self.matches_by_page[p_idx] = rects
                for r_idx, rect in enumerate(rects):
                    self.matches.append((p_idx, rect, r_idx))

        total = len(self.matches)
        if total > 0:
            self.current_match_index = 0
            self._update_current_match()
        else:
            self.current_match_index = -1
            self.lbl_count.setText("0 de 0")
            self.searchClosed.emit()

    def find_next(self):
        if not self.matches:
            return
        self.current_match_index = (self.current_match_index + 1) % len(self.matches)
        self._update_current_match()

    def find_prev(self):
        if not self.matches:
            return
        self.current_match_index = (self.current_match_index - 1) % len(self.matches)
        self._update_current_match()

    def _update_current_match(self):
        total = len(self.matches)
        if total == 0 or self.current_match_index < 0:
            return

        curr = self.current_match_index + 1
        self.lbl_count.setText(f"{curr} de {total}")

        page_idx, rect, idx_on_page = self.matches[self.current_match_index]
        page_rects = self.matches_by_page.get(page_idx, [])
        self.matchSelected.emit(page_idx, idx_on_page, page_rects)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_search()
            event.accept()
        else:
            super().keyPressEvent(event)

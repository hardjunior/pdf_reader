"""
Caixas de diálogo informativas e propriedades do documento PDF
"""

import os
import pymupdf
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTabWidget, QWidget, QFrame,
    QRadioButton, QButtonGroup, QLineEdit, QGroupBox,
    QComboBox, QListWidget, QFileDialog, QMessageBox,
    QTextEdit, QSpinBox, QFormLayout
)


class PropertiesDialog(QDialog):
    """Exibe propriedades e metadados detalhados do arquivo PDF"""
    def __init__(self, doc, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Propriedades do Documento")
        self.resize(480, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        meta = doc.metadata or {}
        file_size_kb = os.path.getsize(file_path) / 1024 if os.path.exists(file_path) else 0
        file_size_str = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{(file_size_kb / 1024):.2f} MB"

        info_grid = [
            ("Arquivo:", os.path.basename(file_path)),
            ("Localização:", os.path.dirname(file_path)),
            ("Tamanho do Arquivo:", file_size_str),
            ("Número de Páginas:", str(len(doc))),
            ("Título:", meta.get("title") or "Não informado"),
            ("Autor:", meta.get("author") or "Não informado"),
            ("Assunto:", meta.get("subject") or "Não informado"),
            ("Palavras-chave:", meta.get("keywords") or "Não informado"),
            ("Criador / Software:", meta.get("creator") or "Não informado"),
            ("Produtor do PDF:", meta.get("producer") or "Não informado"),
            ("Data de Criação:", meta.get("creationDate") or "Não informado"),
            ("Data de Modificação:", meta.get("modDate") or "Não informado"),
            ("Versão do Formato:", meta.get("format") or "PDF"),
        ]

        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setVerticalSpacing(8)

        for row, (label, val) in enumerate(info_grid):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #4b5563;")
            val_lbl = QLabel(val)
            val_lbl.setWordWrap(True)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid_layout.addWidget(lbl, row, 0, Qt.AlignmentFlag.AlignTop)
            grid_layout.addWidget(val_lbl, row, 1, Qt.AlignmentFlag.AlignTop)

        content_widget = QWidget()
        content_widget.setLayout(grid_layout)
        layout.addWidget(content_widget)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(90)
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)


class AboutDialog(QDialog):
    """Janela sobre o software"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre o Leitor de PDF")
        self.resize(420, 320)
        self.setModal(True)

        layout = QVBoxLayout(self)

        title = QLabel("📄 Leitor de PDF Python")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e3a8a; margin-top: 10px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "Um visualizador moderno de documentos PDF inspirado no Adobe Acrobat Reader.\n"
            "Desenvolvido com PyQt6 e PyMuPDF (fitz) de alto desempenho."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #4b5563; text-align: center; margin: 10px 0;")
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)

        shortcuts = QLabel(
            "<b>Atalhos Principais:</b><br>"
            "• <b>Ctrl + O</b>: Abrir documento<br>"
            "• <b>Ctrl + F</b>: Localizar texto<br>"
            "• <b>Ctrl + + / - / 0</b>: Zoom (Mais / Menos / 100%)<br>"
            "• <b>Ctrl + 1 / 2</b>: Ajustar Largura / Página Inteira<br>"
            "• <b>Ctrl + R</b>: Girar 90° horário<br>"
            "• <b>F4</b>: Alternar painel lateral<br>"
            "• <b>F11</b>: Alternar tela cheia"
        )
        shortcuts.setStyleSheet("background-color: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;")
        layout.addWidget(shortcuts)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_ok = QPushButton("Fechar")
        btn_ok.setFixedWidth(80)
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)


class TextEditDialog(QDialog):
    """Diálogo completo para Adicionar ou Editar texto no PDF (CRUD)"""
    COLOR_MAP = {
        "Preto": (0.0, 0.0, 0.0),
        "Azul Escuro": (0.1, 0.2, 0.7),
        "Vermelho": (0.8, 0.1, 0.1),
        "Verde": (0.1, 0.5, 0.1),
        "Cinza Escuro": (0.3, 0.3, 0.3),
        "Branco": (1.0, 1.0, 1.0),
    }

    FILL_MAP = {
        "Transparente": None,
        "Fundo Branco": (1.0, 1.0, 1.0),
        "Fundo Amarelo Claro": (1.0, 1.0, 0.8),
        "Fundo Azul Claro": (0.9, 0.95, 1.0),
    }

    def __init__(self, initial_text="", initial_size=12, initial_color="Preto", initial_fill="Transparente", is_edit=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Texto" if is_edit else "Adicionar Novo Texto ao PDF")
        self.resize(420, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)

        lbl_instruct = QLabel("Digite o texto a ser inserido/modificado:")
        lbl_instruct.setStyleSheet("font-weight: bold; color: #1e293b;")
        layout.addWidget(lbl_instruct)

        from PyQt6.QtWidgets import QTextEdit, QSpinBox, QComboBox, QFormLayout
        self.txt_content = QTextEdit()
        self.txt_content.setPlainText(initial_text)
        self.txt_content.setPlaceholderText("Escreva aqui o texto...")
        layout.addWidget(self.txt_content)

        form = QFormLayout()

        # Tamanho da fonte
        self.spin_size = QSpinBox()
        self.spin_size.setRange(6, 72)
        self.spin_size.setValue(int(initial_size))
        form.addRow("Tamanho da Fonte (pt):", self.spin_size)

        # Cor do texto
        self.combo_color = QComboBox()
        self.combo_color.addItems(list(self.COLOR_MAP.keys()))
        if initial_color in self.COLOR_MAP:
            self.combo_color.setCurrentText(initial_color)
        form.addRow("Cor do Texto:", self.combo_color)

        # Fundo do texto
        self.combo_fill = QComboBox()
        self.combo_fill.addItems(list(self.FILL_MAP.keys()))
        if initial_fill in self.FILL_MAP:
            self.combo_fill.setCurrentText(initial_fill)
        form.addRow("Preenchimento de Fundo:", self.combo_fill)

        layout.addLayout(form)

        # Botões
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_ok = QPushButton("Aplicar Texto" if is_edit else "Inserir Texto")
        self.btn_ok.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px;")
        self.btn_ok.clicked.connect(self._on_accept)
        btn_box.addWidget(self.btn_ok)

        layout.addLayout(btn_box)

    def _on_accept(self):
        if not self.txt_content.toPlainText().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Aviso", "O texto não pode ficar vazio.")
            return
        self.accept()

    def get_data(self):
        text = self.txt_content.toPlainText()
        size = self.spin_size.value()
        color = self.COLOR_MAP.get(self.combo_color.currentText(), (0.0, 0.0, 0.0))
        fill = self.FILL_MAP.get(self.combo_fill.currentText(), None)
        return text, size, color, fill


def parse_page_range(range_str, total_pages):
    """
    Interpreta uma string de intervalo de páginas no formato '1-3, 5, 8'
    Retorna uma lista ordenada de índices 0-indexed (ex: [0, 1, 2, 4, 7]).
    Lança ValueError com mensagem explicativa se houver erro.
    """
    if not range_str or not range_str.strip():
        raise ValueError("O intervalo de páginas não pode estar vazio.")

    pages = []
    tokens = [t.strip() for t in range_str.split(",") if t.strip()]
    if not tokens:
        raise ValueError("Nenhuma página válida especificada.")

    for token in tokens:
        if "-" in token:
            parts = token.split("-")
            if len(parts) != 2:
                raise ValueError(f"Intervalo com formato inválido: '{token}'. Use ex: '1-5'.")
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except ValueError:
                raise ValueError(f"Valores não numéricos no intervalo: '{token}'.")

            if start < 1 or end < 1:
                raise ValueError("Os números de página devem ser maiores que zero.")
            if start > total_pages or end > total_pages:
                raise ValueError(f"Página fora dos limites do documento (1 a {total_pages}): '{token}'.")

            step = 1 if start <= end else -1
            for p in range(start, end + step, step):
                idx = p - 1
                if idx not in pages:
                    pages.append(idx)
        else:
            try:
                p = int(token.strip())
            except ValueError:
                raise ValueError(f"Número de página inválido: '{token}'.")

            if p < 1 or p > total_pages:
                raise ValueError(f"Página fora dos limites do documento (1 a {total_pages}): '{p}'.")

            idx = p - 1
            if idx not in pages:
                pages.append(idx)

    if not pages:
        raise ValueError("Nenhuma página selecionada.")
    return sorted(pages)


class SplitPagesDialog(QDialog):
    """Diálogo completo para Separar ou Exportar Páginas do PDF"""
    def __init__(self, total_pages, current_page_idx, parent=None):
        super().__init__(parent)
        self.total_pages = total_pages
        self.current_page_idx = current_page_idx
        self.setWindowTitle("Separar / Exportar Páginas")
        self.resize(520, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("✂️ Separar ou Exportar Páginas")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a8a; margin-bottom: 2px;")
        layout.addWidget(header)

        # Grupo 1: Seleção de Páginas
        grp_pages = QGroupBox("1. Selecione as Páginas")
        grp_pages.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_pages = QVBoxLayout(grp_pages)
        vbox_pages.setSpacing(8)

        self.rb_current = QRadioButton(f"Página atual (Página {current_page_idx + 1} de {total_pages})")
        self.rb_current.setChecked(True)
        vbox_pages.addWidget(self.rb_current)

        self.rb_range = QRadioButton("Intervalo específico de páginas:")
        vbox_pages.addWidget(self.rb_range)

        h_range = QHBoxLayout()
        h_range.setContentsMargins(20, 0, 0, 0)
        self.txt_range = QLineEdit()
        self.txt_range.setPlaceholderText(f"Ex: 1-3, 5 (1 a {total_pages})")
        self.txt_range.setEnabled(False)
        self.lbl_range_hint = QLabel(f"Total: {total_pages} páginas")
        self.lbl_range_hint.setStyleSheet("color: #64748b; font-size: 11px;")
        h_range.addWidget(self.txt_range)
        h_range.addWidget(self.lbl_range_hint)
        vbox_pages.addLayout(h_range)

        self.rb_all = QRadioButton(f"Todas as páginas do documento ({total_pages} páginas)")
        vbox_pages.addWidget(self.rb_all)

        self.page_group = QButtonGroup(self)
        self.page_group.addButton(self.rb_current)
        self.page_group.addButton(self.rb_range)
        self.page_group.addButton(self.rb_all)
        self.page_group.buttonToggled.connect(self._on_page_mode_changed)

        layout.addWidget(grp_pages)

        # Grupo 2: Formato e Modo de Saída
        grp_mode = QGroupBox("2. Formato e Modo de Exportação")
        grp_mode.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_mode = QVBoxLayout(grp_mode)
        vbox_mode.setSpacing(8)

        self.rb_single_pdf = QRadioButton("📄 Salvar em um único arquivo PDF consolidado")
        self.rb_single_pdf.setChecked(True)
        vbox_mode.addWidget(self.rb_single_pdf)

        self.rb_split_multiple = QRadioButton("📑 Separar cada página em um arquivo PDF individual (1 por página)")
        vbox_mode.addWidget(self.rb_split_multiple)

        self.rb_images = QRadioButton("🖼️ Exportar como Imagens de Alta Resolução")
        vbox_mode.addWidget(self.rb_images)

        # Configurações de imagem
        h_img_opts = QHBoxLayout()
        h_img_opts.setContentsMargins(20, 0, 0, 0)
        lbl_img_fmt = QLabel("Formato:")
        self.combo_img_fmt = QComboBox()
        self.combo_img_fmt.addItems(["PNG (.png)", "JPEG (.jpg)"])
        self.combo_img_fmt.setEnabled(False)

        lbl_img_dpi = QLabel("Resolução:")
        self.combo_img_dpi = QComboBox()
        self.combo_img_dpi.addItems(["150 DPI (Equilibrado)", "300 DPI (Alta Definição)"])
        self.combo_img_dpi.setEnabled(False)

        h_img_opts.addWidget(lbl_img_fmt)
        h_img_opts.addWidget(self.combo_img_fmt)
        h_img_opts.addSpacing(10)
        h_img_opts.addWidget(lbl_img_dpi)
        h_img_opts.addWidget(self.combo_img_dpi)
        h_img_opts.addStretch()
        vbox_mode.addLayout(h_img_opts)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_single_pdf)
        self.mode_group.addButton(self.rb_split_multiple)
        self.mode_group.addButton(self.rb_images)
        self.mode_group.buttonToggled.connect(self._on_output_mode_changed)

        layout.addWidget(grp_mode)

        # Botões
        layout.addStretch()
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_export = QPushButton("Exportar...")
        self.btn_export.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        self.btn_export.clicked.connect(self._on_accept)
        btn_box.addWidget(self.btn_export)

        layout.addLayout(btn_box)

    def _on_page_mode_changed(self):
        self.txt_range.setEnabled(self.rb_range.isChecked())
        if self.rb_range.isChecked():
            self.txt_range.setFocus()

    def _on_output_mode_changed(self):
        is_img = self.rb_images.isChecked()
        self.combo_img_fmt.setEnabled(is_img)
        self.combo_img_dpi.setEnabled(is_img)

    def _on_accept(self):
        try:
            self.get_pages()
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Intervalo Inválido", str(e))

    def get_pages(self):
        """Retorna a lista de índices das páginas selecionadas (0-based)"""
        if self.rb_current.isChecked():
            return [self.current_page_idx]
        elif self.rb_all.isChecked():
            return list(range(self.total_pages))
        else:
            return parse_page_range(self.txt_range.text(), self.total_pages)

    def get_output_mode(self):
        """Retorna 'single_pdf', 'split_multiple', ou 'images'"""
        if self.rb_single_pdf.isChecked():
            return "single_pdf"
        elif self.rb_split_multiple.isChecked():
            return "split_multiple"
        else:
            return "images"

    def get_image_options(self):
        fmt = "png" if "PNG" in self.combo_img_fmt.currentText() else "jpg"
        dpi = 300 if "300" in self.combo_img_dpi.currentText() else 150
        return fmt, dpi


class ImportPdfDialog(QDialog):
    """Diálogo para Importar Páginas de outro Arquivo PDF"""
    def __init__(self, current_page_idx, total_pages, default_file="", parent=None):
        super().__init__(parent)
        self.current_page_idx = current_page_idx
        self.total_pages = total_pages
        self.selected_file = default_file
        self.src_total_pages = 0

        self.setWindowTitle("Importar Páginas de Arquivo PDF")
        self.resize(520, 440)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("➕ Importar Páginas de Arquivo PDF")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a8a; margin-bottom: 2px;")
        layout.addWidget(header)

        # 1. Arquivo de Origem
        grp_file = QGroupBox("1. Selecione o Arquivo PDF")
        grp_file.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_file = QVBoxLayout(grp_file)

        h_file = QHBoxLayout()
        self.txt_file = QLineEdit()
        self.txt_file.setReadOnly(True)
        self.txt_file.setPlaceholderText("Clique no botão ao lado para escolher o PDF...")
        h_file.addWidget(self.txt_file)

        btn_browse = QPushButton("Procurar...")
        btn_browse.clicked.connect(self._browse_file)
        h_file.addWidget(btn_browse)
        vbox_file.addLayout(h_file)

        self.lbl_src_info = QLabel("Nenhum arquivo selecionado.")
        self.lbl_src_info.setStyleSheet("color: #64748b; font-size: 12px;")
        vbox_file.addWidget(self.lbl_src_info)

        layout.addWidget(grp_file)

        # 2. Páginas a Importar
        self.grp_src_pages = QGroupBox("2. Páginas a Importar")
        self.grp_src_pages.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_src_pages = QVBoxLayout(self.grp_src_pages)

        self.rb_all_src = QRadioButton("Todas as páginas do arquivo de origem")
        self.rb_all_src.setChecked(True)
        vbox_src_pages.addWidget(self.rb_all_src)

        self.rb_range_src = QRadioButton("Intervalo específico de páginas:")
        vbox_src_pages.addWidget(self.rb_range_src)

        h_src_range = QHBoxLayout()
        h_src_range.setContentsMargins(20, 0, 0, 0)
        self.txt_src_range = QLineEdit()
        self.txt_src_range.setPlaceholderText("Ex: 1-3, 5")
        self.txt_src_range.setEnabled(False)
        h_src_range.addWidget(self.txt_src_range)
        vbox_src_pages.addLayout(h_src_range)

        self.src_page_group = QButtonGroup(self)
        self.src_page_group.addButton(self.rb_all_src)
        self.src_page_group.addButton(self.rb_range_src)
        self.src_page_group.buttonToggled.connect(lambda: self.txt_src_range.setEnabled(self.rb_range_src.isChecked()))

        layout.addWidget(self.grp_src_pages)

        # 3. Posição de Inserção
        grp_pos = QGroupBox("3. Posição de Inserção no Documento Atual")
        grp_pos.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_pos = QVBoxLayout(grp_pos)

        if total_pages > 0:
            self.rb_after = QRadioButton(f"Depois da página atual (Página {current_page_idx + 1})")
            self.rb_after.setChecked(True)
            vbox_pos.addWidget(self.rb_after)

            self.rb_before = QRadioButton(f"Antes da página atual (Página {current_page_idx + 1})")
            vbox_pos.addWidget(self.rb_before)

            self.rb_start = QRadioButton("No início do documento (Página 1)")
            vbox_pos.addWidget(self.rb_start)

            self.rb_end = QRadioButton(f"No final do documento (após a Página {total_pages})")
            vbox_pos.addWidget(self.rb_end)
        else:
            self.rb_start = QRadioButton("Novo documento (início)")
            self.rb_start.setChecked(True)
            vbox_pos.addWidget(self.rb_start)
            self.rb_after = None
            self.rb_before = None
            self.rb_end = None

        layout.addWidget(grp_pos)

        # Botões
        layout.addStretch()
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_import = QPushButton("Importar Páginas")
        self.btn_import.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        self.btn_import.clicked.connect(self._on_accept)
        btn_box.addWidget(self.btn_import)

        layout.addLayout(btn_box)

        if default_file:
            self._set_file(default_file)

    def _browse_file(self):
        fpath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo PDF para Importar", "", "Arquivos PDF (*.pdf)"
        )
        if fpath:
            self._set_file(fpath)

    def _set_file(self, fpath):
        try:
            doc = pymupdf.open(fpath)
            self.src_total_pages = len(doc)
            doc.close()
            self.selected_file = fpath
            self.txt_file.setText(fpath)
            self.lbl_src_info.setText(f"✓ Arquivo válido com {self.src_total_pages} página(s).")
            self.lbl_src_info.setStyleSheet("color: #16a34a; font-weight: 500;")
            self.rb_all_src.setText(f"Todas as páginas do arquivo de origem ({self.src_total_pages} páginas)")
            self.txt_src_range.setPlaceholderText(f"Ex: 1-{min(3, self.src_total_pages)} (1 a {self.src_total_pages})")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Abrir Arquivo", f"Não foi possível ler o PDF selecionado:\n{e}")
            self.selected_file = ""
            self.src_total_pages = 0
            self.txt_file.clear()
            self.lbl_src_info.setText("Nenhum arquivo válido selecionado.")
            self.lbl_src_info.setStyleSheet("color: #dc2626;")

    def _on_accept(self):
        if not self.selected_file or not os.path.exists(self.selected_file):
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um arquivo PDF de origem válido.")
            return

        try:
            self.get_pages_to_import()
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Intervalo Inválido", str(e))

    def get_pages_to_import(self):
        """Retorna lista de páginas (0-based) a importar, ou None para todas"""
        if self.rb_all_src.isChecked():
            return None
        return parse_page_range(self.txt_src_range.text(), self.src_total_pages)

    def get_target_insert_index(self):
        """Retorna a posição 0-based no documento onde inserir"""
        if self.total_pages == 0:
            return 0
        if self.rb_before and self.rb_before.isChecked():
            return self.current_page_idx
        elif self.rb_start and self.rb_start.isChecked():
            return 0
        elif self.rb_end and self.rb_end.isChecked():
            return self.total_pages
        else:
            return self.current_page_idx + 1

    def get_data(self):
        return self.selected_file, self.get_pages_to_import(), self.get_target_insert_index()


class ImportImageDialog(QDialog):
    """Diálogo para Importar uma ou mais Imagens como Novas Páginas do PDF"""
    def __init__(self, current_page_idx, total_pages, default_images=None, parent=None):
        super().__init__(parent)
        self.current_page_idx = current_page_idx
        self.total_pages = total_pages
        self.image_paths = list(default_images) if default_images else []

        self.setWindowTitle("Importar Imagem como Nova Página")
        self.resize(540, 480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("🖼️ Importar Imagem como Nova Página")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a8a; margin-bottom: 2px;")
        layout.addWidget(header)

        # 1. Imagens Selecionadas
        grp_images = QGroupBox("1. Selecione as Imagens")
        grp_images.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_imgs = QVBoxLayout(grp_images)

        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(120)
        vbox_imgs.addWidget(self.list_widget)

        h_btn = QHBoxLayout()
        btn_add = QPushButton("➕ Adicionar Imagens...")
        btn_add.clicked.connect(self._add_images)
        h_btn.addWidget(btn_add)

        btn_rem = QPushButton("🗑️ Remover Selecionada")
        btn_rem.clicked.connect(self._remove_selected)
        h_btn.addWidget(btn_rem)

        btn_clear = QPushButton("Limpar Lista")
        btn_clear.clicked.connect(self._clear_list)
        h_btn.addWidget(btn_clear)
        vbox_imgs.addLayout(h_btn)

        self.lbl_img_count = QLabel("0 imagem(ns) selecionada(s).")
        self.lbl_img_count.setStyleSheet("color: #64748b; font-size: 12px;")
        vbox_imgs.addWidget(self.lbl_img_count)

        layout.addWidget(grp_images)

        # 2. Posição de Inserção
        grp_pos = QGroupBox("2. Posição de Inserção no Documento")
        grp_pos.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_pos = QVBoxLayout(grp_pos)

        if total_pages > 0:
            self.rb_after = QRadioButton(f"Depois da página atual (Página {current_page_idx + 1})")
            self.rb_after.setChecked(True)
            vbox_pos.addWidget(self.rb_after)

            self.rb_before = QRadioButton(f"Antes da página atual (Página {current_page_idx + 1})")
            vbox_pos.addWidget(self.rb_before)

            self.rb_start = QRadioButton("No início do documento (Página 1)")
            vbox_pos.addWidget(self.rb_start)

            self.rb_end = QRadioButton(f"No final do documento (após a Página {total_pages})")
            vbox_pos.addWidget(self.rb_end)
        else:
            self.rb_start = QRadioButton("Criar novo documento com a(s) imagem(ns)")
            self.rb_start.setChecked(True)
            vbox_pos.addWidget(self.rb_start)
            self.rb_after = None
            self.rb_before = None
            self.rb_end = None

        layout.addWidget(grp_pos)

        # 3. Formato da Página
        grp_fmt = QGroupBox("3. Dimensões da Página")
        grp_fmt.setStyleSheet("QGroupBox { font-weight: bold; }")
        vbox_fmt = QVBoxLayout(grp_fmt)

        self.rb_a4 = QRadioButton("Ajustar à folha A4 padrão (centralizado com margens, retrato/paisagem automático)")
        self.rb_a4.setChecked(True)
        vbox_fmt.addWidget(self.rb_a4)

        self.rb_orig = QRadioButton("Manter dimensões e proporção original da imagem (1:1)")
        vbox_fmt.addWidget(self.rb_orig)

        layout.addWidget(grp_fmt)

        # Botões
        layout.addStretch()
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_import = QPushButton("Inserir Página(s)")
        self.btn_import.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        self.btn_import.clicked.connect(self._on_accept)
        btn_box.addWidget(self.btn_import)

        layout.addLayout(btn_box)

        self._refresh_list()

    def _add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar Imagens", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp);;Todos os Arquivos (*)"
        )
        if files:
            for f in files:
                if f not in self.image_paths:
                    self.image_paths.append(f)
            self._refresh_list()

    def _remove_selected(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            path = item.text()
            if path in self.image_paths:
                self.image_paths.remove(path)
        self._refresh_list()

    def _clear_list(self):
        self.image_paths.clear()
        self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        for p in self.image_paths:
            self.list_widget.addItem(p)
        count = len(self.image_paths)
        self.lbl_img_count.setText(f"{count} imagem(ns) selecionada(s).")
        if count > 0:
            self.lbl_img_count.setStyleSheet("color: #16a34a; font-weight: 500;")
        else:
            self.lbl_img_count.setStyleSheet("color: #64748b;")

    def _on_accept(self):
        if not self.image_paths:
            QMessageBox.warning(self, "Aviso", "Por favor, adicione pelo menos uma imagem.")
            return
        self.accept()

    def get_target_insert_index(self):
        if self.total_pages == 0:
            return 0
        if self.rb_before and self.rb_before.isChecked():
            return self.current_page_idx
        elif self.rb_start and self.rb_start.isChecked():
            return 0
        elif self.rb_end and self.rb_end.isChecked():
            return self.total_pages
        else:
            return self.current_page_idx + 1

    def get_data(self):
        fit_to_a4 = self.rb_a4.isChecked()
        return self.image_paths, self.get_target_insert_index(), fit_to_a4


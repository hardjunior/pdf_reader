"""
Caixas de diálogo informativas e propriedades do documento PDF
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTabWidget, QWidget, QFrame
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

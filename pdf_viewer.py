"""
Componente central de visualização e edição do PDF (com suporte a CRUD de Texto, Anotações, Assinaturas e Borracha)
"""

import sys
sys.modules['pymupdf.layout'] = None

import os
import pymupdf
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QColor, QPen, QBrush, 
    QCursor
)
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QMenu, QApplication, QMessageBox, QFileDialog
)

from dialogs import TextEditDialog


class PageCanvas(QWidget):
    """
    Widget de desenho da página do PDF com suporte a:
    - Visualização nítida
    - Seleção de texto
    - Adicionar texto (CRUD: Create)
    - Editar texto (CRUD: Update)
    - Apagar texto/anotações e Borracha (CRUD: Delete)
    - Marca-texto (Highlighter)
    - Inserção de assinaturas e carimbos
    """
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.pixmap = None
        self.page_size = QSize(0, 0)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Seleção e interação
        self.selecting = False
        self.selection_start = QPoint()
        self.selection_end = QPoint()
        self.selected_text = ""
        self.selected_pdf_rect = None

        # Panning com botão do meio
        self.panning = False
        self.pan_start = QPoint()

    def update_pixmap(self, pixmap, page_size):
        self.pixmap = pixmap
        self.page_size = page_size
        self.resize(page_size.width() + 40, page_size.height() + 40)
        self.update()

    def screen_to_pdf_rect(self, screen_rect):
        """Converte coordenadas da tela (pixels) para coordenadas do PDF (pontos)"""
        if not self.viewer.current_page:
            return pymupdf.Rect(0, 0, 0, 0)
        page_x = max(20, (self.width() - self.page_size.width()) // 2)
        page_y = 20
        scale_x = self.viewer.pdf_page_rect.width / max(1.0, self.page_size.width())
        scale_y = self.viewer.pdf_page_rect.height / max(1.0, self.page_size.height())

        pdf_x0 = (screen_rect.left() - page_x) * scale_x
        pdf_y0 = (screen_rect.top() - page_y) * scale_y
        pdf_x1 = (screen_rect.right() - page_x) * scale_x
        pdf_y1 = (screen_rect.bottom() - page_y) * scale_y
        return pymupdf.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1)

    def screen_to_pdf_point(self, point):
        """Converte um ponto da tela para coordenadas do PDF"""
        page_x = max(20, (self.width() - self.page_size.width()) // 2)
        page_y = 20
        scale_x = self.viewer.pdf_page_rect.width / max(1.0, self.page_size.width())
        scale_y = self.viewer.pdf_page_rect.height / max(1.0, self.page_size.height())
        return pymupdf.Point((point.x() - page_x) * scale_x, (point.y() - page_y) * scale_y)

    def get_annot_at_point(self, point):
        """Identifica se há uma anotação existente no ponto clicado"""
        if not self.viewer.current_page:
            return None
        pdf_pt = self.screen_to_pdf_point(point)
        for annot in self.viewer.current_page.annots():
            if annot.rect.contains(pdf_pt):
                return annot
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Fundo do canvas ao redor da folha
        canvas_bg = QColor(15, 23, 42) if self.viewer.is_dark_theme else QColor(226, 232, 240)
        painter.fillRect(self.rect(), canvas_bg)

        if not self.pixmap:
            return

        # Posição centralizada da folha
        page_x = max(20, (self.width() - self.page_size.width()) // 2)
        page_y = 20
        page_rect = QRect(page_x, page_y, self.page_size.width(), self.page_size.height())

        # Sombra elegante e pronunciada da folha
        shadow_color = QColor(0, 0, 0, 80 if self.viewer.is_dark_theme else 35)
        for i in range(1, 6):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(shadow_color))
            painter.drawRoundedRect(
                page_rect.adjusted(-i, -i, i + 2, i + 3), 4, 4
            )

        # Base branca sólida para a folha (garante contraste máximo)
        painter.fillRect(page_rect, QColor(255, 255, 255))

        # Desenhar a página renderizada
        painter.drawPixmap(page_rect, self.pixmap)

        # Filtro Sépia se ativado
        if self.viewer.page_filter == "sepia":
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
            painter.fillRect(page_rect, QColor(246, 238, 219, 130))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # Borda nítida de contorno da folha
        border_color = QColor(75, 85, 99) if self.viewer.is_dark_theme else QColor(148, 163, 184)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(page_rect)

        # Desenhar correspondências de busca ativas
        scale_x = self.page_size.width() / max(1.0, self.viewer.pdf_page_rect.width)
        scale_y = self.page_size.height() / max(1.0, self.viewer.pdf_page_rect.height)

        if self.viewer.search_matches:
            for idx, r in enumerate(self.viewer.search_matches):
                rx = page_x + (r.x0 * scale_x)
                ry = page_y + (r.y0 * scale_y)
                rw = (r.x1 - r.x0) * scale_x
                rh = (r.y1 - r.y0) * scale_y
                match_rect = QRectF(rx, ry, rw, rh)

                is_current = (idx == self.viewer.current_page_match_idx)
                if is_current:
                    painter.setBrush(QBrush(QColor(255, 140, 0, 180)))
                    painter.setPen(QPen(QColor(230, 81, 0), 1.5))
                else:
                    painter.setBrush(QBrush(QColor(255, 235, 59, 130)))
                    painter.setPen(QPen(QColor(251, 192, 45, 180), 1))

                painter.drawRoundedRect(match_rect, 2, 2)

        # Desenhar retângulo de seleção ou borracha
        if self.selecting and not self.selection_start.isNull() and not self.selection_end.isNull():
            sel_rect = QRect(self.selection_start, self.selection_end).normalized()
            if self.viewer.active_tool == "eraser":
                # Borracha: visual vermelho com tracejado
                painter.setBrush(QBrush(QColor(239, 68, 68, 60)))
                painter.setPen(QPen(QColor(220, 38, 38), 1.5, Qt.PenStyle.DashLine))
                painter.drawRect(sel_rect)
            elif self.viewer.active_tool == "highlight":
                # Marca-texto: visual amarelo
                painter.setBrush(QBrush(QColor(253, 224, 71, 110)))
                painter.setPen(QPen(QColor(234, 179, 8), 1.5, Qt.PenStyle.SolidLine))
                painter.drawRect(sel_rect)
            else:
                # Seleção normal de texto: visual azul
                painter.setBrush(QBrush(QColor(66, 133, 244, 75)))
                painter.setPen(QPen(QColor(26, 115, 232), 1, Qt.PenStyle.DashLine))
                painter.drawRect(sel_rect)

    def mousePressEvent(self, event):
        if not self.viewer.doc:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            page_x = max(20, (self.width() - self.page_size.width()) // 2)
            page_rect = QRect(page_x, 20, self.page_size.width(), self.page_size.height())

            if not page_rect.contains(event.pos()):
                return

            # Ferramenta: Adicionar Novo Texto (CRUD: Create)
            if self.viewer.active_tool == "add_text":
                pdf_pt = self.screen_to_pdf_point(event.pos())
                dlg = TextEditDialog(parent=self)
                if dlg.exec() == TextEditDialog.DialogCode.Accepted:
                    text, size, color, fill = dlg.get_data()
                    self.viewer.add_text_at(pdf_pt, text, size, color, fill)
                return

            # Ferramenta: Inserir Assinatura / Imagem
            if self.viewer.active_tool == "insert_image":
                pdf_pt = self.screen_to_pdf_point(event.pos())
                img_path, _ = QFileDialog.getOpenFileName(
                    self, "Selecionar Imagem da Assinatura / Carimbo", "", 
                    "Imagens (*.png *.jpg *.jpeg *.bmp)"
                )
                if img_path:
                    self.viewer.insert_image_at(pdf_pt, img_path)
                return

            # Demais ferramentas iniciam arrasto/seleção
            self.selecting = True
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.selected_text = ""
            self.selected_pdf_rect = None
            self.update()

        elif event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_start = event.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.selection_end = event.pos()
            self.update()
        elif self.panning:
            delta = event.pos() - self.pan_start
            h_bar = self.viewer.horizontalScrollBar()
            v_bar = self.viewer.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
        else:
            page_x = max(20, (self.width() - self.page_size.width()) // 2)
            page_rect = QRect(page_x, 20, self.page_size.width(), self.page_size.height())
            if page_rect.contains(event.pos()):
                if self.viewer.active_tool == "eraser":
                    self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
                elif self.viewer.active_tool == "add_text":
                    self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
                elif self.viewer.active_tool == "insert_image":
                    self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                elif self.viewer.active_tool == "highlight":
                    self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
                else:
                    self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            sel_rect = QRect(self.selection_start, self.selection_end).normalized()
            
            # Se foi apenas um clique acidental, ignora
            if sel_rect.width() > 4 and sel_rect.height() > 4:
                pdf_rect = self.screen_to_pdf_rect(sel_rect)
                self.selected_pdf_rect = pdf_rect

                if self.viewer.active_tool == "eraser":
                    # Borracha / Apagar Conteúdo (CRUD: Delete)
                    reply = QMessageBox.question(
                        self, "Confirmar Apagar", 
                        "Deseja realmente apagar/ocultar o conteúdo desta área?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.viewer.redact_rect(pdf_rect)

                elif self.viewer.active_tool == "highlight":
                    # Marca-texto na área selecionada
                    self.viewer.add_highlight_rect(pdf_rect)

                else:
                    # Seleção de texto comum
                    self.extract_selected_text()

            self.update()

        elif event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def extract_selected_text(self):
        """Extrai o texto contido no retângulo de seleção do mouse"""
        if not self.viewer.current_page or not self.selected_pdf_rect:
            return
        try:
            self.selected_text = self.viewer.current_page.get_textbox(self.selected_pdf_rect).strip()
            if self.selected_text:
                self.viewer.selectionChanged.emit(self.selected_text)
        except Exception:
            self.selected_text = ""

    def contextMenuEvent(self, event):
        if not self.viewer.doc:
            return

        menu = QMenu(self)
        clicked_annot = self.get_annot_at_point(event.pos())
        pdf_pt = self.screen_to_pdf_point(event.pos())

        # 1. Se clicou em cima de uma anotação existente (CRUD: Update e Delete)
        if clicked_annot:
            annot_type = clicked_annot.type[1]  # Ex: 'FreeText', 'Highlight', etc.
            if annot_type == "FreeText":
                edit_act = menu.addAction("✏️ Editar este Texto...")
                edit_act.triggered.connect(lambda: self._on_edit_annot(clicked_annot))

                del_act = menu.addAction("🗑️ Apagar este Texto")
                del_act.triggered.connect(lambda: self._on_delete_annot(clicked_annot))
                menu.addSeparator()
            else:
                del_act = menu.addAction("🗑️ Remover Anotação / Marcação")
                del_act.triggered.connect(lambda: self._on_delete_annot(clicked_annot))
                menu.addSeparator()

        # 2. Se há texto selecionado pelo usuário
        if self.selected_text:
            copy_action = menu.addAction("📋 Copiar Texto Selecionado")
            copy_action.triggered.connect(self.copy_to_clipboard)

            highlight_action = menu.addAction("🖍️ Destacar com Marca-Texto")
            highlight_action.triggered.connect(self._on_highlight_selection)

            replace_action = menu.addAction("✏️ Substituir Texto Selecionado...")
            replace_action.triggered.connect(self._on_replace_selection)

            erase_action = menu.addAction("🧹 Apagar Texto Selecionado (Borracha)")
            erase_action.triggered.connect(self._on_erase_selection)

            menu.addSeparator()

        # 3. Ações no local clicado
        add_text_act = menu.addAction("✍️ Adicionar Texto Aqui...")
        add_text_act.triggered.connect(lambda: self._on_add_text_here(pdf_pt))

        insert_img_act = menu.addAction("✒️ Inserir Assinatura / Imagem Aqui...")
        insert_img_act.triggered.connect(lambda: self._on_insert_image_here(pdf_pt))

        menu.addSeparator()
        zoom_in_action = menu.addAction("➕ Mais Zoom")
        zoom_in_action.triggered.connect(self.viewer.zoom_in)
        zoom_out_action = menu.addAction("➖ Menos Zoom")
        zoom_out_action.triggered.connect(self.viewer.zoom_out)

        menu.exec(event.globalPos())

    def _on_edit_annot(self, annot):
        """CRUD: Update de anotação FreeText existente"""
        current_text = annot.info.get("content", "")
        # Obtém cores se disponíveis
        dlg = TextEditDialog(initial_text=current_text, is_edit=True, parent=self)
        if dlg.exec() == TextEditDialog.DialogCode.Accepted:
            new_text, size, color, fill = dlg.get_data()
            self.viewer.edit_annot_text(annot, new_text, size, color, fill)

    def _on_delete_annot(self, annot):
        """CRUD: Delete de anotação"""
        self.viewer.delete_annot(annot)

    def _on_highlight_selection(self):
        if self.selected_pdf_rect:
            self.viewer.add_highlight_rect(self.selected_pdf_rect)

    def _on_replace_selection(self):
        """CRUD: Substitui texto original selecionado (Apaga antigo e escreve novo)"""
        if not self.selected_pdf_rect:
            return
        dlg = TextEditDialog(initial_text=self.selected_text, is_edit=True, parent=self)
        if dlg.exec() == TextEditDialog.DialogCode.Accepted:
            new_text, size, color, fill = dlg.get_data()
            self.viewer.replace_text(self.selected_pdf_rect, new_text, size, color, fill)

    def _on_erase_selection(self):
        """CRUD: Apaga o texto original selecionado"""
        if self.selected_pdf_rect:
            self.viewer.redact_rect(self.selected_pdf_rect)

    def _on_add_text_here(self, pdf_pt):
        dlg = TextEditDialog(parent=self)
        if dlg.exec() == TextEditDialog.DialogCode.Accepted:
            text, size, color, fill = dlg.get_data()
            self.viewer.add_text_at(pdf_pt, text, size, color, fill)

    def _on_insert_image_here(self, pdf_pt):
        img_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem da Assinatura / Carimbo", "", 
            "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if img_path:
            self.viewer.insert_image_at(pdf_pt, img_path)

    def copy_to_clipboard(self):
        if self.selected_text:
            QApplication.clipboard().setText(self.selected_text)
            self.viewer.statusMessage.emit("Texto copiado para a área de transferência!")

    def copy_all_page_text(self):
        if self.viewer.current_page:
            text = self.viewer.current_page.get_text()
            QApplication.clipboard().setText(text)
            self.viewer.statusMessage.emit("Texto de toda a página copiado!")


class PDFViewer(QScrollArea):
    """
    Área de rolagem principal que gerencia o zoom, rotação, renderização e ferramentas de edição
    """
    pageChanged = pyqtSignal(int, int)
    zoomChanged = pyqtSignal(float)
    statusMessage = pyqtSignal(str)
    selectionChanged = pyqtSignal(str)
    documentLoaded = pyqtSignal(int)
    documentModified = pyqtSignal()  # Notifica que o documento foi alterado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc = None
        self.current_page_idx = 0
        self.total_pages = 0
        self.zoom = 1.0
        self.fit_mode = None
        self.rotation = 0
        self.is_dark_theme = False
        self.page_filter = "normal"  # "normal", "sepia", "invert"
        self.active_tool = "select"  # "select", "add_text", "eraser", "highlight", "insert_image"

        self.current_page = None
        self.pdf_page_rect = pymupdf.Rect(0, 0, 100, 100)
        self.search_matches = []
        self.current_page_match_idx = -1

        self.canvas = PageCanvas(self)
        self.setWidget(self.canvas)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidgetResizable(False)
        self.setStyleSheet("border: none; background-color: #e5e7eb;")

    def set_tool(self, tool_name):
        self.active_tool = tool_name
        self.statusMessage.emit(f"Ferramenta ativa: {tool_name}")
        self.canvas.update()

    def load_document(self, doc):
        self.doc = doc
        self.total_pages = len(doc)
        self.current_page_idx = 0
        self.rotation = 0
        self.search_matches = []
        self.current_page_match_idx = -1

        self.documentLoaded.emit(self.total_pages)
        self.render_current_page()

    # --- Operações CRUD de Edição de PDF ---

    def add_text_at(self, pdf_point, text, fontsize=12, text_color=(0, 0, 0), fill_color=None):
        """CRUD: Create - Adiciona caixa de texto interativa no PDF"""
        if not self.current_page:
            return

        # Calcula estimativa do retângulo necessário para o texto
        lines = text.split("\n")
        max_line_len = max(len(l) for l in lines) if lines else 10
        width = max(120.0, max_line_len * fontsize * 0.6 + 20)
        height = max(35.0, len(lines) * fontsize * 1.4 + 15)

        rect = pymupdf.Rect(pdf_point.x, pdf_point.y, pdf_point.x + width, pdf_point.y + height)

        annot = self.current_page.add_freetext_annot(
            rect, text, fontsize=fontsize, text_color=text_color, fill_color=fill_color
        )
        annot.update()

        self.documentModified.emit()
        self.render_current_page()
        self.statusMessage.emit("Texto adicionado com sucesso!")

    def edit_annot_text(self, annot, new_text, fontsize=12, text_color=(0, 0, 0), fill_color=None):
        """CRUD: Update - Altera conteúdo e aparência de anotação de texto existente"""
        if not self.current_page:
            return

        annot.set_info(content=new_text)
        annot.update(fontsize=fontsize, text_color=text_color, fill_color=fill_color)

        self.documentModified.emit()
        self.render_current_page()
        self.statusMessage.emit("Texto atualizado com sucesso!")

    def delete_annot(self, annot):
        """CRUD: Delete - Exclui anotação selecionada"""
        if not self.current_page:
            return
        self.current_page.delete_annot(annot)
        self.documentModified.emit()
        self.render_current_page()
        self.statusMessage.emit("Anotação apagada!")

    def redact_rect(self, pdf_rect, fill=(1, 1, 1)):
        """CRUD: Delete - Apaga/Oculta qualquer conteúdo original do PDF (Borracha)"""
        if not self.current_page:
            return
        self.current_page.add_redact_annot(pdf_rect, fill=fill)
        self.current_page.apply_redactions()

        self.documentModified.emit()
        self.render_current_page()
        self.statusMessage.emit("Área apagada com sucesso!")

    def replace_text(self, pdf_rect, new_text, fontsize=12, text_color=(0, 0, 0), fill_color=None):
        """CRUD: Update - Apaga o texto original no local e insere o novo texto"""
        if not self.current_page:
            return
        # 1. Apaga o texto anterior com fundo branco
        self.current_page.add_redact_annot(pdf_rect, fill=(1, 1, 1))
        self.current_page.apply_redactions()

        # 2. Adiciona o novo texto no mesmo retângulo
        rect = pymupdf.Rect(pdf_rect.x0, pdf_rect.y0, pdf_rect.x1, pdf_rect.y1)
        if rect.height < fontsize * 1.5:
            rect.y1 = rect.y0 + (fontsize * 1.5)
        if rect.width < len(new_text) * fontsize * 0.6:
            rect.x1 = rect.x0 + (len(new_text) * fontsize * 0.6)

        annot = self.current_page.add_freetext_annot(
            rect, new_text, fontsize=fontsize, text_color=text_color, fill_color=fill_color
        )
        annot.update()

        self.documentModified.emit()
        self.render_current_page()
        self.statusMessage.emit("Texto substituído com sucesso!")

    def add_highlight_rect(self, pdf_rect, color=(1, 1, 0)):
        """Marca-texto (Highlighter)"""
        if not self.current_page:
            return
        annot = self.current_page.add_highlight_annot(pdf_rect)
        annot.set_colors(stroke=color)
        annot.update()

        self.documentModified.emit()
        self.render_current_page()
        self.statusMessage.emit("Texto destacado!")

    def insert_image_at(self, pdf_point, img_path, width=150):
        """Insere assinatura ou imagem no local indicado"""
        if not self.current_page or not os.path.exists(img_path):
            return

        try:
            # Obtém proporções da imagem
            pix = pymupdf.Pixmap(img_path)
            aspect = pix.height / max(1.0, pix.width)
            height = width * aspect
            pix = None

            rect = pymupdf.Rect(pdf_point.x, pdf_point.y, pdf_point.x + width, pdf_point.y + height)
            self.current_page.insert_image(rect, filename=img_path)

            self.documentModified.emit()
            self.render_current_page()
            self.statusMessage.emit("Assinatura/Imagem inserida com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Inserir Imagem", f"Não foi possível inserir a imagem:\n{e}")

    def delete_specific_page(self, page_idx):
        """Exclui a página especificada do documento"""
        if not self.doc or self.total_pages <= 1:
            QMessageBox.warning(self, "Aviso", "O documento precisa ter pelo menos uma página.")
            return False

        if 0 <= page_idx < self.total_pages:
            self.doc.delete_page(page_idx)
            self.total_pages = len(self.doc)
            if self.current_page_idx >= self.total_pages:
                self.current_page_idx = max(0, self.total_pages - 1)
            elif self.current_page_idx > page_idx:
                self.current_page_idx -= 1

            self.documentModified.emit()
            self.render_current_page()
            self.statusMessage.emit(f"Página {page_idx + 1} excluída. Total restante: {self.total_pages} página(s).")
            return True
        return False

    def delete_current_page(self):
        """Gerenciamento de Páginas: Exclui a página ativa"""
        return self.delete_specific_page(self.current_page_idx)

    def rotate_specific_page_permanent(self, page_idx, degrees=90):
        """Gira e grava a nova orientação permanentemente para uma página específica"""
        if not self.doc or page_idx < 0 or page_idx >= self.total_pages:
            return False
        target_page = self.doc.load_page(page_idx)
        new_rot = (target_page.rotation + degrees) % 360
        target_page.set_rotation(new_rot)
        self.documentModified.emit()
        self.render_current_page()
        self.statusMessage.emit(f"Página {page_idx + 1} girada permanentemente para {new_rot}°.")
        return True

    def rotate_page_permanent(self, degrees=90):
        """Gira e grava a nova orientação permanentemente no PDF"""
        self.rotate_specific_page_permanent(self.current_page_idx, degrees)

    def export_page_as_pdf(self, page_idx, output_path):
        """Exporta uma página específica como um novo arquivo PDF"""
        return self.export_pages_as_pdf([page_idx], output_path)

    def export_pages_as_pdf(self, page_indices, output_path):
        """Exporta um conjunto de páginas para um único arquivo PDF consolidado"""
        if not self.doc or not page_indices:
            return False
        try:
            new_doc = pymupdf.open()
            for pno in page_indices:
                if 0 <= pno < self.total_pages:
                    new_doc.insert_pdf(self.doc, from_page=pno, to_page=pno)
            new_doc.save(output_path, garbage=3, deflate=True)
            new_doc.close()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar PDF", f"Falha ao exportar páginas para PDF:\n{e}")
            return False

    def split_pages_to_folder(self, page_indices, dest_dir, base_name="pagina"):
        """Salva cada página selecionada como um arquivo individual em uma pasta"""
        if not self.doc or not page_indices:
            return 0
        count = 0
        try:
            for pno in page_indices:
                if 0 <= pno < self.total_pages:
                    out_path = os.path.join(dest_dir, f"{base_name}_pag_{pno + 1:03d}.pdf")
                    new_doc = pymupdf.open()
                    new_doc.insert_pdf(self.doc, from_page=pno, to_page=pno)
                    new_doc.save(out_path, garbage=3, deflate=True)
                    new_doc.close()
                    count += 1
            return count
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Separar Páginas", f"Falha ao separar páginas individuais:\n{e}")
            return count

    def export_page_as_image(self, page_idx, output_path, dpi=200):
        """Renderiza e salva uma página como arquivo de imagem"""
        if not self.doc or page_idx < 0 or page_idx >= self.total_pages:
            return False
        try:
            page = self.doc.load_page(page_idx)
            scale = dpi / 72.0
            matrix = pymupdf.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(output_path)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar Imagem", f"Falha ao exportar imagem da página:\n{e}")
            return False

    def export_pages_as_images(self, page_indices, dest_dir, base_name="pagina", img_format="png", dpi=200):
        """Renderiza e salva múltiplas páginas como arquivos de imagem em uma pasta"""
        if not self.doc or not page_indices:
            return 0
        count = 0
        scale = dpi / 72.0
        matrix = pymupdf.Matrix(scale, scale)
        try:
            for pno in page_indices:
                if 0 <= pno < self.total_pages:
                    out_path = os.path.join(dest_dir, f"{base_name}_pag_{pno + 1:03d}.{img_format}")
                    page = self.doc.load_page(pno)
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    pix.save(out_path)
                    count += 1
            return count
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar Imagens", f"Falha ao exportar imagens:\n{e}")
            return count

    def insert_pdf_pages(self, src_pdf_path, insert_at_idx, pages_to_insert=None):
        """Importa e insere páginas de outro arquivo PDF no documento ativo"""
        if not os.path.exists(src_pdf_path):
            return False
        if not self.doc:
            self.doc = pymupdf.open()
            self.total_pages = 0

        try:
            src_doc = pymupdf.open(src_pdf_path)
            src_len = len(src_doc)
            if src_len == 0:
                src_doc.close()
                return False

            insert_pos = max(0, min(insert_at_idx, self.total_pages))
            if pages_to_insert is None:
                self.doc.insert_pdf(src_doc, from_page=0, to_page=src_len - 1, start_at=insert_pos)
            else:
                cur_pos = insert_pos
                for pno in pages_to_insert:
                    if 0 <= pno < src_len:
                        self.doc.insert_pdf(src_doc, from_page=pno, to_page=pno, start_at=cur_pos)
                        cur_pos += 1

            src_doc.close()
            self.total_pages = len(self.doc)
            self.current_page_idx = insert_pos
            self.documentModified.emit()
            self.render_current_page()
            self.statusMessage.emit(f"Páginas importadas com sucesso! Total: {self.total_pages} página(s).")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Importar PDF", f"Falha ao importar páginas do PDF:\n{e}")
            return False

    def insert_image_pages(self, image_paths, insert_at_idx, fit_to_a4=True):
        """Importa uma ou mais imagens como novas páginas no documento"""
        if not image_paths:
            return False
        if not self.doc:
            self.doc = pymupdf.open()
            self.total_pages = 0

        insert_pos = max(0, min(insert_at_idx, self.total_pages))
        cur_pos = insert_pos
        inserted_count = 0

        try:
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    continue
                pix = pymupdf.Pixmap(img_path)
                img_w, img_h = pix.width, pix.height
                pix = None

                if fit_to_a4:
                    if img_w > img_h:
                        page_w, page_h = 841.89, 595.28
                    else:
                        page_w, page_h = 595.28, 841.89

                    margin = 20.0
                    avail_w = page_w - (2 * margin)
                    avail_h = page_h - (2 * margin)
                    scale = min(avail_w / img_w, avail_h / img_h)
                    dest_w = img_w * scale
                    dest_h = img_h * scale
                    dest_x = margin + (avail_w - dest_w) / 2
                    dest_y = margin + (avail_h - dest_h) / 2
                    rect = pymupdf.Rect(dest_x, dest_y, dest_x + dest_w, dest_y + dest_h)
                else:
                    page_w, page_h = float(img_w), float(img_h)
                    rect = pymupdf.Rect(0, 0, page_w, page_h)

                page = self.doc.new_page(pno=cur_pos, width=page_w, height=page_h)
                page.insert_image(rect, filename=img_path)
                cur_pos += 1
                inserted_count += 1

            self.total_pages = len(self.doc)
            self.current_page_idx = insert_pos
            self.documentModified.emit()
            self.render_current_page()
            self.statusMessage.emit(f"{inserted_count} página(s) de imagem inserida(s). Total: {self.total_pages} página(s).")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Inserir Imagem como Página", f"Falha ao inserir imagens:\n{e}")
            return False

    # --- Navegação e Zoom ---

    def go_to_page(self, page_idx):
        if not self.doc or page_idx < 0 or page_idx >= self.total_pages:
            return
        if self.current_page_idx != page_idx or not self.current_page:
            self.current_page_idx = page_idx
            self.render_current_page()

    def next_page(self):
        if self.current_page_idx + 1 < self.total_pages:
            self.go_to_page(self.current_page_idx + 1)

    def prev_page(self):
        if self.current_page_idx > 0:
            self.go_to_page(self.current_page_idx - 1)

    def first_page(self):
        self.go_to_page(0)

    def last_page(self):
        if self.total_pages > 0:
            self.go_to_page(self.total_pages - 1)

    def set_zoom(self, zoom_value, fit_mode=None):
        zoom_value = max(0.2, min(zoom_value, 5.0))
        self.zoom = zoom_value
        self.fit_mode = fit_mode
        self.zoomChanged.emit(self.zoom)
        self.render_current_page()

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.2, fit_mode=None)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.2, fit_mode=None)

    def fit_width(self):
        if not self.doc or not self.current_page:
            return
        self.fit_mode = 'width'
        viewport_width = self.viewport().width() - 60
        if viewport_width > 100:
            target_zoom = viewport_width / self.pdf_page_rect.width
            self.set_zoom(target_zoom, fit_mode='width')

    def fit_page(self):
        if not self.doc or not self.current_page:
            return
        self.fit_mode = 'page'
        viewport_width = self.viewport().width() - 60
        viewport_height = self.viewport().height() - 60
        if viewport_width > 100 and viewport_height > 100:
            zoom_x = viewport_width / self.pdf_page_rect.width
            zoom_y = viewport_height / self.pdf_page_rect.height
            target_zoom = min(zoom_x, zoom_y)
            self.set_zoom(target_zoom, fit_mode='page')

    def rotate_clockwise(self):
        self.rotation = (self.rotation + 90) % 360
        self.render_current_page()

    def rotate_counter_clockwise(self):
        self.rotation = (self.rotation - 90) % 360
        self.render_current_page()

    def set_ui_theme(self, is_dark):
        self.is_dark_theme = is_dark
        if is_dark:
            self.setStyleSheet("border: none; background-color: #0f172a;")
        else:
            self.setStyleSheet("border: none; background-color: #e2e8f0;")
        self.canvas.update()

    def set_page_filter(self, filter_mode):
        """'normal', 'sepia', 'invert'"""
        self.page_filter = filter_mode
        self.render_current_page()

    def set_render_mode(self, mode):
        # Compatibilidade retroativa
        if mode in ("normal", "sepia", "invert"):
            self.set_page_filter(mode)
        elif mode == "dark":
            self.set_ui_theme(True)
            self.set_page_filter("normal")

    def set_search_matches(self, matches, current_match_idx=-1):
        self.search_matches = matches
        self.current_page_match_idx = current_match_idx
        self.canvas.update()

    def render_current_page(self):
        if not self.doc or self.total_pages == 0:
            return

        self.current_page = self.doc.load_page(self.current_page_idx)
        self.pdf_page_rect = self.current_page.rect

        if self.fit_mode == 'width':
            vw = self.viewport().width() - 60
            if vw > 100:
                self.zoom = vw / self.pdf_page_rect.width
        elif self.fit_mode == 'page':
            vw = self.viewport().width() - 60
            vh = self.viewport().height() - 60
            if vw > 100 and vh > 100:
                self.zoom = min(vw / self.pdf_page_rect.width, vh / self.pdf_page_rect.height)

        dpr = self.devicePixelRatioF() if hasattr(self, 'devicePixelRatioF') else 1.0
        render_scale = self.zoom * dpr

        matrix = pymupdf.Matrix(render_scale, render_scale).prerotate(self.rotation)
        pix = self.current_page.get_pixmap(matrix=matrix, alpha=False)

        # Inverte apenas se explicitamente solicitado como filtro noturno da folha
        if self.page_filter == "invert":
            pix.invert_irect()

        qimg = QImage(
            pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
        )
        qimg.setDevicePixelRatio(dpr)
        pixmap = QPixmap.fromImage(qimg)

        display_size = QSize(int(self.pdf_page_rect.width * self.zoom), int(self.pdf_page_rect.height * self.zoom))
        self.canvas.update_pixmap(pixmap, display_size)

        self.pageChanged.emit(self.current_page_idx + 1, self.total_pages)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            vbar = self.verticalScrollBar()
            delta = event.angleDelta().y()
            if delta < 0 and vbar.value() == vbar.maximum():
                if self.current_page_idx + 1 < self.total_pages:
                    self.next_page()
                    vbar.setValue(vbar.minimum())
                    event.accept()
                    return
            elif delta > 0 and vbar.value() == vbar.minimum():
                if self.current_page_idx > 0:
                    self.prev_page()
                    vbar.setValue(vbar.maximum())
                    event.accept()
                    return
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_mode in ('width', 'page'):
            self.render_current_page()

"""
Leitor e Editor de PDF - Aplicação Principal estilo Adobe Acrobat Pro
Inclui Leitor, Navegador e Ferramentas de Edição (CRUD de Texto, Marca-texto, Borracha e Assinaturas)
"""

import sys
# Impede tentativas de carregar pymupdf.layout desnecessário
sys.modules['pymupdf.layout'] = None

import os
import json
import pymupdf
from PyQt6.QtCore import Qt, QUrl, QFileInfo
from PyQt6.QtGui import (
    QAction, QActionGroup, QIcon, QKeySequence, QPainter, QImage, QPixmap
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QSplitter, QVBoxLayout, QWidget, QToolBar, QComboBox,
    QSpinBox, QLabel, QPushButton, QMenu
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from styles import LIGHT_THEME, DARK_THEME, SEARCH_BAR_STYLE, SEARCH_BAR_DARK_STYLE
from pdf_viewer import PDFViewer
from thumbnails import SidebarWidget
from search_widget import SearchBar
from dialogs import PropertiesDialog, AboutDialog, TextEditDialog


def get_base_dir():
    """Retorna o diretório base para arquivos de configuração persistentes"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(rel_path):
    """Retorna o caminho de um recurso embutido ou local"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)


def detect_windows_theme():
    """Detecta se o Windows está em Modo Escuro ou Claro"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if val == 1 else "dark"
    except Exception:
        return "light"


CONFIG_FILE = os.path.join(get_base_dir(), "config.json")


class PDFReaderMainWindow(QMainWindow):
    def __init__(self, initial_file=None):
        super().__init__()
        self.current_file_path = None
        self.doc = None
        self.is_modified = False
        self.config = self._load_config()

        self.setWindowTitle("Leitor e Editor de PDF")
        self.resize(1180, 820)
        self.setAcceptDrops(True)

        self._init_ui()

        # Define tema inicial com alto contraste baseado no Windows
        current_theme = self.config.get("theme")
        if not current_theme:
            current_theme = detect_windows_theme()
        self._apply_theme(current_theme)

        if initial_file and os.path.exists(initial_file):
            self.open_pdf_file(initial_file)
        elif self.config.get("recent_files"):
            last_file = self.config["recent_files"][0]
            if os.path.exists(last_file):
                self.open_pdf_file(last_file)

    def _init_ui(self):
        # Widget Central
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barra de Pesquisa Retrátil (no topo)
        self.search_bar = SearchBar(self)
        self.search_bar.hide()
        self.search_bar.matchSelected.connect(self._on_search_match_selected)
        self.search_bar.searchClosed.connect(self._on_search_closed)
        main_layout.addWidget(self.search_bar)

        # Divisor (Splitter): Painel Lateral + Área do PDF
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.sidebar = SidebarWidget(self)
        self.sidebar.pageSelected.connect(self._on_sidebar_page_selected)
        self.splitter.addWidget(self.sidebar)

        self.viewer = PDFViewer(self)
        self.viewer.pageChanged.connect(self._on_viewer_page_changed)
        self.viewer.zoomChanged.connect(self._on_viewer_zoom_changed)
        self.viewer.statusMessage.connect(self.statusBar().showMessage)
        self.viewer.documentModified.connect(self._on_document_modified)
        self.splitter.addWidget(self.viewer)

        self.splitter.setSizes([260, 920])
        main_layout.addWidget(self.splitter)

        # Menus e Toolbars
        self._create_menus()
        self._create_toolbar()
        self._create_edit_toolbar()

        # Status Bar
        self.status_label = QLabel("Pronto")
        self.statusBar().addPermanentWidget(self.status_label)

    def _create_menus(self):
        menubar = self.menuBar()

        # Menu Arquivo
        file_menu = menubar.addMenu("&Arquivo")
        
        open_action = QAction("📂 &Abrir...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.prompt_open_file)
        file_menu.addAction(open_action)

        self.recent_menu = file_menu.addMenu("🕒 Abrir &Recente")
        self._update_recent_menu()

        save_action = QAction("💾 &Salvar", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_document)
        file_menu.addAction(save_action)

        save_as_action = QAction("💾➕ Salvar &Cópia Como...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_copy_as)
        file_menu.addAction(save_as_action)

        print_action = QAction("🖨️ &Imprimir...", self)
        print_action.setShortcut(QKeySequence.StandardKey.Print)
        print_action.triggered.connect(self.print_document)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        prop_action = QAction("ℹ️ &Propriedades do Documento...", self)
        prop_action.setShortcut("Ctrl+D")
        prop_action.triggered.connect(self.show_properties)
        file_menu.addAction(prop_action)

        file_menu.addSeparator()

        close_action = QAction("✖ &Fechar Arquivo", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_document)
        file_menu.addAction(close_action)

        exit_action = QAction("🚪 &Sair", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Editar
        edit_menu = menubar.addMenu("&Editar")
        
        copy_action = QAction("📋 &Copiar Texto Selecionado", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.viewer.canvas.copy_to_clipboard)
        edit_menu.addAction(copy_action)

        find_action = QAction("🔍 &Localizar...", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.toggle_search)
        edit_menu.addAction(find_action)

        edit_menu.addSeparator()

        add_text_action = QAction("✍️ Inserir Caixa de Texto", self)
        add_text_action.triggered.connect(lambda: self._set_active_tool("add_text"))
        edit_menu.addAction(add_text_action)

        highlight_action = QAction("🖍️ Ferramenta Marca-Texto", self)
        highlight_action.triggered.connect(lambda: self._set_active_tool("highlight"))
        edit_menu.addAction(highlight_action)

        eraser_action = QAction("🧹 Borracha / Apagar Conteúdo", self)
        eraser_action.triggered.connect(lambda: self._set_active_tool("eraser"))
        edit_menu.addAction(eraser_action)

        sig_action = QAction("✒️ Inserir Assinatura / Imagem", self)
        sig_action.triggered.connect(lambda: self._set_active_tool("insert_image"))
        edit_menu.addAction(sig_action)

        # Menu Páginas
        pages_menu = menubar.addMenu("&Páginas")
        del_page_action = QAction("🗑️ Excluir Página Atual", self)
        del_page_action.triggered.connect(self._prompt_delete_page)
        pages_menu.addAction(del_page_action)

        rot_perm_action = QAction("↻ Girar Página Permanentemente", self)
        rot_perm_action.triggered.connect(self._prompt_rotate_page_perm)
        pages_menu.addAction(rot_perm_action)

        # Menu Visualizar
        view_menu = menubar.addMenu("&Visualizar")

        zoom_in_act = QAction("➕ Mais Zoom", self)
        zoom_in_act.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_act.triggered.connect(self.viewer.zoom_in)
        view_menu.addAction(zoom_in_act)

        zoom_out_act = QAction("➖ Menos Zoom", self)
        zoom_out_act.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_act.triggered.connect(self.viewer.zoom_out)
        view_menu.addAction(zoom_out_act)

        actual_size_act = QAction("100% Tamanho Real", self)
        actual_size_act.setShortcut("Ctrl+0")
        actual_size_act.triggered.connect(lambda: self.viewer.set_zoom(1.0))
        view_menu.addAction(actual_size_act)

        fit_width_act = QAction("↔ Ajustar à Largura", self)
        fit_width_act.setShortcut("Ctrl+1")
        fit_width_act.triggered.connect(self.viewer.fit_width)
        view_menu.addAction(fit_width_act)

        fit_page_act = QAction("↕ Ajustar à Página Inteira", self)
        fit_page_act.setShortcut("Ctrl+2")
        fit_page_act.triggered.connect(self.viewer.fit_page)
        view_menu.addAction(fit_page_act)

        view_menu.addSeparator()

        rot_cw_act = QAction("↻ Girar Visualização (Horário)", self)
        rot_cw_act.setShortcut("Ctrl+R")
        rot_cw_act.triggered.connect(self.viewer.rotate_clockwise)
        view_menu.addAction(rot_cw_act)

        rot_ccw_act = QAction("↺ Girar Visualização (Anti-Horário)", self)
        rot_ccw_act.setShortcut("Ctrl+Shift+R")
        rot_ccw_act.triggered.connect(self.viewer.rotate_counter_clockwise)
        view_menu.addAction(rot_ccw_act)

        view_menu.addSeparator()

        toggle_sidebar_act = QAction("📑 Alternar Painel Lateral", self)
        toggle_sidebar_act.setShortcut("F4")
        toggle_sidebar_act.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(toggle_sidebar_act)

        fullscreen_act = QAction("⛶ Tela Cheia", self)
        fullscreen_act.setShortcut("F11")
        fullscreen_act.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_act)

        # Menu Modo de Leitura
        theme_menu = menubar.addMenu("&Modo de Leitura")
        light_act = QAction("☀️ Modo Claro", self)
        light_act.triggered.connect(lambda: self._apply_theme("light"))
        theme_menu.addAction(light_act)

        dark_act = QAction("🌙 Modo Escuro (Noturno)", self)
        dark_act.triggered.connect(lambda: self._apply_theme("dark"))
        theme_menu.addAction(dark_act)

        sepia_act = QAction("📜 Modo Sépia (Papel Confortável)", self)
        sepia_act.triggered.connect(lambda: self._apply_theme("sepia"))
        theme_menu.addAction(sepia_act)

        # Menu Ajuda
        help_menu = menubar.addMenu("A&juda")
        about_act = QAction("ℹ️ Sobre o Leitor e Editor de PDF", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    def _create_toolbar(self):
        toolbar = QToolBar("Barra Principal", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Abrir e Salvar
        btn_open = QAction("📂 Abrir", self)
        btn_open.setToolTip("Abrir documento PDF (Ctrl+O)")
        btn_open.triggered.connect(self.prompt_open_file)
        toolbar.addAction(btn_open)

        self.btn_save = QAction("💾 Salvar", self)
        self.btn_save.setToolTip("Salvar alterações no PDF (Ctrl+S)")
        self.btn_save.triggered.connect(self.save_document)
        toolbar.addAction(self.btn_save)

        btn_print = QAction("🖨️ Imprimir", self)
        btn_print.setToolTip("Imprimir documento (Ctrl+P)")
        btn_print.triggered.connect(self.print_document)
        toolbar.addAction(btn_print)

        toolbar.addSeparator()

        # Alternar Painel
        self.btn_sidebar = QAction("📑 Painel", self)
        self.btn_sidebar.setToolTip("Mostrar/Ocultar painel de miniaturas (F4)")
        self.btn_sidebar.setCheckable(True)
        self.btn_sidebar.setChecked(True)
        self.btn_sidebar.triggered.connect(self.toggle_sidebar)
        toolbar.addAction(self.btn_sidebar)

        toolbar.addSeparator()

        # Navegação de Páginas
        btn_first = QAction("⏮", self)
        btn_first.setToolTip("Primeira Página (Home)")
        btn_first.triggered.connect(self.viewer.first_page)
        toolbar.addAction(btn_first)

        btn_prev = QAction("◀", self)
        btn_prev.setToolTip("Página Anterior (PageUp)")
        btn_prev.triggered.connect(self.viewer.prev_page)
        toolbar.addAction(btn_prev)

        self.spin_page = QSpinBox()
        self.spin_page.setMinimum(1)
        self.spin_page.setMaximum(1)
        self.spin_page.setFixedWidth(55)
        self.spin_page.valueChanged.connect(lambda val: self.viewer.go_to_page(val - 1))
        toolbar.addWidget(self.spin_page)

        self.lbl_total_pages = QLabel(" / 0 ")
        self.lbl_total_pages.setStyleSheet("font-weight: bold; margin-right: 5px;")
        toolbar.addWidget(self.lbl_total_pages)

        btn_next = QAction("▶", self)
        btn_next.setToolTip("Próxima Página (PageDown)")
        btn_next.triggered.connect(self.viewer.next_page)
        toolbar.addAction(btn_next)

        btn_last = QAction("⏭", self)
        btn_last.setToolTip("Última Página (End)")
        btn_last.triggered.connect(self.viewer.last_page)
        toolbar.addAction(btn_last)

        toolbar.addSeparator()

        # Controles de Zoom
        btn_zoom_out = QAction("➖", self)
        btn_zoom_out.setToolTip("Reduzir Zoom (Ctrl+-)")
        btn_zoom_out.triggered.connect(self.viewer.zoom_out)
        toolbar.addAction(btn_zoom_out)

        self.combo_zoom = QComboBox()
        self.combo_zoom.setEditable(False)
        self.combo_zoom.setFixedWidth(100)
        self.combo_zoom.addItems([
            "50%", "75%", "100%", "125%", "150%", "200%", "300%", 
            "Ajustar Largura", "Ajustar Página"
        ])
        self.combo_zoom.setCurrentText("100%")
        self.combo_zoom.currentTextChanged.connect(self._on_combo_zoom_changed)
        toolbar.addWidget(self.combo_zoom)

        btn_zoom_in = QAction("➕", self)
        btn_zoom_in.setToolTip("Aumentar Zoom (Ctrl++)")
        btn_zoom_in.triggered.connect(self.viewer.zoom_in)
        toolbar.addAction(btn_zoom_in)

        btn_fit_w = QAction("↔", self)
        btn_fit_w.setToolTip("Ajustar à Largura da Janela (Ctrl+1)")
        btn_fit_w.triggered.connect(self.viewer.fit_width)
        toolbar.addAction(btn_fit_w)

        btn_fit_p = QAction("↕", self)
        btn_fit_p.setToolTip("Ajustar à Página Inteira (Ctrl+2)")
        btn_fit_p.triggered.connect(self.viewer.fit_page)
        toolbar.addAction(btn_fit_p)

        toolbar.addSeparator()

        # Rotação de Visualização
        btn_rot_ccw = QAction("↺", self)
        btn_rot_ccw.setToolTip("Girar à Esquerda (Ctrl+Shift+R)")
        btn_rot_ccw.triggered.connect(self.viewer.rotate_counter_clockwise)
        toolbar.addAction(btn_rot_ccw)

        btn_rot_cw = QAction("↻", self)
        btn_rot_cw.setToolTip("Girar à Direita (Ctrl+R)")
        btn_rot_cw.triggered.connect(self.viewer.rotate_clockwise)
        toolbar.addAction(btn_rot_cw)

        toolbar.addSeparator()

        # Busca
        btn_search = QAction("🔍 Localizar", self)
        btn_search.setToolTip("Pesquisar no texto (Ctrl+F)")
        btn_search.triggered.connect(self.toggle_search)
        toolbar.addAction(btn_search)

        # Seletor Rápido de Tema
        self.combo_theme = QComboBox()
        self.combo_theme.setFixedWidth(115)
        self.combo_theme.addItems(["☀️ Claro", "🌙 Escuro", "📜 Sépia"])
        self.combo_theme.currentIndexChanged.connect(self._on_quick_theme_changed)
        toolbar.addWidget(self.combo_theme)

    def _create_edit_toolbar(self):
        """Barra de Ferramentas Dedicada à Edição do PDF"""
        edit_toolbar = QToolBar("Ferramentas de Edição", self)
        edit_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, edit_toolbar)

        # Grupo exclusivo de ferramentas
        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        self.act_tool_select = QAction("👆 Selecionar", self)
        self.act_tool_select.setToolTip("Modo Visualização / Seleção normal de texto")
        self.act_tool_select.setCheckable(True)
        self.act_tool_select.setChecked(True)
        self.act_tool_select.triggered.connect(lambda: self._set_active_tool("select"))
        tool_group.addAction(self.act_tool_select)
        edit_toolbar.addAction(self.act_tool_select)

        self.act_tool_add_text = QAction("✍️ Adicionar Texto", self)
        self.act_tool_add_text.setToolTip("Clique em qualquer lugar da página para inserir texto")
        self.act_tool_add_text.setCheckable(True)
        self.act_tool_add_text.triggered.connect(lambda: self._set_active_tool("add_text"))
        tool_group.addAction(self.act_tool_add_text)
        edit_toolbar.addAction(self.act_tool_add_text)

        self.act_tool_eraser = QAction("🧹 Borracha / Apagar", self)
        self.act_tool_eraser.setToolTip("Arraste um retângulo sobre o conteúdo para apagá-lo")
        self.act_tool_eraser.setCheckable(True)
        self.act_tool_eraser.triggered.connect(lambda: self._set_active_tool("eraser"))
        tool_group.addAction(self.act_tool_eraser)
        edit_toolbar.addAction(self.act_tool_eraser)

        self.act_tool_highlight = QAction("🖍️ Marca-Texto", self)
        self.act_tool_highlight.setToolTip("Arraste sobre um trecho para destacar em amarelo")
        self.act_tool_highlight.setCheckable(True)
        self.act_tool_highlight.triggered.connect(lambda: self._set_active_tool("highlight"))
        tool_group.addAction(self.act_tool_highlight)
        edit_toolbar.addAction(self.act_tool_highlight)

        self.act_tool_sig = QAction("✒️ Inserir Assinatura/Imagem", self)
        self.act_tool_sig.setToolTip("Clique na folha para inserir uma imagem ou carimbo de assinatura")
        self.act_tool_sig.setCheckable(True)
        self.act_tool_sig.triggered.connect(lambda: self._set_active_tool("insert_image"))
        tool_group.addAction(self.act_tool_sig)
        edit_toolbar.addAction(self.act_tool_sig)

        edit_toolbar.addSeparator()

        # Ações de Página
        act_del_page = QAction("🗑️ Excluir Página", self)
        act_del_page.setToolTip("Excluir permanentemente a página atual do documento")
        act_del_page.triggered.connect(self._prompt_delete_page)
        edit_toolbar.addAction(act_del_page)

        act_rot_perm = QAction("↻ Girar Página Permanente", self)
        act_rot_perm.setToolTip("Girar e salvar a orientação da página no arquivo")
        act_rot_perm.triggered.connect(self._prompt_rotate_page_perm)
        edit_toolbar.addAction(act_rot_perm)

    def _set_active_tool(self, tool_name):
        self.viewer.set_tool(tool_name)
        if tool_name == "add_text":
            self.statusBar().showMessage("Modo 'Adicionar Texto': Clique na folha onde deseja inserir o texto.", 6000)
        elif tool_name == "eraser":
            self.statusBar().showMessage("Modo 'Borracha': Arraste um retângulo sobre o conteúdo a ser apagado.", 6000)
        elif tool_name == "highlight":
            self.statusBar().showMessage("Modo 'Marca-Texto': Arraste sobre o texto para destacar.", 6000)
        elif tool_name == "insert_image":
            self.statusBar().showMessage("Modo 'Assinatura/Imagem': Clique na folha onde deseja posicionar a assinatura.", 6000)
        else:
            self.statusBar().showMessage("Modo 'Visualização/Seleção' ativado.", 4000)

    def prompt_open_file(self):
        if self._check_unsaved_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo PDF", "", "Arquivos PDF (*.pdf);;Todos os Arquivos (*)"
        )
        if file_path:
            self.open_pdf_file(file_path)

    def open_pdf_file(self, file_path):
        try:
            doc = pymupdf.open(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Abrir Arquivo", f"Não foi possível abrir o PDF:\n{str(e)}")
            return

        self.doc = doc
        self.current_file_path = file_path
        self.is_modified = False
        self._update_window_title()

        self.spin_page.blockSignals(True)
        self.spin_page.setMaximum(len(doc))
        self.spin_page.blockSignals(False)

        self.lbl_total_pages.setText(f" / {len(doc)} ")

        # Carrega no viewer, sidebar e busca
        self.viewer.load_document(doc)
        self.sidebar.load_document(doc)
        self.search_bar.set_document(doc)

        # Restaura última página lida se existir
        last_pages = self.config.get("last_pages", {})
        saved_page = last_pages.get(file_path, 0)
        if 0 < saved_page < len(doc):
            self.viewer.go_to_page(saved_page)

        self._add_to_recent(file_path)
        self.status_label.setText(f"Arquivo carregado: {os.path.basename(file_path)}")

    def save_document(self):
        """Salva as alterações diretamente no arquivo aberto de forma atômica e segura"""
        if not self.doc or not self.current_file_path:
            return

        try:
            curr_page = self.viewer.current_page_idx
            doc_bytes = self.doc.tobytes(garbage=3, deflate=True)
            tmp_path = self.current_file_path + ".tmp"

            with open(tmp_path, "wb") as f:
                f.write(doc_bytes)

            self.doc.close()

            # Substituição atômica no Windows
            if os.path.exists(self.current_file_path):
                os.remove(self.current_file_path)
            os.replace(tmp_path, self.current_file_path)

            # Reabre o documento salvo atualizado
            self.doc = pymupdf.open(self.current_file_path)
            self.viewer.load_document(self.doc)
            self.sidebar.load_document(self.doc)
            self.search_bar.set_document(self.doc)
            self.viewer.go_to_page(curr_page)

            self.is_modified = False
            self._update_window_title()
            self.statusBar().showMessage("Documento salvo com sucesso!", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar as alterações:\n{e}")

    def save_copy_as(self):
        if not self.doc:
            return
        dest_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Cópia do PDF Como", "", "Arquivos PDF (*.pdf)"
        )
        if dest_path:
            try:
                self.doc.save(dest_path)
                QMessageBox.information(self, "Sucesso", "Cópia do arquivo salva com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar cópia:\n{e}")

    def close_document(self):
        if self._check_unsaved_changes():
            return

        if self.doc:
            self.doc.close()
            self.doc = None
            self.current_file_path = None
            self.is_modified = False
            self.viewer.doc = None
            self.viewer.canvas.pixmap = None
            self.viewer.canvas.update()
            self.sidebar.thumbnail_list.clear()
            self.sidebar.outline_tree.clear()
            self.search_bar.clear_search()
            self.spin_page.setMaximum(1)
            self.spin_page.setValue(1)
            self.lbl_total_pages.setText(" / 0 ")
            self.setWindowTitle("Leitor e Editor de PDF")
            self.status_label.setText("Nenhum arquivo aberto")

    def _check_unsaved_changes(self):
        """Retorna True se a operação deve ser cancelada pelo usuário"""
        if self.is_modified and self.doc:
            reply = QMessageBox.question(
                self, "Alterações Não Salvas",
                "O documento possui alterações não salvas. Deseja salvar as alterações agora?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_document()
                return False
            elif reply == QMessageBox.StandardButton.Discard:
                return False
            else:
                return True
        return False

    def closeEvent(self, event):
        if self._check_unsaved_changes():
            event.ignore()
        else:
            event.accept()

    def _on_document_modified(self):
        self.is_modified = True
        self._update_window_title()

    def _update_window_title(self):
        if self.current_file_path:
            fname = os.path.basename(self.current_file_path)
            mod = "• " if self.is_modified else ""
            self.setWindowTitle(f"{mod}{fname} - Leitor e Editor de PDF")
        else:
            self.setWindowTitle("Leitor e Editor de PDF")

    def _prompt_delete_page(self):
        if not self.doc:
            return
        curr_page = self.viewer.current_page_idx + 1
        reply = QMessageBox.question(
            self, "Excluir Página",
            f"Deseja realmente excluir permanentemente a Página {curr_page} do documento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.viewer.delete_current_page():
                self.spin_page.blockSignals(True)
                self.spin_page.setMaximum(len(self.doc))
                self.spin_page.blockSignals(False)
                self.lbl_total_pages.setText(f" / {len(self.doc)} ")
                self.sidebar.load_document(self.doc)

    def _prompt_rotate_page_perm(self):
        if not self.doc:
            return
        self.viewer.rotate_page_permanent(90)
        self.sidebar.load_document(self.doc)

    def print_document(self):
        if not self.doc:
            QMessageBox.information(self, "Aviso", "Nenhum documento aberto para imprimir.")
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        print_dialog = QPrintDialog(printer, self)
        print_dialog.setWindowTitle("Imprimir Documento PDF")

        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter(printer)
            total = len(self.doc)
            from_page = 0
            to_page = total

            if printer.fromPage() > 0:
                from_page = max(0, printer.fromPage() - 1)
            if printer.toPage() > 0:
                to_page = min(total, printer.toPage())

            for i in range(from_page, to_page):
                if i > from_page:
                    printer.newPage()
                page = self.doc.load_page(i)
                matrix = pymupdf.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                qimg = QImage(
                    pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
                )
                rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                painter.drawImage(rect, qimg)

            painter.end()
            QMessageBox.information(self, "Imprimir", "Trabalho de impressão enviado com sucesso!")

    def show_properties(self):
        if not self.doc or not self.current_file_path:
            QMessageBox.information(self, "Aviso", "Nenhum arquivo aberto.")
            return
        dlg = PropertiesDialog(self.doc, self.current_file_path, self)
        dlg.exec()

    def show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def toggle_sidebar(self):
        is_visible = self.sidebar.isVisible()
        self.sidebar.setVisible(not is_visible)
        self.btn_sidebar.setChecked(not is_visible)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def toggle_search(self):
        if not self.doc:
            return
        if self.search_bar.isVisible():
            self.search_bar.close_search()
        else:
            self.search_bar.show_and_focus()

    def _on_search_match_selected(self, page_idx, match_idx_on_page, page_matches):
        self.viewer.go_to_page(page_idx)
        self.viewer.set_search_matches(page_matches, match_idx_on_page)

    def _on_search_closed(self):
        self.viewer.set_search_matches([])

    def _on_sidebar_page_selected(self, page_idx):
        self.viewer.go_to_page(page_idx)

    def _on_viewer_page_changed(self, current_page, total_pages):
        self.spin_page.blockSignals(True)
        self.spin_page.setValue(current_page)
        self.spin_page.blockSignals(False)
        self.sidebar.highlight_page(current_page - 1)

        if self.current_file_path:
            if "last_pages" not in self.config:
                self.config["last_pages"] = {}
            self.config["last_pages"][self.current_file_path] = current_page - 1
            self._save_config()

    def _on_viewer_zoom_changed(self, zoom):
        percent = int(zoom * 100)
        self.combo_zoom.blockSignals(True)
        self.combo_zoom.setEditText(f"{percent}%")
        self.combo_zoom.blockSignals(False)

    def _on_combo_zoom_changed(self, text):
        if text == "Ajustar Largura":
            self.viewer.fit_width()
        elif text == "Ajustar Página":
            self.viewer.fit_page()
        else:
            try:
                val = float(text.replace("%", "").strip()) / 100.0
                self.viewer.set_zoom(val)
            except ValueError:
                pass

    def _on_quick_theme_changed(self, index):
        modes = ["light", "dark", "sepia"]
        if 0 <= index < len(modes):
            self._apply_theme(modes[index])

    def _apply_theme(self, theme_name):
        self.config["theme"] = theme_name
        self._save_config()

        if theme_name == "dark":
            self.setStyleSheet(DARK_THEME)
            self.search_bar.setStyleSheet(SEARCH_BAR_DARK_STYLE)
            self.viewer.set_ui_theme(True)
            self.viewer.set_page_filter("normal")
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(1)
            self.combo_theme.blockSignals(False)
        elif theme_name == "sepia":
            self.setStyleSheet(LIGHT_THEME)
            self.search_bar.setStyleSheet(SEARCH_BAR_STYLE)
            self.viewer.set_ui_theme(False)
            self.viewer.set_page_filter("sepia")
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(2)
            self.combo_theme.blockSignals(False)
        else:  # light
            self.setStyleSheet(LIGHT_THEME)
            self.search_bar.setStyleSheet(SEARCH_BAR_STYLE)
            self.viewer.set_ui_theme(False)
            self.viewer.set_page_filter("normal")
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(0)
            self.combo_theme.blockSignals(False)

    # Suporte a Arrastar e Soltar (Drag & Drop)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf") and os.path.exists(file_path):
                if not self._check_unsaved_changes():
                    self.open_pdf_file(file_path)
                event.acceptProposedAction()
                break

    # Gerenciamento de Histórico e Configurações
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"recent_files": [], "last_pages": {}, "theme": "light"}

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _add_to_recent(self, file_path):
        if "recent_files" not in self.config:
            self.config["recent_files"] = []
        recents = self.config["recent_files"]
        if file_path in recents:
            recents.remove(file_path)
        recents.insert(0, file_path)
        self.config["recent_files"] = recents[:10]
        self._save_config()
        self._update_recent_menu()

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recents = self.config.get("recent_files", [])
        if not recents:
            empty_action = QAction("Nenhum arquivo recente", self)
            empty_action.setEnabled(False)
            self.recent_menu.addAction(empty_action)
            return

        for path in recents:
            if os.path.exists(path):
                action = QAction(f"{os.path.basename(path)} ({path})", self)
                action.triggered.connect(lambda checked, p=path: self.open_pdf_file(p))
                self.recent_menu.addAction(action)

        self.recent_menu.addSeparator()
        clear_action = QAction("Limpar Histórico Recente", self)
        clear_action.triggered.connect(self._clear_recent)
        self.recent_menu.addAction(clear_action)

    def _clear_recent(self):
        self.config["recent_files"] = []
        self._save_config()
        self._update_recent_menu()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Leitor e Editor de PDF")
    app.setStyle("Fusion")
    
    icon_path = get_resource_path("app_icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    else:
        app_icon = None

    initial_file = None
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            cleaned_arg = arg.strip('\"\'')
            if os.path.isfile(cleaned_arg):
                initial_file = os.path.abspath(cleaned_arg)
                break
            elif cleaned_arg.lower().endswith(".pdf"):
                initial_file = os.path.abspath(cleaned_arg)
                break
    
    window = PDFReaderMainWindow(initial_file)
    if app_icon:
        window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

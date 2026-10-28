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
    QSpinBox, QLabel, QPushButton, QMenu, QToolButton,
    QTabWidget, QStackedWidget
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from styles import LIGHT_THEME, DARK_THEME, SEARCH_BAR_STYLE, SEARCH_BAR_DARK_STYLE
from pdf_viewer import PDFViewer
from thumbnails import SidebarWidget
from search_widget import SearchBar
from dialogs import (
    PropertiesDialog, AboutDialog, TextEditDialog,
    SplitPagesDialog, ImportPdfDialog, ImportImageDialog
)
from document_tab import DocumentTab, WelcomePlaceholderWidget


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
    def __init__(self, initial_files=None):
        super().__init__()
        self.config = self._load_config()
        self.active_tool_name = "select"

        self.setWindowTitle("Leitor e Editor de PDF")
        self.resize(1180, 820)
        self.setAcceptDrops(True)

        self._init_ui()

        # Define tema inicial com alto contraste baseado no Windows
        current_theme = self.config.get("theme")
        if not current_theme:
            current_theme = detect_windows_theme()
        self._apply_theme(current_theme)

        # Abre arquivos iniciais ou último recente
        opened_any = False
        if initial_files:
            if isinstance(initial_files, str):
                initial_files = [initial_files]
            for f in initial_files:
                if f and os.path.exists(f):
                    if self.open_pdf_file(f, switch_to=True):
                        opened_any = True

        if not opened_any and self.config.get("recent_files"):
            last_file = self.config["recent_files"][0]
            if os.path.exists(last_file):
                self.open_pdf_file(last_file)

    @property
    def current_tab(self):
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, DocumentTab):
            return widget
        return None

    @property
    def viewer(self):
        tab = self.current_tab
        return tab.viewer if tab else None

    @property
    def sidebar(self):
        tab = self.current_tab
        return tab.sidebar if tab else None

    @property
    def doc(self):
        tab = self.current_tab
        return tab.doc if tab else None

    @doc.setter
    def doc(self, value):
        if self.current_tab:
            self.current_tab.doc = value

    @property
    def current_file_path(self):
        tab = self.current_tab
        return tab.file_path if tab else None

    @current_file_path.setter
    def current_file_path(self, value):
        if self.current_tab:
            self.current_tab.file_path = value

    @property
    def is_modified(self):
        tab = self.current_tab
        return tab.is_modified if tab else False

    @is_modified.setter
    def is_modified(self, value):
        if self.current_tab:
            self.current_tab.is_modified = value
            self._update_tab_title(self.current_tab)

    def _init_ui(self):
        # Widget Central com Stack (Placeholder ou Abas)
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

        # Pilha central: Placeholder de boas-vindas OU abas com arquivos
        self.stack = QStackedWidget(self)

        self.empty_widget = WelcomePlaceholderWidget(self)
        self.empty_widget.openRequested.connect(self.prompt_open_file)
        self.empty_widget.createFromImagesRequested.connect(self.prompt_import_image)
        self.stack.addWidget(self.empty_widget)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self._on_tab_bar_context_menu)

        # Botão '+' na barra de abas
        self.btn_new_tab = QToolButton(self.tab_widget)
        self.btn_new_tab.setText(" ＋ ")
        self.btn_new_tab.setToolTip("Abrir documento em nova aba (Ctrl+T)")
        self.btn_new_tab.clicked.connect(self.prompt_open_file)
        self.tab_widget.setCornerWidget(self.btn_new_tab, Qt.Corner.TopRightCorner)

        self.stack.addWidget(self.tab_widget)
        self.stack.setCurrentWidget(self.empty_widget)
        main_layout.addWidget(self.stack)

        # Menus e Toolbars
        self._create_menus()
        self._create_toolbar()
        self._create_edit_toolbar()

        # Status Bar
        self.status_label = QLabel("Pronto")
        self.statusBar().addPermanentWidget(self.status_label)
        self._set_controls_enabled(False)

    def _create_menus(self):
        menubar = self.menuBar()

        # Menu Arquivo
        file_menu = menubar.addMenu("&Arquivo")

        new_tab_action = QAction("➕ &Nova Aba...", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(self.prompt_open_file)
        file_menu.addAction(new_tab_action)

        open_action = QAction("📂 &Abrir Arquivo(s)...", self)
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

        export_menu = file_menu.addMenu("📤 &Exportar Páginas")
        exp_curr_pdf_act = QAction("📄 Exportar Página Atual como PDF...", self)
        exp_curr_pdf_act.triggered.connect(lambda: self.prompt_export_page_pdf())
        export_menu.addAction(exp_curr_pdf_act)

        exp_curr_img_act = QAction("🖼️ Exportar Página Atual como Imagem...", self)
        exp_curr_img_act.triggered.connect(lambda: self.prompt_export_page_image())
        export_menu.addAction(exp_curr_img_act)

        split_act = QAction("✂️ Separar / Dividir Páginas...", self)
        split_act.triggered.connect(self.prompt_split_pages)
        export_menu.addAction(split_act)

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

        close_action = QAction("✖ &Fechar Aba Atual", self)
        close_action.setShortcut(QKeySequence("Ctrl+W"))
        close_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_action)

        close_all_action = QAction("✖✖ Fechar &Todas as Abas", self)
        close_all_action.setShortcut(QKeySequence("Ctrl+Shift+W"))
        close_all_action.triggered.connect(self.close_all_tabs)
        file_menu.addAction(close_all_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 &Sair", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Editar
        edit_menu = menubar.addMenu("&Editar")

        copy_action = QAction("📋 &Copiar Texto Selecionado", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(lambda: self.viewer.canvas.copy_to_clipboard() if self.viewer else None)
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

        imp_pdf_action = QAction("➕ Importar Páginas de Arquivo PDF...", self)
        imp_pdf_action.triggered.connect(lambda: self.prompt_import_pdf())
        pages_menu.addAction(imp_pdf_action)

        imp_img_action = QAction("🖼️ Importar Imagem como Nova Página...", self)
        imp_img_action.triggered.connect(lambda: self.prompt_import_image())
        pages_menu.addAction(imp_img_action)

        pages_menu.addSeparator()

        exp_pdf_act2 = QAction("📤 Exportar Página Atual como PDF...", self)
        exp_pdf_act2.triggered.connect(lambda: self.prompt_export_page_pdf())
        pages_menu.addAction(exp_pdf_act2)

        exp_img_act2 = QAction("🖼️ Exportar Página Atual como Imagem...", self)
        exp_img_act2.triggered.connect(lambda: self.prompt_export_page_image())
        pages_menu.addAction(exp_img_act2)

        split_act2 = QAction("✂️ Separar / Dividir Páginas...", self)
        split_act2.triggered.connect(self.prompt_split_pages)
        pages_menu.addAction(split_act2)

        pages_menu.addSeparator()

        rot_perm_action = QAction("↻ Girar Página Permanentemente", self)
        rot_perm_action.triggered.connect(self._prompt_rotate_page_perm)
        pages_menu.addAction(rot_perm_action)

        del_page_action = QAction("🗑️ Excluir Página Atual", self)
        del_page_action.triggered.connect(self._prompt_delete_page)
        pages_menu.addAction(del_page_action)

        # Menu Visualizar
        view_menu = menubar.addMenu("&Visualizar")

        zoom_in_act = QAction("➕ Mais Zoom", self)
        zoom_in_act.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_act.triggered.connect(lambda: self.viewer.zoom_in() if self.viewer else None)
        view_menu.addAction(zoom_in_act)

        zoom_out_act = QAction("➖ Menos Zoom", self)
        zoom_out_act.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_act.triggered.connect(lambda: self.viewer.zoom_out() if self.viewer else None)
        view_menu.addAction(zoom_out_act)

        actual_size_act = QAction("100% Tamanho Real", self)
        actual_size_act.setShortcut("Ctrl+0")
        actual_size_act.triggered.connect(lambda: self.viewer.set_zoom(1.0) if self.viewer else None)
        view_menu.addAction(actual_size_act)

        fit_width_act = QAction("↔ Ajustar à Largura", self)
        fit_width_act.setShortcut("Ctrl+1")
        fit_width_act.triggered.connect(lambda: self.viewer.fit_width() if self.viewer else None)
        view_menu.addAction(fit_width_act)

        fit_page_act = QAction("↕ Ajustar à Página Inteira", self)
        fit_page_act.setShortcut("Ctrl+2")
        fit_page_act.triggered.connect(lambda: self.viewer.fit_page() if self.viewer else None)
        view_menu.addAction(fit_page_act)

        view_menu.addSeparator()

        rot_cw_act = QAction("↻ Girar Visualização (Horário)", self)
        rot_cw_act.setShortcut("Ctrl+R")
        rot_cw_act.triggered.connect(lambda: self.viewer.rotate_clockwise() if self.viewer else None)
        view_menu.addAction(rot_cw_act)

        rot_ccw_act = QAction("↺ Girar Visualização (Anti-Horário)", self)
        rot_ccw_act.setShortcut("Ctrl+Shift+R")
        rot_ccw_act.triggered.connect(lambda: self.viewer.rotate_counter_clockwise() if self.viewer else None)
        view_menu.addAction(rot_ccw_act)

        view_menu.addSeparator()

        next_tab_act = QAction("⏭ Próxima Aba", self)
        next_tab_act.setShortcuts([QKeySequence("Ctrl+Tab"), QKeySequence("Ctrl+PgDown")])
        next_tab_act.triggered.connect(self.next_tab)
        view_menu.addAction(next_tab_act)

        prev_tab_act = QAction("⏮ Aba Anterior", self)
        prev_tab_act.setShortcuts([QKeySequence("Ctrl+Shift+Tab"), QKeySequence("Ctrl+PgUp")])
        prev_tab_act.triggered.connect(self.prev_tab)
        view_menu.addAction(prev_tab_act)

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

        # Nova Aba e Abrir
        btn_new_tab = QAction("➕ Nova Aba", self)
        btn_new_tab.setToolTip("Abrir documento em nova aba (Ctrl+T)")
        btn_new_tab.triggered.connect(self.prompt_open_file)
        toolbar.addAction(btn_new_tab)

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

        # Importar (PDF ou Imagem)
        btn_import_menu = QMenu(self)
        act_imp_pdf_tb = btn_import_menu.addAction("➕ Importar Páginas de Arquivo PDF...")
        act_imp_pdf_tb.triggered.connect(lambda: self.prompt_import_pdf())
        act_imp_img_tb = btn_import_menu.addAction("🖼️ Importar Imagem como Nova Página...")
        act_imp_img_tb.triggered.connect(lambda: self.prompt_import_image())

        self.btn_import_tool = QToolButton(self)
        self.btn_import_tool.setText("➕ Importar")
        self.btn_import_tool.setToolTip("Importar páginas de outro PDF ou arquivo de imagem")
        self.btn_import_tool.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_import_tool.setMenu(btn_import_menu)
        toolbar.addWidget(self.btn_import_tool)

        # Exportar / Separar Páginas
        btn_export_menu = QMenu(self)
        act_exp_pdf_tb = btn_export_menu.addAction("📤 Exportar Página Atual como PDF...")
        act_exp_pdf_tb.triggered.connect(lambda: self.prompt_export_page_pdf())
        act_exp_img_tb = btn_export_menu.addAction("🖼️ Exportar Página Atual como Imagem...")
        act_exp_img_tb.triggered.connect(lambda: self.prompt_export_page_image())
        act_split_tb = btn_export_menu.addAction("✂️ Separar / Dividir Páginas...")
        act_split_tb.triggered.connect(self.prompt_split_pages)

        self.btn_export_tool = QToolButton(self)
        self.btn_export_tool.setText("✂️ Separar/Exportar")
        self.btn_export_tool.setToolTip("Separar páginas, exportar página atual ou dividir documento")
        self.btn_export_tool.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_export_tool.setMenu(btn_export_menu)
        toolbar.addWidget(self.btn_export_tool)

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
        btn_first.triggered.connect(lambda: self.viewer.first_page() if self.viewer else None)
        toolbar.addAction(btn_first)

        btn_prev = QAction("◀", self)
        btn_prev.setToolTip("Página Anterior (PageUp)")
        btn_prev.triggered.connect(lambda: self.viewer.prev_page() if self.viewer else None)
        toolbar.addAction(btn_prev)

        self.spin_page = QSpinBox()
        self.spin_page.setMinimum(1)
        self.spin_page.setMaximum(1)
        self.spin_page.setFixedWidth(55)
        self.spin_page.valueChanged.connect(lambda val: self.viewer.go_to_page(val - 1) if self.viewer else None)
        toolbar.addWidget(self.spin_page)

        self.lbl_total_pages = QLabel(" / 0 ")
        self.lbl_total_pages.setStyleSheet("font-weight: bold; margin-right: 5px;")
        toolbar.addWidget(self.lbl_total_pages)

        btn_next = QAction("▶", self)
        btn_next.setToolTip("Próxima Página (PageDown)")
        btn_next.triggered.connect(lambda: self.viewer.next_page() if self.viewer else None)
        toolbar.addAction(btn_next)

        btn_last = QAction("⏭", self)
        btn_last.setToolTip("Última Página (End)")
        btn_last.triggered.connect(lambda: self.viewer.last_page() if self.viewer else None)
        toolbar.addAction(btn_last)

        toolbar.addSeparator()

        # Controles de Zoom
        btn_zoom_out = QAction("➖", self)
        btn_zoom_out.setToolTip("Reduzir Zoom (Ctrl+-)")
        btn_zoom_out.triggered.connect(lambda: self.viewer.zoom_out() if self.viewer else None)
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
        btn_zoom_in.triggered.connect(lambda: self.viewer.zoom_in() if self.viewer else None)
        toolbar.addAction(btn_zoom_in)

        btn_fit_w = QAction("↔", self)
        btn_fit_w.setToolTip("Ajustar à Largura da Janela (Ctrl+1)")
        btn_fit_w.triggered.connect(lambda: self.viewer.fit_width() if self.viewer else None)
        toolbar.addAction(btn_fit_w)

        btn_fit_p = QAction("↕", self)
        btn_fit_p.setToolTip("Ajustar à Página Inteira (Ctrl+2)")
        btn_fit_p.triggered.connect(lambda: self.viewer.fit_page() if self.viewer else None)
        toolbar.addAction(btn_fit_p)

        toolbar.addSeparator()

        # Rotação de Visualização
        btn_rot_ccw = QAction("↺", self)
        btn_rot_ccw.setToolTip("Girar à Esquerda (Ctrl+Shift+R)")
        btn_rot_ccw.triggered.connect(lambda: self.viewer.rotate_counter_clockwise() if self.viewer else None)
        toolbar.addAction(btn_rot_ccw)

        btn_rot_cw = QAction("↻", self)
        btn_rot_cw.setToolTip("Girar à Direita (Ctrl+R)")
        btn_rot_cw.triggered.connect(lambda: self.viewer.rotate_clockwise() if self.viewer else None)
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

        edit_toolbar.addSeparator()

        act_split_page = QAction("✂️ Separar Páginas", self)
        act_split_page.setToolTip("Separar ou extrair páginas do documento atual")
        act_split_page.triggered.connect(self.prompt_split_pages)
        edit_toolbar.addAction(act_split_page)

        act_import_page = QAction("➕ Importar Páginas/Imagens", self)
        act_import_page.setToolTip("Importar páginas de outro PDF ou imagem como nova página")
        act_import_page.triggered.connect(lambda: self.prompt_import_pdf())
        edit_toolbar.addAction(act_import_page)

    def _set_active_tool(self, tool_name):
        self.active_tool_name = tool_name
        if self.viewer:
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
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Abrir Arquivos PDF", "", "Arquivos PDF (*.pdf);;Todos os Arquivos (*)"
        )
        if file_paths:
            for p in file_paths:
                self.open_pdf_file(p)

    def open_pdf_file(self, file_path, switch_to=True):
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Erro", f"O arquivo não foi encontrado:\n{file_path}")
            return False

        abs_path = os.path.abspath(file_path)
        # Verifica se o arquivo já está aberto em alguma aba
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, DocumentTab) and tab.file_path and os.path.abspath(tab.file_path) == abs_path:
                if switch_to:
                    self.tab_widget.setCurrentIndex(i)
                    self.statusBar().showMessage(f"O documento já está aberto na Aba {i + 1}.", 4000)
                return True

        tab = DocumentTab(self)
        try:
            tab.load_file(abs_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Abrir Arquivo", f"Não foi possível abrir o PDF:\n{str(e)}")
            tab.close_tab()
            return False

        tab.pageChanged.connect(self._on_tab_page_changed)
        tab.zoomChanged.connect(self._on_tab_zoom_changed)
        tab.statusMessage.connect(self._on_tab_status_message)
        tab.documentModified.connect(self._on_tab_document_modified)

        self._apply_theme_to_tab(tab)
        if hasattr(self, 'active_tool_name'):
            tab.viewer.set_tool(self.active_tool_name)

        last_pages = self.config.get("last_pages", {})
        saved_page = last_pages.get(abs_path, 0)
        if 0 < saved_page < len(tab.doc):
            tab.viewer.go_to_page(saved_page)

        idx = self.tab_widget.addTab(tab, tab.display_title)
        self.tab_widget.setTabToolTip(idx, abs_path)
        if switch_to:
            self.tab_widget.setCurrentIndex(idx)
            self.stack.setCurrentWidget(self.tab_widget)

        self._add_to_recent(abs_path)
        self.status_label.setText(f"Arquivo carregado: {os.path.basename(abs_path)}")
        return True

    def create_new_tab_with_doc(self, doc, file_path=None, title="Sem Título"):
        tab = DocumentTab(self)
        tab.load_doc(doc, file_path)
        if file_path is None:
            tab.is_modified = True

        tab.pageChanged.connect(self._on_tab_page_changed)
        tab.zoomChanged.connect(self._on_tab_zoom_changed)
        tab.statusMessage.connect(self._on_tab_status_message)
        tab.documentModified.connect(self._on_tab_document_modified)

        self._apply_theme_to_tab(tab)
        if hasattr(self, 'active_tool_name'):
            tab.viewer.set_tool(self.active_tool_name)

        idx = self.tab_widget.addTab(tab, tab.display_title)
        self.tab_widget.setCurrentIndex(idx)
        self.stack.setCurrentWidget(self.tab_widget)
        self._update_window_title()
        return tab

    def save_tab_document(self, tab):
        if not tab or not tab.doc:
            return False

        if not tab.file_path:
            dest_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Documento Como", "", "Arquivos PDF (*.pdf)"
            )
            if not dest_path:
                return False
            try:
                curr_p = tab.viewer.current_page_idx
                tab.doc.save(dest_path, garbage=3, deflate=True)
                tab.file_path = dest_path
                tab.doc.close()
                tab.load_file(dest_path)
                tab.viewer.go_to_page(curr_p)
                tab.is_modified = False
                self._update_tab_title(tab)
                self._update_window_title()
                self._add_to_recent(dest_path)
                self.statusBar().showMessage(f"Documento salvo em '{os.path.basename(dest_path)}'!", 5000)
                return True
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", f"Falha ao salvar:\n{e}")
                return False
        else:
            try:
                curr_p = tab.viewer.current_page_idx
                doc_bytes = tab.doc.tobytes(garbage=3, deflate=True)
                tmp_path = tab.file_path + ".tmp"
                with open(tmp_path, "wb") as f:
                    f.write(doc_bytes)

                tab.doc.close()

                if os.path.exists(tab.file_path):
                    os.remove(tab.file_path)
                os.replace(tmp_path, tab.file_path)

                tab.load_file(tab.file_path)
                tab.viewer.go_to_page(curr_p)
                tab.is_modified = False
                self._update_tab_title(tab)
                self._update_window_title()
                self.statusBar().showMessage("Documento salvo com sucesso!", 5000)
                return True
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar alterações:\n{e}")
                return False

    def save_document(self):
        if self.current_tab:
            self.save_tab_document(self.current_tab)

    def save_copy_as(self):
        tab = self.current_tab
        if not tab or not tab.doc:
            return
        dest_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Cópia do PDF Como", "", "Arquivos PDF (*.pdf)"
        )
        if dest_path:
            try:
                tab.doc.save(dest_path, garbage=3, deflate=True)
                self._add_to_recent(dest_path)
                QMessageBox.information(self, "Sucesso", "Cópia do arquivo salva com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar cópia:\n{e}")

    def close_tab(self, index):
        if index < 0 or index >= self.tab_widget.count():
            return
        tab = self.tab_widget.widget(index)
        if not isinstance(tab, DocumentTab):
            return

        if tab.is_modified and tab.doc:
            self.tab_widget.setCurrentIndex(index)
            fname = tab.tab_name
            reply = QMessageBox.question(
                self, "Alterações Não Salvas",
                f"O documento '{fname}' possui alterações não salvas.\nDeseja salvar as alterações antes de fechar a aba?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_tab_document(tab):
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        tab.close_tab()
        self.tab_widget.removeTab(index)

        if self.tab_widget.count() == 0:
            self._on_no_tabs_active()
        else:
            self._on_tab_changed(self.tab_widget.currentIndex())

    def close_current_tab(self):
        curr = self.tab_widget.currentIndex()
        if curr >= 0:
            self.close_tab(curr)

    def close_other_tabs(self, keep_index):
        for i in range(self.tab_widget.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)

    def close_all_tabs(self):
        for i in range(self.tab_widget.count() - 1, -1, -1):
            self.close_tab(i)

    def close_document(self):
        self.close_current_tab()

    def next_tab(self):
        count = self.tab_widget.count()
        if count > 1:
            next_idx = (self.tab_widget.currentIndex() + 1) % count
            self.tab_widget.setCurrentIndex(next_idx)

    def prev_tab(self):
        count = self.tab_widget.count()
        if count > 1:
            prev_idx = (self.tab_widget.currentIndex() - 1 + count) % count
            self.tab_widget.setCurrentIndex(prev_idx)

    def _duplicate_tab(self, tab_idx):
        tab = self.tab_widget.widget(tab_idx)
        if isinstance(tab, DocumentTab) and tab.file_path and os.path.exists(tab.file_path):
            new_tab = DocumentTab(self)
            new_tab.load_file(tab.file_path)
            new_tab.pageChanged.connect(self._on_tab_page_changed)
            new_tab.zoomChanged.connect(self._on_tab_zoom_changed)
            new_tab.statusMessage.connect(self._on_tab_status_message)
            new_tab.documentModified.connect(self._on_tab_document_modified)
            self._apply_theme_to_tab(new_tab)
            new_tab.viewer.go_to_page(tab.viewer.current_page_idx)
            idx = self.tab_widget.addTab(new_tab, f"{new_tab.display_title} (Cópia)")
            self.tab_widget.setTabToolTip(idx, tab.file_path)
            self.tab_widget.setCurrentIndex(idx)

    def _open_file_folder(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return
        import subprocess
        try:
            subprocess.Popen(['explorer', '/select,', os.path.normpath(file_path)])
        except Exception:
            pass

    def _on_tab_bar_context_menu(self, pos):
        tab_idx = self.tab_widget.tabBar().tabAt(pos)
        if tab_idx < 0:
            return
        tab = self.tab_widget.widget(tab_idx)
        menu = QMenu(self)

        act_close = menu.addAction("✖ Fechar Esta Aba")
        act_close.triggered.connect(lambda: self.close_tab(tab_idx))

        act_close_others = menu.addAction("✖ Fechar Outras Abas")
        act_close_others.triggered.connect(lambda: self.close_other_tabs(tab_idx))

        act_close_all = menu.addAction("✖ Fechar Todas as Abas")
        act_close_all.triggered.connect(self.close_all_tabs)

        menu.addSeparator()

        if isinstance(tab, DocumentTab) and tab.file_path and os.path.exists(tab.file_path):
            act_dup = menu.addAction("📄 Duplicar em Nova Aba")
            act_dup.triggered.connect(lambda: self._duplicate_tab(tab_idx))

            act_folder = menu.addAction("📂 Abrir Pasta no Explorer")
            act_folder.triggered.connect(lambda: self._open_file_folder(tab.file_path))

        menu.exec(self.tab_widget.tabBar().mapToGlobal(pos))

    def _on_tab_changed(self, index):
        tab = self.current_tab
        if tab and tab.doc:
            self.stack.setCurrentWidget(self.tab_widget)
            self.search_bar.set_document(tab.doc)

            total = len(tab.doc)
            curr = tab.viewer.current_page_idx + 1
            self.spin_page.blockSignals(True)
            self.spin_page.setMaximum(max(1, total))
            self.spin_page.setValue(curr)
            self.spin_page.blockSignals(False)
            self.lbl_total_pages.setText(f" / {total} ")

            percent = int(tab.viewer.zoom * 100)
            self.combo_zoom.blockSignals(True)
            self.combo_zoom.setEditText(f"{percent}%")
            self.combo_zoom.blockSignals(False)

            self.btn_sidebar.blockSignals(True)
            self.btn_sidebar.setChecked(tab.sidebar.isVisible())
            self.btn_sidebar.blockSignals(False)

            self._update_window_title()
            self.status_label.setText(f"Aba ativa: {tab.tab_name}")
            self._set_controls_enabled(True)
        else:
            self._on_no_tabs_active()

    def _on_no_tabs_active(self):
        self.stack.setCurrentWidget(self.empty_widget)
        self.search_bar.clear_search()
        self.search_bar.hide()
        self.spin_page.blockSignals(True)
        self.spin_page.setMaximum(1)
        self.spin_page.setValue(1)
        self.spin_page.blockSignals(False)
        self.lbl_total_pages.setText(" / 0 ")
        self.setWindowTitle("Leitor e Editor de PDF")
        self.status_label.setText("Nenhum arquivo aberto")
        self._set_controls_enabled(False)

    def _on_tab_page_changed(self, tab, current_page, total_pages):
        if tab == self.current_tab:
            self.spin_page.blockSignals(True)
            self.spin_page.setValue(current_page)
            self.spin_page.blockSignals(False)
            if tab.file_path:
                if "last_pages" not in self.config:
                    self.config["last_pages"] = {}
                self.config["last_pages"][tab.file_path] = current_page - 1
                self._save_config()

    def _on_tab_zoom_changed(self, tab, zoom):
        if tab == self.current_tab:
            percent = int(zoom * 100)
            self.combo_zoom.blockSignals(True)
            self.combo_zoom.setEditText(f"{percent}%")
            self.combo_zoom.blockSignals(False)

    def _on_tab_status_message(self, tab, msg):
        if tab == self.current_tab:
            self.statusBar().showMessage(msg, 5000)

    def _on_tab_document_modified(self, tab):
        self._update_tab_title(tab)
        if tab == self.current_tab:
            self._update_window_title()

    def _update_tab_title(self, tab):
        idx = self.tab_widget.indexOf(tab)
        if idx >= 0:
            self.tab_widget.setTabText(idx, tab.display_title)
            if tab.file_path:
                self.tab_widget.setTabToolTip(idx, tab.file_path)

    def _update_window_title(self):
        tab = self.current_tab
        if tab and tab.doc:
            fname = tab.tab_name
            mod = "• " if tab.is_modified else ""
            self.setWindowTitle(f"{mod}{fname} - Leitor e Editor de PDF")
        else:
            self.setWindowTitle("Leitor e Editor de PDF")

    def _apply_theme_to_tab(self, tab):
        theme_name = self.config.get("theme", "light")
        is_dark = (theme_name == "dark")
        page_filter = "sepia" if theme_name == "sepia" else "normal"
        tab.viewer.set_ui_theme(is_dark)
        tab.viewer.set_page_filter(page_filter)

    def _set_controls_enabled(self, enabled):
        self.btn_save.setEnabled(enabled)
        self.spin_page.setEnabled(enabled)
        self.combo_zoom.setEnabled(enabled)
        self.btn_sidebar.setEnabled(enabled)

    def closeEvent(self, event):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, DocumentTab) and tab.is_modified and tab.doc:
                self.tab_widget.setCurrentIndex(i)
                fname = tab.tab_name
                reply = QMessageBox.question(
                    self, "Alterações Não Salvas",
                    f"O documento '{fname}' possui alterações não salvas.\nDeseja salvar antes de fechar o aplicativo?",
                    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_tab_document(tab):
                        event.ignore()
                        return
                elif reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return

        # Fecha recursos de todas as abas
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, DocumentTab):
                tab.close_tab()

        event.accept()

    def prompt_export_page_pdf(self, page_idx=None):
        """Exporta uma página específica (ou a página atual) para um arquivo PDF independente"""
        if not self.doc or len(self.doc) == 0:
            QMessageBox.information(self, "Aviso", "Nenhum documento aberto para exportar.")
            return

        target_idx = self.viewer.current_page_idx if page_idx is None else page_idx
        if target_idx < 0 or target_idx >= len(self.doc):
            return

        base_name = "documento"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        suggested_name = f"{base_name}_pagina_{target_idx + 1}.pdf"

        dest_path, _ = QFileDialog.getSaveFileName(
            self, f"Exportar Página {target_idx + 1} como PDF", suggested_name, "Arquivos PDF (*.pdf)"
        )
        if dest_path:
            if self.viewer.export_page_as_pdf(target_idx, dest_path):
                self.statusBar().showMessage(f"Página {target_idx + 1} exportada para '{os.path.basename(dest_path)}'!", 5000)
                QMessageBox.information(self, "Sucesso", f"Página {target_idx + 1} exportada com sucesso como PDF!")

    def prompt_export_page_image(self, page_idx=None):
        """Exporta uma página específica (ou a página atual) como arquivo de imagem (PNG/JPG)"""
        if not self.doc or len(self.doc) == 0:
            QMessageBox.information(self, "Aviso", "Nenhum documento aberto para exportar.")
            return

        target_idx = self.viewer.current_page_idx if page_idx is None else page_idx
        if target_idx < 0 or target_idx >= len(self.doc):
            return

        base_name = "documento"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        suggested_name = f"{base_name}_pagina_{target_idx + 1}.png"

        dest_path, selected_filter = QFileDialog.getSaveFileName(
            self, f"Exportar Página {target_idx + 1} como Imagem", suggested_name,
            "Imagem PNG (*.png);;Imagem JPEG (*.jpg *.jpeg)"
        )
        if dest_path:
            if self.viewer.export_page_as_image(target_idx, dest_path, dpi=200):
                self.statusBar().showMessage(f"Página {target_idx + 1} exportada como imagem!", 5000)
                QMessageBox.information(self, "Sucesso", f"Página {target_idx + 1} exportada com sucesso como imagem!")

    def prompt_split_pages(self):
        """Abre o diálogo avançado para separar páginas, extrair intervalo ou exportar todas"""
        if not self.doc or len(self.doc) == 0:
            QMessageBox.information(self, "Aviso", "Nenhum documento aberto para separar páginas.")
            return

        dlg = SplitPagesDialog(len(self.doc), self.viewer.current_page_idx, parent=self)
        if dlg.exec() == SplitPagesDialog.DialogCode.Accepted:
            pages = dlg.get_pages()
            mode = dlg.get_output_mode()
            base_name = "documento"
            if self.current_file_path:
                base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]

            if mode == "single_pdf":
                suggested_name = f"{base_name}_extracao_{len(pages)}pags.pdf"
                dest_path, _ = QFileDialog.getSaveFileName(
                    self, "Salvar Páginas em Novo PDF", suggested_name, "Arquivos PDF (*.pdf)"
                )
                if dest_path:
                    if self.viewer.export_pages_as_pdf(pages, dest_path):
                        self.statusBar().showMessage("Páginas exportadas com sucesso!", 5000)
                        QMessageBox.information(
                            self, "Sucesso",
                            f"Foram exportadas {len(pages)} página(s) para o arquivo:\n{dest_path}"
                        )

            elif mode == "split_multiple":
                dest_dir = QFileDialog.getExistingDirectory(
                    self, "Selecione a Pasta de Destino para as Páginas Separadas"
                )
                if dest_dir:
                    count = self.viewer.split_pages_to_folder(pages, dest_dir, base_name=base_name)
                    self.statusBar().showMessage(f"{count} páginas separadas salvas com sucesso!", 5000)
                    QMessageBox.information(
                        self, "Sucesso",
                        f"{count} arquivo(s) PDF individual(is) gerado(s) com sucesso na pasta:\n{dest_dir}"
                    )

            elif mode == "images":
                img_fmt, dpi = dlg.get_image_options()
                if len(pages) == 1:
                    pno = pages[0]
                    suggested_name = f"{base_name}_pag_{pno + 1}.{img_fmt}"
                    dest_path, _ = QFileDialog.getSaveFileName(
                        self, "Salvar Imagem da Página", suggested_name,
                        f"Imagem {img_fmt.upper()} (*.{img_fmt})"
                    )
                    if dest_path:
                        if self.viewer.export_page_as_image(pno, dest_path, dpi=dpi):
                            self.statusBar().showMessage("Imagem exportada com sucesso!", 5000)
                            QMessageBox.information(self, "Sucesso", "Imagem da página exportada com sucesso!")
                else:
                    dest_dir = QFileDialog.getExistingDirectory(
                        self, "Selecione a Pasta de Destino para as Imagens"
                    )
                    if dest_dir:
                        count = self.viewer.export_pages_as_images(
                            pages, dest_dir, base_name=base_name, img_format=img_fmt, dpi=dpi
                        )
                        self.statusBar().showMessage(f"{count} imagens salvas com sucesso!", 5000)
                        QMessageBox.information(
                            self, "Sucesso",
                            f"{count} imagem(ns) exportada(s) com sucesso na pasta:\n{dest_dir}"
                        )

    def prompt_import_pdf(self, insert_at=None):
        """Abre diálogo para importar páginas de outro arquivo PDF"""
        curr_idx = self.viewer.current_page_idx if self.doc else 0
        total_p = len(self.doc) if self.doc else 0

        dlg = ImportPdfDialog(curr_idx, total_p, parent=self)
        if dlg.exec() == ImportPdfDialog.DialogCode.Accepted:
            src_file, pages_to_import, target_pos = dlg.get_data()
            if insert_at is not None:
                target_pos = insert_at

            if not self.doc:
                if pages_to_import is None:
                    self.open_pdf_file(src_file)
                    return
                else:
                    self.doc = pymupdf.open()
                    self.current_file_path = None
                    self.viewer.load_document(self.doc)

            success = self.viewer.insert_pdf_pages(src_file, target_pos, pages_to_import)
            if success:
                self._sync_ui_after_pages_changed()

    def prompt_import_image(self, insert_at=None):
        """Abre diálogo para importar uma ou mais imagens como novas páginas do documento"""
        curr_idx = self.viewer.current_page_idx if self.doc else 0
        total_p = len(self.doc) if self.doc else 0

        dlg = ImportImageDialog(curr_idx, total_p, parent=self)
        if dlg.exec() == ImportImageDialog.DialogCode.Accepted:
            images, target_pos, fit_to_a4 = dlg.get_data()
            if insert_at is not None:
                target_pos = insert_at

            if not self.doc:
                self.doc = pymupdf.open()
                self.current_file_path = None
                self.viewer.load_document(self.doc)

            success = self.viewer.insert_image_pages(images, target_pos, fit_to_a4=fit_to_a4)
            if success:
                self._sync_ui_after_pages_changed()

    def _prompt_rotate_specific_page(self, page_idx):
        if not self.doc or page_idx < 0 or page_idx >= len(self.doc):
            return
        self.viewer.rotate_specific_page_permanent(page_idx, 90)
        self.sidebar.load_document(self.doc)

    def _prompt_delete_specific_page(self, page_idx):
        if not self.doc or page_idx < 0 or page_idx >= len(self.doc):
            return
        reply = QMessageBox.question(
            self, "Excluir Página",
            f"Deseja realmente excluir permanentemente a Página {page_idx + 1} do documento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.viewer.delete_specific_page(page_idx):
                self._sync_ui_after_pages_changed()

    def _prompt_delete_page(self):
        self._prompt_delete_specific_page(self.viewer.current_page_idx)

    def _prompt_rotate_page_perm(self):
        self._prompt_rotate_specific_page(self.viewer.current_page_idx)

    def _sync_ui_after_pages_changed(self):
        """Sincroniza os contadores, sidebar e busca após adicionar ou remover páginas"""
        if not self.doc:
            return
        total = len(self.doc)
        curr = self.viewer.current_page_idx + 1
        self.spin_page.blockSignals(True)
        self.spin_page.setMaximum(max(1, total))
        self.spin_page.setValue(curr)
        self.spin_page.blockSignals(False)
        self.lbl_total_pages.setText(f" / {total} ")
        self.sidebar.load_document(self.doc)
        self.search_bar.set_document(self.doc)
        self.is_modified = True
        self._update_window_title()

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
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(1)
            self.combo_theme.blockSignals(False)
        elif theme_name == "sepia":
            self.setStyleSheet(LIGHT_THEME)
            self.search_bar.setStyleSheet(SEARCH_BAR_STYLE)
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(2)
            self.combo_theme.blockSignals(False)
        else:  # light
            self.setStyleSheet(LIGHT_THEME)
            self.search_bar.setStyleSheet(SEARCH_BAR_STYLE)
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(0)
            self.combo_theme.blockSignals(False)

        # Atualiza todas as abas abertas
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, DocumentTab):
                self._apply_theme_to_tab(tab)

    # Suporte a Arrastar e Soltar (Drag & Drop)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        opened_any = False
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf") and os.path.exists(file_path):
                if self.open_pdf_file(file_path):
                    opened_any = True
        if opened_any:
            event.acceptProposedAction()

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

    initial_files = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            cleaned_arg = arg.strip('\"\'')
            if os.path.isfile(cleaned_arg) or cleaned_arg.lower().endswith(".pdf"):
                initial_files.append(os.path.abspath(cleaned_arg))
    
    window = PDFReaderMainWindow(initial_files if initial_files else None)
    if app_icon:
        window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

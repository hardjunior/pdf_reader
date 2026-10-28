"""
Estilos e Temas de Alto Contraste da Interface do Leitor e Editor de PDF
Garante legibilidade perfeita em qualquer configuração do Windows (Dark Mode ou Light Mode)
"""

import sys
import os

def get_icon_path(rel_path):
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel_path).replace('\\', '/')

def get_light_theme():
    icon_close = get_icon_path("icons/close_tab_light.svg")
    icon_white = get_icon_path("icons/close_tab_white.svg")
    return f"""
/* === TEMA CLARO DE ALTO CONTRASTE === */

QWidget {{
    color: #0f172a;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: #f1f5f9;
}}

/* Barra de Menus */
QMenuBar {{
    background-color: #ffffff;
    color: #0f172a;
    border-bottom: 1px solid #cbd5e1;
    padding: 3px 6px;
    font-weight: 500;
}}

QMenuBar::item {{
    background-color: transparent;
    color: #0f172a;
    padding: 5px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: #e2e8f0;
    color: #0284c7;
}}

/* Menus Suspensos */
QMenu {{
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
    color: #0f172a;
}}

QMenu::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}

QMenu::item:disabled {{
    color: #94a3b8;
}}

QMenu::separator {{
    height: 1px;
    background-color: #e2e8f0;
    margin: 4px 6px;
}}

/* Barras de Ferramentas */
QToolBar {{
    background-color: #ffffff;
    border-bottom: 1px solid #cbd5e1;
    spacing: 4px;
    padding: 4px 6px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: #cbd5e1;
    margin: 4px 5px;
}}

/* Botões da Barra de Ferramentas */
QToolButton {{
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 4px 8px;
    color: #0f172a;
    font-weight: 600;
    font-size: 12px;
}}

QToolButton:hover {{
    background-color: #e2e8f0;
    border-color: #94a3b8;
    color: #0284c7;
}}

QToolButton:pressed {{
    background-color: #cbd5e1;
}}

QToolButton:checked {{
    background-color: #2563eb;
    border: 1px solid #1d4ed8;
    color: #ffffff;
}}

QToolButton::menu-indicator {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    right: 2px;
}}

/* Caixas de Texto, SpinBox e ComboBox */
QComboBox, QLineEdit, QSpinBox, QTextEdit {{
    background-color: #ffffff;
    border: 1px solid #94a3b8;
    border-radius: 4px;
    padding: 4px 8px;
    color: #0f172a;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}}

QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QTextEdit:hover {{
    border-color: #2563eb;
}}

QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
    border: 1.5px solid #2563eb;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}}

/* Barra de Status */
QStatusBar {{
    background-color: #ffffff;
    border-top: 1px solid #cbd5e1;
    color: #1e293b;
    font-size: 12px;
    font-weight: 500;
    padding: 3px;
}}

QLabel {{
    color: #0f172a;
}}

/* Painel Lateral / Abas */
QTabWidget::pane {{
    border: 1px solid #cbd5e1;
    background: #ffffff;
}}

QTabBar::tab {{
    background: #e2e8f0;
    border: 1px solid #cbd5e1;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #334155;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background: #cbd5e1;
    color: #0f172a;
}}

QTabBar::tab:selected {{
    background: #ffffff;
    border-bottom-color: #ffffff;
    color: #2563eb;
    font-weight: bold;
}}

QTabBar::close-button {{
    image: url("{icon_close}");
    subcontrol-position: right;
    subcontrol-origin: padding;
    margin-left: 6px;
    padding: 3px;
    border-radius: 3px;
}}

QTabBar::close-button:hover {{
    image: url("{icon_white}");
    background-color: #ef4444;
}}

QTabWidget QToolButton {{
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 3px 6px;
    font-weight: bold;
}}

QTabWidget QToolButton:hover {{
    background-color: #e2e8f0;
    color: #2563eb;
}}

QTreeWidget, QListWidget {{
    background-color: #ffffff;
    border: none;
    outline: none;
    color: #0f172a;
}}

QTreeWidget::item, QListWidget::item {{
    padding: 6px;
    border-radius: 4px;
    color: #0f172a;
}}

QTreeWidget::item:hover, QListWidget::item:hover {{
    background-color: #f1f5f9;
}}

QTreeWidget::item:selected, QListWidget::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}

/* Botões Padrão (Diálogos) */
QPushButton {{
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 6px 14px;
    color: #0f172a;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #e2e8f0;
    border-color: #94a3b8;
}}

QPushButton:pressed {{
    background-color: #cbd5e1;
}}

/* Barras de Rolagem */
QScrollBar:vertical, QScrollBar:horizontal {{
    border: none;
    background: #f1f5f9;
    width: 12px;
    height: 12px;
    margin: 0px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: #94a3b8;
    min-height: 25px;
    min-width: 25px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:hover {{
    background: #64748b;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0px;
    width: 0px;
}}

/* Divisores de Janela */
QSplitter::handle {{
    background-color: #cbd5e1;
}}

QSplitter::handle:hover {{
    background-color: #2563eb;
}}
"""

def get_dark_theme():
    icon_close = get_icon_path("icons/close_tab_dark.svg")
    icon_white = get_icon_path("icons/close_tab_white.svg")
    return f"""
/* === TEMA ESCURO DE ALTO CONTRASTE === */

QWidget {{
    color: #f8fafc;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: #0f172a;
}}

/* Barra de Menus */
QMenuBar {{
    background-color: #1e293b;
    color: #f8fafc;
    border-bottom: 1px solid #334155;
    padding: 3px 6px;
    font-weight: 500;
}}

QMenuBar::item {{
    background-color: transparent;
    color: #f8fafc;
    padding: 5px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: #334155;
    color: #38bdf8;
}}

/* Menus Suspensos */
QMenu {{
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
    color: #f8fafc;
}}

QMenu::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}

QMenu::item:disabled {{
    color: #64748b;
}}

QMenu::separator {{
    height: 1px;
    background-color: #334155;
    margin: 4px 6px;
}}

/* Barras de Ferramentas */
QToolBar {{
    background-color: #1e293b;
    border-bottom: 1px solid #334155;
    spacing: 4px;
    padding: 4px 6px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: #334155;
    margin: 4px 5px;
}}

/* Botões da Barra de Ferramentas */
QToolButton {{
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 4px 8px;
    color: #f8fafc;
    font-weight: 600;
    font-size: 12px;
}}

QToolButton:hover {{
    background-color: #334155;
    border-color: #64748b;
    color: #38bdf8;
}}

QToolButton:pressed {{
    background-color: #1e293b;
}}

QToolButton:checked {{
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
}}

QToolButton::menu-indicator {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    right: 2px;
}}

/* Caixas de Texto, SpinBox e ComboBox */
QComboBox, QLineEdit, QSpinBox, QTextEdit {{
    background-color: #0f172a;
    border: 1px solid #475569;
    border-radius: 4px;
    padding: 4px 8px;
    color: #f8fafc;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}}

QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QTextEdit:hover {{
    border-color: #38bdf8;
}}

QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QTextEdit:focus {{
    border: 1.5px solid #38bdf8;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}}

/* Barra de Status */
QStatusBar {{
    background-color: #1e293b;
    border-top: 1px solid #334155;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 500;
    padding: 3px;
}}

QLabel {{
    color: #f8fafc;
}}

/* Painel Lateral / Abas */
QTabWidget::pane {{
    border: 1px solid #334155;
    background: #0f172a;
}}

QTabBar::tab {{
    background: #1e293b;
    border: 1px solid #334155;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #94a3b8;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background: #334155;
    color: #f8fafc;
}}

QTabBar::tab:selected {{
    background: #0f172a;
    border-bottom-color: #0f172a;
    color: #38bdf8;
    font-weight: bold;
}}

QTabBar::close-button {{
    image: url("{icon_close}");
    subcontrol-position: right;
    subcontrol-origin: padding;
    margin-left: 6px;
    padding: 3px;
    border-radius: 3px;
}}

QTabBar::close-button:hover {{
    image: url("{icon_white}");
    background-color: #ef4444;
}}

QTabWidget QToolButton {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 3px 6px;
    color: #f8fafc;
    font-weight: bold;
}}

QTabWidget QToolButton:hover {{
    background-color: #334155;
    color: #38bdf8;
}}

QTreeWidget, QListWidget {{
    background-color: #0f172a;
    border: none;
    outline: none;
    color: #f8fafc;
}}

QTreeWidget::item, QListWidget::item {{
    padding: 6px;
    border-radius: 4px;
    color: #f8fafc;
}}

QTreeWidget::item:hover, QListWidget::item:hover {{
    background-color: #1e293b;
}}

QTreeWidget::item:selected, QListWidget::item:selected {{
    background-color: #2563eb;
    color: #ffffff;
}}

/* Botões Padrão (Diálogos) */
QPushButton {{
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 6px 14px;
    color: #f8fafc;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #334155;
    border-color: #64748b;
}}

QPushButton:pressed {{
    background-color: #0f172a;
}}

/* Barras de Rolagem */
QScrollBar:vertical, QScrollBar:horizontal {{
    border: none;
    background: #0f172a;
    width: 12px;
    height: 12px;
    margin: 0px;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: #334155;
    min-height: 25px;
    min-width: 25px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:hover {{
    background: #475569;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0px;
    width: 0px;
}}

/* Divisores de Janela */
QSplitter::handle {{
    background-color: #334155;
}}

QSplitter::handle:hover {{
    background-color: #38bdf8;
}}
"""

LIGHT_THEME = get_light_theme()
DARK_THEME = get_dark_theme()

SEARCH_BAR_STYLE = """
QFrame#search_bar_frame {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
}
QLabel {
    color: #0f172a;
    font-weight: 600;
}
"""

SEARCH_BAR_DARK_STYLE = """
QFrame#search_bar_frame {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px 10px;
}
QLabel {
    color: #f8fafc;
    font-weight: 600;
}
"""

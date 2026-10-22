"""
Gera um arquivo PDF de exemplo para testes do leitor
"""

import os
import pymupdf

def create_sample_pdf(filename="exemplo_documento.pdf"):
    out_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(out_dir, filename)
    doc = pymupdf.open()

    # Página 1: Capa e Introdução
    p1 = doc.new_page(width=595, height=842)  # A4
    p1.insert_text((72, 100), "Manual do Leitor de PDF em Python", fontsize=24, color=(0.1, 0.2, 0.5))
    p1.insert_text((72, 140), "Versão 1.0 - Inspirado no Adobe Acrobat Reader", fontsize=14, color=(0.4, 0.4, 0.4))
    
    intro_text = (
        "Bem-vindo ao seu novo Leitor de PDF desenvolvido em Python!\n\n"
        "Este aplicativo foi construído utilizando as seguintes tecnologias de ponta:\n"
        "• PyQt6: Para interface gráfica moderna, fluida e responsiva.\n"
        "• PyMuPDF (fitz): Motor C de altíssimo desempenho para renderização de PDFs.\n\n"
        "Recursos disponíveis no leitor:\n"
        "1. Miniaturas laterais interativas (Thumbnails) carregadas em segundo plano.\n"
        "2. Árvore de Marcadores (Sumário / TOC) navegável.\n"
        "3. Ferramenta de busca com destaque colorido e contagem de ocorrências.\n"
        "4. Modos de leitura: Claro, Noturno (Dark Mode) e Sépia.\n"
        "5. Atalhos de teclado familiares do Adobe Reader (Ctrl+O, Ctrl+F, Ctrl++, Ctrl+-, F4, etc.).\n"
        "6. Rotação de página (horária e anti-horária).\n"
        "7. Arrastar e soltar (Drag and drop) arquivos PDF diretamente na janela."
    )
    p1.insert_textbox(pymupdf.Rect(72, 180, 523, 700), intro_text, fontsize=12, color=(0.15, 0.15, 0.15))

    # Página 2: Atalhos e Recursos
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((72, 80), "Capítulo 1: Atalhos e Navegação", fontsize=20, color=(0.1, 0.2, 0.5))
    
    shortcuts_text = (
        "Tabela de Atalhos de Teclado:\n\n"
        "• Ctrl + O : Abrir novo documento PDF\n"
        "• Ctrl + F : Abrir a barra de pesquisa rápida\n"
        "• Enter / Shift+Enter : Próxima / Anterior ocorrência na busca\n"
        "• Ctrl + + / Ctrl + - : Mais Zoom / Menos Zoom\n"
        "• Ctrl + 0 : Tamanho real (100%)\n"
        "• Ctrl + 1 : Ajustar largura da folha à janela\n"
        "• Ctrl + 2 : Ajustar página inteira\n"
        "• Ctrl + R : Rotacionar 90 graus no sentido horário\n"
        "• Ctrl + Shift + R : Rotacionar 90 graus no sentido anti-horário\n"
        "• F4 : Mostrar / ocultar o painel lateral de miniaturas\n"
        "• F11 : Alternar modo tela cheia\n"
        "• Home / End : Ir para primeira / última página\n"
        "• PageUp / PageDown : Navegar entre páginas\n"
        "• Ctrl + Roda do Mouse : Zoom dinâmico"
    )
    p2.insert_textbox(pymupdf.Rect(72, 120, 523, 700), shortcuts_text, fontsize=12, color=(0.15, 0.15, 0.15))

    # Página 3: Teste de Busca e Conclusão
    p3 = doc.new_page(width=595, height=842)
    p3.insert_text((72, 80), "Capítulo 2: Testes de Busca de Texto", fontsize=20, color=(0.1, 0.2, 0.5))

    search_test_text = (
        "Este parágrafo contém palavras repetidas para testar a busca do leitor:\n\n"
        "O contrato foi assinado digitalmente. Todas as cláusulas do contrato devem ser "
        "respeitadas de acordo com os termos estabelecidos no presente contrato.\n\n"
        "Experimente pressionar Ctrl+F e buscar pela palavra 'contrato'. "
        "Você verá a contagem exata (ex: '1 de 3') e os destaques em amarelo e laranja!\n\n"
        "Também teste selecionar texto com o botão esquerdo do mouse para copiar "
        "usando o menu de contexto do botão direito."
    )
    p3.insert_textbox(pymupdf.Rect(72, 120, 523, 700), search_test_text, fontsize=12, color=(0.15, 0.15, 0.15))

    # Definir Sumário / Marcadores (TOC)
    toc = [
        [1, "Capa e Introdução", 1],
        [1, "Capítulo 1: Atalhos e Navegação", 2],
        [1, "Capítulo 2: Testes de Busca", 3],
    ]
    doc.set_toc(toc)

    # Metadados do documento
    doc.set_metadata({
        "title": "Documento de Demonstração",
        "author": "Leitor PDF Python",
        "subject": "Demonstração de Leitor de PDF estilo Adobe Reader",
        "keywords": "PDF, Python, PyQt6, PyMuPDF, Adobe",
        "creator": "Python PDF Engine",
        "producer": "PyMuPDF"
    })

    doc.save(file_path)
    doc.close()
    print(f"PDF de teste gerado com sucesso: {file_path}")

if __name__ == "__main__":
    create_sample_pdf()

# 📄 Leitor e Editor de PDF em Python (Estilo Adobe Acrobat Pro)

Um visualizador e editor de documentos PDF desktop moderno, fluido e de alto desempenho construído com **Python**, **PyQt6** e o motor **PyMuPDF (fitz)**.

---

## 🚀 Como Iniciar

### 1. Início Rápido (Executável Direto no Windows)
Basta dar um duplo clique no arquivo:
```
LeitorPDF.exe
```
*(Ele é 100% autônomo, não precisa de terminal e abre qualquer PDF com duplo clique).*

### 2. Pelo Terminal (PowerShell / CMD)
```powershell
D:\Projetos\python\pdf_reader\LeitorPDF.exe "caminho\para\seu_arquivo.pdf"
```

---

## 🛠️ Recursos de Edição e CRUD de Texto

### 1. ✍️ Adicionar Texto (Create)
* Ative o botão **✍️ Adicionar Texto** na barra superior e clique em qualquer lugar da folha.
* Um diálogo intuitivo permite definir o texto, tamanho da fonte (pt), cor do texto e cor de fundo.
* O texto inserido torna-se uma caixa interativa padrão PDF.

### 2. ✏️ Editar Texto Existente (Update)
* **Texto Adicionado:** Clique com o botão direito sobre qualquer texto adicionado anteriormente e escolha **"✏️ Editar este Texto..."** para alterar seu conteúdo, fonte ou cor.
* **Texto Original do Documento:** Selecione qualquer trecho de texto com o mouse, clique com o botão direito e escolha **"✏️ Substituir Texto Selecionado..."**. O sistema remove o texto antigo de forma limpa e insere o novo texto no mesmo local!

### 3. 🧹 Apagar / Deletar Texto (Delete)
* **Apagar Caixa de Texto:** Clique com o botão direito sobre o texto adicionado e selecione **"🗑️ Apagar este Texto"**.
* **Borracha de Conteúdo Original:** Ative a ferramenta **🧹 Borracha / Apagar** na barra e arraste um retângulo sobre qualquer texto, imagem ou elemento original do PDF. O conteúdo é removido permanentemente!
* **Apagar Seleção:** Selecione texto com o mouse, clique com botão direito e escolha **"🧹 Apagar Texto Selecionado (Borracha)"**.

### 4. 🖍️ Marca-Texto (Highlighter)
* Selecione a ferramenta **🖍️ Marca-Texto** e arraste sobre o trecho que deseja realçar em amarelo, ou selecione o texto com o mouse e clique com o botão direito > **"Destacar com Marca-Texto"**.

### 5. ✒️ Inserir Assinatura ou Carimbo
* Ative a ferramenta **✒️ Inserir Assinatura/Imagem** e clique no local da folha onde deseja aplicá-la.
* Selecione uma imagem (PNG, JPG, BMP) com fundo transparente ou carimbo digitalizado. Ela será ajustada e gravada no PDF.

### 6. 📑 Gerenciamento, Importação e Exportação de Páginas

* **✂️ Separar / Dividir Páginas (Split PDF):**
  * Acesse via **Menu Páginas > Separar / Dividir Páginas**, ou pelo botão **✂️ Separar/Exportar** na barra de ferramentas, ou clicando com botão direito na miniatura.
  * Permite:
    * **Separar cada página em um arquivo individual** (1 PDF por página) salvando todos em uma pasta escolhida.
    * **Extrair intervalo específico de páginas** (ex: `1-3, 5, 8-10`) em um novo arquivo PDF consolidado.
    * **Exportar páginas como imagens** (PNG ou JPEG) em alta resolução (150 DPI ou 300 DPI).

* **📤 Exportar Página Atual:**
  * **Como PDF:** Salva a página exibida no momento como um arquivo PDF independente em apenas um clique.
  * **Como Imagem:** Salva a página atual em alta definição como arquivo `.png` ou `.jpg`.

* **➕ Importar Páginas de Arquivo PDF (Ficheiro):**
  * Acesse via **Menu Páginas > Importar Páginas de Arquivo PDF...** ou pelo botão **➕ Importar**.
  * Permite importar todas as páginas ou um intervalo específico (`1-5`, `2, 4`) de outro PDF.
  * Escolha a posição de inserção: antes da página atual, depois da página atual, no início ou no fim do documento.

* **🖼️ Importar Imagem como Nova Página:**
  * Acesse via **Menu Páginas > Importar Imagem como Nova Página...** ou pelo botão **➕ Importar**.
  * Suporta formatos PNG, JPG, JPEG, BMP e WebP, inclusive com **seleção múltipla** de fotos/documentos escaneados simultaneamente.
  * Escolha entre ajustar automaticamente para **folha A4** (com detecção inteligente de orientação retrato/paisagem) ou manter as **dimensões originais 1:1**.

* **📑 Menu de Contexto nas Miniaturas:**
  * Clique com o **botão direito do mouse em qualquer miniatura** no painel lateral esquerdo para acessar rapidamente ações como: exportar aquela página em PDF/imagem, inserir outro PDF ou imagem naquele ponto, girar ou excluir.

* **🗑️ Excluir e Girar Páginas:**
  * **Excluir Página:** Clique em **🗑️ Excluir Página** para remover permanentemente a folha selecionada.
  * **Girar Permanente:** Clique em **↻ Girar Página Permanente** para salvar a nova orientação (90°, 180°, 270°).

### 7. 📑 Múltiplas Abas de Documentos (Interface Multi-Tab)

O leitor conta com suporte nativo a **múltiplas abas**, permitindo abrir, visualizar e editar vários documentos simultaneamente na mesma janela:

* **➕ Abrir em Nova Aba (`Ctrl + T`):** Selecione um ou vários arquivos PDF simultaneamente para abri-los em abas separadas, ou clique no botão `＋` no canto direito da barra de abas.
* **✖ Fechar Aba Atual (`Ctrl + W`):** Fecha a aba ativa com proteção contra perda de dados (aviso para salvar se houver alterações não salvas).
* **✖✖ Fechar Todas as Abas (`Ctrl + Shift + W`):** Fecha todas as abas abertas de forma segura.
* **⇆ Alternância Rápida:** Navegue entre abas com `Ctrl + Tab` e `Ctrl + Shift + Tab`, ou reordene as abas livremente arrastando com o mouse.
* **🖱️ Menu de Contexto na Barra de Abas (Botão Direito):**
  * *Fechar Aba*
  * *Fechar Outras Abas*
  * *Duplicar em Nova Aba* (ótimo para comparar partes diferentes do mesmo documento)
  * *Abrir Pasta do Arquivo* (destaca o arquivo diretamente no Explorador do Windows)
* **Independência Total de Estado:** Cada aba gerencia seu próprio arquivo, miniaturas, sumário, nível de zoom, rotação e controle de modificação (`•`).
* **Tela de Boas-Vindas Dinâmica:** Ao fechar todas as abas, uma tela moderna com atalhos rápidos ("Abrir Arquivo PDF" e "Criar a partir de Imagens") é exibida automaticamente.

### 8. 💾 Salvar Alterações
* Pressione **`Ctrl + S`** para salvar diretamente no arquivo aberto (salvamento atômico e seguro).
* Pressione **`Ctrl + Shift + S`** para salvar uma nova cópia do PDF modificado.
* O aplicativo detecta alterações pendentes e exibe um ponto (`•`) no título, além de avisar caso tente fechar sem salvar.

---

## 🔍 Recursos de Leitura e Visualização

* **Renderização High-DPI:** Textos nítidos em monitores Full HD, 4K e telas com escala.
* **Controles de Zoom:** Zoom dinâmico (`Ctrl + Roda`), 100% (`Ctrl + 0`), Ajustar à Largura (`Ctrl + 1`), Ajustar Página (`Ctrl + 2`).
* **Painel Lateral (`F4`):** Miniaturas de página (Thumbnails) e Árvore de Marcadores (Sumário/TOC) clicáveis.
* **Busca Rápida (`Ctrl + F`):** Contagem em tempo real (*"1 de 14"*) com destaque amarelo para todas e laranja para a atual.
* **Modos de Visualização:** Modo Claro, Noturno (Dark Mode) e Sépia (confortável para os olhos).

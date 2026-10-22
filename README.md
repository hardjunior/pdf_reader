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

### 6. 🗑️ Gerenciamento de Páginas
* **Excluir Página:** Clique em **🗑️ Excluir Página** na barra de ferramentas para remover permanentemente a página ativa.
* **Girar Permanente:** Clique em **↻ Girar Página Permanente** para alterar e salvar o ângulo de orientação da página (90°, 180°, 270°).

### 7. 💾 Salvar Alterações
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

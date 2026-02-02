# Playground Streamlit

Este repositório contém um playground simples em Streamlit para explorar datasets e criar visualizações interativas.

Como usar

1. Crie um ambiente virtual (recomendado).

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

2. Rode o app Streamlit:

```powershell
streamlit run app.py
```

Funcionalidades

- Seleção de datasets de exemplo (`Iris`, `Tips`, `Penguins`).
- Upload de CSV pelo painel lateral.
- Visualização interativa com Plotly (scatter, histograma, linha).
- Exibição de primeiras linhas, estatísticas básicas e contagem de nulos.

- Upload e extração de PDFs/TXT: extração de texto completo e tabelas presentes nas páginas (download em CSV).
- Upload e OCR de imagens (PNG, JPG, BMP, GIF, TIFF): extração de texto direto com Tesseract OCR, download em TXT.

Observações

- Se `penguins` não carregar, instale/atualize `seaborn` para a versão que inclui esse dataset.
- Este playground não executa código arbitrário do usuário — serve como ambiente seguro para explorar dados e gráficos.

PDF / TXT

- No painel lateral selecione `Upload PDF / TXT` e envie um arquivo PDF ou TXT.
- Para `TXT` o conteúdo será exibido como texto.
- Para `PDF` o app usa OCR (se ativado) ou extração tradicional. Tabelas extraídas aparecem como tabelas interativas e podem ser baixadas em CSV.

Imagens

- No painel lateral selecione `Upload Imagens` e arraste uma imagem (PNG, JPG, BMP, GIF, TIFF).
- O app exibe a imagem e extrai texto com OCR.
- O texto extraído pode ser baixado em TXT.

Limitações

- A extração funciona melhor em PDFs com texto pesquisável (não imagens). Para PDFs digitalizados (imagens) é necessário adicionar OCR (ex.: `pytesseract`) — posso ajudar a integrar isso se desejar.
- Atualmente suportamos PDF e TXT; suporte a `docx` pode ser adicionado mediante solicitação.
 
OCR (PDFs digitalizados)

- O app agora tem suporte opcional de OCR. Nas opções laterais marque `Ativar OCR para PDFs` para que o app tente extrair texto de imagens dentro do PDF.
- Dependências necessárias:
	- Python: `pytesseract`, `pdf2image`, `Pillow` (estão listadas em `requirements.txt`).
	- Sistema (Windows):
		- Tesseract OCR: instale o binário do Tesseract e adicione-o ao `PATH` (ex.: instale o instalador do Tesseract e reinicie o terminal).
		- Poppler: necessário para `pdf2image` (baixe o binário do Poppler for Windows e adicione o diretório `bin` ao `PATH`).

Instalação no Windows (resumo):

1. Instale Tesseract: baixe o instalador em https://github.com/tesseract-ocr/tesseract (ou https://digi.bib.uni-mannheim.de/tesseract/) e instale. Adicione o caminho do executável (`tesseract.exe`) ao `PATH`.
2. Instale Poppler: baixe um build do Poppler para Windows (ex.: `poppler-win32` / `poppler-xx`), extraia e adicione o diretório `bin` ao `PATH`.
3. No projeto, instale as dependências Python:

```powershell
pip install -r requirements.txt
```

Notas sobre qualidade OCR

- `pdf2image` às vezes produz imagens de baixa qualidade dependendo do PDF e das opções de DPI; aumentar `dpi` ajuda, mas aumenta o tempo de processamento.
- OCR extrai texto melhor que tabelas; extração de tabelas a partir de imagens é menos robusta e pode exigir ferramentas especializadas (ex.: `camelot`/`tabula` combinadas com pré-processamento ou serviços OCR comerciais).
- Se quiser, eu adiciono heurísticas de pré-processamento das imagens (binarização, deskew, remoção de ruído) para melhorar resultados do OCR.

Formatos suportados

- **CSV**: upload simples, visualização e análise interativa.
- **TXT**: exibição de conteúdo.
- **PDF**: extração de texto (OCR ou tradicional), tabelas (download em CSV).
- **Imagens** (PNG, JPG, JPEG, BMP, GIF, TIFF): OCR com extração de texto (download em TXT).

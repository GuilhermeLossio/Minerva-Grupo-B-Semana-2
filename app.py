import io
import streamlit as st
import pandas as pd
import seaborn as sns
import plotly.express as px

# --- Configuração de OCR (PyTesseract e Poppler) ---
# Descomente e ajuste os caminhos se o Tesseract ou Poppler não estiverem no PATH do sistema.
# Isso é comumente necessário no Windows.

# Caminho para o executável do Tesseract OCR
# Exemplo no Windows: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
tesseract_path = None 

# Caminho para o diretório 'bin' do Poppler
# Exemplo no Windows: r"C:\path\to\poppler-23.11.0\Library\bin"
poppler_path = None

try:
	import pdfplumber
except Exception:
	pdfplumber = None
try:
	from pdf2image import convert_from_bytes
except Exception:
	convert_from_bytes = None
try:
	import pytesseract
except Exception:
	pytesseract = None


@st.cache_data
def load_dataset(name: str):
	if name == "Iris":
		return sns.load_dataset("iris")
	if name == "Tips":
		return sns.load_dataset("tips")
	if name == "Penguins":
		try:
			return sns.load_dataset("penguins")
		except Exception:
			return pd.DataFrame()
	return pd.DataFrame()


def main():
	st.set_page_config(page_title="Playground Streamlit", layout="wide")
	st.title("Playground Streamlit — Minerva Grupo B")

	st.sidebar.header("Configurações")
	dataset_choice = st.sidebar.selectbox("Fonte de dados", ["Iris", "Tips", "Penguins", "Upload CSV", "Upload PDF / TXT", "Upload Imagens"])
	chart_type = st.sidebar.selectbox("Tipo de gráfico", ["Scatter", "Histogram", "Line"])
	# OCR options
	ocr_enabled = st.sidebar.checkbox("Ativar OCR para PDFs (requer Tesseract + Poppler)", value=False)
	ocr_force = st.sidebar.checkbox("Forçar OCR mesmo se texto pesquisável", value=False)
	ocr_lang = st.sidebar.text_input("Idioma Tesseract (ex: eng, por)", value="por")
	show_stats = st.sidebar.checkbox("Mostrar estatísticas básicas", value=True)
	show_head = st.sidebar.checkbox("Mostrar primeiras linhas", value=True)

	if dataset_choice == "Upload CSV":
		uploaded = st.sidebar.file_uploader("Envie um arquivo CSV", type=["csv"] )
		if uploaded is not None:
			try:
				df = pd.read_csv(uploaded)
			except Exception:
				st.error("Não foi possível ler o CSV. Verifique o formato e encoding.")
				return
		else:
			st.info("Envie um CSV pelo painel lateral para começar.")
			return

	elif dataset_choice == "Upload PDF / TXT":
		st.header("Upload PDF / TXT")
		# file_uploader in the main area supports drag-and-drop
		uploaded = st.file_uploader("Arraste e solte um arquivo PDF ou TXT aqui", type=["pdf", "txt"], key="pdf_uploader")
		if uploaded is None:
			st.info("Arraste e solte um PDF ou TXT para começar.")
			return

		# Show minimal info only (no tables/text) until user clicks process
		st.write(f"Arquivo carregado: {uploaded.name} — {uploaded.size} bytes")
		if not st.button("Processar arquivo"):
			st.info("Clique em 'Processar arquivo' para extrair texto e tabelas.")
			return

		# Process after explicit user action
		file_bytes = uploaded.read()
		# Handle TXT files
		if uploaded.type == "text/plain" or uploaded.name.lower().endswith('.txt'):
			try:
				text = file_bytes.decode('utf-8', errors='replace')
			except Exception:
				text = str(file_bytes)
			st.subheader("Texto extraído (TXT)")
			st.text_area("Conteúdo do arquivo", value=text, height=300)
			return

		# Handle PDF files
		if uploaded.type == "application/pdf" or uploaded.name.lower().endswith('.pdf'):
			if pdfplumber is None:
				st.error("Dependência `pdfplumber` não está disponível. Instale as dependências e reinicie o app.")
				return

			try:
				full_text = []
				extracted_tables = []
				used_ocr = False

				# Try OCR FIRST if enabled or forced
				if ocr_enabled or ocr_force:
					if convert_from_bytes is None or pytesseract is None:
						st.warning("Bibliotecas de OCR (`pdf2image`/`pytesseract`) não instaladas — não foi possível executar OCR.")
					else:
						try:
							# Aplica o caminho do Tesseract, se configurado
							if tesseract_path:
								pytesseract.pytesseract.tesseract_cmd = tesseract_path

							# Constrói argumentos para o Poppler
							poppler_args = {"poppler_path": poppler_path} if poppler_path else {}
							
							used_ocr = True
							with st.spinner("Executando OCR nas páginas do PDF (pode demorar)..."):
								images = convert_from_bytes(file_bytes, dpi=300, **poppler_args)
								
								ocr_texts = []
								for i, img in enumerate(images):
									try:
										# Tenta extrair com o idioma especificado
										text = pytesseract.image_to_string(img, lang=ocr_lang)
									except Exception:
										# Fallback para o modo padrão sem idioma
										text = pytesseract.image_to_string(img)
									ocr_texts.append(f"--- OCR Página {i+1} ---\n" + text)
								
								full_text = ocr_texts

						except Exception as ocr_error:
							st.error(f"Ocorreu um erro durante a execução do OCR: {ocr_error}")
							st.error(
								"Verifique se o Tesseract e/ou o Poppler estão instalados corretamente em seu sistema. "
								"No Windows, pode ser necessário configurar os caminhos 'tesseract_path' e 'poppler_path' "
								"no topo do arquivo `app.py`."
							)

				# If OCR was not used, try pdfplumber extraction (fallback)
				if not used_ocr:
					with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
						for i, page in enumerate(pdf.pages):
							text = page.extract_text() or ""
							if text:
								full_text.append(f"--- Página {i+1} ---\n" + text)
							# extract_tables returns list of tables on the page
							tables = page.extract_tables()
							for t in tables:
								# convert table (list of rows) to DataFrame
								try:
									df_table = pd.DataFrame(t)
									# if first row looks like header, set as columns
									header = df_table.iloc[0].tolist()
									df_table = df_table[1:]
									df_table.columns = header
								except Exception:
									df_table = pd.DataFrame(t)
								extracted_tables.append(df_table)

				st.subheader("Texto extraído (PDF)")
				if full_text:
					st.text_area("Conteúdo extraído", value="\n\n".join(full_text), height=300)
				else:
					if used_ocr:
						st.info("OCR não retornou texto significativo.")
					else:
						st.info("Nenhum texto pesquisável encontrado no PDF. Ative OCR nas opções laterais para extrair texto de imagens.")

				if extracted_tables:
					st.subheader("Tabelas extraídas")
					for idx, table_df in enumerate(extracted_tables, start=1):
						st.write(f"Tabela {idx}")
						st.dataframe(table_df)
						csv_bytes = table_df.to_csv(index=False).encode('utf-8')
						st.download_button(label=f"Download CSV - Tabela {idx}", data=csv_bytes, file_name=f"table_{idx}.csv", mime="text/csv")
				else:
					st.info("Nenhuma tabela encontrada no PDF. Para tabelas em imagens considere usar OCR+ferramentas especializadas.")
			except Exception as e:
				st.error(f"Erro ao processar PDF: {e}")
			return

	elif dataset_choice == "Upload Imagens":
		st.header("Upload Imagens")
		# file_uploader in the main area supports drag-and-drop for images
		uploaded = st.file_uploader("Arraste e solte uma imagem (PNG, JPG, etc) aqui", type=["png", "jpg", "jpeg", "bmp", "gif", "tiff"], key="image_uploader")
		if uploaded is None:
			st.info("Arraste e solte uma imagem para começar.")
			return

		# Show minimal info only until user clicks process
		st.write(f"Arquivo carregado: {uploaded.name} — {uploaded.size} bytes")
		if not st.button("Processar imagem"):
			st.info("Clique em 'Processar imagem' para extrair texto com OCR.")
			return

		# Process after explicit user action
		try:
			from PIL import Image
			
			# Load and display the image
			image_bytes = uploaded.read()
			image = Image.open(io.BytesIO(image_bytes))
			st.subheader("Imagem carregada")
			st.image(image, use_column_width=True)

			# Apply OCR to the image
			if pytesseract is None:
				st.error("Dependência `pytesseract` não está disponível. Instale as dependências e reinicie o app.")
				return

			try:
				# Aplica o caminho do Tesseract, se configurado
				if tesseract_path:
					pytesseract.pytesseract.tesseract_cmd = tesseract_path

				with st.spinner("Executando OCR na imagem..."):
					# Extract text from image
					extracted_text = pytesseract.image_to_string(image, lang=ocr_lang)

				st.subheader("Texto extraído (OCR)")
				if extracted_text.strip():
					st.text_area("Conteúdo extraído", value=extracted_text, height=300)
				else:
					st.info("OCR não retornou texto significativo.")

				# Offer download as TXT
				txt_bytes = extracted_text.encode('utf-8')
				st.download_button(label="Download Texto (TXT)", data=txt_bytes, file_name=f"ocr_{uploaded.name}.txt", mime="text/plain")

			except Exception as ocr_error:
				st.error(f"Ocorreu um erro durante a execução do OCR: {ocr_error}")
				st.error(
					"Verifique se o Tesseract está instalado corretamente em seu sistema. "
					"No Windows, pode ser necessário configurar o caminho 'tesseract_path' "
					"no topo do arquivo `app.py`."
				)

		except ImportError:
			st.error("Dependência `Pillow` não está disponível. Instale as dependências e reinicie o app.")
		except Exception as e:
			st.error(f"Erro ao processar imagem: {e}")
		return

	else:
		df = load_dataset(dataset_choice)
		if df.empty:
			st.warning("Dataset não disponível localmente.")
			return

	st.subheader(f"Dataset: {dataset_choice}")

	if show_head:
		st.dataframe(df.head())

	if show_stats:
		st.subheader("Estatísticas básicas")
		st.write(df.describe(include='all'))

	numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
	all_cols = df.columns.tolist()

	if not numeric_cols:
		st.info("Nenhuma coluna numérica encontrada para plotagem.")
		return

	col1, col2 = st.columns(2)
	with col1:
		x_col = st.selectbox("Eixo X", all_cols, index=0)
	with col2:
		y_col = st.selectbox("Eixo Y", all_cols, index=1 if len(all_cols) > 1 else 0)

	st.subheader("Visualização")

	try:
		if chart_type == "Scatter":
			fig = px.scatter(df, x=x_col, y=y_col, color=df.columns[0] if df.shape[1] > 0 else None, title=f"Scatter: {x_col} vs {y_col}")
			st.plotly_chart(fig, use_container_width=True)
		elif chart_type == "Histogram":
			fig = px.histogram(df, x=x_col, nbins=30, title=f"Histograma: {x_col}")
			st.plotly_chart(fig, use_container_width=True)
		elif chart_type == "Line":
			fig = px.line(df, x=x_col, y=y_col, title=f"Line: {x_col} vs {y_col}")
			st.plotly_chart(fig, use_container_width=True)
	except Exception as e:
		st.error(f"Erro ao gerar gráfico: {e}")

	st.markdown("---")
	st.subheader("Explorar dados")
	if st.checkbox("Mostrar tipos de coluna"):
		st.write(df.dtypes)

	if st.checkbox("Mostrar valores nulos por coluna"):
		st.write(df.isna().sum())


if __name__ == "__main__":
	main()

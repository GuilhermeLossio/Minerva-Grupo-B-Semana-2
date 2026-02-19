# 🦁 Alea-lumen | Corporate AI Playground

> **Versão:** 1.0.0 (MVP)  
> **Sprint:** 4 Dias  
> **Stack:** Python + Streamlit + OpenAI

Bem-vindo ao repositório oficial do **Alea-lumen**.
Esta plataforma é um *playground* corporativo seguro que permite aos colaboradores utilizarem IA (LLMs) com contexto da empresa, garantindo **compliance** (auditoria), **controle de custos** e **gestão de acessos**.

---

## 🚀 Visão Geral da Arquitetura

O projeto utiliza uma arquitetura **Monolítica Modular** para facilitar o desenvolvimento rápido. Não separamos Frontend e Backend; tudo roda junto via Streamlit.

* **Frontend & Backend:** [Streamlit](https://streamlit.io/)
* **Inteligência (LLM):** OpenAI/Gemini API + LangChain
* **Banco de Dados (Relacional):** SQLite (Local - para usuários/logs)
* **Banco de Dados (Vetorial):** ChromaDB (Local - para documentos/RAG)

---

## 📂 Estrutura de Pastas (Onde trabalhar?)

Para evitar conflitos, cada desenvolvedor é responsável por uma pasta específica. **Não edite arquivos fora da sua responsabilidade sem avisar a equipe.**

```text
alea-lumen/
│
├── .gitignore             # Arquivos ignorados pelo Git (NUNCA remova .env daqui)
├── requirements.txt       # Lista de bibliotecas do projeto
├── README.md              # Este arquivo
├── app.py                 # 🏁 Ponto de Entrada (Roteador de Telas)
│
├── config/                # Configurações Globais
│   └── settings.py        # Carrega variáveis de ambiente (.env)
│
├── database/              # Persistência de Dados
│   ├── init_db.py         # Script para criar tabelas iniciais (Rodar 1x)
│   ├── connection.py      # Conexão com SQLite
│   └── vector_store.py    # 🧠 Lógica do ChromaDB (Dev 1)
│
├── services/              # Regras de Negócio (O "Cérebro")
│   ├── auth_service.py    # 🔐 Login e Permissões (Dev 2)
│   ├── llm_service.py     # 🤖 Chamadas à OpenAI (Dev 1)
│   ├── document_service.py# 📄 Processamento de PDF (Dev 1)
│   └── audit_service.py   # 📊 Logs e Custos (Dev 4)
│
├── ui/                    # Interface Visual (Telas)
│   ├── login_ui.py        # Tela de Login (Dev 2)
│   ├── chat_ui.py         # 💬 Tela de Chat Principal (Dev 3)
│   ├── admin_ui.py        # Painel Admin (Dev 2)
│   └── compliance_ui.py   # Dashboard Auditoria (Dev 4)
│
└── utils/                 # Funções auxiliares genéricas
    └── helpers.py         # Formatadores de texto, validadores, etc.
```

## ⚙️ Instalação e Setup (Passo a Passo)

Siga estes passos rigorosamente na primeira vez que baixar o projeto.

### 1. Clonar o Repositório

```bash
git clone [https://github.com/SEU_USUARIO/alea-lumen.git](https://github.com/SEU_USUARIO/alea-lumen.git)
cd alea-lumen

```

### 2. Criar Ambiente Virtual (Recomendado)

Isso evita bugs com versões do Python.

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt

```

### 4. Configurar Variáveis de Ambiente

1. Crie um arquivo chamado `.env` na raiz do projeto (copie o modelo abaixo).
2. **IMPORTANTE:** Nunca suba este arquivo para o GitHub.

**Conteúdo do `.env`:**

```ini
GOOGLE_API_KEY="AIzaSy..."
ADMIN_DEFAULT_PASS="admin123"

```

### 5. Inicializar o Banco de Dados

Rode este script uma única vez para criar as tabelas de Usuários e Logs vazias:

```bash
python database/init_db.py

```

### 6. Rodar o Projeto

```bash
streamlit run app.py

```

O navegador abrirá automaticamente em `http://localhost:8501`.

---

## 🤝 Fluxo de Trabalho e Git (Regras de Ouro)

Como temos apenas **4 dias**, a organização é vital. Siga o fluxo abaixo:

### 1. Branches (Ramos)

* **`main`**: ⛔ **PROIBIDO COMMIT DIRETO**. Apenas código pronto e testado entra aqui.
* **`develop`**: Branch de integração diária.
* **`feature/SCRUM-ID`**: Onde você trabalha.

### 2. Padrão de Nomes (Jira Integration)

Use sempre o ID do card do Jira para rastreabilidade.

* **Nome da Branch:** `feature/SCRUM-5-banco-vetorial`
* **Mensagem de Commit:** `feat(SCRUM-5): implementa conexão com chromadb`

### 3. Rotina Diária do Desenvolvedor

**☕ De Manhã (Antes de codar):**
Garanta que você tem a versão mais atual do projeto.

```bash
git checkout develop
git pull origin develop
git checkout -b feature/SCRUM-X-minha-tarefa

```

**✅ Ao Terminar uma Task:**

1. Verifique se o código roda sem erros.
2. Commit e Push:
```bash
git add .
git commit -m "feat(SCRUM-X): finalizei tal funcionalidade"
git push origin feature/SCRUM-X-minha-tarefa

```


3. Vá ao GitHub e abra um **Pull Request (PR)** da sua branch para a `develop`.
4. Avise no grupo: *"PR da Task X aberto, alguém revisa?"*

---

## 🛠️ Definição de Pronto (Definition of Done)

Uma tarefa só é considerada **PRONTA** quando:

1. Funciona na máquina local sem erros no terminal.
2. Não quebra o fluxo de outras áreas (ex: Login continua funcionando).
3. O código foi enviado via Pull Request e aprovado por 1 colega.
4. A tarefa foi movida para **Done** no Jira.

---

## 🆘 Troubleshooting (Deu erro?)

* **`ModuleNotFoundError`**: Você esqueceu de ativar a `venv` ou de rodar o `pip install -r requirements.txt`.
* **`OpenAIError`**: Verifique se sua API Key no arquivo `.env` está correta e se você tem créditos na plataforma.
* **Erro de Importação Circular**: Evite importar `services` dentro de `ui` e depois `ui` dentro de `services`. Mantenha o fluxo em uma direção só (UI -> Services -> Database).

---

**🦁 Alea-lumen Team | Foco na entrega!**

```

```

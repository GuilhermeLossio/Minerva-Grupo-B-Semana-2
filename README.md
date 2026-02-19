# Alea Lumen

Aplicacao corporativa em Streamlit para chat com IA, controle de acesso e auditoria local em SQLite.

## O que foi melhorado

- Cadastro de usuarios com baixo acesso em nova aba dedicada para administradores.
- Auditoria de usuarios corrigida para gravar e ler da tabela `user_audit_logs`.
- Validacoes mais robustas no backend de autenticacao:
  - normalizacao de email
  - validacao de formato de email
  - regra minima de senha (8 caracteres)
  - validacao de nivel de acesso
- Rotas/paginas alinhadas com os entrypoints faltantes (`Pages/login.py` e `Pages/users.py`).
- Inicializacao de banco revisada com schema consistente e indices basicos.

## Perfis de acesso

- `ADMIN`: acesso total, inclui SQL Admin, Auditoria e Cadastro de Usuarios.
- `COMPLIANCE`: acesso a App e Auditoria.
- `NORMAL`: acesso apenas ao App.

## Nova aba: Cadastro de Usuarios

Local: menu lateral do app, visivel somente para `ADMIN`.

Aba: `Cadastro de Usuarios`

Funcionalidades:
- cria usuarios com nivel baixo (`NORMAL`)
- valida campos obrigatorios
- valida email
- valida confirmacao de senha
- lista usuarios `NORMAL` ja cadastrados

## Auditoria de usuarios

Tela: `Auditoria`

Agora exibe eventos reais de:
- `users.create`
- `users.update`
- `users.delete`

Fonte dos dados: tabela `user_audit_logs` no SQLite local.

## Setup rapido

1. Criar e ativar ambiente virtual.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias.

```powershell
pip install -r requirements.txt
```

3. Configurar `.env` (na raiz).

Variaveis minimas:

```ini
JWT_SECRET_KEY="troque-esta-chave"
JWT_ALGORITHM="HS256"
JWT_ISSUER="alea-lumen-auth"
JWT_TOKEN_TTL_HOURS="8"
GOOGLE_API_KEY="sua-chave"
```

4. Inicializar banco.

```powershell
python database/init_db.py
```

5. Rodar app.

```powershell
streamlit run app.py
```

## Credenciais iniciais

Ao inicializar o banco sem administradores, o sistema cria automaticamente:

- Email: `admin@local`
- Senha: `Admin`
- Perfil: `ADMIN`

Recomendado: criar outro admin e alterar/remover o padrao em ambiente real.

## Estrutura principal

```text
app.py
Pages/
  index.py
  login.py
  admin.py
  audit.py
  users.py
services/
  auth_service.py
  auth_guard.py
database/
  connection.py
  init_db.py
ui/
  login_ui.py
  chat_ui.py
  compliance_ui.py
  admin_ui.py
  user_registration_ui.py
```

## Observacoes

- O banco SQLite fica em `database/db_users.db`.
- A tabela de auditoria de usuarios eh `user_audit_logs`.
- Logs tecnicos continuam em `logs`.

# Alea Lumen

Corporate Streamlit application for AI chat, local JWT authentication, role-based access control, and SQLite audit tracking.

## Current State

- Single dark mode theme (white mode removed).
- Public account creation flow separated from login (`page=signup`).
- Every new account is created as `NORMAL` (low access).
- Native Streamlit page navigation is hidden in the sidebar:
  - `.streamlit/config.toml` with `showSidebarNavigation = false`
  - CSS fallback in `app.py` that hides `stSidebarNav`.
- Internal sidebar menu no longer shows `Login`.
- Pages restricted to `ADMIN` only:
  - Audit (`Auditoria`)
  - User Management (`Cadastro de Usuarios`)
  - `SQL Admin`
- Access control is reinforced in `services/auth_guard.py` to block direct URL access when the user lacks permission.
- Recent UI updates:
  - consistent login/sign-up form styles
  - input fields no longer flash a white background on focus/autofill
  - chat `stBottomBlockContainer` set to 30% transparency.

## Access Profiles

- `ADMIN`:
  - App
  - Audit (`Auditoria`)
  - User Management (`Cadastro de Usuarios`)
  - SQL Admin
  - user access-level management
- `COMPLIANCE`:
  - App
- `NORMAL`:
  - App

## Navigation Flow

1. Unauthenticated user opens `app.py`.
2. System redirects to login using query param `page=login`.
3. `Create account` button (`Criar conta`) opens the public sign-up screen (`page=signup`).
4. Successful login redirects to `index` (main app).
5. Internal sidebar options depend on role:
   - `ADMIN`: `App`, `Auditoria` (Audit), `Cadastro de Usuarios` (User Management), `SQL Admin`
   - `COMPLIANCE` and `NORMAL`: `App` only

## User Registration

### Public registration (`signup`)

- Dedicated screen opened by the `Create account` (`Criar conta`) button on login.
- Always creates a `NORMAL` account.
- Validates:
  - name
  - email
  - department (`setor`)
  - password confirmation

### Admin registration (`users`)

- Available only for `ADMIN`.
- Creates low-access users (`NORMAL`).
- Allows access-level changes (`NORMAL`, `COMPLIANCE`, `ADMIN`) only for `ADMIN`.
- Lists already registered low-access users.

## Audit

- Screen: `Auditoria` (Audit, `ADMIN` only).
- Source: `user_audit_logs` table in SQLite.
- Expected events:
  - `users.create`
  - `users.update`
  - `users.update_role`
  - `users.delete`
  - `users.self_register`

## Quick Setup

1. Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure `.env` in project root:

```ini
JWT_SECRET_KEY="replace-this-key"
JWT_ALGORITHM="HS256"
JWT_ISSUER="alea-lumen-auth"
JWT_TOKEN_TTL_HOURS="8"
GOOGLE_API_KEY="your-key"
```

4. Initialize database:

```powershell
python database/init_db.py
```

5. Run application:

```powershell
streamlit run app.py
```

## Initial Credentials

If no `ADMIN` exists, the system automatically creates:

- Email: `admin@local`
- Password: `Admin`
- Profile: `ADMIN`

Recommendation: replace this credential immediately in real environments.

## Main Structure

```text
app.py
.streamlit/
  config.toml
Pages/
  index.py
  login.py
  signup.py
  admin.py
  audit.py
  users.py
services/
  auth_service.py
  auth_guard.py
database/
  connection.py
  init_db.py
  create_user.py
ui/
  login_ui.py
  signup_ui.py
  chat_ui.py
  compliance_ui.py
  admin_ui.py
  user_registration_ui.py
  theme.py
  common.py
```

## Notes

- SQLite database: `database/db_users.db`.
- Audit table: `user_audit_logs`.
- Technical logs table: `logs`.
- CLI script `database/create_user.py` creates only low-access users (`NORMAL`).

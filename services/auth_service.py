from __future__ import annotations

from typing import Any, Optional

import bcrypt
import datetime
import json
import jwt
import re

from config.settings import SECRET_KEY, ALGORITHM, ISSUER, TOKEN_TTL_HOURS
from database import connection

ROLE_MAP = {0: "ADMIN", 1: "NORMAL", 2: "COMPLIANCE"}
LOW_ACCESS_LEVEL = 1
VALID_LEVELS = set(ROLE_MAP.keys())
ADMIN_LEVEL = 0
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalize_text(value: str | None) -> str:
    return (value or "").strip()


def _is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def _validate_new_user(usuario: str, email: str, password: str, nivel: int, setor: str) -> Optional[str]:
    if not usuario:
        return "Nome de usuario obrigatorio"
    if not setor:
        return "Setor obrigatorio"
    if not _is_valid_email(email):
        return "Email invalido"
    if nivel not in VALID_LEVELS:
        return "Nivel de acesso invalido"
    if not password or len(password.strip()) < MIN_PASSWORD_LEN:
        return f"Senha deve ter ao menos {MIN_PASSWORD_LEN} caracteres"
    return None


def create_token(user: dict) -> str:
    """Gera um token JWT valido por TOKEN_TTL_HOURS."""
    now = datetime.datetime.utcnow()
    payload = {
        "id": user["id"],
        "usuario": user["usuario"],
        "email": user["email"],
        "setor": user.get("setor"),
        "role": user["role"],
        "iss": ISSUER,
        "iat": now,
        "exp": now + datetime.timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Valida o token e retorna os dados ou None se invalido/expirado."""
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"require": ["exp", "iat", "iss"]},
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def log_error(action: str, message: str, details: str | None = None, token: str | None = None):
    try:
        user_id = None
        if token:
            data = decode_token(token)
            if data:
                user_id = data.get("id")

        with connection.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO logs (user_id, action, message, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, action, message, details, datetime.datetime.now()),
            )
            conn.commit()

    except Exception:
        # log nunca pode derrubar o sistema
        pass


def audit_event(
    action: str,
    user_id_target: int,
    details: dict | None = None,
    token: str | None = None,
    user_id_admin: int | None = None,
):
    """Registra eventos de auditoria de usuarios na tabela user_audit_logs."""
    try:
        actor_id = user_id_admin

        if actor_id is None and token:
            data = decode_token(token)
            if data:
                actor_id = data.get("id")

        details_str = json.dumps(details, ensure_ascii=False) if details else None

        with connection.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_audit_logs (
                    user_id_admin,
                    user_id_target,
                    action,
                    details,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (actor_id, user_id_target, action, details_str, datetime.datetime.now()),
            )
            conn.commit()

    except Exception:
        # auditoria nunca pode derrubar o sistema
        pass


def hash_password(password: str) -> str:
    """Gera hash bcrypt da senha em texto simples."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verificar_password(password: str, hashed: str) -> bool:
    """Confere senha em texto simples contra hash bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def login(email: str, password: str):
    """Valida credenciais e retorna token JWT em caso de sucesso."""
    normalized_email = _normalize_email(email)

    if not normalized_email or not password:
        return json.dumps({"success": False, "message": "Email ou senha invalidos"})

    try:
        with connection.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE lower(email) = ?",
                (normalized_email,),
            ).fetchone()

        # Nao revela se foi email ou senha
        if not user or not verificar_password(password, user["password"]):
            return json.dumps({"success": False, "message": "Email ou senha invalidos"})

        role = ROLE_MAP.get(user["nivel"], "NORMAL")
        user_data = {
            "id": user["id"],
            "usuario": user["usuario"],
            "email": user["email"],
            "setor": user["setor"],
            "role": role,
        }

        token = create_token(user_data)
        return json.dumps({
            "success": True,
            "token": token,
            "role": role,
            "user": user_data,
        })
    except Exception as exc:
        log_error(action="login", message="Erro ao realizar login", details=str(exc))
        return json.dumps({"success": False, "message": "Erro interno ao realizar login"})


def require_auth(token: str, required_role: str | list[str] | set[str] | None = None):
    data = decode_token(token)

    if not data:
        return json.dumps({"success": False, "message": "Sessao expirada ou invalida"})

    if required_role:
        allowed_roles = {required_role} if isinstance(required_role, str) else set(required_role)
        if data.get("role") not in allowed_roles:
            roles_text = ", ".join(sorted(allowed_roles))
            return json.dumps({"success": False, "message": f"Acesso negado: requer {roles_text}"})

    return json.dumps({"success": True, "user": data})


def criar_usuario(token: str, usuario: str, email: str, password: str, nivel: int, setor: str):
    """Cria um usuario novo apos validar permissao e integridade dos dados."""
    auth = json.loads(require_auth(token, "ADMIN"))
    if not auth.get("success"):
        return json.dumps(auth)

    if nivel != LOW_ACCESS_LEVEL:
        return json.dumps({
            "success": False,
            "message": "Novo usuario deve ser criado com nivel NORMAL (baixo acesso)",
        })

    normalized_name = _normalize_text(usuario)
    normalized_email = _normalize_email(email)
    normalized_setor = _normalize_text(setor)

    validation_error = _validate_new_user(
        usuario=normalized_name,
        email=normalized_email,
        password=password,
        nivel=nivel,
        setor=normalized_setor,
    )
    if validation_error:
        return json.dumps({"success": False, "message": validation_error})

    try:
        with connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE lower(email) = ?", (normalized_email,))
            if cursor.fetchone():
                return json.dumps({"success": False, "message": "Usuario ja esta cadastrado"})

            cursor.execute(
                """
                INSERT INTO users (usuario, email, password, nivel, setor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (normalized_name, normalized_email, hash_password(password), nivel, normalized_setor),
            )
            conn.commit()
            new_user_id = cursor.lastrowid

        audit_event(
            action="users.create",
            user_id_target=new_user_id,
            details={
                "usuario": normalized_name,
                "email": normalized_email,
                "nivel": nivel,
                "setor": normalized_setor,
                "role": ROLE_MAP.get(nivel, "NORMAL"),
            },
            token=token,
        )

        return json.dumps({"success": True, "message": "Usuario criado com sucesso"})
    except Exception as exc:
        log_error(
            action="criar_usuario",
            message="Erro ao criar usuario",
            details=str(exc),
            token=token,
        )
        return json.dumps({"success": False, "message": "Erro interno ao criar usuario"})


def cadastro_publico_usuario(usuario: str, email: str, password: str, setor: str):
    """Permite auto-cadastro de usuario com nivel baixo (NORMAL)."""
    normalized_name = _normalize_text(usuario)
    normalized_email = _normalize_email(email)
    normalized_setor = _normalize_text(setor)

    validation_error = _validate_new_user(
        usuario=normalized_name,
        email=normalized_email,
        password=password,
        nivel=LOW_ACCESS_LEVEL,
        setor=normalized_setor,
    )
    if validation_error:
        return json.dumps({"success": False, "message": validation_error})

    try:
        with connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE lower(email) = ?", (normalized_email,))
            if cursor.fetchone():
                return json.dumps({"success": False, "message": "Usuario ja esta cadastrado"})

            cursor.execute(
                """
                INSERT INTO users (usuario, email, password, nivel, setor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    normalized_name,
                    normalized_email,
                    hash_password(password),
                    LOW_ACCESS_LEVEL,
                    normalized_setor,
                ),
            )
            conn.commit()
            new_user_id = cursor.lastrowid

        audit_event(
            action="users.self_register",
            user_id_target=new_user_id,
            details={
                "usuario": normalized_name,
                "email": normalized_email,
                "nivel": LOW_ACCESS_LEVEL,
                "setor": normalized_setor,
                "role": ROLE_MAP.get(LOW_ACCESS_LEVEL, "NORMAL"),
            },
            token=None,
            user_id_admin=None,
        )
        return json.dumps({
            "success": True,
            "message": "Conta criada com sucesso. Seu acesso inicial e NORMAL (baixo).",
        })
    except Exception as exc:
        log_error(
            action="cadastro_publico_usuario",
            message="Erro no cadastro publico de usuario",
            details=str(exc),
            token=None,
        )
        return json.dumps({"success": False, "message": "Erro interno ao criar conta"})


def listar_usuarios(token: str):
    """Retorna todos os usuarios cadastrados para o admin."""
    auth = json.loads(require_auth(token, "ADMIN"))
    if not auth.get("success"):
        return json.dumps(auth)

    try:
        with connection.get_connection() as conn:
            users = conn.execute(
                "SELECT id, usuario, email, setor, nivel, created_at, updated_at FROM users"
            ).fetchall()

        data = [dict(u) for u in users]
        for user in data:
            user["role"] = ROLE_MAP.get(user.get("nivel"), "NORMAL")

        return json.dumps({"success": True, "data": data})
    except Exception as exc:
        log_error(
            action="listar_usuarios",
            message="Erro ao listar usuarios",
            details=str(exc),
            token=token,
        )
        return json.dumps({"success": False, "message": "Erro interno ao buscar usuarios"})


def alterar_nivel_acesso(token: str, target_user_id: int, novo_nivel: int):
    """Altera o nivel de acesso de um usuario. Apenas ADMIN pode executar."""
    auth = json.loads(require_auth(token, "ADMIN"))
    if not auth.get("success"):
        return json.dumps(auth)

    if target_user_id <= 0:
        return json.dumps({"success": False, "message": "Usuario alvo invalido"})

    if novo_nivel not in VALID_LEVELS:
        return json.dumps({"success": False, "message": "Nivel de acesso invalido"})

    actor_id = auth.get("user", {}).get("id")

    try:
        with connection.get_connection() as conn:
            current = conn.execute(
                "SELECT id, usuario, email, nivel FROM users WHERE id = ?",
                (target_user_id,),
            ).fetchone()
            if not current:
                return json.dumps({"success": False, "message": "Usuario nao encontrado"})

            current_level = current["nivel"]
            if current_level == novo_nivel:
                return json.dumps({"success": True, "message": "Nivel de acesso ja esta atualizado"})

            if current_level == ADMIN_LEVEL and novo_nivel != ADMIN_LEVEL:
                admin_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE nivel = ?",
                    (ADMIN_LEVEL,),
                ).fetchone()[0]
                if admin_count <= 1:
                    return json.dumps({
                        "success": False,
                        "message": "Deve existir ao menos um administrador no sistema",
                    })

            conn.execute(
                "UPDATE users SET nivel = ? WHERE id = ?",
                (novo_nivel, target_user_id),
            )
            conn.commit()

        audit_event(
            action="users.update_role",
            user_id_target=target_user_id,
            details={
                "old_nivel": current_level,
                "new_nivel": novo_nivel,
                "old_role": ROLE_MAP.get(current_level, "NORMAL"),
                "new_role": ROLE_MAP.get(novo_nivel, "NORMAL"),
                "actor_id": actor_id,
            },
            token=token,
        )
        return json.dumps({"success": True, "message": "Nivel de acesso atualizado com sucesso"})
    except Exception as exc:
        log_error(
            action="alterar_nivel_acesso",
            message=f"Erro ao alterar nivel de acesso do usuario {target_user_id}",
            details=str(exc),
            token=token,
        )
        return json.dumps({"success": False, "message": "Erro interno ao alterar nivel de acesso"})


def atualizar_usuario(
    token: str,
    target_user_id: int,
    usuario: str | None = None,
    email: str | None = None,
    password: str | None = None,
    nivel: int | None = None,
    setor: str | None = None,
):
    """Atualiza os dados de um usuario existente."""
    auth = json.loads(require_auth(token, "ADMIN"))
    if not auth.get("success"):
        return json.dumps(auth)

    if target_user_id <= 0:
        return json.dumps({"success": False, "message": "Usuario alvo invalido"})

    if nivel is not None and nivel not in VALID_LEVELS:
        return json.dumps({"success": False, "message": "Nivel de acesso invalido"})

    normalized_usuario = _normalize_text(usuario) if usuario is not None else None
    normalized_email = _normalize_email(email) if email is not None else None
    normalized_setor = _normalize_text(setor) if setor is not None else None

    if normalized_email is not None and normalized_email and not _is_valid_email(normalized_email):
        return json.dumps({"success": False, "message": "Email invalido"})

    if password is not None and password.strip() and len(password.strip()) < MIN_PASSWORD_LEN:
        return json.dumps({
            "success": False,
            "message": f"Senha deve ter ao menos {MIN_PASSWORD_LEN} caracteres",
        })

    try:
        with connection.get_connection() as conn:
            cursor = conn.cursor()
            current_user = conn.execute(
                "SELECT id, usuario, email, nivel, setor FROM users WHERE id = ?",
                (target_user_id,),
            ).fetchone()
            if not current_user:
                return json.dumps({"success": False, "message": "Usuario nao encontrado"})

            if nivel is not None and current_user["nivel"] == ADMIN_LEVEL and nivel != ADMIN_LEVEL:
                admin_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE nivel = ?",
                    (ADMIN_LEVEL,),
                ).fetchone()[0]
                if admin_count <= 1:
                    return json.dumps({
                        "success": False,
                        "message": "Deve existir ao menos um administrador no sistema",
                    })

            if normalized_email:
                existing_email = conn.execute(
                    "SELECT id FROM users WHERE lower(email) = ? AND id <> ?",
                    (normalized_email, target_user_id),
                ).fetchone()
                if existing_email:
                    return json.dumps({"success": False, "message": "Email ja cadastrado"})

            set_clauses = []
            values = []

            def add_if_present(col_name: str, value):
                if value is None:
                    return
                if isinstance(value, str) and value.strip() == "":
                    return
                set_clauses.append(f"{col_name} = ?")
                values.append(value)

            add_if_present("usuario", normalized_usuario)
            add_if_present("email", normalized_email)
            add_if_present("nivel", nivel)
            add_if_present("setor", normalized_setor)

            if password is not None and password.strip() != "":
                set_clauses.append("password = ?")
                values.append(hash_password(password))

            if not set_clauses:
                return json.dumps({"success": False, "message": "Nenhum campo para atualizar"})

            changed_fields = [c.split(" = ")[0] for c in set_clauses]
            old_data = dict(current_user)

            cursor.execute(
                """
                UPDATE users
                SET """
                + ", ".join(set_clauses)
                + """
                WHERE id = ?
                """,
                tuple(values + [target_user_id]),
            )
            conn.commit()

            new_values = conn.execute(
                "SELECT usuario, email, nivel, setor FROM users WHERE id = ?",
                (target_user_id,),
            ).fetchone()
            new_data = dict(new_values) if new_values else {}

        audit_event(
            action="users.update",
            user_id_target=target_user_id,
            details={
                "updated_fields": changed_fields,
                "old_data": old_data,
                "new_data": new_data,
            },
            token=token,
        )
        return json.dumps({"success": True, "message": "Usuario atualizado com sucesso"})
    except Exception as exc:
        log_error(
            action="atualizar_usuario",
            message="Erro ao atualizar usuario",
            details=str(exc),
            token=token,
        )
        return json.dumps({"success": False, "message": "Erro interno ao atualizar usuario"})


def deletar_usuario(token: str, target_user_id: int):
    """Deleta usuario existente garantindo regras minimas de seguranca."""
    auth = json.loads(require_auth(token, "ADMIN"))
    if not auth.get("success"):
        return json.dumps(auth)

    actor_id = auth.get("user", {}).get("id")
    if actor_id == target_user_id:
        return json.dumps({"success": False, "message": "Nao e permitido remover o proprio usuario logado"})

    try:
        with connection.get_connection() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if total_users <= 1:
                return json.dumps({
                    "success": False,
                    "message": "Deve existir ao menos um usuario no sistema",
                })

            user_role = conn.execute(
                "SELECT nivel FROM users WHERE id = ?",
                (target_user_id,),
            ).fetchone()
            if not user_role:
                return json.dumps({"success": False, "message": "Usuario nao encontrado"})

            if user_role["nivel"] == 0:
                admin_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE nivel = 0"
                ).fetchone()[0]
                if admin_count <= 1:
                    return json.dumps({
                        "success": False,
                        "message": "Deve existir ao menos um administrador no sistema",
                    })

            conn.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
            conn.commit()

        audit_event(
            action="users.delete",
            user_id_target=target_user_id,
            details=None,
            token=token,
        )
        return json.dumps({"success": True, "message": "Usuario deletado com sucesso"})
    except Exception as exc:
        log_error(
            action="deletar_usuario",
            message=f"Erro ao deletar usuario {target_user_id}",
            details=str(exc),
            token=token,
        )
        return json.dumps({"success": False, "message": "Erro interno ao deletar usuario"})

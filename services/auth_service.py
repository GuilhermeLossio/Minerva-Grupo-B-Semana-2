from typing import Any, Optional
import bcrypt
import json
import jwt
import datetime
from database import connection
from config.settings import SECRET_KEY, ALGORITHM, ISSUER, TOKEN_TTL_HOURS


def create_token(user: dict) -> str:
    """Gera um token JWT válido por 24 horas"""
    now = datetime.datetime.utcnow()
    payload = {
        "id": user["id"],
        "usuario": user["usuario"],
        "email": user["email"],
        "role": user["role"],
        "iss": ISSUER,
        "iat": now,
        "exp": now + datetime.timedelta(hours=TOKEN_TTL_HOURS)  # Expira em 24 horas
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Valida o token e retorna os dados ou None se inválido/expirado"""
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"require": ["exp", "iat", "iss"]}
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def log_error(action: str, message: str, details: str = None, token: str = None):
    try:
        user_id = None
        if token:
            data = decode_token(token)
            if data:
                user_id = data.get("id")

        with connection.get_connection() as conn:
            conn.execute("""
                INSERT INTO logs (user_id, action, message, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, action, message, details, datetime.datetime.now()))
            conn.commit()

    except Exception:
        # log nunca pode derrubar o sistema
        pass

def audit_event(action: str, user_id_target: int, details: dict | None = None, token: str | None = None, user_id_admin: int | None = None):
    """
    Registra eventos de auditoria (CRUD de users) na tabela users.
    - user_id_admin: quem executou (admin). Se não for passado, tenta extrair do token.
    - user_id_target: usuário afetado pela ação.
    - action: ex: users.create / users.update / users.delete
    - details: dict (será salvo como JSON)
    """
    try:
        actor_id = user_id_admin

        if actor_id is None and token:
            data = decode_token(token)
            if data:
                actor_id = data.get("id")

        details_str = json.dumps(details, ensure_ascii=False) if details else None

        with connection.get_connection() as conn:
            conn.execute("""
                INSERT INTO users (user_id_admin, user_id_target, action, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (actor_id, user_id_target, action, details_str, datetime.datetime.now()))
            conn.commit()

    except Exception:
        # auditoria nunca pode derrubar o sistema
        pass

def hash_password(password: str) -> str:
    '''
    Essa função recebe uma senha em texto simples e retorna a senha
    hasheada usando o algoritmo bcrypt.

    Argumentos:
    password -- A senha em texto simples a ser hasheada.
    Retorna:
    A senha hasheada como uma string.
    '''
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )
    return hashed.decode("utf-8")

def verificar_password(password: str, hashed: str) -> bool:
    '''
    Essa função verifica se a senha em texto simples corresponde à
    senha hasheada.

    Argumentos:
    password -- A senha em texto simples a ser verificada.
    hashed -- A senha hasheada para comparação.
    Retorna:
    True se a senha corresponder, False caso contrário.
    '''
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8")
        )
    except Exception:
        return False

def login(email: str, password: str):
    '''
    Essa função verifica as credenciais do usuário para login.

    Argumentos:
    email -- O email do usuário.
    password -- A senha em texto simples do usuário.
    Retorna:
    Um dicionário com os dados do usuário se as credenciais forem válidas, None caso contrário.
    '''
    try: 
        with connection.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

        # Não revela se foi email ou senha
        if not user or not verificar_password(password, user["password"]):
            return json.dumps({
                "success": False,
                "message": "Email ou senha inválidos"
            })
        # Mapeamento de Role
        role_map = {0: "ADMIN", 1: "NORMAL", 2: "COMPLIANCE"}
        role = role_map.get(user["nivel"], "NORMAL")
        user_data = {
            "id": user["id"],
            "usuario": user["usuario"],
            "email": user["email"],
            "role": role
        }
        # Criamos o TOKEN
        token = create_token(user_data)
        return json.dumps({
            "success": True,
            "token": token,
            "role": role,
            "user": user_data
        })
    except Exception as e:
        log_error(
            action="login",
            message="Erro ao realizar login",
            details=str(e))
        return json.dumps({
            "success": False,
            "message": "Erro interno ao realizar login"
        })
    
def require_auth(token: str, required_role: str = None):
    data = decode_token(token)
    
    if not data:
        return json.dumps({
            "success": False,
            "message": "Sessão expirada ou inválida"
        })
    
    if required_role and data["role"] != required_role:
        return json.dumps({
            "success": False,
            "message": f"Acesso negado: Requer {required_role}"
        })
    
    return json.dumps({
        "success": True,
        "user": data
        })

def criar_usuario(token: str, usuario: str, email: str, password: str, nivel: int, setor: str):
    '''
    Essa função verifica se o email já está cadastrado e cria um novo usuário
    no banco de dados com a senha hasheada.

    Argumentos:
    email -- O email do usuário.
    password -- A senha em texto simples do usuário.
    usuario -- O nível do usuário (0 para admin, 1 para usuário normal e 2 para compliance).
    setor -- O setor do usuário.
    Retorna:
    None -- Insere o novo usuário no banco de dados.
    '''
    auth = json.loads(require_auth(token,"ADMIN"))
    if not auth["success"]:
        return json.dumps(auth)
    
    try: 
        with connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM users WHERE email = ?",
                    (email,)
                )
                if cursor.fetchone():
                    return json.dumps({
                        "success": False,
                        "message": "Usuário já está cadastrado"
                    })
                cursor.execute("""
                    INSERT INTO users (usuario, email, password, nivel, setor)
                    VALUES (?, ?, ?, ?, ?)
                """, (usuario, email, hash_password(password), nivel, setor))
                conn.commit()
                new_user_id = cursor.lastrowid
                audit_event(
                    action="users.create",
                    user_id_target=new_user_id,
                    details={
                        "usuario": usuario,
                        "email": email,
                        "nivel": nivel,
                        "setor": setor
                    },
                    token=token
                )
                return json.dumps({
                    "success": True,
                    "message": "Usuário criado com sucesso"
                })
    except Exception as e:
        log_error(
            action="criar_usuario",
            message="Erro ao criar usuário",
            details=str(e),
            token=token)
        return json.dumps({
            "success": False,
            "message": "Erro interno ao criar usuário"
        })

def listar_usuarios(token: str):
    '''
    Essa função retorna uma lista de todos os usuários cadastrados no banco de dados.

    Retorna:
    Uma lista de dicionários, cada um contendo as informações de um usuário.
    '''
    auth = json.loads(require_auth(token,"ADMIN"))
    if not auth["success"]:
        return json.dumps(auth)
    
    try:
        with connection.get_connection() as conn:
            users = conn.execute(
                "SELECT id, usuario, email, setor, nivel FROM users"
                ).fetchall()

        return json.dumps({
            "success": True,
            "data": [dict(u) for u in users]
        })
    except Exception as e:
        log_error(
            action="listar_usuarios",
            message="Erro ao listar usuários",
            details=str(e),
            token=token)
        return json.dumps({
            "success": False,
            "message": "Erro interno ao buscar usuários"
        })

def atualizar_usuario(token: str, target_user_id: int, usuario: str | None = None, email: str | None = None, password: str | None = None, nivel: int | None = None, setor: str | None = None):
    '''
    Essa função atualiza as informações de um usuário existente no banco de dados.

    Argumentos:
    token -- O token do usuário que está tentando atualizar o outro usuário.
    target_user_id -- O ID do usuário a ser atualizado.
    email -- O novo email do usuário.
    usuario -- O novo nível do usuário (0 para admin, 1 para usuário normal e 2 para compliance).
    setor -- O novo setor do usuário.
    Retorna:
    None -- Atualiza as informações do usuário no banco de dados.
    '''
    auth = json.loads(require_auth(token,"ADMIN"))
    if not auth["success"]:
        return json.dumps(auth)
    try:
        with connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM users WHERE id = ?",
                (target_user_id,)
            )
            if not cursor.fetchone():
                return json.dumps({
                    "success": False,
                    "message": "Usuário não encontrado"
                })

            #upadete
            set_clauses = []
            values = []

            def add_if_present(col_name: str, value):
                # regra: None = não atualizar
                # para strings, "" (vazio) = não atualizar também (evita apagar sem querer)
                if value is None:
                    return
                if isinstance(value, str) and value.strip() == "":
                    return
                set_clauses.append(f"{col_name} = ?")
                values.append(value)

            add_if_present("usuario", usuario)
            add_if_present("email", email)
            add_if_present("nivel", nivel)
            add_if_present("setor", setor)

            if password is not None and password.strip() != "":
                set_clauses.append("password = ?")
                values.append(hash_password(password))

            if not set_clauses:
                return json.dumps({
                    "success": False,
                    "message": "Nenhum campo para atualizar"
                })

            changed_fields = [c.split(" = ")[0] for c in set_clauses]
            old_values = conn.execute("SELECT usuario, email, nivel, setor FROM users WHERE id = ?",
                (target_user_id,)).fetchone()
            old_data = dict(old_values) if old_values else {}

            cursor.execute("""
                UPDATE users
                SET """ + ", ".join(set_clauses) + """
                WHERE id = ?
            """, tuple(values + [target_user_id]))
            conn.commit()
            new_values = conn.execute("SELECT usuario, email, nivel, setor FROM users WHERE id = ?",
                (target_user_id,)).fetchone()
            new_data = dict(new_values) if new_values else {}
            audit_event(
                action="users.update",
                user_id_target=target_user_id,
                details={
                    "updated_fields": changed_fields,
                    "old_data": old_data,
                    "new_data": new_data
                },
                token=token
            )
        return json.dumps({
            "success": True,
            "message": "Usuário atualizado com sucesso"
        })
    except Exception as e:
        log_error(
            action="atualizar_usuario",
            message="Erro ao atualizar usuário",
            details=str(e),
            token=token)
        return json.dumps({
            "success": False,
            "message": "Erro interno ao atualizar usuário"
        })

def deletar_usuario(token: str, target_user_id: int):
    '''
    Essa função deleta um usuário existente no banco de dados.

    Argumentos:
    token -- O token do usuário que está tentando deletar o outro usuário.
    target_user_id -- O ID do usuário a ser deletado.
    Retorna:
    None -- Deleta o usuário do banco de dados.
    '''
    auth = json.loads(require_auth(token,"ADMIN"))
    if not auth["success"]:
        return json.dumps(auth)
    
    try: 
        with connection.get_connection() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if total_users <= 1:
                return json.dumps({
                    "success": False,
                    "message": "Deve existir ao menos um usuário no sistema"
                })
            user_role = conn.execute(
                "SELECT nivel FROM users WHERE id = ?",
                (target_user_id,)
            ).fetchone()
            if not user_role:
                return json.dumps({
                    "success": False,
                    "message": "Usuário não encontrado"
                })
            if user_role["nivel"] == 0:
                admin_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE nivel = 0"
                ).fetchone()[0]
                if admin_count <= 1:
                    return json.dumps({
                        "success": False,
                        "message": "Deve existir ao menos um administrador no sistema"
                    })
            
            conn.execute("""
                DELETE FROM users
                WHERE id = ?
            """, (target_user_id,))
            conn.commit()
            audit_event(
                action="users.delete",
                user_id_target=target_user_id,
                details=None,
                token=token
            )
        return json.dumps({
            "success": True,
            "message": "Usuário deletado com sucesso"
        })
    except Exception as e:
        log_error(
            action="deletar_usuario",
            message=f"Erro ao deletar usuário {target_user_id}",
            details=str(e),
            token=token)
        return json.dumps({
            "success": False,
            "message": "Erro interno ao deletar usuário"
        })

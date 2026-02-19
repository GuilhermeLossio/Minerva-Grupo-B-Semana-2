from __future__ import annotations

import argparse
import getpass
import re
import sys
import bcrypt

from database.connection import get_connection
from database.init_db import init_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new user in the database.")
    parser.add_argument("--usuario", required=True, help="Nome do usuario.")
    parser.add_argument("--email", required=True, help="Email do usuario.")
    parser.add_argument("--password", help="Senha do usuario (se omitida, sera solicitada).")
    parser.add_argument(
        "--nivel",
        type=int,
        default=1,
        help="Nivel do usuario (0=ADMIN, 1=NORMAL, 2=COMPLIANCE).",
    )
    parser.add_argument("--setor", required=True, help="Setor do usuario.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not EMAIL_RE.match(args.email):
        print("Erro: email invalido.")
        return 1

    if args.nivel not in (0, 1, 2):
        print("Erro: nivel deve ser 0, 1 ou 2.")
        return 1

    password = args.password or getpass.getpass("Senha: ")
    if not password:
        print("Erro: senha vazia.")
        return 1

    init_db()
    conn = get_connection()
    if conn is None:
        print("Erro: falha ao conectar no banco.")
        return 1

    try:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE email = ?",
            (args.email,),
        ).fetchone()
        if existing:
            print("Erro: email ja cadastrado.")
            return 1

        conn.execute(
            """
            INSERT INTO users (usuario, email, password, nivel, setor)
            VALUES (?, ?, ?, ?, ?)
            """,
            (args.usuario, args.email, hash_password(password), args.nivel, args.setor),
        )
        conn.commit()
        print("Usuario criado com sucesso.")
        return 0
    except Exception as exc:
        print(f"Erro ao criar usuario: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

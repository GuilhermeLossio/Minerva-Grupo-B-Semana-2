import sqlite3
from pathlib import Path

# caminho da pasta onde ESTE arquivo está
BASE_DIR = Path(__file__).resolve().parent
# nome do banco de dados
DB_PATH = BASE_DIR / "db_users.db"

def get_connection():
    """
    Cria e retorna uma conexão com o banco de dados SQLite
    localizado na mesma pasta deste arquivo.
    """
    try: 
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None
import os
from dotenv import load_dotenv

load_dotenv()  # lê o .env

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ISSUER = os.getenv("JWT_ISSUER", "alea-lumen-auth")
TOKEN_TTL_HOURS = int(os.getenv("JWT_TOKEN_TTL_HOURS", "8"))

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY não definida no .env")
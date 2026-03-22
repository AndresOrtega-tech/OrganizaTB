import os
from pathlib import Path

from dotenv import load_dotenv

from supabase import Client, create_client

# Construct the path to the .env file explicitly
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Variables principales de configuración de Supabase
url: str | None = os.environ.get("SUPABASE_URL") or os.environ.get("DATABASE_URL")

# Intentar usar la Service Role Key para tener permisos completos desde el backend
# Aceptamos múltiples nombres comunes para esta variable
key: str | None = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SERVICE_ROLE")
    or os.environ.get("SUPABASE_ANON_KEY")
    or os.environ.get("ANON_KEY")
)

# Alias opcionales para compatibilidad con distintos archivos .env
anon_key: str | None = os.environ.get("ANON_KEY")
service_role: str | None = os.environ.get("SERVICE_ROLE")
database_url: str | None = os.environ.get("DATABASE_URL")

supabase: Client | None = None
if url and key:
    supabase = create_client(url, key)
else:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment variables.")

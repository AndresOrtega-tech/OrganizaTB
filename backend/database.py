import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Construct the path to the .env file explicitly
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

url: str | None = os.environ.get("SUPABASE_URL")
key: str | None = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("ANON_KEY")

supabase: Client | None = None
if url and key:
    supabase = create_client(url, key)
else:
    print("Warning: SUPABASE_URL or SUPABASE_ANON_KEY not found in environment variables.")

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str | None = os.environ.get("SUPABASE_URL")
key: str | None = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("ANON_KEY")

supabase: Client | None = None
if url and key:
    supabase = create_client(url, key)

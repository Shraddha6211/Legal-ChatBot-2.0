# backend/db/supabase_client.py

from supabase import create_client, Client
from config import settings

def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client
    """
    client = create_client(
        settings.supabase_url,
        settings.supabase_key
    )
    print("Connected to Supabase!")
    return client
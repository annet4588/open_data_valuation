import streamlit as st
from typing import Dict, Any
from supabase import create_client

@st.cache_resource
def get_supabase():
    # Create and cache Supabase client
    
    # Read url and key from Streamlit secrets
    supabase_url = st.secrets.get("SUPABASE_URL")
    supabase_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase secrets are missing")
    # Create and return Supabase client
    return create_client(supabase_url, supabase_key)
   
# Save a single valuation result ro DB
def save_valuation(payload: Dict[str, Any]) -> None:
    supabase = get_supabase()
    # Insert valuation record in the table
    result = supabase.table("valuations").insert(payload).execute()
    
    if getattr(result, "error", None):
        raise RuntimeError(result.error)

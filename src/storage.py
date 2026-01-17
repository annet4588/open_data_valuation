import os
import json
from typing import Dict, Any

import streamlit as st
import psycopg2

@st.cache_resource
def get_conn():
    # Create a cache PostgreSQL DB connection for the app
    # - In Streamlit Community Cloud, secrets are used as environment variables
    # - In local development, secrets can be read from .streamlit/secrets.toml
    
    # try to read db URL from environment variables (CLoud)
    db_url = st.secrets.get("DATABASE_URL") or os.environ.get("DATABASE_URL")

    if not db_url:
        raise RuntimeError("DATABASE_URL is not set (add it to Streamlit Secrets).")
    return psycopg2.connect(db_url)

# Save a single valuation result ro DB
def save_valuation(payload: dict) -> None:
    conn = get_conn()
     # Execute a signle INSERT into valuations table
    with conn.cursor() as cur:
        cur.execute(
            
                """
                INSERT INTO valuations
                (submit_id, created_at, dataset_sig, use_case, apply_weights, stars, weights, final_score_percent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (submit_id) DO NOTHING
                
                """,
            ( 
                payload["submit_id"],
                payload["created_at"],
                payload["dataset_sig"],
                payload["use_case"],
                payload["apply_weights"],
                json.dumps(payload["stars"]),
                json.dumps(payload["weights"]),
                payload["final_score_percent"],
            ),
        )
    conn.commit()
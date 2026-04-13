
import os
import streamlit as st
from sqlalchemy import create_engine, inspect, text
from core.models import Base, ensure_schema_compliance

def debug_db():
    print("--- Diagnosticando Problema de Banco ---")
    
    # Simular a lógica de core/models.py
    db_url = 'sqlite:///ballistics.db'
    if "supabase" in st.secrets and "db_url" in st.secrets["supabase"]:
        db_url = st.secrets["supabase"]["db_url"]
        print(f"Detectado Supabase URL: {db_url[:20]}...")
    else:
        print("Usando SQLite padrão.")

    engine = create_engine(db_url)
    
    try:
        print("Tentando Base.metadata.create_all(engine)...")
        Base.metadata.create_all(engine)
        print("Sucesso: create_all")
        
        print("Tentando ensure_schema_compliance(engine)...")
        ensure_schema_compliance(engine)
        print("Sucesso: ensure_schema_compliance")
        
    except Exception as e:
        print(f"FALHA DETECTADA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Mock streamlit secrets if needed or just run
    if not hasattr(st, "secrets"):
        st.secrets = {}
    debug_db()


import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import bcrypt
import uuid
from datetime import datetime
import json

# --- Config ---
# To use this, you must set st.secrets["gsheets"] with your service account JSON.
# And inside "gsheets", you can put "spreadsheet" = "URL_OF_YOUR_SHEET"
# Or pass URL directly.

SPREADSHEET_URL = st.secrets.get("gsheets", {}).get("spreadsheet", "")

def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

def _read_df(worksheet):
    try:
        conn = get_conn()
        df = conn.read(worksheet=worksheet, ttl=0) # ttl=0 for fresh data
        return df
    except Exception as e:
        # If worksheet doesn't exist, return empty DF with expected cols
        return pd.DataFrame()

def _write_df(worksheet, df):
    conn = get_conn()
    conn.update(worksheet=worksheet, data=df)

def generate_id():
    return str(uuid.uuid4())

# --- Models Abstraction ---

class User:
    def __init__(self, data):
        self.id = str(data.get("id", ""))
        self.username = str(data.get("username", ""))
        self.password_hash = str(data.get("password_hash", ""))
        self.name = str(data.get("name", ""))
        self.cpf = str(data.get("cpf", ""))
        self.email = str(data.get("email", ""))
        self.phone = str(data.get("phone", ""))
        self.cr_number = str(data.get("cr_number", ""))
        # Handle date parsing
        cr_exp = data.get("cr_expiration")
        if isinstance(cr_exp, str) and cr_exp and cr_exp != "None":
            try:
                self.cr_expiration = datetime.strptime(cr_exp, "%Y-%m-%d").date()
            except:
                self.cr_expiration = None
        else:
            self.cr_expiration = None
            
        self.address_acervo = str(data.get("address_acervo", ""))
        self.is_premium = int(data.get("is_premium") or 0)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except:
            return False

# --- Data Access Object (DAO) ---

class DB:
    def __init__(self):
        self.url = SPREADSHEET_URL
        
    def get_user_by_username(self, username):
        df = _read_df("users")
        if df.empty: return None
        # Filter
        res = df[df["username"] == username]
        if not res.empty:
            return User(res.iloc[0].to_dict())
        return None
    
    def create_user(self, user_obj):
        df = _read_df("users")
        new_row = {
            "id": generate_id(),
            "username": user_obj.username,
            "password_hash": user_obj.password_hash,
            "name": user_obj.name,
            "cpf": user_obj.cpf,
            "email": user_obj.email,
            "phone": user_obj.phone,
            "cr_number": "",
            "cr_expiration": None,
            "address_acervo": "",
            "is_premium": 0
        }
        # Append
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        _write_df("users", df)
        return True

    def update_user(self, user_obj):
        df = _read_df("users")
        if df.empty: return False
        
        # We need to find the index of the user
        idx = df.index[df['id'] == user_obj.id].tolist()
        if not idx:
            return False
        
        i = idx[0]
        # Update fields
        df.at[i, 'name'] = user_obj.name
        df.at[i, 'cpf'] = user_obj.cpf
        df.at[i, 'email'] = user_obj.email
        df.at[i, 'phone'] = user_obj.phone
        df.at[i, 'cr_number'] = user_obj.cr_number
        df.at[i, 'cr_expiration'] = str(user_obj.cr_expiration) if user_obj.cr_expiration else None
        df.at[i, 'address_acervo'] = user_obj.address_acervo
        df.at[i, 'is_premium'] = user_obj.is_premium
        
        _write_df("users", df)
        return True

# Singleton pattern for easier imports
db = DB()

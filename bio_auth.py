import json
import os
import hashlib
import base64
import streamlit as st
from cryptography.fernet import Fernet

CONFIG_FILE = "device_config.json"
KEY_FILE = ".device_key"


# Biometria Funcional (SG-002 / Auditoria WebAuthn)
try:
    from streamlit_passwordless import signin_widget, register_widget
    HAS_PASSKEYS = True
except ImportError:
    HAS_PASSKEYS = False

def render_biometric_login():
    """Renderiza interface de login biométrico (WebAuthn)."""
    if "streamlit-passwordless" in st.secrets:
        # Modo Funcional (Produção/HTTPS)
        # Retorna o usuário logado via passkey
        return signin_widget()
    return None

def render_biometric_registration():
    """Renderiza interface de registro de nova passkey."""
    if "streamlit-passwordless" in st.secrets:
        st.markdown("##### 🔐 Ativar Biometria (Passkey)")
        st.caption("Registre este dispositivo para logins futuros sem senha.")
        return register_widget()
    return None

# Funções Legadas / Fallback de Dispositivo
def _get_encryption_key():
    """Obtém chave de criptografia Fernet-compatível dos Secrets do Streamlit."""
    try:
        key_raw = st.secrets["device_encryption_key"]
        if isinstance(key_raw, str):
            key_raw = key_raw.encode()
        key_b64 = base64.urlsafe_b64encode(key_raw.ljust(32)[:32])
        return key_b64
    except (FileNotFoundError, KeyError):
        return None

def _encrypt(val):
    """Criptografa um valor usando AES-256 (Fernet)."""
    if not val:
        return ""
    key = _get_encryption_key()
    if not key:
        return "" 
    f = Fernet(key)
    return f.encrypt(val.encode()).decode()

def _decrypt(val):
    """Descriptografa um valor codificado."""
    if not val:
        return ""
    key = _get_encryption_key()
    if not key:
        return ""
    try:
        f = Fernet(key)
        return f.decrypt(val.encode()).decode()
    except Exception:
        return ""

def _hash_username(username):
    """Gera hash do username para validação de integridade (SHA-256)."""
    return hashlib.sha256(username.encode('utf-8')).hexdigest()

def save_biometrics(username):
    """Salva o usuário atual como habilitado para login biométrico neste dispositivo."""
    config = {
        "lp_secure": _encrypt(username),
        "user_hash": _hash_username(username),
        "biometrics_enabled": True
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def clear_biometrics():
    """Remove as credenciais biométricas salvas."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

def check_biometrics_available():
    """Verifica se há um usuário salvo para biometria e valida integridade."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if data.get("biometrics_enabled"):
                    encrypted_user = data.get("lp_secure")
                    if encrypted_user:
                        username = _decrypt(encrypted_user)
                        if username and _hash_username(username) == data.get("user_hash"):
                            return username
        except (json.JSONDecodeError, KeyError, IOError):
            return None
    return None

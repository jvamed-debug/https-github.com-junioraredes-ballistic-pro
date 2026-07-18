import json
import os
import hashlib
import streamlit as st

CONFIG_FILE = "device_config.json"


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
def _encrypt(val):
    """Criptografa um valor usando a suite centralizada de core.models."""
    if not val:
        return ""
    from core.models import get_encryption_suite
    suite = get_encryption_suite()
    if suite is None:
        return ""
    return suite.encrypt(val.encode()).decode()

def _decrypt(val):
    """Descriptografa um valor usando a suite centralizada de core.models."""
    if not val:
        return ""
    from core.models import get_encryption_suite
    suite = get_encryption_suite()
    if suite is None:
        return ""
    try:
        return suite.decrypt(val.encode()).decode()
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

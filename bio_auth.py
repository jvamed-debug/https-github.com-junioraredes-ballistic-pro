import json
import os
import hashlib
import base64
import streamlit as st
from cryptography.fernet import Fernet

CONFIG_FILE = "device_config.json"
KEY_FILE = ".device_key"


def _get_encryption_key():
    """Obtém a chave de criptografia persistente obrigatoriamente dos Secrets do Streamlit."""
    try:
        if "device_encryption_key" in st.secrets:
            # Em conformidade com auditoria SEC-001
            return st.secrets["device_encryption_key"].encode()
    except Exception:
        pass

    # Se chegou aqui, não há chave configurada ou erro ocorreu
    st.error("⚠️ CRITICAL: 'device_encryption_key' não encontrada nos Secrets!")
    st.info("Para habilitar biometria, adicione a chave no arquivo .streamlit/secrets.toml")
    raise PermissionError("Criptografia de dispositivo não inicializada. Verifique st.secrets.")



def _encrypt(val):
    """Criptografa um valor usando AES-256 (Fernet)."""
    if not val: return ""
    f = Fernet(_get_encryption_key())
    return f.encrypt(val.encode()).decode()


def _decrypt(val):
    """Descriptografa um valor codificado."""
    if not val: return ""
    try:
        f = Fernet(_get_encryption_key())
        return f.decrypt(val.encode()).decode()
    except Exception:
        return ""


def _hash_username(username):
    """Gera hash do username para validação de integridade (SHA-256)."""
    return hashlib.sha256(username.encode('utf-8')).hexdigest()


def save_biometrics(username):
    """Salva o usuário atual como habilitado para login biométrico neste dispositivo."""
    config = {
        "lp_secure": _encrypt(username),  # last_user criptografado AES-256
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
                        # Validação dupla: o hash original deve coincidir com o decriptografado
                        if username and _hash_username(username) == data.get("user_hash"):
                            return username
        except (json.JSONDecodeError, KeyError, IOError):
            return None
    return None

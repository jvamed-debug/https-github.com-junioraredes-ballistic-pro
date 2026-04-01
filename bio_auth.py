import json
import os
import hashlib

CONFIG_FILE = "device_config.json"


def _hash_username(username):
    """Gera hash do username para não armazenar em plaintext."""
    return hashlib.sha256(username.encode('utf-8')).hexdigest()


def save_biometrics(username):
    """Salva o usuário atual como habilitado para login biométrico neste dispositivo."""
    config = {
        "last_user": username,
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
    """Verifica se há um usuário salvo para biometria."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if data.get("biometrics_enabled") and data.get("last_user"):
                    return data["last_user"]
        except (json.JSONDecodeError, KeyError, IOError):
            return None
    return None

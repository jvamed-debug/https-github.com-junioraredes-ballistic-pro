import streamlit as st
import bcrypt
from core.models import get_session, User

def authenticate(username, password):
    session = get_session()
    user = session.query(User).filter_by(username=username).first()
    if user and user.check_password(password):
        session.close()
        return user
    session.close()
    return None

def register_user(username, password, name, cpf, email, phone):
    session = get_session()
    existing = session.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        session.close()
        return False, "Usuário ou e-mail já existe."
    
    new_user = User(username=username, name=name, cpf=cpf, email=email, phone=phone)
    new_user.set_password(password)
    session.add(new_user)
    session.commit()
    session.close()
    return True, "Usuário registrado com sucesso!"

def recover_password(identifier):
    session = get_session()
    user = session.query(User).filter((User.email == identifier) | (User.phone == identifier)).first()
    if user:
        session.close()
        return True, f"Instruções enviadas para {identifier}."
    session.close()
    return False, "Usuário não encontrado."

import streamlit as st
import bcrypt
from core.models import managed_session, User

def authenticate(username, password):
    with managed_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            # Expunge para usar o objeto fora da sessão
            session.expunge(user)
            return user
    return None

def register_user(username, password, name, cpf, email, phone):
    with managed_session() as session:
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return False, "Usuário ou e-mail já existe."

        new_user = User(username=username, name=name, cpf=cpf, email=email, phone=phone)
        new_user.set_password(password)
        session.add(new_user)
    return True, "Usuário registrado com sucesso!"

def recover_password(identifier):
    with managed_session() as session:
        user = session.query(User).filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()
        if user:
            return True, f"Instruções enviadas para {identifier}."
    return False, "Usuário não encontrado."

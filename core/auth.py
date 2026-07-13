from core.models import managed_session, User, log_action
from schemas import UserCreate

def authenticate(username, password):
    with managed_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            session.expunge(user)
            log_action(user.id, "auth_login_success", "users", user.id)
            return user

        if user:
            log_action(user.id, "auth_login_failed", "users", user.id, new={"info": "Senha incorreta"})

    return None

def register_user(username, password, name, cpf, email, phone):
    cpf_digits = cpf.replace(".", "").replace("-", "") if cpf else None
    try:
        UserCreate(
            username=username,
            password=password,
            name=name or None,
            cpf=cpf_digits or None,
            email=email or None,
            phone=phone or None,
        )
    except Exception as e:
        return False, str(e)

    with managed_session() as session:
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return False, "Dados informados já estão em uso ou são inválidos."

        new_user = User(username=username, name=name, cpf=cpf, email=email, phone=phone)
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        log_action(new_user.id, "auth_register", "users", new_user.id)
    return True, "Usuário registrado com sucesso!"

def recover_password(identifier):
    """
    Simula envio de recuperação. 
    Segurança: Mensagem genérica para evitar enumeração de usuários.
    """
    with managed_session() as session:
        user = session.query(User).filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()
        
        if user:
            # Em produção, aqui dispararíamos o e-mail/SMS real.
            # Por enquanto, logamos a solicitação para auditoria.
            log_action(user.id, "auth_recovery_requested", "users", user.id)
            
    # Retornamos sempre a mesma mensagem (Segurança contra Enumeração)
    return True, "Se os dados informados estiverem corretos, você receberá instruções de recuperação em instantes."

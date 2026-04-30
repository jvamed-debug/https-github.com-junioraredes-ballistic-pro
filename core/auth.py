from core.models import managed_session, User, log_action

def authenticate(username, password):
    with managed_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            # Expunge para usar o objeto fora da sessão
            session.expunge(user)
            # SEC-003: Log de login bem-sucedido
            log_action(user.id, "auth_login_success", "users", user.id)
            return user
        
        # SEC-003.5: Log de tentativa falha (Importante p/ detectar ataques)
        if user:
            log_action(user.id, "auth_login_failed", "users", user.id, new={"info": "Senha incorreta"})
        
    return None

def register_user(username, password, name, cpf, email, phone):
    with managed_session() as session:
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return False, "Dados informados já estão em uso ou são inválidos."

        new_user = User(username=username, name=name, cpf=cpf, email=email, phone=phone)
        new_user.set_password(password)
        session.add(new_user)
        session.commit() # Flush para obter ID
        # SEC-004: Log de registro
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

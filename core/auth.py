from datetime import datetime, timedelta

from core.models import managed_session, User, LoginAttempt, blind_index, log_action
from schemas import UserCreate

#  Limite de forca-bruta no servidor. Antes vivia em st.session_state (por
#  sessao), entao reconectar zerava a contagem. Agora e persistido.
#
#  Tradeoff conhecido do bloqueio por usuario: um atacante que saiba um login
#  pode trava-lo de proposito falhando N vezes. Por isso a janela e curta e
#  expira sozinha (15 min), e o limite e folgado o suficiente para nao pegar
#  um usuario legitimo que erra a senha algumas vezes. O bcrypt (lento por
#  design) ja limita a taxa real de tentativas.
LOCKOUT_THRESHOLD = 8
LOCKOUT_WINDOW = timedelta(minutes=15)


def _normalize_identifier(identifier):
    return (identifier or "").strip()[:150]


def record_failed_login(identifier):
    identifier = _normalize_identifier(identifier)
    if not identifier:
        return
    with managed_session() as db:
        db.add(LoginAttempt(identifier=identifier))
        #  Limpeza oportunista das tentativas ja fora da janela, para a tabela
        #  nao crescer sem limite.
        cutoff = datetime.utcnow() - LOCKOUT_WINDOW
        db.query(LoginAttempt).filter(LoginAttempt.timestamp < cutoff).delete()


def clear_login_attempts(identifier):
    identifier = _normalize_identifier(identifier)
    if not identifier:
        return
    with managed_session() as db:
        db.query(LoginAttempt).filter(LoginAttempt.identifier == identifier).delete()


def login_lock_remaining(identifier):
    """Segundos restantes de bloqueio para este login, ou 0 se liberado."""
    identifier = _normalize_identifier(identifier)
    if not identifier:
        return 0
    cutoff = datetime.utcnow() - LOCKOUT_WINDOW
    with managed_session() as db:
        #  So os timestamps, como valores simples, para nao segurar objetos ORM
        #  que ficariam detached ao fim da sessao.
        timestamps = [
            row[0] for row in db.query(LoginAttempt.timestamp).filter(
                LoginAttempt.identifier == identifier,
                LoginAttempt.timestamp >= cutoff,
            ).order_by(LoginAttempt.timestamp).all()
        ]
    if len(timestamps) < LOCKOUT_THRESHOLD:
        return 0
    #  Bloqueado ate a N-esima-mais-recente tentativa envelhecer para fora da
    #  janela.
    unlock_at = timestamps[-LOCKOUT_THRESHOLD] + LOCKOUT_WINDOW
    return max(0, int((unlock_at - datetime.utcnow()).total_seconds()))


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
        from sqlalchemy import or_
        conditions = [User.username == username]
        if email:
            #  Busca pelo blind index, nao pela coluna cifrada: o Fernet e
            #  nao-deterministico, entao `User.email == email` nunca casaria e
            #  a duplicata passaria batida.
            conditions.append(User.email_hash == blind_index(email))
        existing = session.query(User).filter(or_(*conditions)).first()
        if existing:
            return False, "Dados informados já estão em uso ou são inválidos."

        #  Grava o CPF ja normalizado (so digitos) — o mesmo valor que foi
        #  validado acima —, e nao a forma com pontos/tracos digitada.
        new_user = User(username=username, name=name, cpf=cpf_digits, email=email, phone=phone)
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
        #  Pelo blind index, pela mesma razao da checagem de duplicata: comparar
        #  contra a coluna cifrada nunca encontraria ninguem em producao.
        id_hash = blind_index(identifier)
        user = session.query(User).filter(
            (User.email_hash == id_hash) | (User.phone_hash == id_hash)
        ).first()

        if user:
            # Em produção, aqui dispararíamos o e-mail/SMS real.
            # Por enquanto, logamos a solicitação para auditoria.
            log_action(user.id, "auth_recovery_requested", "users", user.id)
            
    # Retornamos sempre a mesma mensagem (Segurança contra Enumeração)
    return True, "Se os dados informados estiverem corretos, você receberá instruções de recuperação em instantes."

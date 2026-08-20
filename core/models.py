from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float, Text, DateTime, event
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from contextlib import contextmanager
import bcrypt
import hashlib
import hmac
import json
import base64
import os
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String as SQLString
import streamlit as st

Base = declarative_base()


# ── Índice cego (blind index) para campos cifrados pesquisáveis ──
#
# O Fernet é NÃO-determinístico: o mesmo texto cifra de forma diferente a cada
# gravação. Isso torna impossível procurar por um campo cifrado (email == x
# nunca casa) e faz a constraint `unique` da coluna cifrada nunca disparar.
# Para email/telefone — que precisam ser únicos e pesquisáveis — guardamos, ao
# lado do valor cifrado, um HMAC-SHA256 determinístico do valor normalizado.
# O HMAC preserva a confidencialidade (não é reversível sem a chave) mas é
# estável, então serve de índice e de constraint de unicidade.
def _blind_index_key() -> bytes:
    raw = os.environ.get("BLIND_INDEX_KEY") or os.environ.get("FERNET_KEY")
    if not raw:
        try:
            raw = st.secrets.get("device_encryption_key")
        except Exception:
            raw = None
    if not raw:
        # Fallback de desenvolvimento: deterministico para os testes locais,
        # sem valor de seguranca (nao ha chave configurada nesse modo).
        raw = "ballistic-pro-dev-blind-index"
    if isinstance(raw, str):
        raw = raw.encode()
    #  Deriva uma chave dedicada a partir do material de chave, para nao
    #  reutilizar a chave de cifra diretamente.
    return hashlib.sha256(b"blind-index|" + raw).digest()


def blind_index(value):
    """HMAC determinístico de um valor, ou None se vazio.

    Normaliza (strip + lowercase) para que 'A@X.com' e 'a@x.com' colidam — o
    que é o comportamento correto para e-mail. A mesma normalização vale para
    escrita e busca, mantendo as duas consistentes.
    """
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    return hmac.new(_blind_index_key(), text.encode(), hashlib.sha256).hexdigest()

# Configuração de Criptografia (SG-001 / Auditoria SEC-002)
def get_encryption_suite():
    """Obtém suite de criptografia Fernet. Impede falha silenciosa em produção."""
    import os
    key_raw = None

    # 1. Tenta env var FERNET_KEY (Docker/EasyPanel)
    fernet_env = os.environ.get("FERNET_KEY")
    if fernet_env:
        try:
            return Fernet(fernet_env.encode() if isinstance(fernet_env, str) else fernet_env)
        except Exception:
            pass

    # 2. Tenta Streamlit Secrets (device_encryption_key)
    try:
        key_raw = st.secrets["device_encryption_key"]
    except (FileNotFoundError, KeyError):
        pass

    if key_raw is None:
        is_production = bool(fernet_env) or os.environ.get("DATABASE_URL", "").startswith("postgresql")
        try:
            is_production = is_production or "supabase" in st.secrets or st.secrets.get("environment") == "production"
        except (FileNotFoundError, KeyError):
            pass

        if is_production:
            raise RuntimeError(
                "[CRITICAL SECURITY] Chave de criptografia não encontrada em ambiente de produção. "
                "Configure FERNET_KEY ou device_encryption_key."
            )

        import warnings
        warnings.warn(
            "[SECURITY] Chave de criptografia não encontrada. "
            "Criptografia de PII desabilitada (MODO DESENVOLVIMENTO).",
            stacklevel=2
        )
        return None

    if isinstance(key_raw, str):
        key_raw = key_raw.encode()

    if len(key_raw) == 32:
        key_b64 = base64.urlsafe_b64encode(key_raw)
    else:
        import hashlib
        derived = hashlib.sha256(key_raw).digest()
        key_b64 = base64.urlsafe_b64encode(derived)
    return Fernet(key_b64)

class EncryptedString(TypeDecorator):
    """Criptografa dados sensíveis 'at rest'. Graceful degradation sem chave."""
    impl = SQLString
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        suite = get_encryption_suite()
        if suite is None:
            return value  # Sem criptografia — modo desenvolvimento
        return suite.encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        suite = get_encryption_suite()
        if suite is None:
            return value  # Sem criptografia — modo desenvolvimento
        try:
            return suite.decrypt(value.encode()).decode()
        except Exception:
            # Fallback para dados legados que ainda estão em texto plano
            return value

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    cpf = Column(EncryptedString) # PII Criptografado
    #  A coluna `email` guarda o valor cifrado (nao-deterministico), entao NAO
    #  leva `unique`: a constraint nunca dispararia. A unicidade e a busca
    #  ficam no `email_hash` (blind index), abaixo.
    email = Column(EncryptedString) # PII Criptografado
    email_hash = Column(String(64), unique=True, index=True) # HMAC de email p/ busca e unicidade
    phone = Column(EncryptedString)
    phone_hash = Column(String(64), index=True) # HMAC de telefone p/ busca (recuperacao)
    cr_number = Column(EncryptedString) # Certificado de Registro (Exército)
    cr_expiration = Column(Date) # Validade do CR
    address_acervo = Column(EncryptedString) # Endereço do Acervo
    is_premium = Column(Integer, default=0) # 0=Free, 1=Premium
    
    firearms = relationship("Firearm", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("ReloadSession", back_populates="user", cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    passkeys = relationship("WebAuthnCredential", back_populates="user", cascade="all, delete-orphan")
    dope_cards = relationship("DopeCard", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


#  Mantem email_hash/phone_hash sincronizados com email/phone em toda gravacao,
#  qualquer que seja o caminho (construtor, atribuicao de atributo). No momento
#  do evento, target.email ainda e o texto claro — a cifra so acontece no bind
#  do SQL —, entao e daqui que sai o HMAC. Sem isto, cada ponto que escreve um
#  email teria de lembrar de recalcular o hash, e um esquecido reabriria a
#  brecha de unicidade.
@event.listens_for(User, "before_insert")
@event.listens_for(User, "before_update")
def _sync_user_blind_indexes(mapper, connection, target):
    target.email_hash = blind_index(target.email)
    target.phone_hash = blind_index(target.phone)


class LoginAttempt(Base):
    """Tentativas de login malsucedidas, para limitar forca-bruta no servidor.

    O bloqueio antigo vivia em st.session_state (por sessao do Streamlit),
    entao bastava reconectar para zera-lo. Persistido no banco, o limite passa
    a valer entre sessoes.
    """
    __tablename__ = 'login_attempts'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(150), index=True, nullable=False)
    #  UTC ingenuo (nao-aware) para casar com o que o SQLite devolve na leitura
    #  e evitar comparacao aware-vs-naive nas queries de janela.
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class Firearm(Base):
    __tablename__ = 'firearms'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    model = Column(String, nullable=False)
    sigma = Column(EncryptedString)
    craf = Column(EncryptedString)
    serial = Column(EncryptedString)
    expiration = Column(Date)  # validade do CRAF
    image_url = Column(String) # URL para imagem no S3

    #  Acervo: separa o que e do proprio atirador do que pertence ao clube.
    collection = Column(String, default="pessoal")  # pessoal | clube
    #  GTS (Guia de Trafego): numero cifrado + validade + documento anexado.
    gts = Column(EncryptedString)
    gts_expiration = Column(Date)
    #  Documentos anexados (referencia/URL): CRAF e GTS digitalizados.
    craf_doc_url = Column(String)
    gts_doc_url = Column(String)

    owner = relationship("User", back_populates="firearms")
    sessions = relationship("ReloadSession", back_populates="firearm")

class ReloadSession(Base):
    __tablename__ = 'reload_sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    firearm_id = Column(Integer, ForeignKey('firearms.id'), nullable=True)
    date = Column(Date, nullable=False)
    
    caliber = Column(String, nullable=False)
    projectile = Column(String)
    powder = Column(String)
    charge = Column(Float)
    primer = Column(String)
    case = Column(String)
    quantity = Column(Integer)
    
    velocity_avg = Column(Float)
    velocity_sd = Column(Float)
    grouping_mm = Column(Float)
    image_url = Column(String) # URL para imagem do alvo no S3
    notes = Column(Text)
    
    user = relationship("User", back_populates="sessions")
    firearm = relationship("Firearm", back_populates="sessions")

class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    category = Column(String, nullable=False) # Polvora, Projetil, Espoleta, Estojo
    name = Column(String(100), nullable=False)
    batch_number = Column(String(50), nullable=True)
    expiration_date = Column(Date, nullable=True)
    quantity = Column(Float, default=0.0)
    unit = Column(String, nullable=False) # g, grains, un
    price_unit = Column(Float, default=0.0) # Preço por unidade (ou por g/grain/un)
    
    user = relationship("User", back_populates="inventory")

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(50), nullable=False) # firearm_added, firearm_deleted, firearm_updated
    table_name = Column(String(50))
    record_id = Column(Integer)
    old_value = Column(Text) # JSON string
    new_value = Column(Text) # JSON string
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="audit_logs")


class DopeCard(Base):
    """Cartao de DOPE salvo: a receita de tiro (projetil + arma + zero) que o
    atirador reusa. Vinculado opcionalmente a uma arma cadastrada. O vento e o
    angulo ficam de fora por serem situacionais — o que se guarda e o que nao
    muda de um dia para o outro.
    """
    __tablename__ = 'dope_cards'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    firearm_id = Column(Integer, ForeignKey('firearms.id'))
    name = Column(String, nullable=False)

    #  Projetil / carga.
    weight_grains = Column(Float)
    bc_g1 = Column(Float)
    muzzle_velocity_fps = Column(Float)
    diameter_mm = Column(Float)
    bullet_length_in = Column(Float)

    #  Arma / zero.
    zero_range_m = Column(Float)
    max_range_m = Column(Float)
    step_m = Column(Float)
    sight_height_cm = Column(Float)
    twist_rate_in = Column(Float)
    twist_dir = Column(String)

    #  Torre.
    unit = Column(String)
    click_value = Column(Float)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="dope_cards")
    firearm = relationship("Firearm")


class Activity(Base):
    """Habitualidade / competicao — a atividade de tiro que o CAC precisa
    comprovar. Diferente do ReloadSession (que registra a RECARGA): aqui o que
    importa e a pratica na raia, contabilizada por grupo de equipamento +
    calibre para atender a exigencia legal de frequencia.
    """
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    #  'treino' (habitualidade) ou 'competicao'.
    kind = Column(String, default="treino")
    #  Grupo de equipamento (Pistola, Revolver, Carabina, Espingarda, ...) e
    #  calibre — o par pelo qual as habitualidades sao contadas.
    category = Column(String, nullable=False)
    caliber = Column(String)
    firearm_id = Column(Integer, ForeignKey('firearms.id'))
    shots = Column(Integer, default=0)       # tiros disparados
    location = Column(String)                # clube / local
    value = Column(Float)                     # custo/valor da atividade (opcional)
    image_url = Column(String)               # comprovante/foto (opcional)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="activities")
    firearm = relationship("Firearm")


class Document(Base):
    """Documento do CAC guardado em pasta/categoria, com validade e lembrete.

    Cobre o que nao pertence a uma arma especifica (CR, filiacao a clube,
    apostilamentos, comprovantes, laudos) — o acervo cuida de CRAF/GTS por
    arma; aqui ficam os papeis pessoais e do clube, organizados por pasta.
    """
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    #  Pasta/categoria livre (CR, Clube, Apostilamento, Pessoal, ...).
    folder = Column(String, nullable=False, default="Geral")
    title = Column(String, nullable=False)
    number = Column(EncryptedString)         # numero do documento (sensivel)
    issue_date = Column(Date)                 # emissao
    expiration = Column(Date)                 # validade (dispara lembrete)
    #  Antecedencia, em dias, para lembrar da renovacao (default 30).
    remind_days = Column(Integer, default=30)
    file_url = Column(String)                 # link do digitalizado (opcional)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")


class Event(Base):
    """Evento/competicao de tiro na agenda do atirador.

    Uma agenda simples: o que vem por ai (competicoes, cursos, provas de
    nivel) com data e local, para nao perder inscricao nem prazo. Cada
    usuario ve so os seus.
    """
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    #  competicao | curso | prova | treino | outro
    kind = Column(String, default="competicao")
    location = Column(String)
    url = Column(String)                      # link de inscricao/regulamento
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="events")


class WebAuthnCredential(Base):
    """Passkey (WebAuthn) registrada por um usuario para login biometrico.

    Guardamos a chave PUBLICA da credencial — a privada nunca sai do
    autenticador do dispositivo (Face ID/Touch ID/chave de seguranca). O
    `sign_count` sobe a cada uso e serve para detectar clonagem do
    autenticador.
    """
    __tablename__ = 'webauthn_credentials'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    #  Identificador da credencial (base64url) — unico por passkey.
    credential_id = Column(String, unique=True, index=True, nullable=False)
    #  Chave publica COSE, em base64url.
    public_key = Column(String, nullable=False)
    sign_count = Column(Integer, default=0, nullable=False)
    transports = Column(String)  # JSON: ["internal","hybrid",...] (opcional)
    label = Column(String)       # nome amigavel do dispositivo (opcional)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="passkeys")


class WebAuthnChallenge(Base):
    """Desafio efemero de uma cerimonia WebAuthn (registro ou login).

    O desafio precisa sobreviver entre o passo 'begin' e o 'complete', que
    sao requests distintos. Guardado no banco (e nao em memoria) para
    funcionar mesmo com mais de um worker. Consumido e apagado no complete.
    """
    __tablename__ = 'webauthn_challenges'
    id = Column(Integer, primary_key=True)
    #  Chave de busca: "reg:{user_id}" no registro, "login:{username}" no login.
    key = Column(String, index=True, nullable=False)
    challenge = Column(String, nullable=False)  # base64url
    purpose = Column(String, nullable=False)    # 'register' | 'login'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Database setup

def create_db_engine():
    import os
    # Ordem de prioridade: Env Var -> Secrets -> SQLite local
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        try:
            if "database" in st.secrets:
                db_url = st.secrets["database"].get("url")
            elif "supabase" in st.secrets:
                db_url = st.secrets["supabase"].get("db_url")
        except Exception:
            pass

    if not db_url:
        db_url = 'sqlite:///ballistics.db'
        print("[INFO] Usando SQLite local.")
    else:
        # Suporte a postgres:// -> postgresql:// (necessário p/ SQLAlchemy 2.0+)
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        print(f"[INFO] Conectando ao banco de dados: {db_url.split('@')[-1]}")

    engine_args = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Adicionar timeout de conexão para PostgreSQL
    if "postgresql" in db_url:
        engine_args["connect_args"] = {"connect_timeout": 10}
    
    return create_engine(db_url, **engine_args)

# Initialize engine with resilience
engine = create_db_engine()

def ensure_schema_compliance(engine_to_check):
    """
    Garante que o esquema do banco de dados esteja atualizado.
    Refatorado p/ Auditoria TEC-001: Adicionado tratamento de erro granular e logs.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine_to_check)

    existing_tables = inspector.get_table_names()

    # 0. Colunas de blind index em users (bancos criados antes desta versao).
    #    create_all cria tabelas novas mas nao adiciona colunas a tabelas que
    #    ja existem, entao email_hash/phone_hash precisam de ALTER aqui.
    if 'users' in existing_tables:
        user_cols = [c['name'] for c in inspector.get_columns('users')]
        with engine_to_check.begin() as conn:
            for col_name in ('email_hash', 'phone_hash'):
                if col_name not in user_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} VARCHAR(64)"))
                        print(f"[SCHEMA] Coluna {col_name} adicionada a users.")
                    except Exception as e:
                        print(f"[SCHEMA] Falha ao adicionar {col_name}: {e}")

    # 1. Verificar Tabelas Críticas
    if 'inventory_items' not in existing_tables:
        return

    # 2. Executar Alterações p/ Tabela inventory_items
    columns = [c['name'] for c in inspector.get_columns('inventory_items')]
    
    with engine_to_check.begin() as conn:
        # Renomeação de price_total -> price_unit (Caso legado)
        if 'price_unit' not in columns and 'price_total' in columns:
            try:
                conn.execute(text("ALTER TABLE inventory_items RENAME COLUMN price_total TO price_unit"))
                print("[SCHEMA] Coluna price_total renomeada para price_unit.")
            except Exception as e:
                print(f"[SCHEMA] Erro ao renomear: {e}. Tentando Add Column fallback.")
                try:
                    conn.execute(text("ALTER TABLE inventory_items ADD COLUMN price_unit FLOAT DEFAULT 0.0"))
                except Exception:
                    pass

        # Adição de colunas ausentes
        for col_name, col_type in [('batch_number', 'VARCHAR(50)'), ('expiration_date', 'DATE')]:
            if col_name not in columns:
                try:
                    conn.execute(text(f"ALTER TABLE inventory_items ADD COLUMN {col_name} {col_type}"))
                    print(f"[SCHEMA] Coluna {col_name} adicionada a inventory_items.")
                except Exception as e:
                    print(f"[SCHEMA] Falha ao adicionar {col_name}: {e}")

        # 3. Verificar image_url em outras tabelas
        for table in ['firearms', 'reload_sessions']:
            if table in existing_tables:
                t_cols = [c['name'] for c in inspector.get_columns(table)]
                if 'image_url' not in t_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN image_url VARCHAR"))
                        print(f"[SCHEMA] Coluna image_url adicionada a {table}.")
                    except Exception as e:
                        print(f"[SCHEMA] Falha ao adicionar image_url a {table}: {e}")

        # 3b. Colunas do acervo em firearms (pessoal/clube, GTS e documentos).
        if 'firearms' in existing_tables:
            f_cols = [c['name'] for c in inspector.get_columns('firearms')]
            for col_name, col_type in [
                ('collection', "VARCHAR DEFAULT 'pessoal'"),
                ('gts', 'VARCHAR'),
                ('gts_expiration', 'DATE'),
                ('craf_doc_url', 'VARCHAR'),
                ('gts_doc_url', 'VARCHAR'),
            ]:
                if col_name not in f_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE firearms ADD COLUMN {col_name} {col_type}"))
                        print(f"[SCHEMA] Coluna {col_name} adicionada a firearms.")
                    except Exception as e:
                        print(f"[SCHEMA] Falha ao adicionar {col_name} a firearms: {e}")

        # 4. Verificar colunas de sessão de recarga (primer, case, velocity_sd)
        if 'reload_sessions' in existing_tables:
            rs_cols = [c['name'] for c in inspector.get_columns('reload_sessions')]
            for col_name, col_type in [('primer', 'VARCHAR'), ('case', 'VARCHAR'), ('velocity_sd', 'FLOAT')]:
                if col_name not in rs_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE reload_sessions ADD COLUMN \"{col_name}\" {col_type}"))
                        print(f"[SCHEMA] Coluna {col_name} adicionada a reload_sessions.")
                    except Exception as e:
                        print(f"[SCHEMA] Falha ao adicionar {col_name}: {e}")


# Try to create tables with fallback
try:
    Base.metadata.create_all(engine)
    ensure_schema_compliance(engine)
except Exception as e:
    print(f"[CRITICAL] Erro na conexão primária: {e}. Acionando Fallback SQLite.")
    engine = create_engine('sqlite:///ballistics.db', pool_pre_ping=True)
    Base.metadata.create_all(engine)
    ensure_schema_compliance(engine)
    st.warning("⚠️ Conexão com Banco Remoto falhou. Usando Banco Local temporariamente.")

Session = sessionmaker(bind=engine)

def get_session():
    return Session()


@contextmanager
def managed_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def log_action(user_id, action, table_name, record_id=None, old=None, new=None):
    """Auxiliar para disparar logs de auditoria."""
    with managed_session() as db:
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_value=json.dumps(old) if old else None,
            new_value=json.dumps(new) if new else None
        )
        db.add(log)


def backfill_blind_indexes():
    """Preenche email_hash/phone_hash de usuarios gravados antes desta versao.

    Carregar cada usuario pela ORM decifra email/phone; salvar de volta dispara
    o evento before_update, que recalcula os hashes. Roda so nos que ainda
    estao sem hash, entao e barato apos a primeira passada.
    """
    try:
        with managed_session() as db:
            pendentes = db.query(User).filter(
                User.email.isnot(None), User.email_hash.is_(None)
            ).all()
            for user in pendentes:
                user.email_hash = blind_index(user.email)
                user.phone_hash = blind_index(user.phone)
            if pendentes:
                print(f"[SCHEMA] Blind index preenchido para {len(pendentes)} usuario(s).")
    except Exception as e:
        print(f"[SCHEMA] Falha no backfill de blind index: {e}")


def init_db_if_empty():
    backfill_blind_indexes()
    session = get_session()
    try:
        if session.query(User).count() == 0:
            from datetime import date
            
            # M01: Bloqueio de Segurança em Produção
            import os as _os
            is_production = bool(_os.environ.get("FERNET_KEY")) or _os.environ.get("DATABASE_URL", "").startswith("postgresql")
            try:
                is_production = is_production or "supabase" in st.secrets or "device_encryption_key" in st.secrets
            except (FileNotFoundError, KeyError):
                pass
            
            # Busca senha na env var, no nível raiz dos secrets ou dentro de [passwords]
            admin_pass = _os.environ.get("ADMIN_PASSWORD")
            if not admin_pass:
                try:
                    admin_pass = st.secrets.get("admin_password")
                    if not admin_pass and "passwords" in st.secrets:
                        admin_pass = st.secrets["passwords"].get("admin_password")
                except (FileNotFoundError, KeyError):
                    admin_pass = None

            has_admin_secret = bool(admin_pass)
            
            if is_production and not has_admin_secret:
                print("[CRITICAL] Bloqueio de Segurança: Não foi possível criar admin padrão em produção sem 'admin_password' nos Secrets.")
                return

            if not admin_pass:
                admin_pass = "ballistic_admin_2025!"
            
            admin = User(
                username="atirador_pro",
                name="Atirador Demo",
                cpf="000.000.000-00",
                email="admin@ballisticpro.com",
                phone="(00) 00000-0000",
                cr_number="000000",
                cr_expiration=date(2030, 1, 1),
                is_premium=1
            )
            admin.set_password(admin_pass)
            session.add(admin)
            session.commit()
            print("Usuário padrão 'atirador_pro' criado.")
    except Exception as e:
        print(f"Erro na inicialização do Banco: {e}")
    finally:
        session.close()


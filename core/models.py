from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float, Text, DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from contextlib import contextmanager
import bcrypt
import json
import base64
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String as SQLString
import streamlit as st

Base = declarative_base()

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
    email = Column(EncryptedString, unique=True) # PII Criptografado
    phone = Column(EncryptedString)
    cr_number = Column(EncryptedString) # Certificado de Registro (Exército)
    cr_expiration = Column(Date) # Validade do CR
    address_acervo = Column(EncryptedString) # Endereço do Acervo
    is_premium = Column(Integer, default=0) # 0=Free, 1=Premium
    
    firearms = relationship("Firearm", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("ReloadSession", back_populates="user", cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Firearm(Base):
    __tablename__ = 'firearms'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    model = Column(String, nullable=False)
    sigma = Column(EncryptedString)
    craf = Column(EncryptedString)
    serial = Column(EncryptedString)
    expiration = Column(Date)
    image_url = Column(String) # URL para imagem no S3

    
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
    
    # 1. Verificar Tabelas Críticas
    existing_tables = inspector.get_table_names()
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


def init_db_if_empty():
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
            
            # Busca senha no nível raiz ou dentro de [passwords]
            admin_pass = st.secrets.get("admin_password")
            if not admin_pass and "passwords" in st.secrets:
                admin_pass = st.secrets["passwords"].get("admin_password")
            
            has_admin_secret = admin_pass is not None
            
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


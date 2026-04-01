from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from contextlib import contextmanager
import bcrypt

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    cpf = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    cr_number = Column(String) # Certificado de Registro (Exército)
    cr_expiration = Column(Date) # Validade do CR
    address_acervo = Column(String) # Endereço do Acervo
    is_premium = Column(Integer, default=0) # 0=Free, 1=Premium
    
    firearms = relationship("Firearm", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("ReloadSession", back_populates="user", cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Firearm(Base):
    __tablename__ = 'firearms'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    model = Column(String, nullable=False)
    sigma = Column(String)
    craf = Column(String)
    serial = Column(String)
    expiration = Column(Date)
    
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

# Database setup
import streamlit as st
import os

def create_db_engine():
    # Try to get DB URL from Streamlit Secrets (Production - Supabase)
    db_url = 'sqlite:///ballistics.db'
    try:
        if "supabase" in st.secrets and "db_url" in st.secrets["supabase"]:
            db_url = st.secrets["supabase"]["db_url"]
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
    except Exception as e:
        print(f"[WARN] Não foi possível ler secrets do Supabase ({e}). Usando SQLite local.")
    
    return create_engine(db_url)

# Initialize engine with resilience
engine = create_db_engine()

# Try to create tables, if it fails (e.g. remote DB unreachable), fallback to SQLite
try:
    Base.metadata.create_all(engine)
except Exception as e:
    st.warning("⚠️ Conexão com Banco Remoto falhou. Usando Banco de Dados Local.")
    engine = create_engine('sqlite:///ballistics.db')
    Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def get_session():
    """
    Retorna uma nova sessão do SQLAlchemy.
    Prefira usar `managed_session()` para garantir o fechamento da sessão.
    """
    return Session()

@contextmanager
def managed_session():
    """
    Context manager que garante o fechamento da sessão mesmo em caso de
    exceção ou interrupção por `st.rerun()`.

    Uso:
        with managed_session() as db:
            user = db.get(User, user_id)
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db_if_empty():
    """
    Inicializa o banco de dados com um usuário administrador padrão caso esteja vazio.
    """
    session = get_session()
    try:
        if session.query(User).count() == 0:
            from datetime import date
            # Carrega senha do admin via secrets (obrigatório em produção)
            try:
                admin_pass = st.secrets["admin_password"]
            except (KeyError, FileNotFoundError):
                admin_pass = "ballistic_admin_2025!"
                print("[WARN] 'admin_password' não definido em secrets.toml. Usando senha padrão local.")
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

